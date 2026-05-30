import math
import re
from typing import Any

import requests

from roadsos_app.modules.offline_cache import cache_age_hours, load_cache, save_cache


OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
)
HTTP_TIMEOUT_SECONDS = (4, 25)
GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

# Bump when the query/category schema changes so stale on-disk caches are ignored.
CACHE_SCHEMA_VERSION = "v4"

_SESSION = requests.Session()

OVERPASS_TAGS = {
    "hospital": [
        ("amenity", "hospital"),
        ("amenity", "clinic"),
        ("amenity", "doctors"),
        ("healthcare", "hospital"),
        ("healthcare", "clinic"),
    ],
    "police": [
        ("amenity", "police"),
        ("government", "police"),
    ],
    "fire_station": [
        ("amenity", "fire_station"),
        ("emergency", "fire_station"),
    ],
    "ambulance": [
        ("emergency", "ambulance_station"),
        ("emergency", "ambulance"),
        ("amenity", "ambulance_station"),
        ("healthcare", "ambulance_station"),
        ("healthcare", "ambulance"),
        ("service", "ambulance"),
    ],
    "vehicle_rescue": [
        ("emergency", "rescue"),
        ("emergency", "towing"),
        ("shop", "towing"),
        ("service", "vehicle:towing"),
        ("service", "towing"),
        ("office", "roadside_assistance"),
    ],
    "puncture_shop": [
        ("shop", "tyres"),
        ("shop", "car_repair"),
        ("shop", "motorcycle_repair"),
        ("craft", "car_repair"),
        ("shop", "car"),
    ],
}

NAME_PATTERNS = {
    "ambulance": re.compile(r"\b(ambulance|ems|paramedic)\b", re.IGNORECASE),
    "vehicle_rescue": re.compile(
        r"\b(tow|towing|roadside assistance|breakdown recovery|vehicle recovery)\b",
        re.IGNORECASE,
    ),
    "puncture_shop": re.compile(
        r"\b(puncture|puncher|tyres?|tires?|auto garage|car garage|bike repair|motorcycle repair|car repair)\b",
        re.IGNORECASE,
    ),
}

GOOGLE_PLACES_SEARCHES = {
    "hospital": ("hospital emergency room", "hospital"),
    "police": ("police station", "police"),
    "fire_station": ("fire station", "fire_station"),
    "ambulance": ("ambulance service", None),
    "vehicle_rescue": ("towing service roadside assistance", None),
    "puncture_shop": ("puncture repair tyre shop", None),
}

