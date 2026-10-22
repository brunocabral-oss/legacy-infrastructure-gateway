"""Routing table endpoint."""

from fastapi import APIRouter, Depends, Query, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope
from lig.models.route import Route, RouteProtocol, RouteQuery

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/routes",
    response_model=ResponseEnvelope[list[Route]],
    summary="Get normalized routing table",
)
async def get_device_routes(
    device: str,
    request: Request,
    destination: str | None = Query(
        default=None, description="Filter by destination prefix or host"
    ),
    vrf: str | None = Query(default=None, description="VRF routing table name"),
    protocol: RouteProtocol | None = Query(default=None, description="Protocol filter"),
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[list[Route]]:
    """Retrieve normalized routing table entries matching optional criteria."""
    query = RouteQuery(destination=destination, vrf=vrf, protocol=protocol)
    return await ops.execute_operation(
        device_name=device,
        operation="routes.read",
        executor_func=lambda driver: driver.get_routes(query),
        source_ip=request.client.host if request.client else "127.0.0.1",
        parameters=query.model_dump(exclude_none=True),
        request_id=request.headers.get("x-request-id"),
    )
