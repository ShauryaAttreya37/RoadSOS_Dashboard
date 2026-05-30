from __future__ import annotations

import numpy as np
import streamlit as st

from roadsos_app.modules.emergency_numbers import get_emergency_numbers
from roadsos_app.modules.location import has_location
from roadsos_app.modules.profile_store import load_profile


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
        location = "Location unavailable — ask the user to enable browser GPS or enter coordinates in the sidebar."

    helmet_context = _build_helmet_context()

    return f"""
ROADSOS INCIDENT CONTEXT
========================

RIDER PROFILE:
- Name: {name}
- Blood group: {blood}
- Known allergies: {allergy_text or "None"}
- Medical conditions: {condition_text or "None"}
- Emergency contact: {contact}

LOCATION:
- {location}

LOCAL EMERGENCY NUMBERS:
- Ambulance: {numbers["ambulance"]}
- Police: {numbers["police"]}
- Fire brigade: {numbers["fire"]}
- Unified emergency: {numbers["unified"]}

{helmet_context}

Use all of this context when answering. Reference specific biomechanical numbers (HIC15, BrIC, peak g) when relevant.
If location is unavailable, do not invent coordinates — ask the user to enable GPS.
""".strip()


def _build_helmet_context() -> str:
    """Pull PINN simulation results from session_state and format as structured context."""
    result = st.session_state.get("pinn_result")
    if result is None:
        return "HELMET SENSOR STATUS:\n- No simulation has been run this session. Navigate to Helmet Intelligence and run a scenario first."

    try:
        ax = np.asarray(result["ax"])
        ay = np.asarray(result["ay"])
        az = np.asarray(result["az"])
        ares = np.sqrt(ax**2 + ay**2 + az**2) / 9.81
        peak_accel = float(ares.max())
        skid_arr = np.asarray(result["P_skid"])
        skid_max = float(skid_arr.max())
        hic15 = float(result["hic15"])
        bric = float(result["bric"])
        label = str(result.get("label", "UNKNOWN"))
        scenario = str(result.get("scenario", "Unknown"))

        crash_detected = peak_accel > 6.0
        skid_detected = skid_max > 0.65

        if crash_detected:
            alert = f"CRASH DETECTED — SOS FIRED (peak {peak_accel:.1f} g crossed 6 g impact threshold)"
        elif skid_detected:
            alert = f"SKID WARNING — haptic alert fired (P(skid) = {skid_max:.2f}, threshold 0.65)"
        else:
            alert = f"SAFE — riding within normal parameters"

        hic_risk = (
            "SEVERE — probable moderate TBI, treat as head injury" if hic15 > 1000
            else "ELEVATED — borderline TBI risk, monitor for symptoms" if hic15 > 700
            else "LOW — below clinical head-injury threshold"
        )
        bric_risk = "SEVERE rotational injury risk" if bric > 1.0 else "within safe rotational limits"

        skid_timing = "Yes — skid preceded the crash" if skid_detected and crash_detected else "No clear skid signature"

        return f"""HELMET PINN SENSOR READING (last simulation):
- Scenario simulated: {scenario}
- Helmet alert status: {alert}
- Head Injury Criterion HIC15: {hic15:.0f} — {hic_risk}
- Brain Rotational Injury BrIC: {bric:.3f} — {bric_risk}
- Peak resultant acceleration: {peak_accel:.1f} g  (crash threshold: 6 g)
- Max skid probability P(skid): {skid_max:.2f}  (warning threshold: 0.65)
- PINN injury severity classification: {label}
- Skid preceded crash: {skid_timing}"""
    except Exception as exc:
        return f"HELMET SENSOR STATUS:\n- Data present but could not be read ({exc})."
