import asyncpg
import logging
from typing import List, Dict
import uuid
from datetime import datetime, timedelta
import bcrypt
from db_schema import initialize_database, ensure_partition_exists

class PostgresManager:
    def __init__(self):
        self.pool = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """데이터베이스 연결 풀을 생성하고 테이블을 초기화하는 메서드"""
        self.pool = await asyncpg.create_pool(
            user='chat_admin',
            password='1q2w3e4r!!',
            database='chatting',
            host='localhost',
            port=5432
        )
        await initialize_database(self.pool)

    async def stop(self):
        """데이터베이스 연결 풀을 종료하는 메서드"""
        await self.pool.close()

    async def register_user(self, username: str, password: str, email: str, nickname: str):
        """새 사용자를 등록하는 메서드"""
        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            async with self.pool.acquire() as conn:
                user_id = await conn.fetchval(
                    'INSERT INTO users (id, username, email, nickname, password) VALUES ($1, $2, $3, $4, $5) RETURNING id',
                    uuid.uuid4(), username, email, nickname, hashed_password.decode('utf-8')
                )
            self.logger.info(f"User registered successfully: {username}")
            return True, str(user_id)
        except asyncpg.UniqueViolationError:
            self.logger.warning(f"Attempted to register existing username or email: {username}")
            return False, "Username or email already exists"
        except Exception as e:
            self.logger.error(f"Error registering user {username}: {e}")
            return False, "Error registering user"

    async def login_user(self, username: str, password: str):
        """사용자 로그인을 처리하는 메서드"""
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT id, password, nickname FROM users WHERE username = $1',
                    username
                )
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                self.logger.info(f"Successful login for username: {username}")
                return True, {"user_id": str(user['id']), "nickname": user['nickname']}
            self.logger.warning(f"Failed login attempt for username: {username}")
            return False, "Invalid username or password"
        except Exception as e:
            self.logger.error(f"Error during login for {username}: {e}")
            return False, "Error during login"

    async def save_message(self, sender_id: str, content: str, nickname: str):
        """메시지를 저장하는 메서드"""
        try:
            message_date = datetime.now().date()
            async with self.pool.acquire() as conn:
                await ensure_partition_exists(conn, 'messages', message_date)
                await conn.execute(
                    'INSERT INTO messages (id, sender_id, nickname, content) VALUES ($1, $2, $3, $4)',
                    uuid.uuid4(), uuid.UUID(sender_id), nickname, content
                )
            return True
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            return False

    async def save_user_session(self, user_id: str, ip_address: str):
        """사용자 세션을 저장하는 메서드"""
        try:
            session_date = datetime.now().date()
            async with self.pool.acquire() as conn:
                await ensure_partition_exists(conn, 'user_sessions', session_date)
                await conn.execute(
                    'INSERT INTO user_sessions (id, user_id, ip_address) VALUES ($1, $2, $3)',
                    uuid.uuid4(), uuid.UUID(user_id), ip_address
                )
            return True
        except Exception as e:
            self.logger.error(f"Error saving user session: {e}")
            return False

    async def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """최근 메시지를 가져오는 메서드"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT m.created_at, m.id, m.content, m.nickname, u.username as sender
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    ORDER BY m.created_at DESC
                    LIMIT $1
                ''', limit)
            return [dict(r) for r in rows]
        except Exception as e:
            self.logger.error(f"Error fetching recent messages: {e}")
            return []

    async def get_user_by_id(self, user_id: str):
        """사용자 ID로 사용자 정보를 가져오는 메서드"""
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT id, username, nickname FROM users WHERE id = $1',
                    uuid.UUID(user_id)
                )
            if user:
                return {"id": str(user['id']), "username": user['username'], "nickname": user['nickname']}
            return None
        except Exception as e:
            self.logger.error(f"Error fetching user by ID: {e}")
            return None

    async def save_messages_from_redis(self, messages: List[Dict]):
        """Redis에서 가져온 메시지를 PostgreSQL에 저장하는 메서드"""
        try:
            async with self.pool.acquire() as conn:
                for message in messages:
                    message_date = datetime.fromtimestamp(message['timestamp']).date()
                    await ensure_partition_exists(conn, 'messages', message_date)
                    await conn.execute(
                        'INSERT INTO messages (id, sender_id, nickname, content, created_at) VALUES ($1, $2, $3, $4, $5)',
                        uuid.uuid4(), uuid.UUID(message['sender_id']), message['username'], message['content'],
                        datetime.fromtimestamp(message['timestamp'])
                    )
            return True
        except Exception as e:
            self.logger.error(f"Error saving messages from Redis: {e}")
            return False

postgres_manager = PostgresManager()