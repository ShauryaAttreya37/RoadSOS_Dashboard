from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

import pydeck as pdk
import requests


OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
TOMTOM_FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/14/json"
TOMTOM_INCIDENTS_URL = "https://api.tomtom.com/traffic/services/5/incidentDetails"
DARK_MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
HTTP_TIMEOUT_SECONDS = (4, 18)
MAX_ROAD_RADIUS_M = 5000
MAX_ROADS = 180
MAX_FLOW_SAMPLES = 18

GREEN = [118, 185, 0, 235]
AMBER = [255, 143, 0, 245]
RED = [229, 57, 53, 250]
ROAD_GREY = [164, 177, 190, 210]
USER_BLUE = [79, 195, 247, 255]

_SESSION = requests.Session()

ROAD_PRIORITY = {
    "motorway": 0,
    "trunk": 1,
    "primary": 2,
    "secondary": 3,
    "tertiary": 4,
    "residential": 5,
    "unclassified": 6,
    "service": 7,
}

INCIDENT_LABELS = {
    0: "Unknown",
    1: "Accident",
    2: "Fog",
    3: "Dangerous conditions",
    4: "Rain",
    5: "Ice",
    6: "Traffic jam",
    7: "Lane closed",
    8: "Road closed",
    9: "Road works",
    10: "Wind",
    11: "Flooding",
    14: "Broken-down vehicle",
}


def fetch_road_network(lat: float, lon: float, radius_m: int) -> list[dict[str, Any]]:
    radius_m = min(max(500, int(radius_m)), MAX_ROAD_RADIUS_M)
    query = f"""
[out:json][timeout:18];
way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|service)$"](around:{radius_m},{lat:.7f},{lon:.7f});
out tags geom qt;
""".strip()
    payload = _fetch_overpass(query)
    roads = []
    for element in payload.get("elements", []):
        geometry = element.get("geometry") or []
        path = [
            [float(point["lon"]), float(point["lat"])]
            for point in geometry
            if "lat" in point and "lon" in point
            and _haversine(lat, lon, float(point["lat"]), float(point["lon"])) <= radius_m / 1000 * 1.35
        ]
        if len(path) < 2:
            continue
        tags = element.get("tags") or {}
        highway = str(tags.get("highway", "unclassified"))
        mid_lon, mid_lat = path[len(path) // 2]
        roads.append(
            {
                "road_id": int(element.get("id", 0)),
                "name": str(tags.get("name") or tags.get("ref") or highway.replace("_", " ").title()),
                "highway": highway,
                "path": path,
                "line_color": _road_color(highway),
                "width": _road_width(highway),
                "lat": mid_lat,
                "lon": mid_lon,
                "distance_km": round(_haversine(lat, lon, mid_lat, mid_lon), 2),
                "status": f"Mapped {highway.replace('_', ' ')} road",
                "source": "OpenStreetMap topology",
            }
        )
    roads.sort(key=lambda road: (ROAD_PRIORITY.get(road["highway"], 99), road["distance_km"]))
    return roads[:MAX_ROADS]


def fetch_weather_advisory(lat: float, lon: float) -> dict[str, Any]:
    response = _SESSION.get(
        OPEN_METEO_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    current = response.json().get("current") or {}
    precipitation = float(current.get("precipitation") or 0)
    snowfall = float(current.get("snowfall") or 0)
    wind_speed = float(current.get("wind_speed_10m") or 0)
    risk, advisory = _weather_risk(precipitation, snowfall, wind_speed)
    return {
        "source": "Open-Meteo current conditions",
        "observed_at": str(current.get("time") or "Unavailable"),
        "temperature_c": float(current.get("temperature_2m") or 0),
        "precipitation_mm": precipitation,
        "wind_kmh": wind_speed,
        "weather_code": int(current.get("weather_code") or 0),
        "risk": risk,
        "advisory": advisory,
    }


def fetch_live_traffic(
    lat: float,
    lon: float,
    radius_m: int,
    roads: list[dict[str, Any]],
    api_key: str | None,
) -> dict[str, Any]:
    if not api_key:
        return {
            "configured": False,
            "source": "TomTom Traffic not configured",
            "flows": [],
            "incidents": [],
            "updated_at": None,
            "errors": [],
        }

    sampled_roads = _flow_sample_roads(roads)
    flows = []
    errors = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_fetch_flow_segment, road, api_key): road for road in sampled_roads}
        for future in as_completed(futures):
            try:
                flow = future.result()
                if flow:
                    flows.append(flow)
            except requests.RequestException as exc:
                errors.append(str(exc))

    try:
        incidents = _fetch_incidents(lat, lon, radius_m, api_key)
    except requests.RequestException as exc:
        incidents = []
        errors.append(str(exc))

    return {
        "configured": True,
        "source": "TomTom Traffic live flow and incidents",
        "flows": flows,
        "incidents": incidents,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "errors": errors[:3],
    }


