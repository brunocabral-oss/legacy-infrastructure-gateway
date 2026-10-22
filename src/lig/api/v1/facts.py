"""Device facts endpoint."""

from fastapi import APIRouter, Depends, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope
from lig.models.facts import DeviceFacts

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/facts",
    response_model=ResponseEnvelope[DeviceFacts],
    summary="Get normalized device facts",
)
async def get_device_facts(
    device: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[DeviceFacts]:
    """Retrieve normalized hardware, OS version, uptime, and identity facts."""
    return await ops.execute_operation(
        device_name=device,
        operation="facts.read",
        executor_func=lambda driver: driver.get_facts(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        request_id=request.headers.get("x-request-id"),
    )
