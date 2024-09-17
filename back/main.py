# 필요한 모듈들을 임포트합니다.
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Set
import json
import asyncio
import logging
from postgresql_manager import postgres_manager
from pydantic import BaseModel, Field
import uuid
import time
from collections import defaultdict, deque

# FastAPI 애플리케이션을 생성합니다.
app = FastAPI()

# CORS 설정을 추가합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진을 허용합니다.
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드를 허용합니다.
    allow_headers=["*"],  # 모든 헤더를 허용합니다.
)

# 로깅을 설정합니다.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # 활성 연결을 저장하는 딕셔너리입니다.
        self.active_connections: Dict[str, WebSocket] = {}
        # 사용자별 메시지 기록을 저장하는 딕셔너리입니다.
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=4))
        # 사용자 밴 정보를 저장하는 딕셔너리입니다.
        self.user_ban_until: Dict[str, float] = {}
        # 스팸 감지를 위한 설정입니다.
        self.spam_window = 5  # 5초 동안의 메시지를 검사합니다.
        self.spam_threshold = 4  # 5초 동안 4개 이상의 동일 메시지를 스팸으로 간주합니다.
        # 백그라운드 태스크를 저장하는 집합입니다.
        self.background_tasks: Set[asyncio.Task] = set()

    async def connect(self, websocket: WebSocket, user_id: str):
        # 웹소켓 연결을 수락합니다.
        await websocket.accept()
        # 이전 세션이 있다면 연결을 해제합니다.
        if user_id in self.active_connections:
            await self.disconnect_previous_session(user_id)
        # 새 연결을 저장합니다.
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
        # 백그라운드 태스크가 없다면 시작합니다.
        if not self.background_tasks:
            self.start_background_tasks()

    async def disconnect_previous_session(self, user_id: str):
        # 이전 세션이 있다면 연결을 해제합니다.
        if user_id in self.active_connections:
            prev_websocket = self.active_connections[user_id]
            await prev_websocket.send_json({"type": "session_expired"})
            await prev_websocket.close()
            del self.active_connections[user_id]
            logger.info(f"Previous session for user {user_id} disconnected")

    async def disconnect(self, user_id: str):
        # 사용자 연결을 해제합니다.
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
        # 모든 연결이 해제되면 백그라운드 태스크를 중지합니다.
        if len(self.active_connections) == 0:
            self.stop_background_tasks()

    async def broadcast(self, message: str, sender_id: str, username: str):
        # 사용자가 밴 상태인지 확인합니다.
        if self.is_user_banned(sender_id):
            ban_time_left = int(self.user_ban_until[sender_id] - time.time())
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": ban_time_left
            })
            return

        # 메시지를 기록하고 스팸인지 검사합니다.
        current_time = time.time()
        self.user_messages[sender_id].append((message, current_time))
        if self.is_spam(sender_id):
            self.ban_user(sender_id)
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": 20  # 20초 밴
            })
            return

        # 메시지 저장을 백그라운드 태스크로 실행합니다.
        asyncio.create_task(self.save_message_to_db(sender_id, message))
        # 모든 사용자에게 메시지를 브로드캐스트합니다.
        await self.broadcast_to_all(json.dumps({
            "message": message,
            "sender": sender_id,
            "username": username,
            "timestamp": int(time.time() * 1000)
        }))

    def is_spam(self, sender_id: str):
        # 스팸 여부를 검사합니다.
        if len(self.user_messages[sender_id]) < self.spam_threshold:
            return False
        current_time = time.time()
        oldest_message_time = self.user_messages[sender_id][0][1]
        if current_time - oldest_message_time <= self.spam_window:
            return all(msg == self.user_messages[sender_id][0][0] for msg, _ in self.user_messages[sender_id])
        return False

    def ban_user(self, user_id: str):
        # 사용자를 밴 상태로 설정합니다.
        self.user_ban_until[user_id] = time.time() + 20  # 20초 밴

    async def broadcast_to_all(self, message: str):
        # 모든 연결된 사용자에게 메시지를 전송합니다.
        dead_connections = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                dead_connections.append(user_id)
        # 죽은 연결을 정리합니다.
        for dead in dead_connections:
            await self.disconnect(dead)

    def is_user_banned(self, user_id: str) -> bool:
        # 사용자가 밴 상태인지 확인합니다.
        if user_id in self.user_ban_until:
            if time.time() >= self.user_ban_until[user_id]:
                del self.user_ban_until[user_id]
                self.user_messages[user_id].clear()  # 밴 해제 시 메시지 기록 초기화
                return False
            return True
        return False

    async def periodic_user_count_update(self):
        # 주기적으로 연결된 사용자 수를 업데이트합니다.
        while True:
            count = len(self.active_connections)
            await self.broadcast_to_all(json.dumps({"type": "user_count", "count": count}))
            await asyncio.sleep(1)  # 1초 대기

    async def cleanup_old_data(self):
        # 오래된 데이터를 정리합니다.
        while True:
            current_time = time.time()
            for user_id in list(self.user_messages.keys()):
                if not self.user_messages[user_id] or current_time - self.user_messages[user_id][-1][1] > 3600:  # 1시간
                    del self.user_messages[user_id]
                if user_id in self.user_ban_until:
                    del self.user_ban_until[user_id]
            await asyncio.sleep(3600)  # 1시간마다 실행

    async def check_connections(self):
        # 연결 상태를 확인합니다.
        while True:
            for user_id, connection in list(self.active_connections.items()):
                try:
                    await connection.send_json({"type": "ping"})
                except Exception:
                    await self.disconnect(user_id)
            await asyncio.sleep(60)  # 60초마다 실행

    def start_background_tasks(self):
        # 백그라운드 태스크를 시작합니다.
        self.background_tasks.add(asyncio.create_task(self.periodic_user_count_update()))
        self.background_tasks.add(asyncio.create_task(self.cleanup_old_data()))
        self.background_tasks.add(asyncio.create_task(self.check_connections()))

    def stop_background_tasks(self):
        # 백그라운드 태스크를 중지합니다.
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()

    async def save_message_to_db(self, sender_id: str, message: str):
        # 메시지를 데이터베이스에 저장합니다.
        try:
            await postgres_manager.save_message(sender_id, message)
        except Exception as e:
            logger.error(f"Failed to save message from {sender_id}: {e}")

