from qal_kernel.services import ServiceDescriptor, ServiceRegistry


async def test_registry_reports_failed_and_raised_health_checks() -> None:
    registry = ServiceRegistry()

    async def healthy() -> bool:
        return True

    async def broken() -> bool:
        raise RuntimeError("probe failure")

    registry.register(ServiceDescriptor("healthy", "1", healthy))
    registry.register(ServiceDescriptor("broken", "1", broken))
    assert registry.names() == ("broken", "healthy")
    assert await registry.readiness() == {"healthy": True, "broken": False}
