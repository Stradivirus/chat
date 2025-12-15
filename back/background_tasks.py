import asyncio
import logging
from redis_manager import redis_manager

# 로깅 설정
logger = logging.getLogger(__name__)

async def periodic_user_count_update(manager):
    """
    주기적으로 활성 사용자 수를 업데이트하고 모든 연결에 전송하는 함수
    """
    while True:
        try:
            # Redis에서 활성 연결 수 가져오기
            count = await redis_manager.get_active_connections_count()
            # 모든 활성 연결에 사용자 수 업데이트 메시지 전송
            for connection in manager.active_connections.values():
                try:
                    await connection.send_json({"type": "user_count", "count": count})
                except Exception:
                    pass # 연결 끊긴 클라이언트는 무시
            # 1초 대기
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("periodic_user_count_update task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic user count update: {e}", exc_info=True)
            await asyncio.sleep(5)

def start_background_tasks(manager):
    """
    백그라운드 태스크들을 시작하는 함수
    """
    # 사용자 수 업데이트 태스크만 실행 (DB 동기화 로직 제거됨)
    manager.background_tasks.add(asyncio.create_task(periodic_user_count_update(manager)))
    # ConnectionManager 내부 관리 태스크 시작 (ping, cleanup 등)
    manager.start_background_tasks()

def stop_background_tasks(manager):
    """
    실행 중인 모든 백그라운드 태스크를 중지하는 함수
    """
    for task in manager.background_tasks:
        if not task.cancelled():
            task.cancel()
    manager.background_tasks.clear()
    logger.info("All background tasks stopped")