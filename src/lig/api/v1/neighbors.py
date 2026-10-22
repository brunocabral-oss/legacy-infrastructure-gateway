"""Neighbor discovery endpoint."""

from fastapi import APIRouter, Depends, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope
from lig.models.neighbor import Neighbor

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/neighbors",
    response_model=ResponseEnvelope[list[Neighbor]],
    summary="Get LLDP/CDP neighbors",
)
async def get_device_neighbors(
    device: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[list[Neighbor]]:
    """Retrieve discovered LLDP or CDP neighbors."""
    return await ops.execute_operation(
        device_name=device,
        operation="neighbors.read",
        executor_func=lambda driver: driver.get_neighbors(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        request_id=request.headers.get("x-request-id"),
    )
