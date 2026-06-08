import io
import json
from html import escape
import re
import sys
from datetime import datetime
from pathlib import Path

import qrcode
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from roadsos_app.modules.emergency_numbers import get_global_sos_profile
from roadsos_app.modules.location import has_location, init_location_state, render_location_sidebar
from roadsos_app.modules.profile_store import load_profile, save_profile
from roadsos_app.modules.translator import tr
from roadsos_app.modules.ui import (
    GREEN,
    RED,
    alert_banner,
    blood_badge,
    get_colors,
    get_theme,
    initials,
    inject_global_css,
    micon,
    page_header,
    render_theme_toggle,
    sidebar_brand,
)


st.set_page_config(page_title="RoadSoS | Rider Profile & SOS", page_icon=":material/sports_motorsports:", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
init_location_state()
sidebar_brand()
render_theme_toggle()
render_location_sidebar()

c = get_colors()
is_dark = get_theme() == "dark"
sos_profile = get_global_sos_profile(str(st.session_state.get("country_code", "XX")))


def safe_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def rider_id_from_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "roadsos-rider"


def make_qr(url: str) -> bytes:
    qr = qrcode.QRCode(version=2, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    # Use theme colors for QR code
    fill = c["TEXT"]
    back = c["CARD_BG"]


def safe_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def rider_id_from_name(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "roadsos-rider"


def make_qr(url: str) -> bytes:
    qr = qrcode.QRCode(version=2, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    # Use theme colors for QR code
    fill = c["TEXT"]
    back = c["CARD_BG"]
    image = qr.make_image(fill_color=fill, back_color=back).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


page_header(tr("Rider Profile & SOS"), tr("Medical handoff packet for responders and bystanders."), tr("QR READY"), RED, icon="badge")

left, right = st.columns(2)
profile = load_profile()

with left:
    with st.form("profile"):
        blood_options = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        rider_name = st.text_input(tr("Name"), profile["rider_name"])
        blood_group = st.selectbox(
            tr("Blood Group"),
            blood_options,
            index=blood_options.index(profile["blood_group"]) if profile["blood_group"] in blood_options else 4,
        )
        allergies = st.text_input(tr("Allergies"), profile["allergies"])
        conditions = st.text_area(tr("Medical Conditions"), profile["conditions"])
        emergency_contact = st.text_input(tr("Emergency Contact"), profile["emergency_contact"])
        lat_default = f"{float(st.session_state.lat):.4f}" if has_location() else ""
        lon_default = f"{float(st.session_state.lon):.4f}" if has_location() else ""
        lat = st.text_input(tr("Last known latitude"), lat_default)
        lon = st.text_input(tr("Last known longitude"), lon_default)
        submitted = st.form_submit_button(tr("Save Profile"), type="primary")

rider_id = rider_id_from_name(rider_name)
sos_packet = {
    "type": "CRASH_ALERT",
    "severity": "HIGH",
    "lat": safe_float(lat),
    "lon": safe_float(lon),
    "rider_id": rider_id,
    "rider_name": rider_name,
    "blood_group": blood_group,
    "allergies": allergies,
    "medical_conditions": conditions,
    "emergency_contact": emergency_contact,
    "global_sos": {
        "country_code": sos_profile["country_code"],
        "unified": sos_profile["unified"],
        "ambulance": sos_profile["ambulance"],
        "police": sos_profile["police"],
        "fire": sos_profile["fire"],
        "coverage": sos_profile["coverage"],
    },
    "handoff": "offline_qr",
    "timestamp": datetime.now().isoformat(timespec="seconds"),
}
handoff_payload = json.dumps(sos_packet, separators=(",", ":"))
safe_rider_name = escape(rider_name)
safe_allergies = escape(allergies or "None")
safe_conditions = escape(conditions or "None")
safe_emergency_contact = escape(emergency_contact)

with right:
    st.markdown(
        f"""
<div class="profile-card">
  <div class="profile-avatar">{initials(rider_name)}</div>
  <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.8rem;">
    <div style="color:{c["TEXT"]};font-size:1.45rem;font-weight:800;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.04em;">{safe_rider_name}</div>
    {blood_badge(blood_group)}
  </div>
  <div style="margin-bottom:0.9rem;">
    <span class="chip">{tr("Allergies")}: {safe_allergies}</span>
    <span class="chip">{tr("Conditions")}: {safe_conditions}</span>
  </div>
  <div style="color:{c["MUTED"]};font-size:0.75rem;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.06em;font-weight:700;margin-bottom:0.25rem;">{micon("call", size=16, color=c["MUTED"])} {tr("Emergency contact")}</div>
  <div style="color:{GREEN};font-weight:800;font-size:1.15rem;font-family:'Outfit';letter-spacing:0.04em;">{safe_emergency_contact}</div>
  <a href="tel:{escape(str(sos_profile["unified"]), quote=True)}" class="btn-call"
     style="display:block;text-align:center;margin-top:1rem;padding:10px 12px;border-radius:6px;text-decoration:none;">
    {micon("sos", size=17)} {tr("Call Global SOS")} ({escape(str(sos_profile["unified"]))})
  </a>
</div>
""",
        unsafe_allow_html=True,
    )

if submitted:
    save_profile(rider_name, blood_group, allergies, conditions, emergency_contact)
    st.session_state.rider_name = rider_name
    st.session_state.blood_group = blood_group
    st.session_state.allergies = allergies
    st.session_state.conditions = conditions
    st.session_state.emergency_contact = emergency_contact
    alert_banner("safe", tr("Profile preview updated. The SOS packet below reflects the current form values."))

st.markdown(f"<h3 style='margin-top:1.5rem;'>{tr('SOS Packet Preview')}</h3>", unsafe_allow_html=True)
st.code(json.dumps(sos_packet, indent=2), language="json")

aid_col, qr_col = st.columns([0.62, 0.38])
with aid_col:
    st.markdown(
        f"""
<div class="profile-card" style="height: 100%;">
  <div style="color:{RED};font-weight:800;margin-bottom:0.9rem;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.08em;font-size:0.95rem;">{tr("WHO / Red Cross crash response protocol")}</div>
  <div style="color:{c["TEXT"]};line-height:1.7;font-size:0.9rem;font-family:'Inter';">
    <b>1.</b> {tr("Secure the scene first. Move traffic away, switch off ignition, and call emergency services.")}<br>
    <b>2.</b> {tr("Do not move the rider unless fire, traffic, or flooding creates immediate danger.")}<br>
    <b>3.</b> {tr("Check response, airway, breathing, and severe bleeding. Start CPR only if trained and needed.")}<br>
    <b>4.</b> {tr("Stabilize the head and neck manually. Treat suspected spine injury as real until responders arrive.")}<br>
    <b>5.</b> {tr("Apply firm direct pressure to heavy bleeding with clean cloth or gauze.")}<br>
    <b>6.</b> {tr("Keep the rider warm, calm, and still. Share the QR profile and GPS location with responders.")}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

with qr_col:
    st.markdown(
        f"""
<div class="profile-card" style="text-align:center;">
  <div style="color:{c["MUTED"]};font-size:0.75rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.8rem;font-family:'Outfit';font-weight:700;">
    {tr("Emergency QR")}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.image(make_qr(handoff_payload), width="stretch")
    st.caption(tr("Scan for the offline emergency medical packet"))
