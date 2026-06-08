import sys
import io
import re
import json
from html import escape
from datetime import datetime
from pathlib import Path
import qrcode
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roadsos_app.modules.location import has_location, init_location_state, render_location_sidebar
from roadsos_app.modules.config import get_secret
from roadsos_app.modules.emergency_numbers import get_global_sos_profile
from roadsos_app.modules.translator import tr
from roadsos_app.modules.profile_store import load_profile
from roadsos_app.modules.ui import (
    AMBER,
    GREEN,
    RED,
    get_colors,
    inject_global_css,
    micon,
    page_header,
    render_theme_toggle,
    sidebar_brand,
    stat_card,
    initials,
    blood_badge,
)

st.set_page_config(page_title="RoadSoS | Command Center", page_icon=":material/sports_motorsports:", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
init_location_state()
sidebar_brand()
render_theme_toggle()
render_location_sidebar()

c = get_colors()


def ai_engine_status() -> tuple[str, str]:
    """Report which AI provider is wired up, for the live status bar."""
    try:
        if get_secret("OPENROUTER_API_KEY"):
            return "OpenRouter", GREEN
        if get_secret("ANTHROPIC_API_KEY"):
            return "Claude", GREEN
    except Exception:
        pass
    return "Offline fallback", AMBER


def status_chip(label: str, value: str, color: str) -> str:
    return (
        f'<div style="display:flex;align-items:center;gap:10px;padding:10px 16px;'
        f'background:{c["CARD_BG"]};border:1px solid {c["BORDER"]};border-radius:10px;flex:1;min-width:180px;">'
        f'<span style="width:9px;height:9px;border-radius:50%;background:{color};box-shadow:0 0 8px {color};"></span>'
        f'<div style="line-height:1.25;">'
        f'<div style="font-family:\'Outfit\';font-size:0.62rem;font-weight:700;letter-spacing:0.12em;'
        f'text-transform:uppercase;color:{c["MUTED"]};">{label}</div>'
        f'<div style="font-family:\'Outfit\';font-size:0.92rem;font-weight:800;color:{c["TEXT"]};">{value}</div>'
        f"</div></div>"
    )


def make_qr(url: str) -> bytes:
    qr = qrcode.QRCode(version=2, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    fill = c["TEXT"]
    back = c["CARD_BG"]
    image = qr.make_image(fill_color=fill, back_color=back).convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


page_header(
    tr("RoadSoS Command Center"),
    tr("Smart helmet intelligence, emergency routing, rider medical handoff, and road-safety AI."),
    tr("OPS READY"),
    GREEN,
    icon="space_dashboard",
)

# ── Live system status bar ──────────────────────────────────────────────────
ai_name, ai_color = ai_engine_status()
loc_city = st.session_state.get("city") or "Unknown"
loc_source = st.session_state.get("location_source", "Unavailable")
loc_color = GREEN if has_location() else AMBER
sos_profile = get_global_sos_profile(str(st.session_state.get("country_code", "XX")))

st.markdown(
    '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:1.8rem;">'
    + status_chip(tr("System"), tr("Online"), GREEN)
    + status_chip(tr("AI Engine"), tr(ai_name), ai_color)
    + status_chip(tr("Location"), f"{tr(loc_city)} · {tr(loc_source)}", loc_color)
    + status_chip(tr("Services"), tr("OpenStreetMap Live"), GREEN)
    + "</div>",
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    stat_card(tr("Edge Model"), "PINN", tr("on-helmet"), AMBER)
with k2:
    stat_card(tr("Service Layer"), "OSM", tr("global"), GREEN)
with k3:
    stat_card(tr("Offline Cache"), "24", tr("hours"), GREEN)
with k4:
    stat_card(tr("Global SOS"), sos_profile["unified"], tr("ready"), RED)

modules = [
    ("pages/1_PINN_Dashboard.py", "sports_motorsports", "Helmet Intelligence",
     "Run Normal, Oil Patch, or Crash scenarios with PINN biomechanics, severity scoring, and AI first aid."),
    ("pages/2_Nearby_Services.py", "location_on", "Nearby Services",
     "Hospitals, police, fire & rescue, ambulance, towing, and repair — sorted by distance, cached offline."),
    ("pages/3_Emergency_Profile.py", "badge", "Rider Profile & SOS",
     "Generate the emergency medical packet and scannable QR handoff for first responders."),
    ("pages/4_AI_Assistant.py", "smart_toy", "RoadSoS AI Assistant",
     "Ask global first-aid and road-crash questions, with India-specific legal guidance when the incident is in India."),
    ("pages/5_Live_Dashboard.py", "sensors", "Live Helmet Stream",
     "Real-time IMU feed with rolling crash detection, skid prediction, and an auto-firing SOS event log."),
]

col_left, col_right = st.columns([0.55, 0.45])

with col_left:
    st.markdown(
        f'<div style="font-family:\'Outfit\';font-weight:800;font-size:1.05rem;color:{c["TEXT"]};'
        f'text-transform:uppercase;letter-spacing:0.08em;margin:0.6rem 0 1rem;'
        f'border-left:3px solid {GREEN};padding-left:0.7rem;">{tr("Mission Modules")}</div>',
        unsafe_allow_html=True,
    )
    for path, icon, title, desc in modules:
        st.markdown(
            f"""
<div class="profile-card" style="padding:1rem 1.2rem;margin-bottom:0.4rem;height:auto;">
  <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.4rem;">
    {micon(icon, size=24, color=GREEN, fill=True)}
    <span style="color:{c["TEXT"]};font-weight:800;font-family:'Outfit';text-transform:uppercase;
         letter-spacing:0.04em;font-size:0.95rem;">{tr(title)}</span>
  </div>
  <div style="color:{c["MUTED"]};font-size:0.83rem;font-family:'Inter';line-height:1.5;">{tr(desc)}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.page_link(path, label=f"{tr('Open')} {tr(title)}", icon=":material/arrow_forward:", use_container_width=True)

with col_right:
    st.markdown(
        f'<div style="font-family:\'Outfit\';font-weight:800;font-size:1.05rem;color:{c["TEXT"]};'
        f'text-transform:uppercase;letter-spacing:0.08em;margin:0.6rem 0 1rem;'
        f'border-left:3px solid {RED};padding-left:0.7rem;">{tr("Active Rider Profile")}</div>',
        unsafe_allow_html=True,
    )
    
    # Load profile details
    profile = load_profile()
    rider_name = profile["rider_name"]
    blood_group = profile["blood_group"]
    allergies = profile["allergies"] or "None"
    conditions = profile["conditions"] or "None"
    emergency_contact = profile["emergency_contact"]
    
    # Render compact profile card
    st.markdown(
        f"""
<div class="profile-card" style="border-color:{RED}33;border-left:3px solid {RED};">
  <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
    <div class="profile-avatar" style="width:55px;height:55px;border-radius:8px;font-size:1.3rem;margin-bottom:0;box-shadow:0 3px 8px {GREEN}33;">{initials(rider_name)}</div>
    <div>
      <div style="color:{c["TEXT"]};font-size:1.2rem;font-weight:800;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.04em;line-height:1.1;">{escape(rider_name)}</div>
      <div style="margin-top:0.25rem;">{blood_badge(blood_group)}</div>
    </div>
  </div>
  <div style="margin-bottom:0.8rem;display:flex;flex-direction:column;gap:4px;">
    <div style="font-size:0.82rem;color:{c["MUTED"]};font-family:'Inter';"><b style="color:{c["TEXT"]};">{tr("Allergies")}:</b> {escape(tr(allergies))}</div>
    <div style="font-size:0.82rem;color:{c["MUTED"]};font-family:'Inter';"><b style="color:{c["TEXT"]};">{tr("Conditions")}:</b> {escape(tr(conditions))}</div>
  </div>
  <div style="color:{c["MUTED"]};font-size:0.7rem;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.06em;font-weight:700;margin-bottom:0.1rem;">{micon("call", size=14, color=c["MUTED"])} {tr("Emergency Contact")}</div>
  <div style="color:{GREEN};font-weight:800;font-size:1.05rem;font-family:'Outfit';letter-spacing:0.04em;">{escape(emergency_contact)}</div>
  <a href="tel:{escape(str(sos_profile["unified"]), quote=True)}" class="btn-call" style="display:block;text-align:center;margin-top:0.8rem;padding:8px 10px;border-radius:6px;text-decoration:none;font-size:0.8rem;">
    {micon("sos", size=15)} {tr("Call Global SOS")} ({escape(str(sos_profile["unified"]))})
  </a>
</div>
""",
        unsafe_allow_html=True,
    )
    
    # Generate packet and QR
    rider_id = re.sub(r"[^a-z0-9]+", "-", rider_name.lower()).strip("-") or "roadsos-rider"
    lat_val = st.session_state.get("lat")
    lon_val = st.session_state.get("lon")
    
    # Handle optional float casting safely
    try:
        lat_float = float(lat_val) if lat_val else None
    except ValueError:
        lat_float = None
    try:
        lon_float = float(lon_val) if lon_val else None
    except ValueError:
        lon_float = None

    sos_packet = {
        "type": "CRASH_ALERT",
        "severity": "HIGH",
        "lat": lat_float,
        "lon": lon_float,
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
    
    st.markdown("<div style='margin-top:0.8rem;'></div>", unsafe_allow_html=True)
    q1, q2 = st.columns([0.4, 0.6])
    with q1:
        st.image(make_qr(handoff_payload), width=120)
    with q2:
        st.markdown(
            f"""
<div style="font-family:'Inter';font-size:0.8rem;color:{c["MUTED"]};line-height:1.45;">
  <b>{tr("Emergency QR Packet")}</b><br>
  {tr("Responders can scan this offline to read crucial medical and SOS details immediately.")}
</div>
""",
            unsafe_allow_html=True,
        )
        st.page_link("pages/3_Emergency_Profile.py", label=tr("Edit Profile / View Details"), icon=":material/edit:")

# ── Emergency colour legend ─────────────────────────────────────────────────
st.markdown(
    f"""
<div class="en-strip" style="margin-top:1.5rem;padding:1.2rem 1.5rem;">
  <div style="color:{RED};font-weight:800;margin-bottom:0.5rem;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.08em;font-size:0.9rem;">{tr("Emergency-first interface")}</div>
  <div style="color:{c["MUTED"]};font-size:0.88rem;line-height:1.55;font-family:'Inter';">
    <b style="color:{RED};">{tr("Red")}</b> {tr("is reserved for crash-critical states")} ·
    <b style="color:{AMBER};">{tr("Amber")}</b> {tr("means warning")} ·
    <b style="color:{GREEN};">{tr("Green")}</b> {tr("means safe, open, cached, or ready.")}
  </div>
</div>
""",
    unsafe_allow_html=True,
)
