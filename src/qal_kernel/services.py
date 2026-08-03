"""Service contracts and registry."""

import asyncio
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
            raise DuplicateRegistrationError(
                f"Service already registered: {service.name}"
            )
        self._services[service.name] = service

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._services))

    async def readiness(self) -> dict[str, bool]:
        snapshot = tuple(sorted(self._services.items()))

        results = await asyncio.gather(
            *(self._probe(descriptor) for _, descriptor in snapshot)
        )

        return {
            name: result
            for (name, _), result in zip(snapshot, results, strict=True)
        }

    @staticmethod
    async def _probe(descriptor: ServiceDescriptor) -> bool:
        try:
            return await descriptor.health_check()
        except Exception:
            return False
