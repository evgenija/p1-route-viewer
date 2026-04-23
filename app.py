import os
from datetime import datetime

import polyline as polyline_lib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api_client import get_route

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def _classify_suspicious(wp: dict, prev_wp: dict | None) -> dict | None:
    if not wp["is_suspicious"] or not prev_wp:
        return None
    try:
        t1 = datetime.fromisoformat(prev_wp["timestamp"])
        t2 = datetime.fromisoformat(wp["timestamp"])
        gap_min = (t2 - t1).total_seconds() / 60
        if gap_min >= 60:
            return {"type": "C", "hours": int(gap_min // 60), "mins": int(gap_min % 60)}
        return {"type": "B", "speed": wp.get("speed_kmh"), "gap_min": int(gap_min)}
    except Exception:
        return {"type": "unknown"}


def _error_badge(pct: float | None) -> str:
    if pct is None:
        return ""
    if pct <= 5:
        return "✅"
    if pct <= 12:
        return "🔶"
    return "🔴"


@app.get("/")
async def root():
    return {"status": "ok", "service": "p1-route-viewer"}


@app.get("/route/{route_id}", response_class=HTMLResponse)
async def show_route(request: Request, route_id: int):
    try:
        data = await get_route(route_id)
    except Exception as exc:
        return HTMLResponse(f"<h2>Помилка з'єднання з P1: {exc}</h2>", status_code=502)

    if data is None:
        return templates.TemplateResponse(
            request, "404.html", {"route_id": route_id}, status_code=404
        )

    decoded_polyline = None
    if data.get("route_polyline"):
        try:
            decoded_polyline = polyline_lib.decode(data["route_polyline"])
        except Exception:
            pass

    odometer_diff = None
    error_pct = None
    if data.get("odometer_start") and data.get("odometer_finish"):
        odometer_diff = round(data["odometer_finish"] - data["odometer_start"], 1)
        if odometer_diff > 0 and data.get("total_km"):
            error_pct = round(abs(data["total_km"] - odometer_diff) / odometer_diff * 100, 1)

    waypoints = data["waypoints"]
    for i, wp in enumerate(waypoints):
        prev = waypoints[i - 1] if i > 0 else None
        wp["suspicious_info"] = _classify_suspicious(wp, prev)

    suspicious_count = sum(1 for wp in waypoints if wp["is_suspicious"])

    try:
        start_dt = datetime.fromisoformat(data["start_time"])
        date_str = start_dt.strftime("%d.%m.%Y")
    except Exception:
        date_str = ""

    return templates.TemplateResponse(request, "route.html", {
        "route": data,
        "decoded_polyline": decoded_polyline,
        "odometer_diff": odometer_diff,
        "error_pct": error_pct,
        "error_badge": _error_badge(error_pct),
        "suspicious_count": suspicious_count,
        "date_str": date_str,
    })
