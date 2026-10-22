"""Base credential models and provider interface."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class DeviceCredential(BaseModel):
    """Normalized credential for device authentication."""

    username: str = Field(description="Service username")
    password: str = Field(description="Service password")
    secret: str | None = Field(default=None, description="Optional enable/privileged password")
    ssh_key_file: str | None = Field(default=None, description="Optional path to private SSH key")


class CredentialProvider(ABC):
    """Abstract interface for retrieving credentials by profile name."""

    @abstractmethod
    def get_credential(self, profile_name: str) -> DeviceCredential:
        """Retrieve credentials for the specified profile.

        Raises KeyError or LIGException if profile is not found.
        """
        ...
