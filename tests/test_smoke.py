"""
Smoke тести для app.py — перевіряють що endpoints відповідають.
Запускаються з живим сервером або через httpx.AsyncClient(app=app).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, AsyncMock

os.environ.setdefault("P1_API_URL", "https://example.com")
os.environ.setdefault("ROUTE_API_TOKEN", "test_token")


@pytest.fixture
def client():
    from httpx import AsyncClient, ASGITransport
    from app import app
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_root_returns_ok(client):
    async with client as c:
        resp = await c.get("/")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_route_not_found_returns_404(client):
    with patch("app.get_route", new=AsyncMock(return_value=None)):
        async with client as c:
            resp = await c.get("/route/99999")
    assert resp.status_code == 404
    assert "<div" in resp.text


@pytest.mark.asyncio
async def test_route_found_returns_200_with_map(client):
    mock_data = {
        "route_id": 99,
        "driver_id": 1,
        "driver_name": "Тест Водій",
        "start_time": "2026-04-23T08:00:00",
        "end_time": "2026-04-23T17:00:00",
        "total_km": 100.0,
        "odometer_start": 10000.0,
        "odometer_finish": 10100.0,
        "route_polyline": None,
        "waypoints": [
            {"id": 1, "name": "Старт", "lat": 50.45, "lon": 30.52,
             "timestamp": "2026-04-23T08:00:00", "is_suspicious": False,
             "distance_km": None, "speed_kmh": None},
            {"id": 2, "name": "Фініш", "lat": 50.50, "lon": 30.60,
             "timestamp": "2026-04-23T17:00:00", "is_suspicious": False,
             "distance_km": 8.5, "speed_kmh": 45.0},
        ],
    }
    with patch("app.get_route", new=AsyncMock(return_value=mock_data)):
        async with client as c:
            resp = await c.get("/route/99")
    assert resp.status_code == 200
    assert 'id="map"' in resp.text
    assert "Маршрут #99" in resp.text
