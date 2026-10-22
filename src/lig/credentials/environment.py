"""Environment variable-based credential provider."""

import os

from lig.credentials.base import CredentialProvider, DeviceCredential


class EnvironmentCredentialProvider(CredentialProvider):
    """Retrieves device credentials from environment variables.

    Pattern:
      LIG_CRED_<PROFILE>_USERNAME
      LIG_CRED_<PROFILE>_PASSWORD
      LIG_CRED_<PROFILE>_SECRET
      LIG_CRED_<PROFILE>_SSH_KEY_FILE
    """

    def __init__(
        self, fallback_username: str = "lig_reader_lab", fallback_password: str = "mock_pass"
    ) -> None:
        self.fallback_username = fallback_username
        self.fallback_password = fallback_password

    def get_credential(self, profile_name: str) -> DeviceCredential:
        prefix = f"LIG_CRED_{profile_name.upper()}_"
        username = os.environ.get(f"{prefix}USERNAME") or self.fallback_username
        password = os.environ.get(f"{prefix}PASSWORD") or self.fallback_password
        secret = os.environ.get(f"{prefix}SECRET")
        ssh_key_file = os.environ.get(f"{prefix}SSH_KEY_FILE")

        return DeviceCredential(
            username=username,
            password=password,
            secret=secret,
            ssh_key_file=ssh_key_file,
        )
