"""
Unit тести для api_client.py — не потребують живого P1.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


MOCK_ROUTE = {
    "route_id": 42,
    "driver_id": 123,
    "driver_name": "Іван Тестовий",
    "start_time": "2026-04-23T08:00:00",
    "end_time": "2026-04-23T17:00:00",
    "total_km": 153.5,
    "odometer_start": 15000.0,
    "odometer_finish": 15153.5,
    "route_polyline": "abc~encoded",
    "waypoints": [],
}


def _make_response(status_code: int, json_data=None, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


def test_get_route_returns_none_on_404():
    import asyncio
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_make_response(404))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("api_client.P1_API_URL", "https://example.com"), \
         patch("api_client.ROUTE_API_TOKEN", "token123"), \
         patch("httpx.AsyncClient", return_value=mock_cm):
        from api_client import get_route
        result = asyncio.run(get_route(9999))
    assert result is None


def test_get_route_returns_dict_on_200():
    import asyncio
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_make_response(200, json_data=MOCK_ROUTE))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("api_client.P1_API_URL", "https://example.com"), \
         patch("api_client.ROUTE_API_TOKEN", "token123"), \
         patch("httpx.AsyncClient", return_value=mock_cm):
        from api_client import get_route
        result = asyncio.run(get_route(42))
    assert result is not None
    assert result["route_id"] == 42
    assert result["driver_name"] == "Іван Тестовий"


def test_get_route_raises_on_401():
    import asyncio
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_make_response(401))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("api_client.P1_API_URL", "https://example.com"), \
         patch("api_client.ROUTE_API_TOKEN", "wrong"), \
         patch("httpx.AsyncClient", return_value=mock_cm):
        from api_client import get_route
        with pytest.raises(RuntimeError, match="ROUTE_API_TOKEN"):
            asyncio.run(get_route(42))


def test_get_route_raises_without_p1_url():
    import asyncio
    with patch("api_client.P1_API_URL", ""):
        from api_client import get_route
        with pytest.raises(RuntimeError, match="P1_API_URL"):
            asyncio.run(get_route(1))