# ConnectionManager 인스턴스를 생성합니다.
manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    # 애플리케이션 시작 시 PostgreSQL 연결을 초기화합니다.
    await postgres_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    # 애플리케이션 종료 시 PostgreSQL 연결을 종료하고 백그라운드 태스크를 중지합니다.
    await postgres_manager.stop()
    manager.stop_background_tasks()

class UserRegister(BaseModel):
    # 사용자 등록을 위한 Pydantic 모델입니다.
    email: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    nickname: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/register")
async def register(user: UserRegister):
    # 사용자 등록 엔드포인트입니다.
    logger.info(f"Register attempt for user: {user.username}")
    success, message = await postgres_manager.register_user(user.username, user.password, user.email, user.nickname)
    if not success:
        logger.warning(f"Registration failed for user {user.username}: {message}")
        raise HTTPException(status_code=400, detail=message)
    logger.info(f"Registration successful for user: {user.username}")
    # 회원가입 성공 후 자동 로그인을 수행합니다.
    login_success, login_result = await postgres_manager.login_user(user.username, user.password)
    if not login_success:
        raise HTTPException(status_code=400, detail="Registration successful, but auto-login failed")
    return {"message": "Registration and login successful", "user_id": login_result, "username": user.username}

class LoginData(BaseModel):
    # 로그인을 위한 Pydantic 모델입니다.
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/login")
async def login(login_data: LoginData):
    # 로그인 엔드포인트입니다.
    logger.info(f"Login attempt for user: {login_data.username}")
    success, result = await postgres_manager.login_user(login_data.username, login_data.password)
    if not success:
        logger.warning(f"Login failed for user {login_data.username}: {result}")
        raise HTTPException(status_code=400, detail=result)
    logger.info(f"Login successful for user: {login_data.username}")
    return {"message": "Login successful", "user_id": result, "username": login_data.username}

@app.get("/recent_messages")
async def get_recent_messages(limit: int = 50):
    # 최근 메시지를 조회하는 엔드포인트입니다.
    messages = await postgres_manager.get_recent_messages(limit)
    return {"messages": messages}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # 웹소켓 연결을 처리하는 엔드포인트입니다.
    user = await postgres_manager.get_user_by_id(user_id)
    if not user:
        await websocket.close(code=4000)
        return

    username = user['username']
    await manager.connect(websocket, user_id)

    try:
        while True:
            try:
                # 클라이언트로부터 메시지를 받습니다.
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message_data = json.loads(data)
                message = message_data.get("message")
                if message:
                    await manager.broadcast(message, user_id, username)
                else:
                    logger.warning(f"Invalid message format from user {user_id}")
            except asyncio.TimeoutError:
                # 60초 동안 메시지가 없으면 ping을 보냅니다.
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
            except Exception as e:
                logger.error(f"Unexpected error with user {user_id}: {e}")
                break
    finally:
        # 연결이 종료되면 정리 작업을 수행합니다.
        await manager.disconnect(user_id)
        await manager.broadcast(f"{username}님이 퇴장하셨습니다.", "system", "System")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)