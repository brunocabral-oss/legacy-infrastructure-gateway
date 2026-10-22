"""Diagnostic endpoints (Ping and Traceroute)."""

from fastapi import APIRouter, Depends, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope
from lig.models.diagnostics import PingRequest, PingResult, TracerouteRequest, TracerouteResult

router = APIRouter(prefix="/devices", tags=["Diagnostics"])


@router.post(
    "/{device}/diagnostics/ping",
    response_model=ResponseEnvelope[PingResult],
    summary="Execute remote ping diagnostic",
)
async def execute_device_ping(
    device: str,
    ping_request: PingRequest,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[PingResult]:
    """Execute ICMP ping diagnostic originating from the device."""
    return await ops.execute_operation(
        device_name=device,
        operation="diagnostics.ping",
        executor_func=lambda driver: driver.ping(ping_request),
        source_ip=request.client.host if request.client else "127.0.0.1",
        parameters=ping_request.model_dump(),
        request_id=request.headers.get("x-request-id"),
    )


@router.post(
    "/{device}/diagnostics/traceroute",
    response_model=ResponseEnvelope[TracerouteResult],
    summary="Execute remote traceroute diagnostic",
)
async def execute_device_traceroute(
    device: str,
    traceroute_request: TracerouteRequest,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[TracerouteResult]:
    """Execute traceroute hop discovery diagnostic originating from the device."""
    return await ops.execute_operation(
        device_name=device,
        operation="diagnostics.traceroute",
        executor_func=lambda driver: driver.traceroute(traceroute_request),
        source_ip=request.client.host if request.client else "127.0.0.1",
        parameters=traceroute_request.model_dump(),
        request_id=request.headers.get("x-request-id"),
    )
