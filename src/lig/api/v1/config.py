"""Running configuration endpoint."""

from fastapi import APIRouter, Depends, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/config/running",
    response_model=ResponseEnvelope[str],
    summary="Get sanitized running configuration",
)
async def get_device_running_config(
    device: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[str]:
    """Retrieve running configuration with credentials sanitized."""
    return await ops.execute_operation(
        device_name=device,
        operation="config.running.read",
        executor_func=lambda driver: driver.get_running_config(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        request_id=request.headers.get("x-request-id"),
    )
