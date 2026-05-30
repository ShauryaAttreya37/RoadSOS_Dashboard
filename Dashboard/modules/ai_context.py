from __future__ import annotations

import streamlit as st

from modules.emergency_numbers import get_emergency_numbers
from modules.location import has_location
from modules.profile_store import load_profile


def build_incident_context(
    *,
    rider_name: str | None = None,
    blood_group: str | None = None,
    allergies: str | None = None,
    conditions: str | None = None,
    emergency_contact: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    city: str | None = None,
    country_name: str | None = None,
    country_code: str | None = None,
    location_source: str | None = None,
) -> str:
    profile = load_profile()
    name = rider_name or st.session_state.get("rider_name") or profile["rider_name"]
    blood = blood_group or st.session_state.get("blood_group") or profile["blood_group"]
    allergy_text = allergies or st.session_state.get("allergies") or profile["allergies"]
    condition_text = conditions or st.session_state.get("conditions") or profile["conditions"]
    contact = emergency_contact or st.session_state.get("emergency_contact") or profile["emergency_contact"]

    resolved_country_code = str(country_code or st.session_state.get("country_code", "XX"))
    resolved_country_name = str(country_name or st.session_state.get("country_name", "Unknown"))
    resolved_city = str(city or st.session_state.get("city", "Unknown"))
    source = str(location_source or st.session_state.get("location_source", "Unavailable"))
    numbers = get_emergency_numbers(resolved_country_code)

    if lat is not None and lon is not None:
        location = (
            f"{resolved_city}, {resolved_country_name}; coordinates "
            f"{float(lat):.6f}, {float(lon):.6f}; source {source}"
        )
    elif has_location():
        location = (
            f"{resolved_city}, {resolved_country_name}; coordinates "
            f"{float(st.session_state.lat):.6f}, {float(st.session_state.lon):.6f}; source {source}"
        )
    else:
        location = "Location unavailable; tell the user to enable browser GPS or enter real coordinates before dispatch."

    return f"""
Current RoadSoS incident context:
- Rider: {name}
- Blood group: {blood}
- Known allergies: {allergy_text or "None"}
- Medical conditions: {condition_text or "None"}
- Emergency contact: {contact}
- Location: {location}
- Local emergency numbers: ambulance {numbers["ambulance"]}, police {numbers["police"]}, fire {numbers["fire"]}, unified {numbers["unified"]}

When answering, use this context. If the location is unavailable, do not invent one; ask for browser GPS/manual coordinates.
""".strip()
