"""Device facts normalized model."""

from pydantic import BaseModel, Field


class DeviceFacts(BaseModel):
    """Normalized device system facts."""

    hostname: str = Field(description="Configured device hostname")
    fqdn: str | None = Field(default=None, description="Fully qualified domain name")
    vendor: str = Field(description="Hardware vendor (e.g. Cisco, Fortinet)")
    model: str = Field(description="Hardware chassis or model name")
    os_version: str = Field(description="Operating system release version")
    serial_number: str | None = Field(default=None, description="Primary chassis serial number")
    uptime_seconds: int | None = Field(default=None, description="System uptime in seconds")
    interfaces_count: int | None = Field(
        default=None, description="Total physical/logical interfaces"
    )
