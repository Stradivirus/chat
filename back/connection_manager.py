from fastapi import WebSocket
from typing import Dict, Set
from collections import defaultdict, deque
import json
import time
import logging
import asyncio
from redis_manager import redis_manager

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=4))
        self.user_ban_until: Dict[str, float] = {}
        self.spam_window = 5
        self.spam_threshold = 4
        self.background_tasks: Set = set()
        self.user_count = 0

    async def connect(self, websocket: WebSocket, sender_id: str, username: str):
        await websocket.accept()
        if sender_id in self.active_connections:
            await self.disconnect_previous_session(sender_id)
        self.active_connections[sender_id] = websocket
        await redis_manager.add_active_connection(sender_id)
        logger.info(f"User {username} (ID: {sender_id}) connected. Total connections: {len(self.active_connections)}")
        await self.send_user_count_update(websocket)

    async def disconnect_previous_session(self, sender_id: str):
        if sender_id in self.active_connections:
            prev_websocket = self.active_connections[sender_id]
            await prev_websocket.send_json({"type": "session_expired"})
            await prev_websocket.close()
            del self.active_connections[sender_id]
            await redis_manager.remove_active_connection(sender_id)
            logger.info(f"Previous session for user {sender_id} disconnected")

    async def disconnect(self, sender_id: str):
        if sender_id in self.active_connections:
            del self.active_connections[sender_id]
            await redis_manager.remove_active_connection(sender_id)
            logger.info(f"User {sender_id} disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str, sender_id: str, username: str):
        if await self.is_user_banned(sender_id):
            ban_time_left = int(self.user_ban_until[sender_id] - time.time())
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": ban_time_left
            })
            return

        current_time = time.time()
        self.user_messages[sender_id].append((message, current_time))
        if self.is_spam(sender_id):
            await self.ban_user(sender_id)
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": 20
            })
            return

        message_data = {
            "type": "chat",
            "message": message,
            "sender_id": sender_id,
            "username": username,
            "timestamp": int(current_time * 1000)
        }
        await redis_manager.publish_message("chat", json.dumps(message_data))

    def is_spam(self, sender_id: str):
        if len(self.user_messages[sender_id]) < self.spam_threshold:
            return False
        current_time = time.time()
        oldest_message_time = self.user_messages[sender_id][0][1]
        if current_time - oldest_message_time <= self.spam_window:
            return all(msg == self.user_messages[sender_id][0][0] for msg, _ in self.user_messages[sender_id])
        return False

    async def ban_user(self, sender_id: str):
        ban_duration = 20
        self.user_ban_until[sender_id] = time.time() + ban_duration
        await redis_manager.add_user_to_ban_list(sender_id, ban_duration)

    async def is_user_banned(self, sender_id: str) -> bool:
        if sender_id in self.user_ban_until:
            if time.time() >= self.user_ban_until[sender_id]:
                del self.user_ban_until[sender_id]
                self.user_messages[sender_id].clear()
                return False
            return True
        return await redis_manager.is_user_banned(sender_id)

    async def handle_redis_messages(self):
        pubsub = await redis_manager.subscribe("chat")
        while True:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message is not None and message['type'] == 'message':
                    message_data = json.loads(message['data'])
                    for sender_id, connection in list(self.active_connections.items()):
                        try:
                            await connection.send_json(message_data)
                        except Exception as e:
                            logger.error(f"Error sending message to user {sender_id}: {e}")
                            await self.disconnect(sender_id)
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in Redis message handling: {e}")
                await asyncio.sleep(1)  # Wait before trying to reconnect

    async def start_redis_listener(self):
        self.background_tasks.add(asyncio.create_task(self.handle_redis_messages()))

    def stop_redis_listener(self):
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()

    def update_user_count(self, count: int):
        self.user_count = count

    async def send_user_count_update(self, websocket: WebSocket):
        await websocket.send_json({"type": "user_count", "count": self.user_count})