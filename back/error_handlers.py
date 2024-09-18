# error_handlers.py

from functools import wraps
import logging
import asyncpg

logger = logging.getLogger(__name__)

def handle_error(func):
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
            # PostgreSQL 관련 에러 처리
            logger.error(f"Database error: {e}")
            return False, "Database error occurred"
        except Exception as e:
            # 기타 예상치 못한 에러 처리
            logger.error(f"Unexpected error: {e}")
            return False, "An unexpected error occurred"
    return wrapper