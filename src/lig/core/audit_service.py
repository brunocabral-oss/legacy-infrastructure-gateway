"""Audit service recording immutable interaction events and ensuring credential redaction."""

import json
import logging
from typing import Any
from uuid import uuid4

from lig.models.audit import AuditDecision, AuditEvent, AuditResult

logger = logging.getLogger("lig.audit")

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "private_key",
    "authorization",
    "community",
    "credential",
    "key",
}


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redact sensitive key values from dictionaries or lists."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_sensitive_data(v)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    return data


class AuditService:
    """Service responsible for emitting immutable audit logs and storing audit telemetry."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record_event(
        self,
        request_id: str,
        device: str,
        operation: str,
        source_ip: str,
        decision: AuditDecision,
        result: AuditResult,
        duration_ms: int,
        driver: str = "core",
        transport: str = "none",
        actor: str = "anonymous",
        parameters: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> AuditEvent:
        """Create, log and persist an audit event."""
        clean_params = redact_sensitive_data(parameters or {})
        clean_err_msg = redact_sensitive_data(error_message) if error_message else None

        event = AuditEvent(
            event_id=f"evt_{uuid4().hex[:12]}",
            request_id=request_id,
            actor=actor,
            consumer="rest-api",
            source_ip=source_ip,
            device=device,
            operation=operation,
            parameters=clean_params,
            decision=decision,
            driver=driver,
            transport=transport,
            result=result,
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=clean_err_msg,
        )

        self._events.append(event)
        # Emit structured log output
        logger.info("AUDIT_EVENT: %s", json.dumps(event.model_dump(mode="json")))
        return event

    def get_events(self, limit: int = 100) -> list[AuditEvent]:
        """Retrieve recorded in-memory events for diagnostics/testing."""
        return self._events[-limit:]
