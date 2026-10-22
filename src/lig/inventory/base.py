"""Abstract inventory provider definition."""

from abc import ABC, abstractmethod

from lig.models.device import Device


class InventoryProvider(ABC):
    """Abstract interface for device inventory storage."""

    @abstractmethod
    async def get_device(self, name: str) -> Device | None:
        """Fetch a single device by its unique name."""
        ...

    @abstractmethod
    async def list_devices(self) -> list[Device]:
        """List all registered devices in inventory."""
        ...
