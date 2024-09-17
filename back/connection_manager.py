# connection_manager.py

import asyncio
from fastapi import WebSocket
from typing import Dict, Set
from collections import defaultdict, deque
import json
import time
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=4))
        self.user_ban_until: Dict[str, float] = {}
        self.spam_window = 5
        self.spam_threshold = 4
        self.background_tasks: Set[asyncio.Task] = set()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id in self.active_connections:
            await self.disconnect_previous_session(user_id)
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

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

    async def broadcast(self, message: str, sender_id: str = None, username: str = None):
        if sender_id and username:
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
                    "time_left": 20
                })
                return

            message_data = {
                "message": message,
                "sender": sender_id,
                "username": username,
                "timestamp": int(time.time() * 1000)
            }
        else:
            try:
                message_data = json.loads(message)
            except json.JSONDecodeError:
                message_data = {"type": "system", "message": message}

        dead_connections = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message_data)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                dead_connections.append(user_id)

        for dead in dead_connections:
            await self.disconnect(dead)

    def is_spam(self, sender_id: str):
        if len(self.user_messages[sender_id]) < self.spam_threshold:
            return False
        current_time = time.time()
        oldest_message_time = self.user_messages[sender_id][0][1]
        if current_time - oldest_message_time <= self.spam_window:
            return all(msg == self.user_messages[sender_id][0][0] for msg, _ in self.user_messages[sender_id])
        return False

    def ban_user(self, user_id: str):
        self.user_ban_until[user_id] = time.time() + 20

    def is_user_banned(self, user_id: str) -> bool:
        if user_id in self.user_ban_until:
            if time.time() >= self.user_ban_until[user_id]:
                del self.user_ban_until[user_id]
                self.user_messages[user_id].clear()
                return False
            return True
        return False