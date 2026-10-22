"""Device and inventory API endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from lig.api.dependencies import get_driver_manager, get_inventory_provider
from lig.core.driver_manager import DriverManager
from lig.inventory.base import InventoryProvider
from lig.models.capabilities import CapabilityProfile
from lig.models.device import Device

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[Device], summary="List all inventory devices")
async def list_devices(
    inventory: InventoryProvider = Depends(get_inventory_provider),
) -> list[Device]:
    """Retrieve all devices configured in the gateway inventory."""
    return await inventory.list_devices()


@router.get("/{device}", response_model=Device, summary="Get device inventory metadata")
async def get_device(
    device: str,
    inventory: InventoryProvider = Depends(get_inventory_provider),
) -> Device:
    """Retrieve inventory details for a specific device."""
    dev = await inventory.get_device(device)
    if not dev:
        raise HTTPException(status_code=404, detail=f"Device '{device}' not found")
    return dev


@router.get(
    "/{device}/capabilities",
    response_model=CapabilityProfile,
    summary="Get device capability profile",
)
async def get_device_capabilities(
    device: str,
    driver_manager: DriverManager = Depends(get_driver_manager),
) -> CapabilityProfile:
    """Retrieve the declared capability matrix for the device platform."""
    _, driver = await driver_manager.get_driver_for_device(device)
    return driver.capabilities()
