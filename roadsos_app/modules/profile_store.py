from __future__ import annotations

from datetime import datetime

import streamlit as st

_SESSION_KEY = "roadsos_rider_profile"

_DEFAULTS: dict = {
    "rider_name": "Ravi Kumar",
    "blood_group": "O+",
    "allergies": "None",
    "conditions": "None",
    "emergency_contact": "+91XXXXXXXXXX",
    "saved_at": None,
}


def load_profile() -> dict:
    data = st.session_state.get(_SESSION_KEY)
    if isinstance(data, dict):
        return {**_DEFAULTS, **data}
    return dict(_DEFAULTS)


def save_profile(
    rider_name: str,
    blood_group: str,
    allergies: str,
    conditions: str,
    emergency_contact: str,
) -> None:
    payload = {
        "rider_name": rider_name,
        "blood_group": blood_group,
        "allergies": allergies,
        "conditions": conditions,
        "emergency_contact": emergency_contact,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    st.session_state[_SESSION_KEY] = payload
