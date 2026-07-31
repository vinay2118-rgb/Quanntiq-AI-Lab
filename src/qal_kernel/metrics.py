"""Kernel metrics with an isolated Prometheus registry."""

from prometheus_client import CollectorRegistry, Counter, Gauge, generate_latest


class KernelMetrics:
    """Owns metrics to avoid global-registry collisions in tests and app factories."""

    def __init__(self) -> None:
        self.registry = CollectorRegistry(auto_describe=True)
        self.lifecycle_state = Gauge(
            "qal_kernel_lifecycle_state",
            "Whether the kernel is in the running state",
            registry=self.registry,
        )
        self.events_published = Counter(
            "qal_kernel_events_published_total",
            "Events successfully published by the kernel",
            registry=self.registry,
        )

    def render(self) -> bytes:
        return generate_latest(self.registry)
