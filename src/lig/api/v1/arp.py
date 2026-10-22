"""ARP table endpoint."""

from fastapi import APIRouter, Depends, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.arp import ArpEntry
from lig.models.common import ResponseEnvelope

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/arp",
    response_model=ResponseEnvelope[list[ArpEntry]],
    summary="Get normalized ARP table",
)
async def get_device_arp_table(
    device: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[list[ArpEntry]]:
    """Retrieve ARP resolution entries."""
    return await ops.execute_operation(
        device_name=device,
        operation="arp.read",
        executor_func=lambda driver: driver.get_arp_table(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        request_id=request.headers.get("x-request-id"),
    )
