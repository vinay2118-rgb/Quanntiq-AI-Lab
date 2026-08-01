"""Small explicit dependency-injection container for kernel-owned services."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any, TypeVar, cast

from qal_kernel.errors import (
    CircularDependencyError,
    DependencyNotFoundError,
    DuplicateRegistrationError,
    InvalidDependencyError,
)

T = TypeVar("T")
Factory = Callable[["Container"], Any]


class Container:
    """Thread-safe container supporting instances and lazy singleton factories."""

    def __init__(self) -> None:
        self._instances: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Factory] = {}
        self._resolving: list[type[Any]] = []
        self._lock = RLock()

    def register_instance(self, contract: type[T], instance: T) -> None:
        """Register an existing instance for a dependency contract."""
        with self._lock:
            self._ensure_available(contract)
            self._instances[contract] = instance

    def register_factory(
        self,
        contract: type[T],
        factory: Callable[[Container], T],
    ) -> None:
        """Register a factory whose result is created once on first resolution."""
        with self._lock:
            self._ensure_available(contract)
            self._factories[contract] = factory

    def resolve(self, contract: type[T]) -> T:
        """Resolve a registered dependency and cache factory-created instances."""
        with self._lock:
            existing = self._instances.get(contract)
            if existing is not None:
                return cast(T, existing)

            factory = self._factories.get(contract)
            if factory is None:
                raise DependencyNotFoundError(
                    f"No dependency registered for {contract.__name__}"
                )

            if contract in self._resolving:
                cycle_start = self._resolving.index(contract)
                cycle = [*self._resolving[cycle_start:], contract]
                path = " -> ".join(item.__name__ for item in cycle)
                raise CircularDependencyError(
                    f"Circular dependency detected: {path}"
                )

            self._resolving.append(contract)
            try:
                instance = factory(self)

                if not isinstance(instance, contract):
                    raise InvalidDependencyError(
                        f"Factory for {contract.__name__} returned "
                        f"{type(instance).__name__}"
                    )

                self._instances[contract] = instance
                return instance
            finally:
                self._resolving.pop()

    def _ensure_available(self, contract: type[Any]) -> None:
        """Reject registrations that would replace an existing dependency."""
        if contract in self._instances or contract in self._factories:
            raise DuplicateRegistrationError(
                f"Dependency already registered: {contract.__name__}"
            )
