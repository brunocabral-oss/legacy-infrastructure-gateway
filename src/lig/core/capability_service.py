"""Capability service for verifying platform-level operation support."""

from lig.core.exceptions import CapabilityNotSupportedError
from lig.drivers.base import InfrastructureDriver
from lig.models.capabilities import CapabilityProfile


class CapabilityService:
    """Verifies that a target device driver supports the requested operation."""

    @staticmethod
    def verify_capability(driver: InfrastructureDriver, operation: str) -> None:
        """Verify driver capability for an operation.

        Raises CapabilityNotSupportedError if unsupported.
        """
        profile: CapabilityProfile = driver.capabilities()
        cap = profile.capabilities.get(operation)

        if not cap or not cap.supported:
            reason = cap.description if cap else "Capability not declared by platform driver"
            raise CapabilityNotSupportedError(
                device=driver.device.name,
                operation=operation,
                reason=reason,
            )
