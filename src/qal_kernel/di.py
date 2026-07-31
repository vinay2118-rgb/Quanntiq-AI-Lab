"""Small explicit dependency-injection container for kernel-owned services."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any, TypeVar, cast

from qal_kernel.errors import DependencyNotFoundError, DuplicateRegistrationError

T = TypeVar("T")
Factory = Callable[["Container"], Any]


class Container:
    """Thread-safe container supporting singleton instances and lazy factories."""

    def __init__(self) -> None:
        self._instances: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Factory] = {}
        self._lock = RLock()

    def register_instance(self, contract: type[T], instance: T) -> None:
        with self._lock:
            self._ensure_available(contract)
            self._instances[contract] = instance

    def register_factory(self, contract: type[T], factory: Callable[[Container], T]) -> None:
        with self._lock:
            self._ensure_available(contract)
            self._factories[contract] = factory

    def resolve(self, contract: type[T]) -> T:
        with self._lock:
            if contract in self._instances:
                return cast(T, self._instances[contract])
            factory = self._factories.get(contract)
            if factory is None:
                raise DependencyNotFoundError(f"No dependency registered for {contract.__name__}")
            instance = factory(self)
            self._instances[contract] = instance
            return cast(T, instance)

    def _ensure_available(self, contract: type[Any]) -> None:
        if contract in self._instances or contract in self._factories:
            raise DuplicateRegistrationError(f"Dependency already registered: {contract.__name__}")
