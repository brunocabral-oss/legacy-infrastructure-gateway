"""Driver Manager coordinating device concurrency, timeout and driver instantiation."""

import asyncio
from collections.abc import Coroutine
from typing import Any

from lig.core.exceptions import (
    DeviceDisabledError,
    DeviceNotFoundError,
    DeviceTimeoutError,
)
from lig.drivers.base import InfrastructureDriver
from lig.drivers.registry import DriverRegistry
from lig.inventory.base import InventoryProvider
from lig.models.device import Device
from lig.settings.config import settings


class DriverManager:
    """Coordinates inventory resolution, concurrency locking and driver lifecycle."""

    def __init__(
        self,
        inventory: InventoryProvider,
        registry: DriverRegistry,
        concurrency_limit: int = settings.device_concurrency_limit,
        timeout_seconds: int = settings.global_timeout_seconds,
    ) -> None:
        self.inventory = inventory
        self.registry = registry
        self.concurrency_limit = concurrency_limit
        self.timeout_seconds = timeout_seconds
        self._device_semaphores: dict[str, asyncio.Semaphore] = {}

    def _get_semaphore(self, device_name: str) -> asyncio.Semaphore:
        if device_name not in self._device_semaphores:
            self._device_semaphores[device_name] = asyncio.Semaphore(self.concurrency_limit)
        return self._device_semaphores[device_name]

    async def get_driver_for_device(self, device_name: str) -> tuple[Device, InfrastructureDriver]:
        """Fetch device from inventory and instantiate driver."""
        device = await self.inventory.get_device(device_name)
        if not device:
            raise DeviceNotFoundError(device_name)
        if not device.enabled:
            raise DeviceDisabledError(device_name)

        driver = self.registry.get_driver(device)
        return device, driver

    async def execute_with_guardrails(
        self, device_name: str, coro: Coroutine[Any, Any, Any]
    ) -> Any:
        """Execute a driver coroutine with per-device concurrency and global timeout limits."""
        semaphore = self._get_semaphore(device_name)
        try:
            async with semaphore:
                return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        except asyncio.TimeoutError as err:
            raise DeviceTimeoutError(device_name, self.timeout_seconds) from err
