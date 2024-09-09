from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio
import time

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str, sender_id: str):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "message": message,
                    "sender": sender_id,
                    "timestamp": int(time.time() * 1000)
                })
            except RuntimeError:
                dead_connections.append(connection)
            except Exception as e:
                print(f"Error sending message: {e}")
                dead_connections.append(connection)
        
        # Remove dead connections
        for dead in dead_connections:
            self.active_connections.remove(dead)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                message_data = json.loads(data)
                message = message_data.get("message") or message_data.get("text") or data
                await manager.broadcast(message, client_id)
            except asyncio.TimeoutError:
                # This is just to allow checking the connection periodically
                pass
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                await manager.broadcast(f"Client #{client_id} left the chat", "system")
                break
            except Exception as e:
                print(f"Error: {e}")
                break
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)