SERVICE_QUERIES = {
    category: " | ".join(f'node["{key}"="{value}"]' for key, value in tags)
    for category, tags in OVERPASS_TAGS.items()
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def eta_minutes(distance_km: float) -> int:
    return max(1, round(distance_km / 30 * 60))


def build_overpass_query(lat: float, lon: float, radius_m: int) -> str:
    selectors = []
    grouped_tags: dict[str, set[str]] = {}
    for tags in OVERPASS_TAGS.values():
        for key, value in tags:
            grouped_tags.setdefault(key, set()).add(value)
    for key, values in grouped_tags.items():
        # nwr = node + way + relation, so buildings/areas (police, fire,
        # hospital campuses) are matched, not only point nodes.
        value_regex = "|".join(re.escape(value) for value in sorted(values))
        selectors.append(f'nwr["{key}"~"^({value_regex})$"](around:{radius_m},{lat:.7f},{lon:.7f});')
    joined = "\n  ".join(selectors)
    return f"[out:json][timeout:25];\n(\n  {joined}\n);\nout center tags qt;"


def fetch_nearby_services(
    lat: float,
    lon: float,
    radius_m: int = 5000,
    google_maps_api_key: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    provider = "google" if google_maps_api_key else "osm"
    key = f"{CACHE_SCHEMA_VERSION}_{provider}_{lat:.3f}_{lon:.3f}_{radius_m}"
    cached = load_cache(key)
    if cached is not None:
        _ensure_schema(cached)
        meta = dict(cached.get("_meta") or {})
        meta.update({"source": "cache", "age_hours": cache_age_hours(key), "cache_key": key})
        cached["_meta"] = meta
        return cached

    query = build_overpass_query(lat, lon, radius_m)
    headers = {
        "User-Agent": "RoadSoS/1.0 Emergency Dashboard (hackathon project)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    payload = _fetch_overpass_json(query, headers)

    services: dict[str, list[dict[str, Any]]] = {category: [] for category in OVERPASS_TAGS}
    seen: set[tuple[str, str, int]] = set()

    for element in payload.get("elements", []):
        item_lat, item_lon = _element_coordinates(element)
        if item_lat is None or item_lon is None:
            continue

        tags = element.get("tags", {})
        category = _category_for_tags(tags)
        if category is None:
            continue

        item_id = int(element.get("id", 0))
        dedupe_key = (str(element.get("type", "")), category, item_id)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        distance = round(haversine(lat, lon, item_lat, item_lon), 2)
        services[category].append(
            {
                "name": _tag(tags, "name", "operator", "brand") or _fallback_name(category),
                "category": category.replace("_", " ").title(),
                "lat": item_lat,
                "lon": item_lon,
                "distance_km": distance,
                "eta_min": eta_minutes(distance),
                "phone": _tag(tags, "phone", "contact:phone", "mobile", "contact:mobile") or "Not listed",
                "address": _address(tags),
                "emergency": tags.get("emergency"),
                "source": "OpenStreetMap",
            }
        )

    _add_emergency_hospital_fallbacks(services)
    places_errors = []
    if google_maps_api_key:
        places_errors = _enrich_from_google_places(services, lat, lon, radius_m, google_maps_api_key)

    _dedupe_services(services)
    for category in services:
        services[category].sort(key=lambda item: item["distance_km"])

    services["_meta"] = {
        "source": "live",
        "age_hours": 0.0,
        "cache_key": key,
        "provider": "OpenStreetMap + Google Places" if google_maps_api_key else "OpenStreetMap",
        "warnings": places_errors,
    }
    save_cache(key, services)
    return services


def _fetch_overpass_json(query: str, headers: dict[str, str]) -> dict[str, Any]:
    errors = []
    for url in OVERPASS_URLS:
        try:
            response = _SESSION.post(url, data={"data": query}, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError("All Overpass endpoints failed. " + " | ".join(errors))


def count_total_contacts(services: dict[str, list[dict[str, Any]]]) -> int:
    return sum(len(value) for key, value in services.items() if key != "_meta")


def _ensure_schema(services: dict[str, Any]) -> None:
    for category in OVERPASS_TAGS:
        services.setdefault(category, [])
    for old_key in ("clinic", "towing", "car_showroom"):
        services.pop(old_key, None)


def _element_coordinates(element: dict[str, Any]) -> tuple[float | None, float | None]:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if center and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None, None


def _category_for_tags(tags: dict[str, str]) -> str | None:
    for category, category_tags in OVERPASS_TAGS.items():
        if any(tags.get(key) == value for key, value in category_tags):
            return category
    searchable = " ".join(
        str(tags.get(name, ""))
        for name in ("name", "brand", "operator", "description")
    )
    for category, pattern in NAME_PATTERNS.items():
        if pattern.search(searchable):
            return category
    return None


def _add_emergency_hospital_fallbacks(services: dict[str, list[dict[str, Any]]]) -> None:
    if services["ambulance"]:
        return
    for hospital in services["hospital"]:
        if hospital.get("emergency") != "yes":
            continue
        services["ambulance"].append(
            {
                **hospital,
                "category": "Emergency hospital dispatch fallback",
                "status": "CALL TO CONFIRM",
                "source": "OpenStreetMap emergency=yes hospital fallback",
            }
        )


def _enrich_from_google_places(
    services: dict[str, list[dict[str, Any]]],
    lat: float,
    lon: float,
    radius_m: int,
    api_key: str,
) -> list[str]:
    errors = []
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,places.location,"
            "places.nationalPhoneNumber,places.googleMapsUri,places.primaryType"
        ),
    }
    for category, (text_query, included_type) in GOOGLE_PLACES_SEARCHES.items():
        body: dict[str, Any] = {
            "textQuery": text_query,
            "pageSize": 20,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": float(min(radius_m, 50_000)),
                }
            },
        }
        if category in {"ambulance", "vehicle_rescue"}:
            body["includePureServiceAreaBusinesses"] = True
        if included_type:
            body["includedType"] = included_type
            body["strictTypeFiltering"] = True
        try:
            response = _SESSION.post(
                GOOGLE_PLACES_TEXT_SEARCH_URL,
                json=body,
                headers=headers,
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            errors.append(f"{category}: {exc}")
            continue

        for place in payload.get("places", []):
            location = place.get("location") or {}
            place_lat = location.get("latitude")
            place_lon = location.get("longitude")
            if place_lat is None or place_lon is None:
                continue
            distance = round(haversine(lat, lon, float(place_lat), float(place_lon)), 2)
            if distance > radius_m / 1000:
                continue
            display_name = place.get("displayName") or {}
            services[category].append(
                {
                    "name": display_name.get("text") or category.replace("_", " ").title(),
                    "category": category.replace("_", " ").title(),
                    "lat": float(place_lat),
                    "lon": float(place_lon),
                    "distance_km": distance,
                    "eta_min": eta_minutes(distance),
                    "phone": place.get("nationalPhoneNumber") or "Not listed",
                    "address": place.get("formattedAddress") or "Not listed",
                    "maps_url": place.get("googleMapsUri"),
                    "source": "Google Places",
                }
            )
    return errors


def _dedupe_services(services: dict[str, list[dict[str, Any]]]) -> None:
    for category, items in services.items():
        if category == "_meta":
            continue
        unique = {}
        for item in items:
            name = re.sub(r"\W+", "", str(item.get("name", "")).lower())
            identity = (
                name,
                round(float(item.get("lat", 0)), 4),
                round(float(item.get("lon", 0)), 4),
            )
            existing = unique.get(identity)
            if existing is None or existing.get("source") != "Google Places":
                unique[identity] = item
        services[category] = list(unique.values())


def _tag(tags: dict[str, str], *names: str) -> str | None:
    for name in names:
        value = tags.get(name)
        if value:
            return value
    return None


def _address(tags: dict[str, str]) -> str:
    full = _tag(tags, "addr:full")
    if full:
        return full
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]
    address = ", ".join(part for part in parts if part)
    return address or "Not listed"


def _fallback_name(category: str) -> str:
    return category.replace("_", " ").title()
