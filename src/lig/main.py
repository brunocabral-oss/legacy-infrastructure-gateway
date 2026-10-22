"""Main FastAPI application entrypoint for Legacy Infrastructure Gateway."""

from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from lig.api.dependencies import get_driver_registry, get_inventory_provider
from lig.api.errors import register_error_handlers
from lig.api.v1.router import api_v1_router
from lig.observability.logging import setup_logging
from lig.observability.metrics import REQUEST_COUNT, get_metrics_payload
from lig.settings.config import settings

# Setup logging
setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Vendor-agnostic API gateway transforming legacy network infrastructure "
        "into normalized, auditable resources."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register standardized error handlers
register_error_handlers(app)


@app.middleware("http")
async def correlation_and_metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Ensure x-request-id correlation header and track Prometheus metrics."""
    req_id = request.headers.get("x-request-id") or f"req_{uuid4().hex[:12]}"
    request.state.request_id = req_id

    response = await call_next(request)
    response.headers["x-request-id"] = req_id

    # Record metric
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    ).inc()

    return response


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


# Health and observability endpoints
@app.get("/health/live", tags=["Health"], summary="Liveness probe")
async def health_live() -> dict[str, str]:
    """Liveness probe verifying that the HTTP server is alive."""
    return {"status": "alive", "version": settings.version}


@app.get("/health/ready", tags=["Health"], summary="Readiness probe")
async def health_ready() -> dict[str, str]:
    """Readiness probe validating inventory and driver registry state."""
    inventory = get_inventory_provider()
    devices = await inventory.list_devices()
    registry = get_driver_registry()

    return {
        "status": "ready",
        "version": settings.version,
        "devices_count": str(len(devices)),
        "mock_driver_registered": str(registry.is_registered("mock")),
    }


@app.get("/metrics", tags=["Observability"], summary="Prometheus metrics")
async def metrics() -> Response:
    """Expose Prometheus telemetry metrics."""
    payload, content_type = get_metrics_payload()
    return Response(content=payload, media_type=content_type)


# Mount API V1
app.include_router(api_v1_router)


def run_server() -> None:
    """Entry point for CLI script."""
    import uvicorn

    uvicorn.run("lig.main:app", host=settings.host, port=settings.port, reload=settings.debug)


if __name__ == "__main__":
    run_server()
