"""Error handlers converting domain exceptions into standardized HTTP responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from lig.core.exceptions import (
    AuthenticationError,
    CapabilityNotSupportedError,
    ConcurrencyLimitError,
    DeviceConnectionError,
    DeviceDisabledError,
    DeviceNotFoundError,
    DeviceTimeoutError,
    DriverNotFoundError,
    LIGException,
    PolicyDeniedError,
)
from lig.models.common import ErrorResponse


def register_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on FastAPI application instance."""

    @app.exception_handler(DeviceNotFoundError)
    async def device_not_found_handler(request: Request, exc: DeviceNotFoundError) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=404, content=content)

    @app.exception_handler(DeviceDisabledError)
    async def device_disabled_handler(request: Request, exc: DeviceDisabledError) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=400, content=content)

    @app.exception_handler(CapabilityNotSupportedError)
    async def capability_unsupported_handler(
        request: Request, exc: CapabilityNotSupportedError
    ) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            operation=exc.operation,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=501, content=content)

    @app.exception_handler(PolicyDeniedError)
    async def policy_denied_handler(request: Request, exc: PolicyDeniedError) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=403, content=content)

    @app.exception_handler(DriverNotFoundError)
    async def driver_not_found_handler(request: Request, exc: DriverNotFoundError) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=501, content=content)

    @app.exception_handler(DeviceTimeoutError)
    async def device_timeout_handler(request: Request, exc: DeviceTimeoutError) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=504, content=content)

    @app.exception_handler(ConcurrencyLimitError)
    async def concurrency_limit_handler(
        request: Request, exc: ConcurrencyLimitError
    ) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=429, content=content)

    @app.exception_handler(DeviceConnectionError)
    async def device_connection_handler(
        request: Request, exc: DeviceConnectionError
    ) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=502, content=content)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            device=exc.device,
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=401, content=content)

    @app.exception_handler(LIGException)
    async def generic_lig_handler(request: Request, exc: LIGException) -> JSONResponse:
        content = ErrorResponse(
            request_id=request.headers.get("x-request-id", "unknown"),
            error_code=exc.error_code,
            message=exc.message,
        ).model_dump(mode="json")
        return JSONResponse(status_code=500, content=content)
