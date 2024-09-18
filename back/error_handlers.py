from functools import wraps
import logging
import asyncpg
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

def handle_error(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncpg.UniqueViolationError:
            logger.warning(f"Attempted to insert duplicate data")
            return False, "Duplicate data error"
        except asyncpg.PostgresError as e:
            logger.error(f"Database error: {e}")
            return False, "Database error occurred"
        except RedisError as e:
            logger.error(f"Redis error: {e}")
            return False, "Redis error occurred"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, "An unexpected error occurred"
    return wrapper