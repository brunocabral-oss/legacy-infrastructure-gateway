"""Unit tests for the AuditService and credential redaction."""

from lig.core.audit_service import AuditService, redact_sensitive_data
from lig.models.audit import AuditDecision, AuditResult


def test_redact_sensitive_keys() -> None:
    raw_payload = {
        "username": "admin",
        "password": "supersecretpassword123",
        "api_token": "token_abc123456",
        "enable_secret": "cisco_enable_pass",
        "community": "public",
        "nested": {
            "private_key": "-----BEGIN RSA PRIVATE KEY-----",
            "normal_field": "visible_value",
        },
    }

    cleaned = redact_sensitive_data(raw_payload)

    assert cleaned["username"] == "admin"
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["api_token"] == "[REDACTED]"
    assert cleaned["enable_secret"] == "[REDACTED]"
    assert cleaned["community"] == "[REDACTED]"
    assert cleaned["nested"]["private_key"] == "[REDACTED]"
    assert cleaned["nested"]["normal_field"] == "visible_value"


def test_audit_service_recording() -> None:
    service = AuditService()
    event = service.record_event(
        request_id="req_test_001",
        device="VDORTD-A",
        operation="routes.read",
        source_ip="192.168.1.50",
        decision=AuditDecision.ALLOWED,
        result=AuditResult.SUCCESS,
        duration_ms=45,
        parameters={"vrf": "lab", "password": "should_be_redacted"},
    )

    assert event.request_id == "req_test_001"
    assert event.decision == AuditDecision.ALLOWED
    assert event.parameters["vrf"] == "lab"
    assert event.parameters["password"] == "[REDACTED]"
    assert len(service.get_events()) == 1
