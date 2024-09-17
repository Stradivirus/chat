# background_tasks.py

import asyncio
import json
import time

async def periodic_user_count_update(manager):
    while True:
        count = len(manager.active_connections)
        await manager.broadcast(json.dumps({"type": "user_count", "count": count}))
        await asyncio.sleep(1)

async def cleanup_old_data(manager):
    while True:
        current_time = time.time()
        for user_id in list(manager.user_messages.keys()):
            if not manager.user_messages[user_id] or current_time - manager.user_messages[user_id][-1][1] > 3600:
                del manager.user_messages[user_id]
            if user_id in manager.user_ban_until:
                del manager.user_ban_until[user_id]
        await asyncio.sleep(3600)

async def check_connections(manager):
    while True:
        for user_id, connection in list(manager.active_connections.items()):
            try:
                await connection.send_json({"type": "ping"})
            except Exception:
                await manager.disconnect(user_id)
        await asyncio.sleep(60)

def start_background_tasks(manager):
    manager.background_tasks.add(asyncio.create_task(periodic_user_count_update(manager)))
    manager.background_tasks.add(asyncio.create_task(cleanup_old_data(manager)))
    manager.background_tasks.add(asyncio.create_task(check_connections(manager)))

def stop_background_tasks(manager):
    for task in manager.background_tasks:
        task.cancel()
    manager.background_tasks.clear()