SERVICE_PIN_COLORS: dict[str, list[int]] = {
    "trauma_centre":  [255, 82, 82, 245],
    "hospital":       [229, 57, 53, 230],
    "police":         [79, 195, 247, 230],
    "fire_station":   [255, 110, 64, 230],
    "ambulance":      [255, 143, 0, 230],
    "vehicle_rescue": [118, 185, 0, 230],
    "puncture_shop":  [149, 117, 205, 230],
    "showroom":       [38, 198, 218, 230],
}


def build_road_state_deck(
    lat: float,
    lon: float,
    roads: list[dict[str, Any]],
    traffic: dict[str, Any],
    view_mode: str = "Road Map",
    services: dict[str, list[dict[str, Any]]] | None = None,
) -> pdk.Deck:
    flows = traffic.get("flows") or []
    incidents = traffic.get("incidents") or []
    incident_paths = [incident for incident in incidents if len(incident.get("path") or []) > 1]
    del roads

    # ── Service pins ──────────────────────────────────────────────────────────
    pin_data: list[dict[str, Any]] = []
    if services:
        for category, items in services.items():
            if category.startswith("_"):
                continue
            color = SERVICE_PIN_COLORS.get(category, [200, 200, 200, 200])
            for svc in items:
                svc_lat = svc.get("lat")
                svc_lon = svc.get("lon")
                if svc_lat is None or svc_lon is None:
                    continue
                pin_data.append({
                    "lat": float(svc_lat),
                    "lon": float(svc_lon),
                    "name": svc.get("name", category),
                    "status": f"{svc.get('distance_km', '--')} km · ETA {svc.get('eta_min', '--')} min",
                    "source": category.replace("_", " ").title(),
                    "color": color,
                })

    layers = [
        # Service location pins
        pdk.Layer(
            "ScatterplotLayer",
            pin_data,
            get_position="[lon, lat]",     # string expression — evaluated per row
            get_fill_color="color",
            get_line_color=[255, 255, 255, 160],
            get_radius=60,
            line_width_min_pixels=1,
            stroked=True,
            pickable=True,
            auto_highlight=True,
        ),
        # Rider GPS
        pdk.Layer(
            "ScatterplotLayer",
            [{"lat": lat, "lon": lon,
              "name": "Rider GPS", "status": "Current rider position",
              "source": "Detected location"}],
            get_position="[lon, lat]",     # string expression — evaluated per row
            get_fill_color=USER_BLUE,
            get_line_color=[255, 255, 255, 255],
            get_radius=80,
            line_width_min_pixels=2,
            stroked=True,
            pickable=True,
        ),
    ]
    if flows:
        layers.extend(
            [
                pdk.Layer(
                    "PathLayer",
                    flows,
                    get_path="path",
                    get_color="line_color",
                    get_width="width",
                    width_units="pixels",
                    pickable=True,
                    auto_highlight=True,
                ),
                pdk.Layer(
                    "ColumnLayer",
                    flows,
                    get_position="[lon, lat]",
                    get_elevation="elevation",
                    elevation_scale=1,
                    radius=22,
                    get_fill_color="line_color",
                    disk_resolution=8,
                    pickable=True,
                    extruded=True,
                ),
            ]
        )
    if incident_paths:
        layers.append(
            pdk.Layer(
                "PathLayer",
                incident_paths,
                get_path="path",
                get_color="line_color",
                get_width=8,
                width_units="pixels",
                pickable=True,
            )
        )
    if incidents:
        layers.append(
            pdk.Layer(
                "ColumnLayer",
                incidents,
                get_position="[lon, lat]",
                get_elevation="elevation",
                elevation_scale=1,
                radius=35,
                get_fill_color="line_color",
                disk_resolution=8,
                pickable=True,
                extruded=True,
            )
        )
    is_3d = view_mode == "3D Operations"
    return pdk.Deck(
        map_style=DARK_MAP_STYLE,
        map_provider="carto",
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=13.0,
            min_zoom=10,
            max_zoom=18,
            pitch=38 if is_3d else 0,
            bearing=-18 if is_3d else 0,
        ),
        layers=layers,
        tooltip={
            "html": (
                "<b>{name}</b><br/>"
                "{status}<br/>"
                "<span style='color:#8B949E'>{source}</span>"
            ),
            "style": {
                "backgroundColor": "#0F1115",
                "color": "#F0F6FC",
                "fontFamily": "Inter, sans-serif",
                "border": "1px solid #22252A",
            },
        },
    )


