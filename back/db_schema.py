import asyncpg
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def create_tables(conn):
    """필요한 테이블과 인덱스를 생성하는 메서드"""
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
    
    # messages 테이블 생성 (파티션 테이블)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            id UUID NOT NULL,
            sender_id UUID NOT NULL,
            nickname VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (sender_id) REFERENCES users(id)
        ) PARTITION BY RANGE (created_at)
    ''')
    
    # user_sessions 테이블 생성 (파티션 테이블)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            login_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            ip_address INET NOT NULL,
            logout_time TIMESTAMP WITH TIME ZONE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        ) PARTITION BY RANGE (login_time)
    ''')
    
    # 파티션 생성 함수 정의
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
    
    # 초기 파티션 생성
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
        CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_login_time ON user_sessions(login_time);
        CREATE INDEX IF NOT EXISTS idx_user_sessions_ip_address ON user_sessions(ip_address);
    ''')

async def ensure_partition_exists(conn, table_name: str, date: datetime.date):
    """지정된 날짜에 대한 파티션이 존재하는지 확인하고, 없으면 생성하는 메서드"""
    partition_name = f"{table_name}_{date.strftime('%Y_%m_%d')}"
    partition_exists = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = $1 AND n.nspname = 'public')",
        partition_name
    )
    if not partition_exists:
        logger.info(f"Creating new partitions for {table_name} starting from {date}")
        for i in range(7):  # 7일간의 파티션 생성
            await conn.execute(
                f"SELECT create_time_partition('{table_name}', $1)",
                date + timedelta(days=i)
            )

async def initialize_database(pool):
    """데이터베이스 초기화 및 테이블 생성"""
    async with pool.acquire() as conn:
        await create_tables(conn)