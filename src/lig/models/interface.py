"""Interface normalized models."""

from enum import Enum

from pydantic import BaseModel, Field


class InterfaceAdminStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class InterfaceOperStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    LOWER_LAYER_DOWN = "lower_layer_down"
    UNKNOWN = "unknown"


class InterfaceIP(BaseModel):
    """IP address assigned to an interface."""

    address: str = Field(description="IPv4 or IPv6 address")
    prefix_length: int = Field(description="Subnet mask length in CIDR notation")
    is_primary: bool = Field(
        default=True, description="Whether this is the primary IP on the interface"
    )


class Interface(BaseModel):
    """Normalized network interface model."""

    name: str = Field(description="Canonical interface name (e.g. GigabitEthernet0/0/1)")
    description: str | None = Field(default=None, description="Configured interface description")
    enabled: bool = Field(default=True, description="Administrative state enabled/disabled")
    admin_status: InterfaceAdminStatus = Field(default=InterfaceAdminStatus.UP)
    oper_status: InterfaceOperStatus = Field(default=InterfaceOperStatus.UP)
    mac_address: str | None = Field(default=None, description="Physical MAC address")
    mtu: int | None = Field(
        default=None, description="Configured Maximum Transmission Unit in bytes"
    )
    speed_mbps: int | None = Field(default=None, description="Interface link speed in Mbps")
    ip_addresses: list[InterfaceIP] = Field(
        default_factory=list, description="Configured IP addresses"
    )
