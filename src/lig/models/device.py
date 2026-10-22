"""Device representation and inventory models."""

from enum import Enum

from pydantic import BaseModel, Field


class DevicePlatform(str, Enum):
    """Supported vendor platforms in LIG."""

    CISCO_IOS = "cisco_ios"
    CISCO_IOSXR = "cisco_iosxr"
    FORTIOS = "fortios"
    GENERIC_SSH = "generic_ssh"
    MOCK = "mock"


class DeviceTransport(str, Enum):
    """Transport protocol used to communicate with the device."""

    SSH = "ssh"
    NAPALM = "napalm"
    MOCK = "mock"


class Device(BaseModel):
    """Device entity in the inventory."""

    name: str = Field(description="Unique device identifier / hostname")
    host: str = Field(description="IP address or FQDN for management")
    platform: DevicePlatform = Field(description="Operating platform / OS")
    transport: DeviceTransport = Field(
        default=DeviceTransport.SSH, description="Communication transport"
    )
    port: int = Field(default=22, description="Management port")
    credential_profile: str = Field(
        default="lab_reader", description="Reference to credential profile"
    )
    site: str = Field(default="lab", description="Physical or logical site")
    environment: str = Field(default="lab", description="Environment: lab, staging, production")
    enabled: bool = Field(default=True, description="Whether device is active for operations")
