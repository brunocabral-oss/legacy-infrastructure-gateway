"""Audit event models according to the LIG specification."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuditDecision(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"


class AuditResult(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class AuditEvent(BaseModel):
    """Immutable audit log event recording every gateway interaction."""

    event_id: str = Field(description="Unique event ID")
    request_id: str = Field(description="Correlating HTTP request ID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC event timestamp",
    )
    actor: str = Field(
        default="anonymous", description="User or service identity requesting operation"
    )
    consumer: str = Field(
        default="rest-api", description="Interface or system consuming the gateway"
    )
    source_ip: str = Field(description="Client IP address initiating the request")
    device: str = Field(description="Target network device name")
    operation: str = Field(description="Semantic operation requested (e.g. routes.read)")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Non-sensitive operation parameters (redacted)",
    )
    decision: AuditDecision = Field(description="Policy decision: allowed or denied")
    driver: str = Field(description="Driver handling the request")
    transport: str = Field(description="Transport protocol utilized")
    result: AuditResult = Field(description="Execution result")
    duration_ms: int = Field(description="Total execution time in milliseconds")
    error_code: str | None = Field(default=None, description="Standardized error code if failed")
    error_message: str | None = Field(default=None, description="Redacted error message if failed")
