import redis.asyncio as redis
import json
import time
from typing import List, Dict

class RedisManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        self.redis = await redis.from_url("redis://localhost")

    async def disconnect(self):
        if self.redis is not None:
            await self.redis.close()

    async def add_message(self, sender_id: str, message: str, username: str):
        message_data = {
            "content": message,
            "sender_id": sender_id,
            "username": username,
            "timestamp": time.time(),
            "retry_count": 0
        }
        await self.redis.lpush(f"user:{sender_id}:messages", json.dumps(message_data))
        await self.redis.ltrim(f"user:{sender_id}:messages", 0, 49)  # 최근 50개 메시지만 유지
        await self.redis.lpush("all_messages", json.dumps(message_data))
        await self.redis.ltrim("all_messages", 0, 499)  # 전체 최근 500개 메시지 유지

    async def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        messages = await self.redis.lrange("all_messages", 0, limit - 1)
        return [json.loads(msg) for msg in messages]

    async def get_messages_to_save(self) -> List[Dict]:
        all_messages = await self.redis.lrange("all_messages", 0, -1)
        messages_to_save = []
        for msg in all_messages:
            msg_data = json.loads(msg)
            if msg_data['retry_count'] < 30:
                messages_to_save.append(msg_data)
        return messages_to_save

    async def update_message_retry_count(self, message: Dict):
        message['retry_count'] += 1
        await self.redis.lrem("all_messages", 1, json.dumps(message))
        await self.redis.lpush("all_messages", json.dumps(message))

    async def remove_saved_message(self, message: Dict):
        await self.redis.lrem("all_messages", 1, json.dumps(message))

    async def add_active_connection(self, sender_id: str):
        await self.redis.sadd("active_connections", sender_id)

    async def remove_active_connection(self, sender_id: str):
        await self.redis.srem("active_connections", sender_id)

    async def get_active_connections_count(self) -> int:
        return await self.redis.scard("active_connections")

    async def publish_message(self, channel: str, message: str):
        await self.redis.publish(channel, message)

    async def subscribe(self, channel: str):
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def add_user_to_ban_list(self, sender_id: str, ban_duration: int):
        await self.redis.setex(f"banned:{sender_id}", ban_duration, "1")

    async def is_user_banned(self, sender_id: str) -> bool:
        return await self.redis.exists(f"banned:{sender_id}")

redis_manager = RedisManager()