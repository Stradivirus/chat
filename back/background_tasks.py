import asyncio
import logging
from redis_manager import redis_manager
from postgresql_manager import postgres_manager

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
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in periodic user count update: {e}", exc_info=True)
            await asyncio.sleep(5)

async def cleanup_old_data(manager):
    """
    오래된 메시지와 만료된 사용자 차단 정보를 정리하는 함수
    """
    while True:
        try:
            current_time = asyncio.get_event_loop().time()
            for sender_id in list(manager.user_messages.keys()):
                # 1시간 이상 지난 메시지 삭제
                if not manager.user_messages[sender_id] or current_time - manager.user_messages[sender_id][-1][1] > 3600:
                    del manager.user_messages[sender_id]
                # 만료된 사용자 차단 정보 삭제
                if sender_id in manager.user_ban_until and current_time >= manager.user_ban_until[sender_id]:
                    del manager.user_ban_until[sender_id]
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in cleanup old data: {e}", exc_info=True)
            await asyncio.sleep(60)

async def check_connections(manager):
    """
    주기적으로 연결 상태를 확인하고 끊어진 연결을 정리하는 함수
    """
    while True:
        try:
            for sender_id, connection in list(manager.active_connections.items()):
                try:
                    # 각 연결에 ping 메시지 전송
                    await connection.send_json({"type": "ping"})
                except Exception:
                    # 연결 실패 시 연결 해제 및 Redis에서 제거
                    await manager.disconnect(sender_id)
                    await redis_manager.remove_active_connection(sender_id)
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in check connections: {e}", exc_info=True)
            await asyncio.sleep(5)

async def sync_redis_to_postgres():
    """
    Redis의 메시지를 주기적으로 PostgreSQL에 동기화하는 함수
    """
    last_sync_time = asyncio.get_event_loop().time()
    while True:
        try:
            current_time = asyncio.get_event_loop().time()
            # Redis에서 최근 메시지 50개 가져오기
            messages = await redis_manager.get_recent_messages(50)
            # 50개 이상 메시지가 있거나 마지막 동기화 후 10초 이상 지났을 때 동기화
            if len(messages) >= 50 or current_time - last_sync_time >= 10:
                success = await postgres_manager.save_messages_from_redis(messages)
                if success:
                    # 동기화 성공 시 Redis에서 해당 메시지 삭제
                    await redis_manager.clear_synced_messages(len(messages))
                    last_sync_time = current_time
                    logger.info(f"Synced {len(messages)} messages to PostgreSQL")
                else:
                    logger.error("Failed to sync messages to PostgreSQL")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in sync_redis_to_postgres: {e}", exc_info=True)
            await asyncio.sleep(5)

def start_background_tasks(manager):
    """
    백그라운드 태스크들을 시작하는 함수
    """
    manager.background_tasks.add(asyncio.create_task(periodic_user_count_update(manager)))
    manager.background_tasks.add(asyncio.create_task(cleanup_old_data(manager)))
    manager.background_tasks.add(asyncio.create_task(check_connections(manager)))
    manager.background_tasks.add(asyncio.create_task(sync_redis_to_postgres()))

def stop_background_tasks(manager):
    """
    실행 중인 모든 백그라운드 태스크를 중지하는 함수
    """
    for task in manager.background_tasks:
        task.cancel()
    manager.background_tasks.clear()