"""FastAPI application factory and operational endpoints."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from qal_kernel.config import Settings, get_settings
from qal_kernel.errors import KernelError
from qal_kernel.kernel import Kernel, build_kernel
from qal_kernel.logging import configure_logging


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    version: str
    checks: dict[str, bool] | None = None


def create_app(settings: Settings | None = None, kernel: Kernel | None = None) -> FastAPI:
    """Create an isolated application instance suitable for production and tests."""

    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)
    active_kernel = kernel or build_kernel(active_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.kernel = active_kernel
        await active_kernel.start()
        try:
            yield
        finally:
            await active_kernel.stop()

    app = FastAPI(
        title="Quanntiq AI Lab Platform Kernel",
        version=active_settings.service_version,
        docs_url=None if active_settings.environment == "production" else "/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    @app.exception_handler(KernelError)
    async def kernel_error_handler(_request: Request, exc: KernelError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "kernel_error", "detail": str(exc)},
        )

    @app.get("/health/live", response_model=HealthResponse, tags=["operations"])
    async def liveness() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=active_settings.service_name,
            version=active_settings.service_version,
        )

    @app.get("/health/ready", response_model=HealthResponse, tags=["operations"])
    async def readiness(response: Response) -> HealthResponse:
        ready, checks = await active_kernel.ready()
        if not ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="ready" if ready else "not_ready",
            service=active_settings.service_name,
            version=active_settings.service_version,
            checks=checks,
        )

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(active_kernel.metrics.render(), media_type="text/plain; version=0.0.4")

    return app
