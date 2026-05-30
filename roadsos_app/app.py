import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roadsos_app.modules.location import has_location, init_location_state, render_location_sidebar
from roadsos_app.modules.config import get_secret
from roadsos_app.modules.emergency_numbers import get_global_sos_profile
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


page_header(
    "RoadSoS Command Center",
    "Smart helmet intelligence, emergency routing, rider medical handoff, and road-safety AI.",
    "OPS READY",
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
    + status_chip("System", "Online", GREEN)
    + status_chip("AI Engine", ai_name, ai_color)
    + status_chip("Location", f"{loc_city} · {loc_source}", loc_color)
    + status_chip("Services", "OpenStreetMap Live", GREEN)
    + "</div>",
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    stat_card("Edge Model", "PINN", "on-helmet", AMBER)
with k2:
    stat_card("Service Layer", "OSM", "global", GREEN)
with k3:
    stat_card("Offline Cache", "24", "hours", GREEN)
with k4:
    stat_card("Global SOS", sos_profile["unified"], "ready", RED)

# ── Module navigation ─────────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-family:\'Outfit\';font-weight:800;font-size:1.05rem;color:{c["TEXT"]};'
    f'text-transform:uppercase;letter-spacing:0.08em;margin:0.6rem 0 1rem;'
    f'border-left:3px solid {GREEN};padding-left:0.7rem;">Mission Modules</div>',
    unsafe_allow_html=True,
)

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

cols = st.columns(2)
for idx, (path, icon, title, desc) in enumerate(modules):
    with cols[idx % 2]:
        st.markdown(
            f"""
<div class="profile-card" style="padding:1.2rem 1.4rem;margin-bottom:0.4rem;">
  <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.5rem;">
    {micon(icon, size=26, color=GREEN, fill=True)}
    <span style="color:{c["TEXT"]};font-weight:800;font-family:'Outfit';text-transform:uppercase;
         letter-spacing:0.04em;font-size:1rem;">{title}</span>
  </div>
  <div style="color:{c["MUTED"]};font-size:0.88rem;font-family:'Inter';line-height:1.55;">{desc}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.page_link(path, label=f"Open {title}", icon=":material/arrow_forward:", use_container_width=True)

# ── Emergency colour legend ─────────────────────────────────────────────────
st.markdown(
    f"""
<div class="en-strip" style="margin-top:1.5rem;padding:1.2rem 1.5rem;">
  <div style="color:{RED};font-weight:800;margin-bottom:0.5rem;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.08em;font-size:0.9rem;">Emergency-first interface</div>
  <div style="color:{c["MUTED"]};font-size:0.88rem;line-height:1.55;font-family:'Inter';">
    <b style="color:{RED};">Red</b> is reserved for crash-critical states ·
    <b style="color:{AMBER};">Amber</b> means warning ·
    <b style="color:{GREEN};">Green</b> means safe, open, cached, or ready.
  </div>
</div>
""",
    unsafe_allow_html=True,
)
