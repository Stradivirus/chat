import asyncpg
import logging
from typing import List, Dict
import uuid
from datetime import datetime, timedelta
import bcrypt

class PostgresManager:
    def __init__(self):
        # 데이터베이스 연결 풀을 저장할 변수
        self.pool = None
        # 로거 설정
        self.logger = logging.getLogger(__name__)

    async def start(self):
        # 데이터베이스 연결 풀 생성
        self.pool = await asyncpg.create_pool(
            user='chat_admin',
            password='1q2w3e4r!!',
            database='chatting',
            host='localhost',
            port=5432
        )
        # 테이블 생성 메서드 호출
        await self.create_tables()

    async def stop(self):
        # 데이터베이스 연결 풀 종료
        await self.pool.close()

    async def create_tables(self):
        # 데이터베이스 테이블 생성
        async with self.pool.acquire() as conn:
            # users 테이블 생성
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    nickname VARCHAR(50) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # user_sessions 테이블 생성 (파티션 테이블)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    ip_address INET NOT NULL,
                    login_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    logout_time TIMESTAMP WITH TIME ZONE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) PARTITION BY RANGE (login_time)
            ''')
            
            # messages 테이블 생성 (파티션 테이블)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id UUID NOT NULL,
                    user_id UUID NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) PARTITION BY RANGE (created_at)
            ''')
            
            # 파티션 생성을 위한 함수 정의
            await conn.execute('''
                CREATE OR REPLACE FUNCTION create_time_partition(table_name text, date date)
                RETURNS void AS $$
                DECLARE
                    partition_date DATE := $2;
                    partition_name TEXT := table_name || '_' || to_char(partition_date, 'YYYY_MM_DD');
                    start_date TIMESTAMP := partition_date;
                    end_date TIMESTAMP := partition_date + INTERVAL '1 day';
                BEGIN
                    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
                        FOR VALUES FROM (%L) TO (%L)',
                        partition_name, table_name, start_date, end_date);
                END;
                $$ LANGUAGE plpgsql;
            ''')
            
            # 초기 파티션 생성 (현재 날짜부터 7일간)
            await conn.execute('''
                DO $$
                DECLARE
                    i INT;
                BEGIN
                    FOR i IN 0..6 LOOP
                        PERFORM create_time_partition('messages', CURRENT_DATE + i);
                        PERFORM create_time_partition('user_sessions', CURRENT_DATE + i);
                    END LOOP;
                END $$;
            ''')
            
            # 인덱스 생성
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
                CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_login_time ON user_sessions(login_time);
                CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);
            ''')

    async def ensure_partition_exists(self, table_name: str, date: datetime.date):
        # 지정된 날짜의 파티션이 존재하는지 확인하고, 없으면 생성
        async with self.pool.acquire() as conn:
            partition_name = f"{table_name}_{date.strftime('%Y_%m_%d')}"
            partition_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = $1 AND n.nspname = 'public')",
                partition_name
            )
            if not partition_exists:
                self.logger.info(f"Creating new partitions for {table_name} starting from {date}")
                for i in range(7):  # 7일간의 파티션 생성
                    await conn.execute(
                        f"SELECT create_time_partition('{table_name}', $1)",
                        date + timedelta(days=i)
                    )

    async def register_user(self, username: str, password: str, email: str, nickname: str):
        # 새 사용자 등록
        try:
            # 비밀번호 해싱
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
        # 사용자 로그인
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT id, password FROM users WHERE username = $1',
                    username
                )
                if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                    self.logger.info(f"Successful login for username: {username}")
                    return True, str(user['id'])
            self.logger.warning(f"Failed login attempt for username: {username}")
            return False, "Invalid username or password"
        except Exception as e:
            self.logger.error(f"Error during login for {username}: {e}")
            return False, "Error during login"

    async def save_message(self, user_id: str, content: str):
        # 채팅 메시지 저장
        try:
            message_date = datetime.now().date()
            await self.ensure_partition_exists('messages', message_date)
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'INSERT INTO messages (id, user_id, content) VALUES ($1, $2, $3)',
                    uuid.uuid4(), uuid.UUID(user_id), content
                )
            return True
        except Exception as e:
            self.logger.error(f"Error saving message: {e}")
            return False

    async def save_user_session(self, user_id: str, ip_address: str):
        # 사용자 세션 정보 저장
        try:
            session_date = datetime.now().date()
            await self.ensure_partition_exists('user_sessions', session_date)
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'INSERT INTO user_sessions (id, user_id, ip_address) VALUES ($1, $2, $3)',
                    uuid.uuid4(), uuid.UUID(user_id), ip_address
                )
            return True
        except Exception as e:
            self.logger.error(f"Error saving user session: {e}")
            return False

    async def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        # 최근 메시지 조회
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT m.id, m.content, m.created_at, u.username as sender
                    FROM messages m
                    JOIN users u ON m.user_id = u.id
                    ORDER BY m.created_at DESC
                    LIMIT $1
                ''', limit)
            return [dict(r) for r in rows]
        except Exception as e:
            self.logger.error(f"Error fetching recent messages: {e}")
            return []

    async def get_user_by_id(self, user_id: str):
        # 사용자 ID로 사용자 정보 조회
        try:
            async with self.pool.acquire() as conn:
                user = await conn.fetchrow(
                    'SELECT id, username FROM users WHERE id = $1',
                    uuid.UUID(user_id)
                )
                if user:
                    return {"id": str(user['id']), "username": user['username']}
            return None
        except Exception as e:
            self.logger.error(f"Error fetching user by ID: {e}")
            return None

# PostgresManager 인스턴스 생성
postgres_manager = PostgresManager()