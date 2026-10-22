"""MAC address table normalized model."""

from pydantic import BaseModel, Field


class MacEntry(BaseModel):
    """Normalized MAC address table forwarding entry."""

    mac_address: str = Field(description="Hardware MAC address")
    vlan_id: int | None = Field(default=None, description="VLAN identifier")
    interface: str = Field(description="Port or interface name")
    entry_type: str = Field(default="dynamic", description="Type: dynamic, static")
    is_active: bool = Field(default=True, description="Whether MAC entry is active")
