import json
import nats
from typing import Callable, Awaitable


class NATSClient:
    def __init__(self, servers: list[str]):
        self.servers = servers
        self._conn = None

    async def connect(self):
        self._conn = await nats.connect(servers=self.servers)

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def publish(self, subject: str, data: dict):
        if not self._conn:
            raise RuntimeError("NATS not connected")
        await self._conn.publish(subject, json.dumps(data).encode())

    async def subscribe(self, subject: str, callback: Callable[[dict], Awaitable[None]]):
        if not self._conn:
            raise RuntimeError("NATS not connected")

        async def handler(msg):
            data = json.loads(msg.data.decode())
            await callback(data)

        await self._conn.subscribe(subject, cb=handler)
