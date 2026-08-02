import asyncio
from dataclasses import FrozenInstanceError
from datetime import UTC
from typing import cast

import pytest

from qal_kernel.errors import InvalidEventTopicError
from qal_kernel.events import DeliveryReport, Event, EventBus


async def test_event_bus_delivers_to_subscribers() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    await bus.subscribe("test.event", handler)
    event = Event(topic="test.event", payload={"value": 42})

    report = await bus.publish(event)

    assert received == [event]
    assert report == DeliveryReport(
        event_id=event.event_id,
        topic=event.topic,
        matched_handlers=1,
        successful_deliveries=1,
        failures=(),
    )


def test_event_receives_unique_identity_and_utc_timestamp() -> None:
    first = Event(topic="test.event", payload={})
    second = Event(topic="test.event", payload={})

    assert first.event_id != second.event_id
    assert first.occurred_at.tzinfo is UTC
    assert second.occurred_at.tzinfo is UTC


def test_event_envelope_is_frozen() -> None:
    event = Event(topic="test.event", payload={})

    with pytest.raises(FrozenInstanceError):
        event.topic = "changed.event"  # type: ignore[misc]


@pytest.mark.parametrize(
    "topic",
    [
        "",
        " ",
        ".test",
        "test.",
        "test..event",
        "Test.event",
        "test event",
        "test/event",
        "test@event",
    ],
)
def test_event_rejects_invalid_string_topics(topic: str) -> None:
    with pytest.raises(InvalidEventTopicError):
        Event(topic=topic, payload={})


def test_event_rejects_non_string_topic() -> None:
    with pytest.raises(InvalidEventTopicError):
        Event(topic=cast(str, 42), payload={})


async def test_subscription_operations_reject_invalid_topics() -> None:
    bus = EventBus()

    async def handler(event: Event) -> None:
        del event

    with pytest.raises(InvalidEventTopicError):
        await bus.subscribe("Invalid.Topic", handler)

    with pytest.raises(InvalidEventTopicError):
        await bus.unsubscribe("invalid..topic", handler)


async def test_duplicate_subscription_is_idempotent() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    await bus.subscribe("test.event", handler)
    await bus.subscribe("test.event", handler)

    report = await bus.publish(Event(topic="test.event", payload={}))

    assert len(received) == 1
    assert report.matched_handlers == 1
    assert report.successful_deliveries == 1


async def test_unsubscribe_is_deterministic() -> None:
    bus = EventBus()

    async def handler(event: Event) -> None:
        del event

    assert await bus.unsubscribe("test.event", handler) is False

    await bus.subscribe("test.event", handler)

    assert await bus.unsubscribe("test.event", handler) is True
    assert await bus.unsubscribe("test.event", handler) is False

    report = await bus.publish(Event(topic="test.event", payload={}))

    assert report.matched_handlers == 0


async def test_publish_without_subscribers_returns_empty_report() -> None:
    bus = EventBus()
    event = Event(topic="test.empty", payload={})

    report = await bus.publish(event)

    assert report.event_id == event.event_id
    assert report.topic == event.topic
    assert report.matched_handlers == 0
    assert report.successful_deliveries == 0
    assert report.failures == ()


async def test_handler_failures_are_isolated_and_sanitized() -> None:
    bus = EventBus()
    received: list[str] = []

    async def first_handler(event: Event) -> None:
        del event
        received.append("first")

    async def failing_handler(event: Event) -> None:
        del event
        received.append("failing")
        raise ValueError("unsafe\nmultiline message")

    async def final_handler(event: Event) -> None:
        del event
        received.append("final")

    await bus.subscribe("test.event", first_handler)
    await bus.subscribe("test.event", failing_handler)
    await bus.subscribe("test.event", final_handler)

    report = await bus.publish(Event(topic="test.event", payload={}))

    assert received == ["first", "failing", "final"]
    assert report.matched_handlers == 3
    assert report.successful_deliveries == 2
    assert len(report.failures) == 1
    assert report.failures[0].handler.endswith(
        "test_handler_failures_are_isolated_and_sanitized.<locals>.failing_handler"
    )
    assert report.failures[0].exception_type == "ValueError"
    assert report.failures[0].message == "unsafe multiline message"


async def test_failure_results_follow_registration_order() -> None:
    bus = EventBus()

    async def slow_failure(event: Event) -> None:
        del event
        await asyncio.sleep(0)
        raise RuntimeError("first")

    async def fast_failure(event: Event) -> None:
        del event
        raise LookupError("second")

    await bus.subscribe("test.event", slow_failure)
    await bus.subscribe("test.event", fast_failure)

    report = await bus.publish(Event(topic="test.event", payload={}))

    assert [failure.message for failure in report.failures] == ["first", "second"]


async def test_concurrent_duplicate_subscriptions_remain_idempotent() -> None:
    bus = EventBus()
    delivery_count = 0

    async def handler(event: Event) -> None:
        nonlocal delivery_count
        del event
        delivery_count += 1

    await asyncio.gather(
        *(bus.subscribe("test.concurrent", handler) for _ in range(20))
    )

    report = await bus.publish(Event(topic="test.concurrent", payload={}))

    assert delivery_count == 1
    assert report.matched_handlers == 1
    assert report.successful_deliveries == 1