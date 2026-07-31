from qal_kernel.events import Event, EventBus


async def test_event_bus_delivers_to_subscribers() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    await bus.subscribe("test.event", handler)
    event = Event(topic="test.event", payload={"value": 42})
    await bus.publish(event)
    assert received == [event]
