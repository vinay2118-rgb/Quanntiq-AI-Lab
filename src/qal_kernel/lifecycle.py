"""Deterministic lifecycle state management."""

import asyncio
from collections.abc import Awaitable, Callable
from enum import StrEnum

from qal_kernel.errors import InvalidLifecycleTransitionError

LifecycleHook = Callable[[], Awaitable[None]]


class LifecycleState(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class LifecycleManager:
    """Coordinates ordered startup and reverse-ordered shutdown hooks."""

    def __init__(self) -> None:
        self._state = LifecycleState.CREATED
        self._startup_hooks: list[LifecycleHook] = []
        self._shutdown_hooks: list[LifecycleHook] = []
        self._lock = asyncio.Lock()

    @property
    def state(self) -> LifecycleState:
        return self._state

    def add_startup_hook(self, hook: LifecycleHook) -> None:
        self._startup_hooks.append(hook)

    def add_shutdown_hook(self, hook: LifecycleHook) -> None:
        self._shutdown_hooks.append(hook)

    async def start(self) -> None:
        async with self._lock:
            if self._state is not LifecycleState.CREATED:
                raise InvalidLifecycleTransitionError(f"Cannot start from {self._state}")
            self._state = LifecycleState.STARTING
            try:
                for hook in self._startup_hooks:
                    await hook()
                self._state = LifecycleState.RUNNING
            except Exception:
                self._state = LifecycleState.FAILED
                raise

    async def stop(self) -> None:
        async with self._lock:
            if self._state is not LifecycleState.RUNNING:
                raise InvalidLifecycleTransitionError(f"Cannot stop from {self._state}")
            self._state = LifecycleState.STOPPING
            try:
                for hook in reversed(self._shutdown_hooks):
                    await hook()
                self._state = LifecycleState.STOPPED
            except Exception:
                self._state = LifecycleState.FAILED
                raise
