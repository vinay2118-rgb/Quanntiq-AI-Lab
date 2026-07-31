"""Typed asynchronous in-process event bus foundation."""

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

EventHandler = Callable[["Event"], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable event envelope with traceable identity and timestamp."""

    topic: str
    payload: dict[str, Any]
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus:
    """Concurrent publisher with isolated subscriber execution."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        async with self._lock:
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)

    async def publish(self, event: Event) -> None:
        async with self._lock:
            handlers = tuple(self._subscribers.get(event.topic, ()))
        if handlers:
            await asyncio.gather(*(handler(event) for handler in handlers))
