"""Typed asynchronous in-process event bus foundation."""

import asyncio
import re
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from qal_kernel.errors import InvalidEventTopicError

EventHandler = Callable[["Event"], Awaitable[None]]

_TOPIC_PATTERN = re.compile(r"[a-z0-9_-]+(?:\.[a-z0-9_-]+)*\Z")


def _validate_topic(topic: str) -> None:
    """Validate an event routing topic."""
    if not isinstance(topic, str) or _TOPIC_PATTERN.fullmatch(topic) is None:
        raise InvalidEventTopicError(f"Invalid event topic: {topic!r}")


def _handler_identity(handler: EventHandler) -> str:
    """Return a stable descriptive identity for a subscribed handler."""
    module = getattr(handler, "__module__", type(handler).__module__)
    name = getattr(handler, "__qualname__", type(handler).__qualname__)
    return f"{module}.{name}"


def _sanitize_error(error: Exception) -> str:
    """Return a single-line error message suitable for delivery reporting."""
    return " ".join(str(error).splitlines())


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable event envelope with traceable identity and timestamp."""

    topic: str
    payload: dict[str, Any]
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        _validate_topic(self.topic)


@dataclass(frozen=True, slots=True)
class DeliveryFailure:
    """Sanitized details of one failed handler delivery."""

    handler: str
    exception_type: str
    message: str


@dataclass(frozen=True, slots=True)
class DeliveryReport:
    """Immutable summary of an event publication attempt."""

    event_id: UUID
    topic: str
    matched_handlers: int
    successful_deliveries: int
    failures: tuple[DeliveryFailure, ...]


class EventBus:
    """Concurrent publisher with isolated subscriber execution."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe a handler to a validated topic idempotently."""
        _validate_topic(topic)
        async with self._lock:
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: EventHandler) -> bool:
        """Remove a handler from a topic when it is currently subscribed."""
        _validate_topic(topic)
        async with self._lock:
            handlers = self._subscribers.get(topic)
            if handlers is None or handler not in handlers:
                return False

            handlers.remove(handler)
            if not handlers:
                del self._subscribers[topic]
            return True

    async def publish(self, event: Event) -> DeliveryReport:
        """Publish an event and return an ordered delivery report."""
        _validate_topic(event.topic)
        async with self._lock:
            handlers = tuple(self._subscribers.get(event.topic, ()))

        results = await asyncio.gather(
            *(self._deliver(handler, event) for handler in handlers)
        )
        failures = tuple(result for result in results if result is not None)

        return DeliveryReport(
            event_id=event.event_id,
            topic=event.topic,
            matched_handlers=len(handlers),
            successful_deliveries=len(handlers) - len(failures),
            failures=failures,
        )

    @staticmethod
    async def _deliver(
        handler: EventHandler,
        event: Event,
    ) -> DeliveryFailure | None:
        try:
            await handler(event)
        except Exception as error:
            return DeliveryFailure(
                handler=_handler_identity(handler),
                exception_type=type(error).__name__,
                message=_sanitize_error(error),
            )
        return None