"""Integration tests for REST API endpoints using FastAPI TestClient."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from lig.api.dependencies import get_audit_service
from lig.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"X-API-Key": "lig_reader_dev_token"},
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_ready(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["mock_driver_registered"] == "True"


@pytest.mark.asyncio
async def test_metrics(client: AsyncClient) -> None:
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "lig_http_requests_total" in response.text


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient) -> None:
    response = await client.get("/api/v1/devices")
    assert response.status_code == 200
    devices = response.json()
    assert len(devices) >= 1
    device_names = [d["name"] for d in devices]
    assert "mock-router" in device_names


@pytest.mark.asyncio
async def test_get_device_capabilities(client: AsyncClient) -> None:
    response = await client.get("/api/v1/devices/mock-router/capabilities")
    assert response.status_code == 200
    caps = response.json()
    assert caps["driver"] == "mock_driver"
    assert "facts.read" in caps["capabilities"]
    assert caps["capabilities"]["facts.read"]["supported"] is True


@pytest.mark.asyncio
async def test_get_device_facts(client: AsyncClient) -> None:
    response = await client.get("/api/v1/devices/mock-router/facts")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["device"] == "mock-router"
    assert body["operation"] == "facts.read"
    assert body["data"]["hostname"] == "VDORTD-A"
    assert body["data"]["vendor"] == "Cisco"
    assert body["metadata"]["normalized"] is True
    assert "x-request-id" in response.headers


@pytest.mark.asyncio
async def test_get_device_routes_with_filter(client: AsyncClient) -> None:
    response = await client.get("/api/v1/devices/mock-router/routes?vrf=lab")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    routes = body["data"]
    assert len(routes) == 1
    assert routes[0]["vrf"] == "lab"
    assert routes[0]["prefix"] == "192.0.2.48/32"
    assert routes[0]["next_hop"] == "198.51.100.140"


@pytest.mark.asyncio
async def test_unsupported_capability_returns_501(client: AsyncClient) -> None:
    # MAC table is explicitly unsupported on mock-router
    response = await client.get("/api/v1/devices/mock-router/mac-addresses")
    assert response.status_code == 501
    err = response.json()
    assert err["error_code"] == "CAPABILITY_NOT_SUPPORTED"
    assert "MAC address table not available" in err["message"]


@pytest.mark.asyncio
async def test_unknown_device_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/devices/nonexistent-device-999/facts")
    assert response.status_code == 404
    err = response.json()
    assert err["error_code"] == "DEVICE_NOT_FOUND"


@pytest.mark.asyncio
async def test_diagnostics_ping(client: AsyncClient) -> None:
    payload = {
        "destination": "192.168.199.48",
        "count": 5,
        "timeout_seconds": 2,
    }
    response = await client.post("/api/v1/devices/mock-router/diagnostics/ping", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["destination"] == "192.168.199.48"
    assert body["data"]["packets_transmitted"] == 5
    assert body["data"]["packet_loss_percentage"] == 0.0


@pytest.mark.asyncio
async def test_audit_log_generation(client: AsyncClient) -> None:
    audit_service = get_audit_service()
    initial_count = len(audit_service.get_events())

    # Make a call
    await client.get("/api/v1/devices/mock-router/interfaces")

    events = audit_service.get_events()
    assert len(events) > initial_count
    last_event = events[-1]
    assert last_event.device == "mock-router"
    assert last_event.operation == "interfaces.read"
    assert last_event.result == "success"
