import asyncio
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable):
        self._handlers[event_type].append(handler)

    async def publish(self, event_type: str, data: Any = None):
        event = {"type": event_type, "data": data}
        await self._queue.put(event)

    async def process_events(self):
        while True:
            event = await self._queue.get()
            handlers = self._handlers.get(event["type"], [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event["data"])
                    else:
                        handler(event["data"])
                except Exception:
                    pass
            self._queue.task_done()


event_bus = EventBus()
