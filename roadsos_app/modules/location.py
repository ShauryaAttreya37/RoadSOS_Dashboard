from __future__ import annotations

import requests
import streamlit as st

from roadsos_app.modules.ui import location_pill


IPAPI_URL = "https://ipapi.co/json/"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
HTTP_TIMEOUT_SECONDS = 3
REVERSE_GEOCODE_PRECISION = 4

_LOCATION_DEFAULTS = {
    "lat": None,
    "lon": None,
    "country_code": "XX",
    "city": "Location unavailable",
    "country_name": "Unknown",
    "location_source": "Unavailable",
    "location_error": None,
    "_location_detection_complete": False,
}

_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "User-Agent": "RoadSoS/1.0 Emergency Dashboard (hackathon project)",
        "Accept": "application/json",
    }
)


def get_browser_location() -> tuple[float | None, float | None]:
    try:
        from streamlit_js_eval import get_geolocation
    except Exception:
        return None, None

    try:
        loc = get_geolocation()
    except Exception:
        return None, None

    if loc and "coords" in loc:
        coords = loc["coords"]
        try:
            lat = float(coords["latitude"])
            lon = float(coords["longitude"])
        except (KeyError, TypeError, ValueError):
            return None, None
        if _valid_coordinates(lat, lon):
            return lat, lon
    return None, None


@st.cache_data(ttl=900, show_spinner=False)
def get_ip_location() -> tuple[float | None, float | None, str, str, str, str | None]:
    try:
        response = _SESSION.get(IPAPI_URL, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        if not _valid_coordinates(lat, lon):
            raise ValueError("IP geolocation returned invalid coordinates.")
        return (
            lat,
            lon,
            (data.get("country_code") or "XX").upper(),
            data.get("city", "") or "Detected city",
            data.get("country_name", "") or "Detected country",
            None,
        )
    except Exception as exc:
        return None, None, "XX", "Location unavailable", "Unknown", str(exc)


def reverse_geocode(lat: float, lon: float) -> tuple[str, str, str]:
    if not _valid_coordinates(lat, lon):
        return "XX", "Detected GPS fix", "Unknown"

    return _reverse_geocode_cached(
        round(float(lat), REVERSE_GEOCODE_PRECISION),
        round(float(lon), REVERSE_GEOCODE_PRECISION),
    )


@st.cache_data(ttl=86400, show_spinner=False)
def _reverse_geocode_cached(lat: float, lon: float) -> tuple[str, str, str]:
    try:
        response = _SESSION.get(
            NOMINATIM_URL,
            params={
                "format": "jsonv2",
                "lat": f"{lat:.7f}",
                "lon": f"{lon:.7f}",
                "zoom": 10,
                "addressdetails": 1,
            },
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("suburb")
            or data.get("name")
            or "Detected GPS fix"
        )
        country_code = (address.get("country_code") or "XX").upper()
        country_name = address.get("country") or "Unknown"
        return country_code, city, country_name
    except Exception:
        return "XX", "Detected GPS fix", "Unknown"


def init_location_state() -> None:
    for key, value in _LOCATION_DEFAULTS.items():
        st.session_state.setdefault(key, value)

    if st.session_state.get("_location_detection_complete"):
        return
    if has_location():
        st.session_state._location_detection_complete = True
        return

    browser_lat, browser_lon = get_browser_location()
    if (
        browser_lat is not None
        and browser_lon is not None
        and _valid_coordinates(browser_lat, browser_lon)
    ):
        country_code, city, country_name = reverse_geocode(browser_lat, browser_lon)
        _store_location(browser_lat, browser_lon, country_code, city, country_name, "Browser")
        return

    lat, lon, country_code, city, country_name, error = get_ip_location()
    if lat is not None and lon is not None:
        _store_location(lat, lon, country_code, city, country_name, "IP")
        return

    st.session_state.location_error = error or "Unable to detect location."
    st.session_state._location_detection_complete = True


def has_location() -> bool:
    return _valid_coordinates(st.session_state.get("lat"), st.session_state.get("lon"))


def render_location_sidebar() -> None:
    if has_location():
        location_pill(
            float(st.session_state.lat),
            float(st.session_state.lon),
            str(st.session_state.get("city", "")),
            str(st.session_state.get("country_name", "")),
            str(st.session_state.get("location_source", "Detected")),
        )
    else:
        st.sidebar.warning(
            "Location is unavailable. Allow browser location permission or enter real coordinates manually."
        )

    with st.sidebar.expander("Location Override", expanded=not has_location()):
        lat = st.number_input("Latitude", value=float(st.session_state.lat or 0.0), format="%.6f")
        lon = st.number_input("Longitude", value=float(st.session_state.lon or 0.0), format="%.6f")
        country_code = st.text_input("Country code", value=str(st.session_state.get("country_code", "XX"))).upper()
        city = st.text_input("City label", value=str(st.session_state.get("city", "")))
        country_name = st.text_input("Country label", value=str(st.session_state.get("country_name", "")))
        if st.button("Apply Location", width="stretch"):
            if not _valid_coordinates(lat, lon):
                st.error("Enter valid latitude and longitude values before applying.")
                return
            _store_location(
                lat,
                lon,
                country_code or "XX",
                city or "Manual location",
                country_name or "Unknown",
                "Manual",
            )
            st.rerun()
        if st.button("Detect Location Again", width="stretch"):
            reset_location_detection(clear_ip_cache=True)
            st.rerun()


def reset_location_detection(*, clear_ip_cache: bool = False) -> None:
    for key, value in _LOCATION_DEFAULTS.items():
        st.session_state[key] = value
    if clear_ip_cache:
        get_ip_location.clear()


def _store_location(
    lat: float,
    lon: float,
    country_code: str,
    city: str,
    country_name: str,
    source: str,
) -> None:
    st.session_state.lat = float(lat)
    st.session_state.lon = float(lon)
    st.session_state.country_code = country_code
    st.session_state.city = city
    st.session_state.country_name = country_name
    st.session_state.location_source = source
    st.session_state.location_error = None
    st.session_state._location_detection_complete = True


def _valid_coordinates(lat: object, lon: object) -> bool:
    try:
        lat_float = float(lat)
        lon_float = float(lon)
    except (TypeError, ValueError):
        return False
    return -90 <= lat_float <= 90 and -180 <= lon_float <= 180
