# main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Set
import logging
from postgresql_manager import postgres_manager
from pydantic import BaseModel, Field
from connection_manager import ConnectionManager
from error_handlers import handle_error
from background_tasks import start_background_tasks, stop_background_tasks
import json

# FastAPI 애플리케이션 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ConnectionManager 인스턴스 생성
manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    await postgres_manager.start()
    start_background_tasks(manager)

@app.on_event("shutdown")
async def shutdown_event():
    await postgres_manager.stop()
    stop_background_tasks(manager)

class UserRegister(BaseModel):
    email: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    nickname: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/register")
@handle_error
async def register(user: UserRegister):
    success, message = await postgres_manager.register_user(user.username, user.password, user.email, user.nickname)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    login_success, login_result = await postgres_manager.login_user(user.username, user.password)
    if not login_success:
        raise HTTPException(status_code=400, detail="Registration successful, but auto-login failed")
    return {"message": "Registration and login successful", "user_id": login_result, "username": user.username}

class LoginData(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/login")
@handle_error
async def login(login_data: LoginData):
    success, result = await postgres_manager.login_user(login_data.username, login_data.password)
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return {"message": "Login successful", "user_id": result, "username": login_data.username}

@app.get("/recent_messages")
@handle_error
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
                data = await websocket.receive_json()
                await manager.broadcast(data['message'], user_id, username)
            except WebSocketDisconnect:
                break
    finally:
        await manager.disconnect(user_id)
        await manager.broadcast(json.dumps({"type": "system", "message": f"{username}님이 퇴장하셨습니다."}), "system", "System")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)