"""Platform kernel composition root."""

from dataclasses import dataclass

import structlog

from qal_kernel.config import Settings
from qal_kernel.database import Database
from qal_kernel.di import Container
from qal_kernel.events import Event, EventBus
from qal_kernel.lifecycle import LifecycleManager
from qal_kernel.metrics import KernelMetrics
from qal_kernel.services import ServiceDescriptor, ServiceRegistry

logger = structlog.get_logger(__name__)


@dataclass(slots=True)
class Kernel:
    """Runtime facade over the platform's foundational services."""

    settings: Settings
    container: Container
    services: ServiceRegistry
    lifecycle: LifecycleManager
    events: EventBus
    metrics: KernelMetrics

    async def start(self) -> None:
        await self.lifecycle.start()
        self.metrics.lifecycle_state.set(1)
        await self.events.publish(
            Event(
                topic="kernel.started",
                payload={"version": self.settings.service_version},
            )
        )
        self.metrics.events_published.inc()
        await logger.ainfo("kernel_started", version=self.settings.service_version)

    async def stop(self) -> None:
        await self.events.publish(Event(topic="kernel.stopping", payload={}))
        self.metrics.events_published.inc()
        await self.lifecycle.stop()
        self.metrics.lifecycle_state.set(0)
        await logger.ainfo("kernel_stopped")

    async def ready(self) -> tuple[bool, dict[str, bool]]:
        checks = await self.services.readiness()
        return self.lifecycle.state.value == "running" and all(checks.values()), checks


def build_kernel(settings: Settings) -> Kernel:
    """Compose all kernel services without hidden global mutation."""

    container = Container()
    services = ServiceRegistry()
    lifecycle = LifecycleManager()
    events = EventBus()
    metrics = KernelMetrics()
    database = Database(str(settings.database_url))

    container.register_instance(Settings, settings)
    container.register_instance(Database, database)
    container.register_instance(EventBus, events)
    container.register_instance(ServiceRegistry, services)
    container.register_instance(LifecycleManager, lifecycle)
    container.register_instance(KernelMetrics, metrics)

    services.register(ServiceDescriptor("database", "1", database.healthy))
    lifecycle.add_shutdown_hook(database.close)
    return Kernel(settings, container, services, lifecycle, events, metrics)
