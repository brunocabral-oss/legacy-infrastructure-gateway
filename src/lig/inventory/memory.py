"""In-memory inventory provider for development and testing."""

from lig.inventory.base import InventoryProvider
from lig.models.device import Device, DevicePlatform, DeviceTransport


class InMemoryInventory(InventoryProvider):
    """In-memory dictionary-backed inventory provider."""

    def __init__(self, initial_devices: list[Device] | None = None) -> None:
        self._devices: dict[str, Device] = {}
        if initial_devices:
            for dev in initial_devices:
                self._devices[dev.name] = dev
        else:
            # Seed with default mock and initial LAB devices
            self._seed_defaults()

    def _seed_defaults(self) -> None:
        default_devices = [
            Device(
                name="mock-router",
                host="127.0.0.1",
                platform=DevicePlatform.MOCK,
                transport=DeviceTransport.MOCK,
                port=22,
                credential_profile="lab_reader",
                site="lab",
                environment="development",
                enabled=True,
            ),
            Device(
                name="VDORTD-A",
                host="192.168.199.45",
                platform=DevicePlatform.CISCO_IOS,
                transport=DeviceTransport.SSH,
                port=22,
                credential_profile="lab_reader",
                site="lab",
                environment="lab",
                enabled=True,
            ),
            Device(
                name="ASR-LAB",
                host="192.168.100.10",
                platform=DevicePlatform.CISCO_IOSXR,
                transport=DeviceTransport.SSH,
                port=22,
                credential_profile="lab_reader",
                site="lab",
                environment="lab",
                enabled=True,
            ),
            Device(
                name="CAGE",
                host="192.168.200.138",
                platform=DevicePlatform.FORTIOS,
                transport=DeviceTransport.SSH,
                port=22,
                credential_profile="lab_reader",
                site="lab",
                environment="lab",
                enabled=True,
            ),
        ]
        for dev in default_devices:
            self._devices[dev.name] = dev

    async def get_device(self, name: str) -> Device | None:
        return self._devices.get(name)

    async def list_devices(self) -> list[Device]:
        return list(self._devices.values())
