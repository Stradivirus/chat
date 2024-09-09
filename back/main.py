from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import json
import asyncio
import time
import logging
from kafka_user import kafka_user_manager

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 환경에서는 구체적인 오리진을 지정해야 합니다
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str, sender_id: str):
        dead_connections = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json({
                    "message": message,
                    "sender": sender_id,
                    "timestamp": int(time.time() * 1000)
                })
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                dead_connections.append(client_id)
        
        # Remove dead connections
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    await kafka_user_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    await kafka_user_manager.stop()

@app.post("/register")
async def register(username: str, password: str):
    success, message = await kafka_user_manager.register_user(username, password)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.post("/login")
async def login(username: str, password: str):
    success, result = kafka_user_manager.login_user(username, password)
    if not success:
        raise HTTPException(status_code=400, detail=result)
    return {"message": "Login successful", "user_id": result}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message_data = json.loads(data)
                message = message_data.get("message") or message_data.get("text") or data
                await manager.broadcast(message, client_id)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from client {client_id}")
            except Exception as e:
                logger.error(f"Unexpected error with client {client_id}: {e}")
                break
    finally:
        manager.disconnect(client_id)
        await manager.broadcast(f"Client #{client_id} left the chat", "system")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)