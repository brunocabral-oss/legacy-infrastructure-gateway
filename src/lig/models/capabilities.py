"""Capabilities model declaring what operations a platform/driver supports."""

from enum import Enum

from pydantic import BaseModel, Field


class CapabilityStatus(str, Enum):
    """Support status for a specific capability."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class OperationCapability(BaseModel):
    """Specification of an individual capability."""

    supported: bool = Field(description="Whether the capability is functional")
    status: CapabilityStatus = Field(default=CapabilityStatus.SUPPORTED)
    description: str | None = None
    restrictions: list[str] = Field(default_factory=list)


class CapabilityProfile(BaseModel):
    """Collection of declared capabilities for a given driver and platform."""

    driver: str
    platform: str
    version: str = "0.1.0"
    capabilities: dict[str, OperationCapability] = Field(
        default_factory=dict,
        description="Map of semantic operations (e.g. 'routes.read') to capability details",
    )

    def is_supported(self, operation: str) -> bool:
        """Check if an operation is explicitly supported."""
        cap = self.capabilities.get(operation)
        return cap.supported if cap is not None else False
