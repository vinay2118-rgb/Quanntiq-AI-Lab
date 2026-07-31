from fastapi.testclient import TestClient

from qal_kernel.api import create_app
from qal_kernel.config import Settings
from qal_kernel.kernel import build_kernel


def test_operational_endpoints() -> None:
    settings = Settings(environment="testing")
    kernel = build_kernel(settings)

    async def database_ready() -> bool:
        return True

    descriptor = kernel.services._services["database"]
    kernel.services._services["database"] = type(descriptor)(
        descriptor.name, descriptor.version, database_ready
    )
    app = create_app(settings, kernel)

    with TestClient(app) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")
        metrics = client.get("/metrics")

    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert ready.status_code == 200
    assert ready.json()["checks"] == {"database": True}
    assert metrics.status_code == 200
    assert "qal_kernel_lifecycle_state" in metrics.text
