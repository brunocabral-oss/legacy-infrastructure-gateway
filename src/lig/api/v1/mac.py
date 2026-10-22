"""MAC address forwarding table endpoint."""

from fastapi import APIRouter, Depends, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope
from lig.models.mac import MacEntry

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/mac-addresses",
    response_model=ResponseEnvelope[list[MacEntry]],
    summary="Get normalized MAC address table",
)
async def get_device_mac_table(
    device: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[list[MacEntry]]:
    """Retrieve layer 2 MAC address forwarding table."""
    return await ops.execute_operation(
        device_name=device,
        operation="mac.read",
        executor_func=lambda driver: driver.get_mac_table(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        request_id=request.headers.get("x-request-id"),
    )
