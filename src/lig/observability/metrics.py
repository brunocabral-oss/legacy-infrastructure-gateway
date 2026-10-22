"""Prometheus metrics instrumentation."""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "lig_http_requests_total",
    "Total HTTP requests handled by LIG",
    ["method", "endpoint", "status_code"],
)

OPERATION_DURATION = Histogram(
    "lig_device_operation_duration_seconds",
    "Duration of device operations in seconds",
    ["device", "operation", "status"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

AUDIT_EVENTS = Counter(
    "lig_audit_events_total",
    "Total audit events recorded",
    ["operation", "decision", "result"],
)


def get_metrics_payload() -> tuple[bytes, str]:
    """Generate Prometheus scrape payload."""
    return generate_latest(), CONTENT_TYPE_LATEST
