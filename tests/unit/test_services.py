import asyncio

import pytest

from qal_kernel.errors import DuplicateRegistrationError
from qal_kernel.services import ServiceDescriptor, ServiceRegistry


async def test_registry_supports_empty_service_collection() -> None:
    registry = ServiceRegistry()

    assert registry.names() == ()
    assert await registry.readiness() == {}


async def test_registry_rejects_duplicate_without_replacing_original() -> None:
    registry = ServiceRegistry()

    async def original_health_check() -> bool:
        return True

    async def replacement_health_check() -> bool:
        return False

    original = ServiceDescriptor("database", "1", original_health_check)
    registry.register(original)

    with pytest.raises(
        DuplicateRegistrationError,
        match="Service already registered: database",
    ):
        registry.register(
            ServiceDescriptor("database", "2", replacement_health_check)
        )

    assert registry._services["database"] is original
    assert await registry.readiness() == {"database": True}


async def test_registry_returns_service_names_in_sorted_order() -> None:
    registry = ServiceRegistry()

    async def healthy() -> bool:
        return True

    registry.register(ServiceDescriptor("worker", "1", healthy))
    registry.register(ServiceDescriptor("database", "1", healthy))
    registry.register(ServiceDescriptor("api", "1", healthy))

    assert registry.names() == ("api", "database", "worker")


async def test_readiness_is_concurrent_isolated_and_deterministic() -> None:
    registry = ServiceRegistry()
    task_ids: set[int] = set()

    async def record_task(result: bool) -> bool:
        task = asyncio.current_task()
        assert task is not None
        task_ids.add(id(task))
        await asyncio.sleep(0)
        return result

    async def healthy() -> bool:
        return await record_task(True)

    async def unhealthy() -> bool:
        return await record_task(False)

    async def broken() -> bool:
        await record_task(True)
        raise RuntimeError("probe failure")

    registry.register(ServiceDescriptor("unhealthy", "1", unhealthy))
    registry.register(ServiceDescriptor("healthy", "1", healthy))
    registry.register(ServiceDescriptor("broken", "1", broken))

    result = await registry.readiness()

    assert result == {
        "broken": False,
        "healthy": True,
        "unhealthy": False,
    }
    assert tuple(result) == ("broken", "healthy", "unhealthy")
    assert len(task_ids) == 3


async def test_readiness_uses_stable_registry_snapshot() -> None:
    registry = ServiceRegistry()
    probe_started = asyncio.Event()
    release_probe = asyncio.Event()

    async def delayed() -> bool:
        probe_started.set()
        await release_probe.wait()
        return True

    async def added_later() -> bool:
        return True

    registry.register(ServiceDescriptor("initial", "1", delayed))

    readiness_task = asyncio.create_task(registry.readiness())
    await probe_started.wait()

    registry.register(ServiceDescriptor("added", "1", added_later))
    release_probe.set()

    assert await readiness_task == {"initial": True}
    assert await registry.readiness() == {
        "added": True,
        "initial": True,
    }


async def test_readiness_propagates_task_cancellation() -> None:
    registry = ServiceRegistry()
    probe_started = asyncio.Event()
    block_probe = asyncio.Event()

    async def waiting() -> bool:
        probe_started.set()
        await block_probe.wait()
        return True

    registry.register(ServiceDescriptor("waiting", "1", waiting))

    readiness_task = asyncio.create_task(registry.readiness())
    await probe_started.wait()
    readiness_task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await readiness_task
