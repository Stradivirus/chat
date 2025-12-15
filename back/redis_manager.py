import redis.asyncio as redis
import json
import time
import os
from typing import List, Dict

class RedisManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        """Redis 서버에 연결하는 메서드"""
        redis_url = os.getenv('REDIS_URL', "redis://localhost")
        self.redis = await redis.from_url(redis_url)

    async def disconnect(self):
        """Redis 연결을 종료하는 메서드"""
        if self.redis is not None:
            await self.redis.close()

    async def add_message(self, sender_id: str, message: str, username: str, nickname: str):
        """새 메시지를 Redis에 추가하는 메서드"""
        # 메시지 데이터 구성
        message_data = {
            "content": message,
            "sender_id": sender_id,
            "username": username,
            "nickname": nickname,
            "timestamp": time.time()
        }
        
        # 전체 메시지 저장 (최근 20개 유지 - 사용자 요청 반영)
        # 리스트에 넣고 바로 trim하여 20개만 남김
        await self.redis.lpush("all_messages", json.dumps(message_data))
        await self.redis.ltrim("all_messages", 0, 19)

    async def get_recent_messages(self, limit: int = 20) -> List[Dict]:
        """최근 메시지를 가져오는 메서드"""
        # 'all_messages' 리스트에서 지정된 개수만큼 가져옴 (최대 20개)
        messages = await self.redis.lrange("all_messages", 0, limit - 1)
        # JSON 문자열을 파이썬 딕셔너리로 변환하여 반환
        return [json.loads(msg) for msg in messages]

    async def add_active_connection(self, sender_id: str):
        """활성 연결을 추가하는 메서드"""
        await self.redis.sadd("active_connections", sender_id)

    async def remove_active_connection(self, sender_id: str):
        """활성 연결을 제거하는 메서드"""
        await self.redis.srem("active_connections", sender_id)

    async def get_active_connections_count(self) -> int:
        """활성 연결 수를 가져오는 메서드"""
        return await self.redis.scard("active_connections")

# RedisManager 인스턴스 생성
redis_manager = RedisManager()