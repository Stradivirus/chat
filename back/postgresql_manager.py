import asyncpg
import logging
from typing import List, Dict
import uuid
from datetime import datetime, timedelta
import bcrypt
import os
import ssl
import asyncio
from db_schema import initialize_database, ensure_partition_exists

class PostgresManager:
    def __init__(self):
        self.pool = None
        self.logger = logging.getLogger(__name__)
        self._connection_params = None

    async def start(self):
        """데이터베이스 연결 매개변수를 설정하고 테이블을 초기화하는 메서드"""
        # SSL 컨텍스트 생성 (Supabase는 SSL 필요)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # 연결 매개변수 저장
        self._connection_params = {
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'database': os.getenv('POSTGRES_DB'),
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'command_timeout': 30,
            'server_settings': {
                'application_name': 'chat_app',
                'jit': 'off'
            }
        }
        
        # 연결 테스트 및 데이터베이스 초기화
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Testing PostgreSQL connection (attempt {attempt + 1}/{max_retries})")
                conn = await asyncpg.connect(**self._connection_params)
                await conn.fetchval('SELECT 1')
                await initialize_database(conn)  # 임시 풀 대신 단일 연결로 초기화
                await conn.close()
                self.logger.info("PostgreSQL connection test successful")
                break
                
            except asyncpg.exceptions.InternalServerError as e:
                if "Max client connections reached" in str(e):
                    self.logger.warning(f"Max connections reached on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        self.logger.info(f"Waiting {retry_delay} seconds before retry...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        self.logger.error("Failed to connect after all retries")
                        raise
                else:
                    raise
            except Exception as e:
                self.logger.error(f"Unexpected error connecting to PostgreSQL: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    raise

    async def get_connection(self):
        """새로운 데이터베이스 연결을 생성합니다"""
        if not self._connection_params:
            raise RuntimeError("Database not initialized. Call start() first.")
        return await asyncpg.connect(**self._connection_params)

    async def stop(self):
        """데이터베이스 연결을 정리하는 메서드"""
        self._connection_params = None
        self.logger.info("PostgreSQL connection parameters cleared")

    async def register_user(self, username: str, password: str, email: str, nickname: str):
        """새 사용자를 등록하는 메서드"""
        conn = None
        try:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn = await self.get_connection()
            user_id = await conn.fetchval(
                'INSERT INTO users (id, username, email, nickname, password) VALUES ($1, $2, $3, $4, $5) RETURNING id',
                uuid.uuid4(), username, email, nickname, hashed_password.decode('utf-8')
            )
            self.logger.info(f"User registered successfully: {username}")
            return True, str(user_id)
        except asyncpg.UniqueViolationError:
            self.logger.warning(f"Attempted to register existing username or email: {username}")
            return False, "Username or email already exists"
        except asyncpg.PostgresConnectionError as e:
            self.logger.error(f"Database connection error during user registration: {e}")
            return False, "Database connection error"
        except Exception as e:
            self.logger.error(f"Error registering user {username}: {e}")
            return False, "Error registering user"
        finally:
            if conn:
                await conn.close()

    async def login_user(self, username: str, password: str):
        """사용자 로그인을 처리하는 메서드"""
        conn = None
        try:
            conn = await self.get_connection()
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
        finally:
            if conn:
                await conn.close()

    async def save_message(self, sender_id: str, content: str, nickname: str):
        """메시지를 저장하는 메서드"""
        conn = None
        try:
            message_date = datetime.now().date()
            conn = await self.get_connection()
            await ensure_partition_exists(conn, 'messages', message_date)
            await conn.execute(
                'INSERT INTO messages (sender_id, nickname, content) VALUES ($1, $2, $3)',
                uuid.UUID(sender_id), nickname, content
            )
            return True
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            return False
        finally:
            if conn:
                await conn.close()

    async def save_user_session(self, user_id: str, ip_address: str):
        """사용자 세션을 저장하는 메서드"""
        conn = None
        try:
            session_date = datetime.now().date()
            conn = await self.get_connection()
            await ensure_partition_exists(conn, 'user_sessions', session_date)
            await conn.execute(
                'INSERT INTO user_sessions (id, user_id, ip_address) VALUES ($1, $2, $3)',
                uuid.uuid4(), uuid.UUID(user_id), ip_address
            )
            return True
        except Exception as e:
            self.logger.error(f"Error saving user session: {e}")
            return False
        finally:
            if conn:
                await conn.close()

    async def get_recent_messages_from_db(self, limit: int = 50) -> List[Dict]:
        """데이터베이스에서 최근 메시지를 가져오는 메서드"""
        conn = None
        try:
            conn = await self.get_connection()
            rows = await conn.fetch('''
                SELECT m.created_at, m.content, m.nickname, u.username as sender
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                ORDER BY m.created_at DESC
                LIMIT $1
            ''', limit)
            return [dict(r) for r in rows]
        except Exception as e:
            self.logger.error(f"Error fetching recent messages from database: {e}")
            return []
        finally:
            if conn:
                await conn.close()

    async def get_user_by_id(self, user_id: str):
        """사용자 ID로 사용자 정보를 가져오는 메서드"""
        conn = None
        try:
            conn = await self.get_connection()
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
        finally:
            if conn:
                await conn.close()

    async def save_messages_from_redis(self, messages: List[Dict]):
        """Redis에서 가져온 메시지를 PostgreSQL에 저장하는 메서드"""
        if not messages:
            return True
            
        conn = None
        try:
            conn = await self.get_connection()
            async with conn.transaction():
                for message in messages:
                    # 사용자 ID가 유효한지 확인
                    user_exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM users WHERE id = $1)', uuid.UUID(message['sender_id']))
                    if not user_exists:
                        self.logger.warning(f"Skipping message from non-existent user: {message['sender_id']}")
                        continue

                    message_date = datetime.fromtimestamp(message['timestamp']).date()
                    await ensure_partition_exists(conn, 'messages', message_date)
                    await conn.execute(
                        'INSERT INTO messages (sender_id, nickname, content, created_at) VALUES ($1, $2, $3, $4)',
                        uuid.UUID(message['sender_id']), message['nickname'], message['content'],
                        datetime.fromtimestamp(message['timestamp'])
                    )
            self.logger.info(f"Successfully saved {len(messages)} messages from Redis to PostgreSQL")
            return True
        except asyncpg.PostgresConnectionError as e:
            self.logger.error(f"Database connection error saving messages from Redis: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error saving messages from Redis: {e}")
            return False
        finally:
            if conn:
                await conn.close()

    async def check_duplicate(self, field: str, value: str) -> bool:
        """이메일, 사용자 이름, 닉네임의 중복을 확인하는 메서드"""
        conn = None
        try:
            conn = await self.get_connection()
            count = await conn.fetchval(f'SELECT COUNT(*) FROM users WHERE {field} = $1', value)
            return count > 0
        except Exception as e:
            self.logger.error(f"Error checking duplicate {field}: {e}")
            return False
        finally:
            if conn:
                await conn.close()

async def initialize_database(conn_or_pool):
    """Pool 또는 Connection 객체를 받아서 db_schema의 create_tables를 호출"""
    from db_schema import create_tables, ensure_partition_exists
    if hasattr(conn_or_pool, "acquire"):
        async with conn_or_pool.acquire() as conn:
            await create_tables(conn)
            # 현재 날짜에 대한 파티션만 생성
            current_date = datetime.now().date()
            await ensure_partition_exists(conn, 'messages', current_date)
            await ensure_partition_exists(conn, 'user_sessions', current_date)
    else:
        await create_tables(conn_or_pool)
        current_date = datetime.now().date()
        await ensure_partition_exists(conn_or_pool, 'messages', current_date)
        await ensure_partition_exists(conn_or_pool, 'user_sessions', current_date)

# PostgresManager 인스턴스 생성
postgres_manager = PostgresManager()