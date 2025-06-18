import asyncio
from typing import List

from fastapi import WebSocket


class AlertWebSocketManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, message: dict):
        for conn in self.connections:
            await conn.send_json(message)

    def broadcast_sync(self, message: dict):
        """
        Thread-safe enqueue of the async broadcast coroutine
        on the running event loop—no circular imports required.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        # Schedule the broadcast coroutine to run on the loop
        loop.call_soon_threadsafe(asyncio.create_task, self.broadcast(message))


manager = AlertWebSocketManager()
