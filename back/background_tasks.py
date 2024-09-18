# background_tasks.py

import asyncio
import json
import time

async def periodic_user_count_update(manager):
    while True:
        # 현재 활성 연결 수를 계산
        count = len(manager.active_connections)
        # 모든 연결에 사용자 수 업데이트를 브로드캐스트
        await manager.broadcast(json.dumps({"type": "user_count", "count": count}))
        # 1초 대기
        await asyncio.sleep(1)

async def cleanup_old_data(manager):
    while True:
        current_time = time.time()
        for user_id in list(manager.user_messages.keys()):
            # 1시간 이상 메시지가 없는 사용자의 데이터 삭제
            if not manager.user_messages[user_id] or current_time - manager.user_messages[user_id][-1][1] > 3600:
                del manager.user_messages[user_id]
            # 만료된 사용자 차단 정보 삭제
            if user_id in manager.user_ban_until:
                del manager.user_ban_until[user_id]
        # 1시간마다 실행
        await asyncio.sleep(3600)

async def check_connections(manager):
    while True:
        for user_id, connection in list(manager.active_connections.items()):
            try:
                # 각 연결에 ping 메시지 전송
                await connection.send_json({"type": "ping"})
            except Exception:
                # 연결 실패 시 해당 사용자 연결 해제
                await manager.disconnect(user_id)
        # 1분마다 실행
        await asyncio.sleep(60)

def start_background_tasks(manager):
    # 백그라운드 작업 시작
    manager.background_tasks.add(asyncio.create_task(periodic_user_count_update(manager)))
    manager.background_tasks.add(asyncio.create_task(cleanup_old_data(manager)))
    manager.background_tasks.add(asyncio.create_task(check_connections(manager)))

def stop_background_tasks(manager):
    # 모든 백그라운드 작업 중지 및 정리
    for task in manager.background_tasks:
        task.cancel()
    manager.background_tasks.clear()