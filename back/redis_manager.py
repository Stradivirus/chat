import redis.asyncio as redis
import json
import time
from typing import List, Dict

class RedisManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        """Redis 서버에 연결하는 메서드"""
        self.redis = await redis.from_url("redis://localhost")

    async def disconnect(self):
        """Redis 연결을 종료하는 메서드"""
        if self.redis is not None:
            await self.redis.close()

    async def add_message(self, sender_id: str, message: str, username: str):
        """새 메시지를 Redis에 추가하는 메서드"""
        message_data = {
            "content": message,
            "sender_id": sender_id,
            "username": username,
            "timestamp": time.time()
        }
        # 사용자별 메시지 저장 (최근 50개)
        await self.redis.lpush(f"user:{sender_id}:messages", json.dumps(message_data))
        await self.redis.ltrim(f"user:{sender_id}:messages", 0, 49)
        
        # 전체 메시지 저장 (최근 500개)
        await self.redis.lpush("all_messages", json.dumps(message_data))
        await self.redis.ltrim("all_messages", 0, 499)

    async def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """최근 메시지를 가져오는 메서드"""
        messages = await self.redis.lrange("all_messages", 0, limit - 1)
        return [json.loads(msg) for msg in messages]

    async def get_user_messages(self, sender_id: str, limit: int = 50) -> List[Dict]:
        """특정 사용자의 최근 메시지를 가져오는 메서드"""
        messages = await self.redis.lrange(f"user:{sender_id}:messages", 0, limit - 1)
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

    async def clear_synced_messages(self, count: int):
        """동기화된 메시지를 Redis에서 제거하는 메서드"""
        await self.redis.ltrim("all_messages", count, -1)

redis_manager = RedisManager()