def traffic_summary(traffic: dict[str, Any]) -> dict[str, int]:
    flows = traffic.get("flows") or []
    incidents = traffic.get("incidents") or []
    return {
        "flows": len(flows),
        "congested": sum(flow.get("status") in {"Slow", "Heavy", "Closed"} for flow in flows),
        "incidents": len(incidents),
        "closures": sum(incident.get("category") == "Road closed" for incident in incidents)
        + sum(bool(flow.get("road_closed")) for flow in flows),
    }


def _fetch_overpass(query: str) -> dict[str, Any]:
    headers = {
        "User-Agent": "RoadSoS/1.0 Road Intelligence Dashboard",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    errors = []
    for url in OVERPASS_URLS:
        try:
            response = _SESSION.post(url, data={"data": query}, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("Road topology lookup failed. " + " | ".join(errors))


def _fetch_flow_segment(road: dict[str, Any], api_key: str) -> dict[str, Any] | None:
    response = _SESSION.get(
        TOMTOM_FLOW_URL,
        params={
            "key": api_key,
            "point": f"{road['lat']:.7f},{road['lon']:.7f}",
            "unit": "KMPH",
            "openLr": "false",
        },
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json().get("flowSegmentData") or {}
    if not data:
        return None
    current_speed = float(data.get("currentSpeed") or 0)
    free_flow_speed = float(data.get("freeFlowSpeed") or 0)
    ratio = current_speed / free_flow_speed if free_flow_speed > 0 else 1.0
    road_closed = bool(data.get("roadClosure"))
    status, color = _traffic_status(ratio, road_closed)
    delay_pct = max(0, min(100, round((1 - ratio) * 100)))
    path = _flow_path(data, road["path"])
    return {
        "name": road["name"],
        "status": f"{status}: {current_speed:.0f}/{free_flow_speed:.0f} km/h, {delay_pct}% delay",
        "source": "TomTom Traffic live flow",
        "lat": road["lat"],
        "lon": road["lon"],
        "path": path,
        "line_color": color,
        "width": 7,
        "elevation": 185 if road_closed else 22 + delay_pct * 1.7,
        "current_speed": round(current_speed),
        "free_flow_speed": round(free_flow_speed),
        "confidence": float(data.get("confidence") or 0),
        "road_closed": road_closed,
    }


def _fetch_incidents(lat: float, lon: float, radius_m: int, api_key: str) -> list[dict[str, Any]]:
    min_lon, min_lat, max_lon, max_lat = _bounding_box(lat, lon, min(radius_m, MAX_ROAD_RADIUS_M))
    fields = (
        "{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,"
        "events{description,code,iconCategory},startTime,endTime,from,to,length,delay,roadNumbers,"
        "timeValidity,probabilityOfOccurrence,numberOfReports,lastReportTime}}}"
    )
    response = _SESSION.get(
        TOMTOM_INCIDENTS_URL,
        params={
            "key": api_key,
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "fields": fields,
            "language": "en-GB",
            "timeValidityFilter": "present",
        },
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    incidents = []
    for incident in response.json().get("incidents") or []:
        geometry = incident.get("geometry") or {}
        properties = incident.get("properties") or {}
        path, point = _incident_geometry(geometry)
        if point is None:
            continue
        category = INCIDENT_LABELS.get(int(properties.get("iconCategory") or 0), "Traffic incident")
        events = properties.get("events") or []
        description = str(events[0].get("description")) if events else category
        incidents.append(
            {
                "name": category,
                "status": description,
                "source": "TomTom Traffic live incident",
                "category": category,
                "lat": point[1],
                "lon": point[0],
                "path": path,
                "line_color": RED,
                "elevation": 145,
                "delay_seconds": properties.get("delay"),
                "last_report_time": properties.get("lastReportTime"),
            }
        )
    return incidents[:60]


def _flow_sample_roads(roads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    seen = set()
    for road in roads:
        identity = (road["name"], round(float(road["lat"]), 3), round(float(road["lon"]), 3))
        if identity in seen:
            continue
        seen.add(identity)
        selected.append(road)
        if len(selected) >= MAX_FLOW_SAMPLES:
            break
    return selected


def _flow_path(data: dict[str, Any], fallback: list[list[float]]) -> list[list[float]]:
    coordinates = ((data.get("coordinates") or {}).get("coordinate")) or []
    path = [
        [float(point["longitude"]), float(point["latitude"])]
        for point in coordinates
        if "latitude" in point and "longitude" in point
    ]
    if len(path) >= 2:
        return path
    return [[point[0], point[1]] for point in fallback]


def _incident_geometry(geometry: dict[str, Any]) -> tuple[list[list[float]], list[float] | None]:
    coordinates = geometry.get("coordinates") or []
    if geometry.get("type") == "Point" and len(coordinates) >= 2:
        point = [float(coordinates[0]), float(coordinates[1])]
        return [[point[0], point[1]]], point
    if geometry.get("type") == "LineString" and coordinates:
        path = [[float(point[0]), float(point[1])] for point in coordinates if len(point) >= 2]
        return path, path[len(path) // 2][:2] if path else None
    return [], None


def _weather_risk(precipitation: float, snowfall: float, wind_speed: float) -> tuple[str, str]:
    if snowfall > 0:
        return "HIGH", "Snowfall is active. Treat exposed roads as potentially slippery."
    if precipitation >= 2.5:
        return "HIGH", "Heavy precipitation is active. Expect reduced grip and visibility."
    if precipitation > 0:
        return "ELEVATED", "Precipitation is active. Wet-surface exposure is possible."
    if wind_speed >= 40:
        return "ELEVATED", "Strong wind is active. Use caution on open roads and flyovers."
    return "LOW", "No weather-driven road hazard is indicated by the current observation."


def _traffic_status(ratio: float, road_closed: bool) -> tuple[str, list[int]]:
    if road_closed:
        return "Closed", RED
    if ratio < 0.45:
        return "Heavy", RED
    if ratio < 0.72:
        return "Slow", AMBER
    return "Flowing", GREEN


def _road_width(highway: str) -> int:
    return max(2, 8 - ROAD_PRIORITY.get(highway, 7) // 2)


def _road_color(highway: str) -> list[int]:
    priority = ROAD_PRIORITY.get(highway, 7)
    if priority <= 2:
        return [190, 205, 220, 245]
    if priority <= 4:
        return ROAD_GREY
    return [115, 130, 145, 175]


def _bounding_box(lat: float, lon: float, radius_m: int) -> tuple[float, float, float, float]:
    lat_delta = radius_m / 111_320
    lon_delta = radius_m / max(1, 111_320 * math.cos(math.radians(lat)))
    return lon - lon_delta, lat - lat_delta, lon + lon_delta, lat + lat_delta


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))
