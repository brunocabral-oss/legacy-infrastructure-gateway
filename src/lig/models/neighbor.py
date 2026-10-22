"""LLDP/CDP Neighbor discovery normalized model."""

from enum import Enum

from pydantic import BaseModel, Field


class NeighborProtocol(str, Enum):
    LLDP = "lldp"
    CDP = "cdp"
    UNKNOWN = "unknown"


class Neighbor(BaseModel):
    """Normalized neighbor information from LLDP or CDP."""

    local_interface: str = Field(description="Local port connected to the neighbor")
    remote_hostname: str = Field(description="Neighbor device system name")
    remote_port: str = Field(description="Neighbor remote interface/port name")
    remote_platform: str | None = Field(default=None, description="Neighbor platform/description")
    protocol: NeighborProtocol = Field(default=NeighborProtocol.LLDP)
