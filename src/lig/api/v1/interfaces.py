"""Interface endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request

from lig.api.dependencies import get_operation_service
from lig.core.operation_service import OperationService
from lig.models.common import ResponseEnvelope
from lig.models.interface import Interface

router = APIRouter(prefix="/devices", tags=["Operational State"])


@router.get(
    "/{device}/interfaces",
    response_model=ResponseEnvelope[list[Interface]],
    summary="Get all normalized interfaces",
)
async def get_device_interfaces(
    device: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[list[Interface]]:
    """Retrieve normalized physical and logical interfaces with IP addresses."""
    return await ops.execute_operation(
        device_name=device,
        operation="interfaces.read",
        executor_func=lambda driver: driver.get_interfaces(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        request_id=request.headers.get("x-request-id"),
    )


@router.get(
    "/{device}/interfaces/{interface_name:path}",
    response_model=ResponseEnvelope[Interface],
    summary="Get specific normalized interface",
)
async def get_device_single_interface(
    device: str,
    interface_name: str,
    request: Request,
    ops: OperationService = Depends(get_operation_service),
) -> ResponseEnvelope[Interface]:
    """Retrieve details for a single interface by name."""
    envelope = await ops.execute_operation(
        device_name=device,
        operation="interfaces.read",
        executor_func=lambda driver: driver.get_interfaces(),
        source_ip=request.client.host if request.client else "127.0.0.1",
        parameters={"interface": interface_name},
        request_id=request.headers.get("x-request-id"),
    )

    matching = next((i for i in envelope.data if i.name.lower() == interface_name.lower()), None)
    if not matching:
        raise HTTPException(
            status_code=404, detail=f"Interface '{interface_name}' not found on device '{device}'"
        )

    return ResponseEnvelope[Interface](
        request_id=envelope.request_id,
        device=envelope.device,
        operation="interfaces.read",
        status="success",
        data=matching,
        metadata=envelope.metadata,
    )
