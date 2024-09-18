import asyncio
import json
import time
from redis_manager import redis_manager
from postgresql_manager import postgres_manager
import logging

logger = logging.getLogger(__name__)

async def periodic_user_count_update(manager):
    while True:
        try:
            count = await redis_manager.get_active_connections_count()
            manager.update_user_count(count)
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in periodic user count update: {e}", exc_info=True)
            await asyncio.sleep(5)

async def cleanup_old_data(manager):
    while True:
        try:
            current_time = time.time()
            for sender_id in list(manager.user_messages.keys()):
                if not manager.user_messages[sender_id] or current_time - manager.user_messages[sender_id][-1][1] > 3600:
                    del manager.user_messages[sender_id]
                if sender_id in manager.user_ban_until:
                    del manager.user_ban_until[sender_id]
            await asyncio.sleep(3600)
        except Exception as e:
            logger.error(f"Error in cleanup old data: {e}", exc_info=True)
            await asyncio.sleep(60)

async def check_connections(manager):
    while True:
        try:
            for sender_id, connection in list(manager.active_connections.items()):
                try:
                    await connection.send_json({"type": "ping"})
                except Exception:
                    await manager.disconnect(sender_id)
                    await redis_manager.remove_active_connection(sender_id)
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in check connections: {e}", exc_info=True)
            await asyncio.sleep(5)

async def save_messages_to_db():
    while True:
        try:
            messages = await redis_manager.get_messages_to_save()
            if messages:
                success = await postgres_manager.save_messages_from_redis(messages)
                if success:
                    for message in messages:
                        await redis_manager.remove_saved_message(message)
                else:
                    for message in messages:
                        await redis_manager.update_message_retry_count(message)
            await asyncio.sleep(60)  # 1분 대기
        except Exception as e:
            logger.error(f"Error in save messages to db: {e}", exc_info=True)
            await asyncio.sleep(5)

def start_background_tasks(manager):
    manager.background_tasks.add(asyncio.create_task(periodic_user_count_update(manager)))
    manager.background_tasks.add(asyncio.create_task(cleanup_old_data(manager)))
    manager.background_tasks.add(asyncio.create_task(check_connections(manager)))
    manager.background_tasks.add(asyncio.create_task(save_messages_to_db()))
    manager.background_tasks.add(asyncio.create_task(manager.start_redis_listener()))

def stop_background_tasks(manager):
    for task in manager.background_tasks:
        task.cancel()
    manager.background_tasks.clear()
    manager.stop_redis_listener()