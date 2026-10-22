"""Routing table normalized models."""

from enum import Enum

from pydantic import BaseModel, Field


class RouteProtocol(str, Enum):
    CONNECTED = "connected"
    STATIC = "static"
    OSPF = "ospf"
    BGP = "bgp"
    ISIS = "isis"
    EIGRP = "eigrp"
    RIP = "rip"
    OTHER = "other"


class RouteQuery(BaseModel):
    """Query parameters to filter routes."""

    destination: str | None = Field(default=None, description="Destination prefix or IP to match")
    vrf: str | None = Field(default=None, description="Virtual Routing and Forwarding table name")
    protocol: RouteProtocol | None = Field(default=None, description="Routing protocol to filter")


class Route(BaseModel):
    """Normalized routing table entry."""

    prefix: str = Field(description="Destination CIDR prefix (e.g. 192.168.1.0/24)")
    protocol: RouteProtocol = Field(description="Protocol from which route was learned")
    next_hop: str | None = Field(default=None, description="Next hop IP address")
    outgoing_interface: str | None = Field(
        default=None, description="Outgoing egress interface name"
    )
    vrf: str = Field(default="default", description="VRF instance name")
    distance: int | None = Field(default=None, description="Administrative distance")
    metric: int | None = Field(default=None, description="Route metric")
    active: bool = Field(default=True, description="Whether route is active in FIB")
    age_seconds: int | None = Field(default=None, description="Route age in seconds")
