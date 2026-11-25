#!/usr/bin/env python3
"""Standalone demonstration script for Legacy Infrastructure Gateway (LIG).

Queries the FastAPI application using TestClient (zero external network/hardware required),
exercising liveness, device inventory, normalized device facts, routes, and audit logs,
and printing clean formatted JSON output.
"""

import json
import sys

from fastapi.testclient import TestClient

from lig.main import app


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_json(data: dict | list) -> None:
    print(json.dumps(data, indent=2))


def main() -> None:
    print_section("Legacy Infrastructure Gateway (LIG) - Multivendor Demo")

    # Initialize TestClient with authentication header required for /api/v1/ endpoints
    token = "lig_reader_dev_token"
    client = TestClient(app, headers={"X-API-Key": token})

    # 1. Health / Liveness Probe
    print_section("1. Liveness Probe (/health/live)")
    response = client.get("/health/live")
    print(f"Status Code: {response.status_code}")
    print_json(response.json())
    assert response.status_code == 200

    # 2. Readiness Probe
    print_section("2. Readiness Probe (/health/ready)")
    response = client.get("/health/ready")
    print(f"Status Code: {response.status_code}")
    print_json(response.json())
    assert response.status_code == 200

    # 3. Device Inventory List (/api/v1/devices)
    print_section("3. Device Inventory (/api/v1/devices)")
    response = client.get("/api/v1/devices")
    print(f"Status Code: {response.status_code}")
    devices = response.json()
    print_json(devices)
    assert response.status_code == 200
    assert len(devices) > 0

    # Extract available device IDs/names
    device_names = [d["name"] for d in devices]
    print(f"\nDiscovered Device IDs in Inventory: {device_names}")

    # Pick a target device for operational queries (e.g. 'mock-router' or first available)
    target_device = "mock-router" if "mock-router" in device_names else device_names[0]
    print(f"Selected target device for operational queries: '{target_device}'")

    # 4. Normalized Device Facts (/api/v1/devices/{device}/facts)
    print_section(f"4. Normalized Device Facts (/api/v1/devices/{target_device}/facts)")
    response = client.get(f"/api/v1/devices/{target_device}/facts")
    print(f"Status Code: {response.status_code}")
    print_json(response.json())
    assert response.status_code == 200

    # 5. Routing Table (/api/v1/devices/{device}/routes)
    print_section(f"5. Routing Table (/api/v1/devices/{target_device}/routes)")
    response = client.get(f"/api/v1/devices/{target_device}/routes")
    print(f"Status Code: {response.status_code}")
    print_json(response.json())
    assert response.status_code == 200

    # 6. Audit Logs (/api/v1/diagnostics/audit or via audit service / test verification)
    # Check api routers or audit endpoint if available, or write audit logs via dependency
    print_section("6. Audit Log Records")
    from lig.api.dependencies import get_audit_service
    audit_service = get_audit_service()
    events = audit_service.get_events(limit=5)
    audit_payload = [e.model_dump(mode="json") for e in events]
    print_json(audit_payload)
    assert len(audit_payload) > 0

    print_section("Demo Completed Successfully with Exit Code 0!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}", file=sys.stderr)
        sys.exit(1)
