"""Registry for mapping platform types to driver implementations."""

from typing import Type

from lig.core.exceptions import DriverNotFoundError
from lig.drivers.base import InfrastructureDriver
from lig.drivers.cisco_ios.driver import CiscoIOSDriver
from lig.drivers.cisco_iosxr.driver import CiscoIOSXRDriver
from lig.drivers.fortios.driver import FortiOSDriver
from lig.drivers.mock.driver import MockDriver
from lig.models.device import Device, DevicePlatform


class DriverRegistry:
    """Registry maintaining driver factory mappings."""

    def __init__(self) -> None:
        self._drivers: dict[str, Type[InfrastructureDriver]] = {}
        # Register standard built-in drivers
        self.register(DevicePlatform.MOCK.value, MockDriver)
        self.register(DevicePlatform.CISCO_IOS.value, CiscoIOSDriver)
        self.register(DevicePlatform.CISCO_IOSXR.value, CiscoIOSXRDriver)
        self.register(DevicePlatform.FORTIOS.value, FortiOSDriver)

    def register(self, platform: str, driver_cls: Type[InfrastructureDriver]) -> None:
        """Register a driver class for a specific platform string."""
        self._drivers[platform] = driver_cls

    def get_driver(self, device: Device) -> InfrastructureDriver:
        """Instantiate the appropriate driver for a device."""
        platform_key = (
            device.platform.value if hasattr(device.platform, "value") else str(device.platform)
        )
        driver_cls = self._drivers.get(platform_key)
        if not driver_cls:
            raise DriverNotFoundError(platform_key)
        return driver_cls(device)

    def is_registered(self, platform: str) -> bool:
        """Check if a platform has a registered driver."""
        return platform in self._drivers
