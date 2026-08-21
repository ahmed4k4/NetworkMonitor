import asyncio
import json
import threading
import queue
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from typing import Optional

app = FastAPI()


# Thread-safe queue for broadcasting messages from background threads
broadcast_queue: queue.Queue = queue.Queue()


class ConnectionManager:
    def __init__(self):
        self.clients: set[WebSocket] = set()
        self.client_subscriptions: dict[WebSocket, set[str]] = {}
        self._broadcast_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()
        
        # Start broadcast consumer if not already running
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._consume_broadcast_queue())

    def disconnect(self, websocket: WebSocket):
        self.clients.discard(websocket)
        self.client_subscriptions.pop(websocket, None)

    async def _consume_broadcast_queue(self):
        """Consume messages from the thread-safe queue and broadcast to clients"""
        loop = asyncio.get_event_loop()
        while True:
            try:
                # Wait for message with timeout to allow checking if clients exist
                message = await loop.run_in_executor(
                    None, lambda: broadcast_queue.get(timeout=1.0)
                )
                await self._broadcast_to_clients(message)
            except queue.Empty:
                # No messages, check if we still have clients
                if not self.clients:
                    break
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[WS] Broadcast consumer error: {e}")
                await asyncio.sleep(0.1)

    async def _broadcast_to_clients(self, message: dict):
        disconnected = []
        message_type = message.get("type", "")
        
        for websocket in self.clients:
            try:
                # If client has subscriptions, only send if message type matches
                subscriptions = self.client_subscriptions.get(websocket, set())
                if not subscriptions or message_type in subscriptions or "system_status" in subscriptions:
                    await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast immediately (for use within async context)"""
        await self._broadcast_to_clients(message)

    def broadcast_threadsafe(self, message: dict):
        """Thread-safe broadcast from background threads"""
        try:
            broadcast_queue.put_nowait(message)
        except queue.Full:
            print("[WS] Broadcast queue full, dropping message")

    def subscribe(self, websocket: WebSocket, topics: list[str]):
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].update(topics)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    # Validate token if provided
    if token:
        # Token validation could be added here
        pass
    
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WS] Received from client: {data}")
            
            # Handle subscription requests
            if data.startswith("subscribe:"):
                topics = data.split(":", 1)[1].split(",")
                manager.subscribe(websocket, topics)
                await websocket.send_json({"type": "subscribed", "topics": topics})
                
    except WebSocketDisconnect:
        print("[WS] Client disconnected gracefully")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS] Connection error: {e}")
        manager.disconnect(websocket)
