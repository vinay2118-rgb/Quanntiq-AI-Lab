import pytest

from qal_kernel.errors import InvalidLifecycleTransitionError
from qal_kernel.lifecycle import LifecycleManager, LifecycleState


async def test_lifecycle_orders_startup_and_reverse_shutdown() -> None:
    manager = LifecycleManager()
    calls: list[str] = []

    async def first() -> None:
        calls.append("first")

    async def second() -> None:
        calls.append("second")

    manager.add_startup_hook(first)
    manager.add_startup_hook(second)
    manager.add_shutdown_hook(first)
    manager.add_shutdown_hook(second)
    await manager.start()
    await manager.stop()
    assert calls == ["first", "second", "second", "first"]
    assert manager.state is LifecycleState.STOPPED


async def test_lifecycle_rejects_invalid_transition() -> None:
    manager = LifecycleManager()
    with pytest.raises(InvalidLifecycleTransitionError):
        await manager.stop()
