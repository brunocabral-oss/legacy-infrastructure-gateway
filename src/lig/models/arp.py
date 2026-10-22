"""ARP table normalized model."""

from pydantic import BaseModel, Field


class ArpEntry(BaseModel):
    """Normalized ARP table entry."""

    ip_address: str = Field(description="IPv4 address")
    mac_address: str = Field(description="Hardware MAC address")
    interface: str = Field(description="Associated interface name")
    age_seconds: int | None = Field(default=None, description="ARP cache age in seconds")
    entry_type: str = Field(default="dynamic", description="Type: dynamic, static, or local")
