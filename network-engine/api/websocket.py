import asyncio
import json
import threading
import queue
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from typing import Optional, Dict, Set
from datetime import datetime

from api.security import verify_token
from api.auth import get_user_from_token

app = FastAPI()


# Thread-safe queue for broadcasting messages from background threads
broadcast_queue: queue.Queue = queue.Queue()


class ConnectionManager:
    def __init__(self):
        self.clients: Set[WebSocket] = set()
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}
        self.client_info: Dict[WebSocket, Dict] = {}  # Store user info, connection time
        self._broadcast_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket, user_info: Optional[Dict] = None):
        await websocket.accept()
        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()
        self.client_info[websocket] = {
            "user": user_info,
            "connected_at": datetime.utcnow().isoformat(),
        }
        
        # Start broadcast consumer if not already running
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._consume_broadcast_queue())

    def disconnect(self, websocket: WebSocket):
        self.clients.discard(websocket)
        self.client_subscriptions.pop(websocket, None)
        self.client_info.pop(websocket, None)

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

    def unsubscribe(self, websocket: WebSocket, topics: list[str]):
        if websocket in self.client_subscriptions:
            for topic in topics:
                self.client_subscriptions[websocket].discard(topic)


manager = ConnectionManager()


def validate_token(token: Optional[str]) -> Optional[Dict]:
    """Validate JWT token and return user info if valid"""
    if not token:
        return None
    try:
        # Query params are always strings, ensure proper encoding
        if isinstance(token, str):
            token = token.strip()
        user = get_user_from_token(token)
        return user
    except Exception as e:
        print(f"[WS] Token validation failed: {e}")
        return None


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None
):
    # Validate token if provided
    user_info = validate_token(token)
    
    if token and not user_info:
        # Token provided but invalid
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
        return
    
    await manager.connect(websocket, user_info)
    
    # Send welcome message with connection info
    await websocket.send_json({
        "type": "connected",
        "data": {
            "authenticated": user_info is not None,
            "user": user_info.get("username") if user_info else None,
            "server_time": datetime.utcnow().isoformat(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WS] Received from client: {data}")
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                # Legacy support for "subscribe:topic1,topic2" format
                if data.startswith("subscribe:"):
                    topics = data.split(":", 1)[1].split(",")
                    manager.subscribe(websocket, topics)
                    await websocket.send_json({
                        "type": "subscribed",
                        "data": {"topics": topics},
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                elif data.startswith("unsubscribe:"):
                    topics = data.split(":", 1)[1].split(",")
                    manager.unsubscribe(websocket, topics)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "data": {"topics": topics},
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Invalid message format. Use JSON or 'subscribe:topic1,topic2'"},
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                continue
            
            # Handle structured JSON messages
            message_type = message.get("type", "")
            request_id = message.get("requestId")
            payload = message.get("data", {})
            
            # Helper to send response
            async def send_response(response_type: str, response_data: dict = None):
                await websocket.send_json({
                    "type": response_type,
                    "data": response_data or {},
                    "requestId": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            
            if message_type == "subscribe":
                topics = payload.get("topics", [])
                if isinstance(topics, str):
                    topics = [topics]
                manager.subscribe(websocket, topics)
                await send_response("subscribed", {"topics": topics})
                
            elif message_type == "unsubscribe":
                topics = payload.get("topics", [])
                if isinstance(topics, str):
                    topics = [topics]
                manager.unsubscribe(websocket, topics)
                await send_response("unsubscribed", {"topics": topics})
                
            elif message_type == "ping":
                # Respond with pong
                await send_response("pong", {"received_at": payload.get("timestamp")})
                
            elif message_type == "pong":
                # Client responded to our ping - just acknowledge
                pass
                
            elif message_type == "auth":
                # Re-authentication request
                new_token = payload.get("token")
                if new_token:
                    new_user = validate_token(new_token)
                    if new_user:
                        manager.client_info[websocket]["user"] = new_user
                        await send_response("auth_success", {"user": new_user.get("username")})
                    else:
                        await send_response("auth_failed", {"message": "Invalid token"})
                else:
                    await send_response("auth_failed", {"message": "Token required"})
                    
            else:
                # Unknown message type
                await send_response("error", {"message": f"Unknown message type: {message_type}"})
                
    except WebSocketDisconnect:
        print("[WS] Client disconnected gracefully")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"[WS] Connection error: {e}")
        manager.disconnect(websocket)