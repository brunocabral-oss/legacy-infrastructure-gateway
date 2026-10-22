"""Common and generic models for the normalized domain."""

from datetime import datetime, timezone
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class FieldAvailability(str, Enum):
    """Semantic availability status for attributes that may not be supported by all vendors."""

    AVAILABLE = "available"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class OperationMetadata(BaseModel):
    """Metadata describing the operational execution and translation details."""

    driver: str = Field(description="Name of the driver used for the operation")
    transport: str = Field(description="Transport protocol (e.g., ssh, napalm, mock)")
    normalized: bool = Field(
        default=True, description="Indicates if the data follows normalized schema"
    )
    duration_ms: int = Field(description="Operation duration in milliseconds")
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the collection",
    )
    warnings: list[str] = Field(
        default_factory=list, description="Any operational or parsing warnings"
    )
    unsupported_fields: list[str] = Field(
        default_factory=list,
        description="Fields defined in normalized contract but not supported by this platform",
    )


T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standardized API response wrapper according to LIG specification."""

    request_id: str = Field(description="Unique correlation ID for tracing and audit")
    device: str = Field(description="Target device identifier")
    operation: str = Field(description="Semantic operation performed (e.g. routes.read)")
    status: str = Field(default="success", description="Execution status: success or error")
    data: T = Field(description="Payload data")
    metadata: OperationMetadata = Field(description="Operational execution metadata")


class ErrorResponse(BaseModel):
    """Standardized error envelope."""

    request_id: str
    device: str | None = None
    operation: str | None = None
    error_code: str
    message: str
    detail: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
