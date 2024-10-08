from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import logging
from postgresql_manager import postgres_manager
from redis_manager import redis_manager
from pydantic import BaseModel, Field
from connection_manager import ConnectionManager
from error_handlers import handle_error
from background_tasks import start_background_tasks, stop_background_tasks
import json
import asyncio

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()

# CORS 미들웨어 설정
# 클라이언트 사이드 애플리케이션이 API에 접근할 수 있도록 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],  # 로컬 개발 환경에서의 접근 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ConnectionManager 인스턴스 생성
# WebSocket 연결을 관리하는 객체
manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트 핸들러"""
    await postgres_manager.start()  # PostgreSQL 연결 시작
    await redis_manager.connect()  # Redis 연결 시작
    await redis_manager.redis.delete("active_connections")  # active_connections 초기화
    start_background_tasks(manager)  # 백그라운드 작업 시작

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트 핸들러"""
    await postgres_manager.stop()  # PostgreSQL 연결 종료
    await redis_manager.disconnect()  # Redis 연결 종료
    stop_background_tasks(manager)  # 백그라운드 작업 종료

class UserRegister(BaseModel):
    """사용자 등록을 위한 Pydantic 모델"""
    email: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    nickname: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/register")
@handle_error
async def register(user: UserRegister):
    """사용자 등록 엔드포인트"""
    success, message = await postgres_manager.register_user(user.username, user.password, user.email, user.nickname)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    login_success, login_result = await postgres_manager.login_user(user.username, user.password)
    if not login_success:
        raise HTTPException(status_code=400, detail="Registration successful, but auto-login failed")
    return {"message": "Registration and login successful", "user_id": login_result["user_id"], "username": user.username, "nickname": login_result["nickname"]}

class LoginData(BaseModel):
    """로그인을 위한 Pydantic 모델"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@app.post("/login")
@handle_error
async def login(login_data: LoginData):
    """로그인 엔드포인트"""
    success, result = await postgres_manager.login_user(login_data.username, login_data.password)
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return {"message": "Login successful", "user_id": result["user_id"], "username": login_data.username, "nickname": result["nickname"]}

class DuplicateCheckData(BaseModel):
    """중복 체크를 위한 Pydantic 모델"""
    email: str = Field(None, min_length=1)
    username: str = Field(None, min_length=1)
    nickname: str = Field(None, min_length=1)

@app.post("/check_duplicate")
@handle_error
async def check_duplicate(data: DuplicateCheckData):
    """중복 체크 엔드포인트"""
    if data.email:
        is_duplicate = await postgres_manager.check_duplicate('email', data.email)
        return {"isDuplicate": is_duplicate}
    elif data.username:
        is_duplicate = await postgres_manager.check_duplicate('username', data.username)
        return {"isDuplicate": is_duplicate}
    elif data.nickname:
        is_duplicate = await postgres_manager.check_duplicate('nickname', data.nickname)
        return {"isDuplicate": is_duplicate}
    else:
        raise HTTPException(status_code=400, detail="Invalid request")

@app.get("/recent_messages")
@handle_error
async def get_recent_messages(limit: int = 50):
    """최근 메시지를 가져오는 엔드포인트"""
    messages = await redis_manager.get_recent_messages(limit)
    return {"messages": messages}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket 연결을 처리하는 엔드포인트"""
    user = await postgres_manager.get_user_by_id(user_id)
    if not user:
        await websocket.close(code=4003)  # 유효하지 않은 사용자 ID
        logger.warning(f"Invalid user ID attempted to connect: {user_id}")
        return

    username = user['username']
    nickname = user['nickname']
    await manager.connect(websocket, user_id, username, nickname)

    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data['message'], user_id, username, nickname)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        await manager.disconnect(user_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)