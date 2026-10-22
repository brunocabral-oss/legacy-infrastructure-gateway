"""Integration tests for security, token authentication, and rate limiting."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from lig.main import app
from lig.security.rate_limit import SlidingWindowRateLimiter


@pytest.fixture
async def unauthed_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_api_v1_rejects_unauthenticated_request(unauthed_client: AsyncClient) -> None:
    response = await unauthed_client.get("/api/v1/devices")
    assert response.status_code == 401
    assert "Authentication credentials were not provided" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_v1_rejects_invalid_token(unauthed_client: AsyncClient) -> None:
    headers = {"X-API-Key": "invalid_fake_token_12345"}
    response = await unauthed_client.get("/api/v1/devices", headers=headers)
    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_v1_accepts_bearer_token(unauthed_client: AsyncClient) -> None:
    headers = {"Authorization": "Bearer lig_reader_dev_token"}
    response = await unauthed_client.get("/api/v1/devices", headers=headers)
    assert response.status_code == 200
    devices = response.json()
    assert isinstance(devices, list)


@pytest.mark.asyncio
async def test_api_v1_accepts_api_key_header(unauthed_client: AsyncClient) -> None:
    headers = {"X-API-Key": "lig_reader_dev_token"}
    response = await unauthed_client.get("/api/v1/devices", headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_and_metrics_remain_public(unauthed_client: AsyncClient) -> None:
    # Public health endpoints MUST not require authentication
    res_live = await unauthed_client.get("/health/live")
    assert res_live.status_code == 200

    res_ready = await unauthed_client.get("/health/ready")
    assert res_ready.status_code == 200

    res_metrics = await unauthed_client.get("/metrics")
    assert res_metrics.status_code == 200


def test_sliding_window_rate_limiter() -> None:
    # Test rate limiter logic directly with tight limit
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10)
    key = "test_client_ip"

    # 3 allowed
    limiter.check_rate_limit(key)
    limiter.check_rate_limit(key)
    limiter.check_rate_limit(key)

    # 4th must raise 429
    with pytest.raises(HTTPException) as exc_info:
        limiter.check_rate_limit(key)
    assert "Rate limit exceeded" in str(exc_info.value.detail)
