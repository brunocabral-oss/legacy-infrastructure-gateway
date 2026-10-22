"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for Legacy Infrastructure Gateway."""

    # Application
    app_name: str = "Legacy Infrastructure Gateway"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Policies & Security
    read_only_mode: bool = True
    raw_commands_enabled: bool = False
    configuration_changes_enabled: bool = False
    default_policy: str = "deny"
    global_timeout_seconds: int = 30
    device_concurrency_limit: int = 3

    # Database
    database_url: str = "sqlite+aiosqlite:///./lig.sqlite3"

    # Mock settings
    enable_mock_driver: bool = True

    model_config = SettingsConfigDict(
        env_prefix="LIG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
