import json
import time
from pathlib import Path
from typing import Any


CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
CACHE_TTL_SECONDS = 86400


def cache_path(key: str) -> Path:
    safe_key = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in key)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{safe_key}.json"


def load_cache(key: str, *, allow_expired: bool = False) -> dict[str, Any] | None:
    path = cache_path(key)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    timestamp = float(payload.get("timestamp", 0))
    if not allow_expired and time.time() - timestamp > CACHE_TTL_SECONDS:
        return None

    data = payload.get("data")
    return data if isinstance(data, dict) else None


def save_cache(key: str, data: dict[str, Any]) -> None:
    payload = {"timestamp": time.time(), "data": data}
    path = cache_path(key)
    temporary_path = path.with_suffix(f".{time.time_ns()}.tmp")
    try:
        temporary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def is_cache_fresh(key: str) -> bool:
    return load_cache(key) is not None


def cache_age_hours(key: str) -> float:
    path = cache_path(key)
    if not path.exists():
        return float("inf")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        timestamp = float(payload.get("timestamp", 0))
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return float("inf")

    return max(0.0, (time.time() - timestamp) / 3600.0)


def clear_cache() -> int:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    removed = 0
    for path in CACHE_DIR.glob("*.json"):
        path.unlink(missing_ok=True)
        removed += 1
    return removed
