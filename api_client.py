import os
import httpx

P1_API_URL = os.getenv("P1_API_URL", "").rstrip("/")
ROUTE_API_TOKEN = os.getenv("ROUTE_API_TOKEN", "")


async def get_route(route_id: int) -> dict | None:
    if not P1_API_URL:
        raise RuntimeError("P1_API_URL not configured")
    if not ROUTE_API_TOKEN:
        raise RuntimeError("ROUTE_API_TOKEN not configured")
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{P1_API_URL}/api/route/{route_id}",
            headers={"Authorization": f"Bearer {ROUTE_API_TOKEN}"},
        )
    if resp.status_code == 404:
        return None
    if resp.status_code == 401:
        raise RuntimeError("Invalid ROUTE_API_TOKEN — check Railway env vars")
    resp.raise_for_status()
    return resp.json()
