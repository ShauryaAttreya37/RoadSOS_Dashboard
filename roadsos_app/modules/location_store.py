from __future__ import annotations

import json
import time
from pathlib import Path

_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "last_location.json"


def save_last_location(
    lat: float,
    lon: float,
    country_code: str,
    city: str,
    country_name: str,
    source: str,
) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "lat": lat,
        "lon": lon,
        "country_code": country_code,
        "city": city,
        "country_name": country_name,
        "source": source,
        "saved_at": time.time(),
    }
    tmp = _STORE_PATH.with_suffix(f".{time.time_ns()}.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(_STORE_PATH)
    finally:
        tmp.unlink(missing_ok=True)


def load_last_location() -> dict | None:
    if not _STORE_PATH.exists():
        return None
    try:
        data = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and "lat" in data and "lon" in data else None
    except (json.JSONDecodeError, OSError):
        return None
