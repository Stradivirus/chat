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

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str, sender_id: str, username: str):
        success = await postgres_manager.save_message(sender_id, message)
        if not success:
            logger.error(f"Failed to save message from {sender_id}")

        dead_connections = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json({
                    "message": message,
                    "sender": sender_id,
                    "username": username,
                    "timestamp": int(time.time() * 1000)
                })
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                dead_connections.append(user_id)
        
        for dead in dead_connections:
            self.disconnect(dead)

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
        manager.disconnect(user_id)
        await manager.broadcast(f"{username}님이 퇴장하셨습니다.", "system", "System")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)