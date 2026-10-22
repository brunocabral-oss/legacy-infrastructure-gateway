"""Unit tests for the CapabilityService."""

import pytest

from lig.core.capability_service import CapabilityService
from lig.core.exceptions import CapabilityNotSupportedError
from lig.drivers.mock.driver import MockDriver
from lig.models.device import Device, DevicePlatform, DeviceTransport


@pytest.fixture
def mock_device() -> Device:
    return Device(
        name="test-mock",
        host="127.0.0.1",
        platform=DevicePlatform.MOCK,
        transport=DeviceTransport.MOCK,
    )


def test_supported_capability_passes(mock_device: Device) -> None:
    driver = MockDriver(mock_device)
    # facts.read is supported on MockDriver
    CapabilityService.verify_capability(driver, "facts.read")


def test_unsupported_capability_raises_error(mock_device: Device) -> None:
    driver = MockDriver(mock_device)
    # mac.read is configured as supported=False on MockDriver
    with pytest.raises(CapabilityNotSupportedError) as exc_info:
        CapabilityService.verify_capability(driver, "mac.read")

    assert exc_info.value.device == "test-mock"
    assert exc_info.value.operation == "mac.read"
    assert "MAC address table not available" in exc_info.value.message
