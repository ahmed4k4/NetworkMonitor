#!/usr/bin/env python
"""Test WebSocket connection and messages"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # Subscribe to topics
        await websocket.send("subscribe:traffic_update,device_online,device_offline,system_status,flow_update,alert")
        print("Sent subscription request")

        # Listen for messages
        for i in range(30):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(message)
                print(f"[{i}] {data.get('type', 'unknown')}")
            except asyncio.TimeoutError:
                print(f"[{i}] Timeout - no message")
            except Exception as e:
                print(f"[{i}] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())