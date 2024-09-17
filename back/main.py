from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import json
import asyncio
import logging
from postgresql_manager import postgres_manager
from pydantic import BaseModel, Field
import uuid
import time
from collections import defaultdict, deque

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=4))
        self.user_ban_until: Dict[str, float] = {}
        self.spam_window = 5  # 5초 동안의 메시지를 검사
        self.spam_threshold = 4  # 5초 동안 4개 이상의 동일 메시지를 스팸으로 간주
        self.user_count_task = None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id in self.active_connections:
            await self.disconnect_previous_session(user_id)
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
        if self.user_count_task is None:
            self.user_count_task = asyncio.create_task(self.periodic_user_count_update())

    async def disconnect_previous_session(self, user_id: str):
        if user_id in self.active_connections:
            prev_websocket = self.active_connections[user_id]
            await prev_websocket.send_json({"type": "session_expired"})
            await prev_websocket.close()
            del self.active_connections[user_id]
            logger.info(f"Previous session for user {user_id} disconnected")

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
        if len(self.active_connections) == 0 and self.user_count_task:
            self.user_count_task.cancel()
            self.user_count_task = None

    async def broadcast(self, message: str, sender_id: str, username: str):
        if self.is_user_banned(sender_id):
            ban_time_left = int(self.user_ban_until[sender_id] - time.time())
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": ban_time_left
            })
            return

        current_time = time.time()
        self.user_messages[sender_id].append((message, current_time))

        if self.is_spam(sender_id):
            self.ban_user(sender_id)
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": 20  # 20초 밴
            })
            return

        success = await postgres_manager.save_message(sender_id, message)
        if not success:
            logger.error(f"Failed to save message from {sender_id}")

        await self.broadcast_to_all(json.dumps({
            "message": message,
            "sender": sender_id,
            "username": username,
            "timestamp": int(time.time() * 1000)
        }))

    def is_spam(self, sender_id: str):
        if len(self.user_messages[sender_id]) < self.spam_threshold:
            return False
        
        current_time = time.time()
        oldest_message_time = self.user_messages[sender_id][0][1]
        
        if current_time - oldest_message_time <= self.spam_window:
            return all(msg == self.user_messages[sender_id][0][0] for msg, _ in self.user_messages[sender_id])
        
        return False

    def ban_user(self, user_id: str):
        self.user_ban_until[user_id] = time.time() + 20  # 20초 밴

    async def broadcast_to_all(self, message: str):
        dead_connections = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                dead_connections.append(user_id)
        
        for dead in dead_connections:
            await self.disconnect(dead)

    def is_user_banned(self, user_id: str) -> bool:
        if user_id in self.user_ban_until:
            if time.time() >= self.user_ban_until[user_id]:
                del self.user_ban_until[user_id]
                self.user_messages[user_id].clear()  # 밴 해제 시 메시지 기록 초기화
                return False
            return True
        return False

    async def periodic_user_count_update(self):
        while True:
            await asyncio.sleep(1)  # 1초 대기
            count = len(self.active_connections)
            await self.broadcast_to_all(json.dumps({"type": "user_count", "count": count}))

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    await postgres_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    await postgres_manager.stop()

class UserRegister(BaseModel):
    email: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    nickname: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/register")
async def register(user: UserRegister):
    logger.info(f"Register attempt for user: {user.username}")
    success, message = await postgres_manager.register_user(user.username, user.password, user.email, user.nickname)
    if not success:
        logger.warning(f"Registration failed for user {user.username}: {message}")
        raise HTTPException(status_code=400, detail=message)
    logger.info(f"Registration successful for user: {user.username}")
    # 회원가입 성공 후 자동 로그인
    login_success, login_result = await postgres_manager.login_user(user.username, user.password)
    if not login_success:
        raise HTTPException(status_code=400, detail="Registration successful, but auto-login failed")
    return {"message": "Registration and login successful", "user_id": login_result, "username": user.username}

class LoginData(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/login")
async def login(login_data: LoginData):
    logger.info(f"Login attempt for user: {login_data.username}")
    success, result = await postgres_manager.login_user(login_data.username, login_data.password)
    if not success:
        logger.warning(f"Login failed for user {login_data.username}: {result}")
        raise HTTPException(status_code=400, detail=result)
    logger.info(f"Login successful for user: {login_data.username}")
    return {"message": "Login successful", "user_id": result, "username": login_data.username}

@app.get("/recent_messages")
async def get_recent_messages(limit: int = 50):
    messages = await postgres_manager.get_recent_messages(limit)
    return {"messages": messages}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    user = await postgres_manager.get_user_by_id(user_id)
    if not user:
        await websocket.close(code=4000)
        return
    
    username = user['username']
    await manager.connect(websocket, user_id)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message_data = json.loads(data)
                message = message_data.get("message")
                
                if message:
                    await manager.broadcast(message, user_id, username)
                else:
                    logger.warning(f"Invalid message format from user {user_id}")
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
            except Exception as e:
                logger.error(f"Unexpected error with user {user_id}: {e}")
                break
    finally:
        await manager.disconnect(user_id)
        await manager.broadcast(f"{username}님이 퇴장하셨습니다.", "system", "System")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)