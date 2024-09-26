from functools import wraps
import logging
import asyncpg
from redis.exceptions import RedisError

# 로깅 설정
logger = logging.getLogger(__name__)

def handle_error(func):
    """
    데이터베이스 및 Redis 작업에서 발생할 수 있는 오류를 처리하는 데코레이터
    
    이 데코레이터는 비동기 함수에 적용되어, 다양한 예외 상황을 처리합니다.
    처리된 결과는 (성공 여부, 메시지) 형태의 튜플로 반환됩니다.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            # 원래 함수 실행
            # 데코레이트된 함수를 그대로 실행하고 결과를 반환
            return await func(*args, **kwargs)
        except asyncpg.UniqueViolationError:
            # 중복 데이터 삽입 시도 시 처리
            # 예: 이미 존재하는 사용자 이름으로 회원가입 시도 등
            logger.warning(f"Attempted to insert duplicate data")
            return False, "Duplicate data error"
        except asyncpg.PostgresError as e:
            # PostgreSQL 관련 오류 처리
            # 데이터베이스 연결 실패, 쿼리 실행 오류 등
            logger.error(f"Database error: {e}")
            return False, "Database error occurred"
        except RedisError as e:
            # Redis 관련 오류 처리
            # Redis 연결 실패, 명령 실행 오류 등
            logger.error(f"Redis error: {e}")
            return False, "Redis error occurred"
        except Exception as e:
            # 기타 예상치 못한 오류 처리
            # 위의 특정 예외로 잡히지 않은 모든 예외 상황
            logger.error(f"Unexpected error: {e}")
            return False, "An unexpected error occurred"
    return wrapper