"""Tests for the health endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(app_client):
    response = await app_client.get("/api/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["version"] == "0.1.0"
    assert "qdrant_connected" in data
    assert "postgres_connected" in data
