from functools import wraps
import logging
import asyncpg
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

def handle_error(func):
    """
    데이터베이스 및 Redis 작업에서 발생할 수 있는 오류를 처리하는 데코레이터
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # 원래 함수 실행
            return await func(*args, **kwargs)
        except asyncpg.UniqueViolationError:
            # 중복 데이터 삽입 시도 시 처리
            logger.warning(f"Attempted to insert duplicate data")
            return False, "Duplicate data error"
        except asyncpg.PostgresError as e:
            # PostgreSQL 관련 오류 처리
            logger.error(f"Database error: {e}")
            return False, "Database error occurred"
        except RedisError as e:
            # Redis 관련 오류 처리
            logger.error(f"Redis error: {e}")
            return False, "Redis error occurred"
        except Exception as e:
            # 기타 예상치 못한 오류 처리
            logger.error(f"Unexpected error: {e}")
            return False, "An unexpected error occurred"
    return wrapper