import asyncio
import logging
from redis_manager import redis_manager
from postgresql_manager import postgres_manager

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
                await connection.send_json({"type": "user_count", "count": count})
            # 1초 대기 후 다음 업데이트 실행
            await asyncio.sleep(1)
        except Exception as e:
            # 오류 발생 시 로그 기록 및 5초 대기 후 재시도
            logger.error(f"Error in periodic user count update: {e}", exc_info=True)
            await asyncio.sleep(5)

async def sync_redis_to_postgres():
    """
    Redis의 메시지를 주기적으로 PostgreSQL에 동기화하는 함수
    """
    # 마지막 동기화 시간 초기화
    last_sync_time = asyncio.get_event_loop().time()
    while True:
        try:
            # 현재 시간 가져오기
            current_time = asyncio.get_event_loop().time()
            # Redis에서 최근 메시지 50개 가져오기
            messages = await redis_manager.get_recent_messages(50)
            # 50개 이상 메시지가 있거나 마지막 동기화 후 10초 이상 지났을 때 동기화
            if len(messages) >= 50 or current_time - last_sync_time >= 10:
                # PostgreSQL에 메시지 저장
                success = await postgres_manager.save_messages_from_redis(messages)
                if success and messages:  # 메시지가 있고 성공적으로 저장된 경우에만 처리
                    # 동기화 성공 시 Redis에서 해당 메시지 삭제
                    await redis_manager.clear_synced_messages(len(messages))
                    last_sync_time = current_time
                    logger.info(f"Synced {len(messages)} messages to PostgreSQL")
                elif not success:
                    logger.error("Failed to sync messages to PostgreSQL")
            # 1초 대기 후 다음 동기화 확인
            await asyncio.sleep(1)
        except Exception as e:
            # 오류 발생 시 로그 기록 및 5초 대기 후 재시도
            logger.error(f"Error in sync_redis_to_postgres: {e}", exc_info=True)
            await asyncio.sleep(5)

def start_background_tasks(manager):
    """
    백그라운드 태스크들을 시작하는 함수
    """
    # 각 백그라운드 태스크를 생성하고 manager의 background_tasks 세트에 추가
    manager.background_tasks.add(asyncio.create_task(periodic_user_count_update(manager)))
    manager.background_tasks.add(asyncio.create_task(sync_redis_to_postgres()))
    # ConnectionManager 클래스의 메서드를 직접 호출
    manager.start_background_tasks()

def stop_background_tasks(manager):
    """
    실행 중인 모든 백그라운드 태스크를 중지하는 함수
    """
    # 모든 백그라운드 태스크 취소
    for task in manager.background_tasks:
        task.cancel()
    # background_tasks 세트 초기화
    manager.background_tasks.clear()