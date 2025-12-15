from fastapi import WebSocket
from typing import Dict, Set
from collections import defaultdict, deque
import json
import time
import logging
import asyncio
from redis_manager import redis_manager
from postgresql_manager import postgres_manager  # DB 저장을 위해 추가

# 로깅 설정
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # 활성 웹소켓 연결을 저장하는 딕셔너리
        self.active_connections: Dict[str, WebSocket] = {}
        # 사용자별 최근 메시지를 저장하는 딕셔너리 (최대 4개)
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=4))
        # 사용자 차단 정보를 저장하는 딕셔너리
        self.user_ban_until: Dict[str, float] = {}
        # 사용자 닉네임을 저장하는 딕셔너리
        self.user_nicknames: Dict[str, str] = {}
        # 스팸 감지를 위한 설정
        self.spam_window = 5
        self.spam_threshold = 4
        # 백그라운드 태스크를 저장하는 집합
        self.background_tasks: Set = set()

    async def connect(self, websocket: WebSocket, sender_id: str, username: str, nickname: str):
        """새로운 웹소켓 연결을 처리하는 메서드"""
        await websocket.accept()
        if sender_id in self.active_connections:
            await self.disconnect_previous_session(sender_id)
        
        self.active_connections[sender_id] = websocket
        self.user_nicknames[sender_id] = nickname
        await redis_manager.add_active_connection(sender_id)
        
        logger.info(f"User {username} connected. Total: {len(self.active_connections)}")
        await self.send_user_count_update(websocket)

    async def disconnect_previous_session(self, sender_id: str):
        """이전 세션을 종료하는 메서드"""
        if sender_id in self.active_connections:
            prev_websocket = self.active_connections[sender_id]
            try:
                await prev_websocket.send_json({"type": "session_expired"})
                await prev_websocket.close()
            except Exception as e:
                logger.error(f"Error closing previous session: {e}")
            
            if sender_id in self.active_connections:
                del self.active_connections[sender_id]
            
            await redis_manager.remove_active_connection(sender_id)

    async def disconnect(self, sender_id: str):
        """웹소켓 연결을 종료하는 메서드"""
        if sender_id in self.active_connections:
            del self.active_connections[sender_id]
            if sender_id in self.user_nicknames:
                del self.user_nicknames[sender_id]
            await redis_manager.remove_active_connection(sender_id)
            logger.info(f"User {sender_id} disconnected.")

    async def broadcast(self, message: str, sender_id: str, username: str, nickname: str):
        """메시지를 브로드캐스트하고 저장하는 메서드"""
        # 1. 차단 체크
        if await self.is_user_banned(sender_id):
            ban_time_left = int(self.user_ban_until[sender_id] - time.time())
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": ban_time_left
            })
            return

        current_time = time.time()
        
        # 2. 스팸 체크
        self.user_messages[sender_id].append((message, current_time))
        if self.is_spam(sender_id):
            await self.ban_user(sender_id)
            await self.active_connections[sender_id].send_json({
                "type": "chat_banned",
                "time_left": 20
            })
            return

        # 3. 메시지 전송 준비
        message_data = {
            "type": "chat",
            "message": message,
            "sender_id": sender_id,
            "username": username,
            "nickname": nickname,
            "timestamp": int(current_time * 1000)
        }

        # 4. Redis 저장 (최근 20개 유지용)
        await redis_manager.add_message(sender_id, message, username, nickname)
        
        # 5. DB 직접 저장 (영구 보관용) - 비동기로 실행하여 응답 지연 방지
        # asyncio.create_task를 사용하여 브로드캐스팅을 기다리지 않고 백그라운드에서 저장
        asyncio.create_task(postgres_manager.save_message(sender_id, message, nickname))

        # 6. 클라이언트 전송
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message_data)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

    def is_spam(self, sender_id: str):
        """스팸 메시지 여부를 판단하는 메서드"""
        if len(self.user_messages[sender_id]) < self.spam_threshold:
            return False
        current_time = time.time()
        oldest_message_time = self.user_messages[sender_id][0][1]
        if current_time - oldest_message_time <= self.spam_window:
            return all(msg == self.user_messages[sender_id][0][0] for msg, _ in self.user_messages[sender_id])
        return False

    async def ban_user(self, sender_id: str):
        """사용자를 일시적으로 차단하는 메서드"""
        self.user_ban_until[sender_id] = time.time() + 20

    async def is_user_banned(self, sender_id: str) -> bool:
        """사용자의 차단 여부를 확인하는 메서드"""
        if sender_id in self.user_ban_until:
            if time.time() >= self.user_ban_until[sender_id]:
                del self.user_ban_until[sender_id]
                self.user_messages[sender_id].clear()
                return False
            return True
        return False

    async def send_user_count_update(self, websocket: WebSocket):
        """현재 접속자 수를 전송"""
        user_count = await redis_manager.get_active_connections_count()
        await websocket.send_json({"type": "user_count", "count": user_count})

    async def check_connections(self):
        """연결 상태 주기적 확인"""
        while True:
            try:
                for sender_id, connection in list(self.active_connections.items()):
                    try:
                        await connection.send_json({"type": "ping"})
                    except Exception:
                        await self.disconnect(sender_id)
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Connection check error: {e}")
                await asyncio.sleep(5)

    async def cleanup_old_data(self):
        """오래된 메모리 데이터 정리"""
        while True:
            try:
                current_time = time.time()
                for sender_id in list(self.user_messages.keys()):
                    if not self.user_messages[sender_id] or current_time - self.user_messages[sender_id][-1][1] > 3600:
                        del self.user_messages[sender_id]
                    if sender_id in self.user_ban_until and current_time >= self.user_ban_until[sender_id]:
                        del self.user_ban_until[sender_id]
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(60)

    def start_background_tasks(self):
        """백그라운드 태스크 시작"""
        self.background_tasks.add(asyncio.create_task(self.check_connections()))
        self.background_tasks.add(asyncio.create_task(self.cleanup_old_data()))

    def stop_background_tasks(self):
        """백그라운드 태스크 종료"""
        for task in self.background_tasks:
            task.cancel()
        self.background_tasks.clear()