#!/usr/bin/env python
"""Test WebSocket broadcast"""
import asyncio
import queue
from api.websocket import manager as ws_manager, broadcast_queue

async def test():
    # Check if there's a broadcast task
    print(f'Clients: {len(ws_manager.clients)}')
    print(f'Broadcast task: {ws_manager._broadcast_task}')
    task_done = ws_manager._broadcast_task.done() if ws_manager._broadcast_task else "None"
    print(f'Task done: {task_done}')
    
    # Add a message
    ws_manager.broadcast_threadsafe({'type': 'traffic_update', 'data': {'device_id': 'test', 'download_speed_bps': 1000}})
    print(f'Queue size after: {broadcast_queue.qsize()}')
    
    await asyncio.sleep(2)
    print(f'Queue size after wait: {broadcast_queue.qsize()}')
    print('Done')

asyncio.run(test())