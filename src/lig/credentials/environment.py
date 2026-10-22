"""Environment and YAML file-based credential provider."""

import os
from pathlib import Path
from typing import Any

import yaml

from lig.credentials.base import CredentialProvider, DeviceCredential


class EnvironmentCredentialProvider(CredentialProvider):
    """Retrieves device credentials from credentials.yaml or environment variables.

    Lookup Order:
      1. Environment variables:
         LIG_CRED_<PROFILE>_USERNAME
         LIG_CRED_<PROFILE>_PASSWORD
         LIG_CRED_<PROFILE>_SECRET
         LIG_CRED_<PROFILE>_SSH_KEY_FILE
      2. Configuration file:
         config/credentials.yaml, credentials.yaml, /app/config/credentials.yaml
      3. Safe development fallbacks
    """

    def __init__(
        self,
        fallback_username: str = "lig_reader_lab",
        fallback_password: str = "mock_pass",
        config_path: str | Path | None = None,
    ) -> None:
        self.fallback_username = fallback_username
        self.fallback_password = fallback_password
        self._file_credentials: dict[str, dict[str, Any]] = {}
        self._load_file_credentials(config_path)

    def _load_file_credentials(self, explicit_path: str | Path | None) -> None:
        candidate_paths = [
            explicit_path,
            os.environ.get("LIG_CREDENTIALS_FILE"),
            Path("config/credentials.yaml"),
            Path("credentials.yaml"),
            Path("/app/config/credentials.yaml"),
        ]

        for p in candidate_paths:
            if p and Path(p).is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        if "credentials" in data and isinstance(data["credentials"], dict):
                            self._file_credentials = data["credentials"]
                        elif isinstance(data, dict):
                            self._file_credentials = data
                        break
                except Exception:
                    pass

    def get_credential(self, profile_name: str) -> DeviceCredential:
        prefix = f"LIG_CRED_{profile_name.upper()}_"
        file_profile = self._file_credentials.get(profile_name, {})

        username = (
            os.environ.get(f"{prefix}USERNAME")
            or file_profile.get("username")
            or self.fallback_username
        )
        password = (
            os.environ.get(f"{prefix}PASSWORD")
            or file_profile.get("password")
            or self.fallback_password
        )
        secret = os.environ.get(f"{prefix}SECRET") or file_profile.get("secret")
        ssh_key_file = os.environ.get(f"{prefix}SSH_KEY_FILE") or file_profile.get("ssh_key_file")

        return DeviceCredential(
            username=str(username),
            password=str(password),
            secret=secret,
            ssh_key_file=ssh_key_file,
        )
