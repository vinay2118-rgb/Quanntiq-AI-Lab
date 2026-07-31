"""Service contracts and registry."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from qal_kernel.errors import DuplicateRegistrationError

HealthCheck = Callable[[], Awaitable[bool]]


@dataclass(frozen=True, slots=True)
class ServiceDescriptor:
    """Operational metadata and readiness probe for a platform service."""

    name: str
    version: str
    health_check: HealthCheck


class ServiceRegistry:
    """Registry with explicit duplicate protection and aggregate readiness."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceDescriptor] = {}

    def register(self, service: ServiceDescriptor) -> None:
        if service.name in self._services:
            raise DuplicateRegistrationError(f"Service already registered: {service.name}")
        self._services[service.name] = service

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._services))

    async def readiness(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for name, descriptor in self._services.items():
            try:
                results[name] = await descriptor.health_check()
            except Exception:
                results[name] = False
        return results
