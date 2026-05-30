"""Live streaming helmet sensor dashboard — auto-refreshes every 2 s."""
from __future__ import annotations

import time

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from modules.location import init_location_state, render_location_sidebar
from modules.profile_store import load_profile
from modules.ui import (
    AMBER,
    GREEN,
    RED,
    alert_banner,
    get_colors,
    get_theme,
    inject_global_css,
    page_header,
    render_theme_toggle,
    sidebar_brand,
    stat_card,
)

st.set_page_config(page_title="RoadSoS | Live Helmet Stream", page_icon="🪖", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
init_location_state()
sidebar_brand()
render_theme_toggle()
render_location_sidebar()

c = get_colors()
is_dark = get_theme() == "dark"

plt.style.use("dark_background")

# ── Session init ─────────────────────────────────────────────────────────────

def _init_live_state() -> None:
    if "live_running" not in st.session_state:
        st.session_state.live_running = False
    if "live_scenario" not in st.session_state:
        st.session_state.live_scenario = "Normal Riding"
    if "live_tick" not in st.session_state:
        st.session_state.live_tick = 0
    if "live_buf_ax" not in st.session_state:
        st.session_state.live_buf_ax = []
    if "live_buf_ay" not in st.session_state:
        st.session_state.live_buf_ay = []
    if "live_buf_az" not in st.session_state:
        st.session_state.live_buf_az = []
    if "live_buf_t" not in st.session_state:
        st.session_state.live_buf_t = []
    if "live_buf_skid" not in st.session_state:
        st.session_state.live_buf_skid = []
    if "live_sos_fired" not in st.session_state:
        st.session_state.live_sos_fired = False
    if "live_alerts" not in st.session_state:
        st.session_state.live_alerts: list[str] = []

_init_live_state()
_BUF_MAX = 300  # keep last 300 samples in the rolling window

# ── Synthetic IMU generator ───────────────────────────────────────────────────

def _next_samples(scenario: str, tick: int, n: int = 5) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(tick)
    t = np.linspace(tick * 0.02, (tick + n) * 0.02, n)
    if scenario == "Normal Riding":
        ax = rng.normal(0, 0.4, n)
        ay = rng.normal(0, 0.4, n)
        az = rng.normal(9.81, 0.3, n)
        skid = np.clip(rng.uniform(0.0, 0.25, n), 0, 1)
    elif scenario == "Oil Patch":
        ax = rng.normal(1.5, 1.2, n)
        ay = rng.normal(2.0, 1.8, n)
        az = rng.normal(9.0, 0.9, n)
        skid = np.clip(rng.uniform(0.45, 0.80, n), 0, 1)
    else:  # Crash
        factor = min(1.0, (tick % 50) / 20)
        ax = rng.normal(0, 0.5, n) + factor * rng.uniform(30, 80, n)
        ay = rng.normal(0, 0.5, n) + factor * rng.uniform(20, 60, n)
        az = rng.normal(9.81, 0.5, n) - factor * rng.uniform(5, 15, n)
        skid = np.clip(rng.uniform(0.7, 0.99, n), 0, 1)
    return t, ax, ay, az, skid


def _resultant_g(ax, ay, az) -> np.ndarray:
    return np.sqrt(np.array(ax) ** 2 + np.array(ay) ** 2 + np.array(az) ** 2) / 9.81


# ── Dark-mode rolling chart ───────────────────────────────────────────────────

def _rolling_chart(title: str, t, values, threshold: float, line_color: str,
                   ylabel: str, threshold_label: str):
    fig, ax = plt.subplots(figsize=(7, 2.8))
    
    # Enforcing dark mode per RULE[AGENTS.md]
    fig.patch.set_facecolor("#050505")
    ax.set_facecolor("#0F1115")
    
    ax.tick_params(colors="#8B949E", labelsize=8)
    ax.xaxis.label.set_color("#8B949E")
    ax.yaxis.label.set_color("#8B949E")
    
    # Sharp technical grid lines
    ax.grid(color="#1F232B", linewidth=0.5, linestyle="-", alpha=0.8)
    
    if len(t) > 1:
        # Neon glowing signal lines (double line rendering)
        # Glow bloom
        ax.plot(t, values, color=line_color, linewidth=4.0, alpha=0.35)
        # Sharp trace
        ax.plot(t, values, color=line_color, linewidth=1.5)
        # Backlit area fill-under path
        ax.fill_between(t, values, alpha=0.08, color=line_color)
        
    ax.axhline(threshold, color=AMBER, linewidth=1.0, linestyle="--", label=threshold_label)
    
    ax.set_title(title.upper(), color="#F0F6FC", pad=12, fontsize=10, fontweight="bold", fontfamily="sans-serif")
    ax.set_xlabel("TIME (S)", fontsize=8, fontweight="bold")
    ax.set_ylabel(ylabel.upper(), fontsize=8, fontweight="bold")
    
    for spine in ax.spines.values():
        spine.set_edgecolor("#22252A")
        
    ax.legend(facecolor="#0F1115", edgecolor="#22252A", labelcolor="#F0F6FC", fontsize=8)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ── Sidebar controls ──────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Live Controls")
    scenario = st.selectbox(
        "Scenario",
        ["Normal Riding", "Oil Patch", "Crash"],
        index=["Normal Riding", "Oil Patch", "Crash"].index(st.session_state.live_scenario),
    )
    st.session_state.live_scenario = scenario
    refresh_ms = st.select_slider(
        "Refresh rate",
        options=[500, 1000, 2000, 3000],
        value=1000,
        format_func=lambda v: f"{v} ms",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("▶ Start" if not st.session_state.live_running else "⏸ Pause",
                     type="primary", use_container_width=True):
            st.session_state.live_running = not st.session_state.live_running
            st.rerun()
    with col_b:
        if st.button("↺ Reset", use_container_width=True):
            for k in ["live_tick", "live_buf_ax", "live_buf_ay", "live_buf_az",
                      "live_buf_t", "live_buf_skid", "live_sos_fired", "live_alerts"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state.live_running = False
            st.rerun()

    st.markdown("---")
    profile = load_profile()
    rider_saved_at = profile.get("saved_at") or "not saved yet"
    st.markdown(
        f"""
<div style="font-size:0.8rem;color:{c["MUTED"]};">
  💾 <b style="color:{c["TEXT"]};">{profile['rider_name']}</b><br>
  {profile['blood_group']} · {profile['emergency_contact']}<br>
  <span style="font-size:0.72rem;">Saved: {rider_saved_at}</span>
</div>
""",
        unsafe_allow_html=True,
    )

# ── Page header ───────────────────────────────────────────────────────────────

page_header(
    "📡 Live Helmet Stream",
    "Real-time IMU sensor feed with crash detection and skid prediction.",
    "LIVE" if st.session_state.live_running else "PAUSED",
    RED if st.session_state.live_running else AMBER,
)

# ── Tick and buffer update ────────────────────────────────────────────────────

if st.session_state.live_running:
    t_new, ax_new, ay_new, az_new, skid_new = _next_samples(
        st.session_state.live_scenario, st.session_state.live_tick
    )
    st.session_state.live_tick += 5
    st.session_state.live_buf_t.extend(t_new.tolist())
    st.session_state.live_buf_ax.extend(ax_new.tolist())
    st.session_state.live_buf_ay.extend(ay_new.tolist())
    st.session_state.live_buf_az.extend(az_new.tolist())
    st.session_state.live_buf_skid.extend(skid_new.tolist())
    # Rolling window
    for key in ["live_buf_t", "live_buf_ax", "live_buf_ay", "live_buf_az", "live_buf_skid"]:
        if len(st.session_state[key]) > _BUF_MAX:
            st.session_state[key] = st.session_state[key][-_BUF_MAX:]

# Derived metrics
buf_t = st.session_state.live_buf_t
buf_ax = st.session_state.live_buf_ax
buf_ay = st.session_state.live_buf_ay
buf_az = st.session_state.live_buf_az
buf_skid = st.session_state.live_buf_skid

if buf_t:
    ares = _resultant_g(buf_ax, buf_ay, buf_az)
    peak_accel = float(np.max(ares))
    curr_accel = float(ares[-1])
    skid_max = float(np.max(buf_skid))
    curr_skid = float(buf_skid[-1])
    sample_count = len(buf_t)
    elapsed = buf_t[-1] - buf_t[0] if len(buf_t) > 1 else 0.0
else:
    peak_accel = curr_accel = skid_max = curr_skid = 0.0
    sample_count = 0
    elapsed = 0.0

crash_detected = peak_accel > 6.0 and st.session_state.live_scenario == "Crash"
skid_detected = skid_max > 0.65 and not crash_detected

# ── Alert banner ──────────────────────────────────────────────────────────────

if not buf_t:
    st.markdown(
        f"""
<div style="background:{c["CARD_BG"]};border:1px solid {c["BORDER"]};border-radius:2px;
     padding:1.2rem 1.5rem;margin-bottom:1.5rem;color:{c["MUTED"]};text-align:center;">
    Press <b style="color:{c["TEXT"]};">▶ Start</b> in the sidebar to begin the live sensor stream.
</div>
""",
        unsafe_allow_html=True,
    )
elif crash_detected:
    if not st.session_state.live_sos_fired:
        st.session_state.live_sos_fired = True
        ts = time.strftime("%H:%M:%S")
        st.session_state.live_alerts.append(f"{ts} — CRASH at {peak_accel:.1f}g")
    alert_banner("crash", f"Impact {peak_accel:.1f}g — SOS packet auto-fired. Emergency contact notified.")
elif skid_detected:
    alert_banner("warning", f"P(skid)={skid_max:.2f} — Low-friction surface detected. Haptic alert firing.")
else:
    alert_banner("safe", "IMU stream remains below safe thresholds.")

# ── Stat cards ────────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    stat_card("Current Accel", f"{curr_accel:.2f}", "g", RED if curr_accel > 6 else GREEN)
with c2:
    stat_card("Peak Accel", f"{peak_accel:.2f}", "g", RED if peak_accel > 6 else AMBER)
with c3:
    stat_card("P(skid) now", f"{curr_skid:.2f}", "", AMBER if curr_skid > 0.65 else GREEN)
with c4:
    stat_card("Samples", sample_count, "", c["TEXT"])
with c5:
    stat_card("Elapsed", f"{elapsed:.1f}", "s", c["TEXT"])

# ── Rolling charts ────────────────────────────────────────────────────────────

if buf_t:
    ch1, ch2 = st.columns(2)
    ares_arr = _resultant_g(buf_ax, buf_ay, buf_az)
    with ch1:
        _rolling_chart("Resultant Acceleration (live)", buf_t, ares_arr, 6.0, RED,
                       "Acceleration (g)", "Impact threshold 6 g")
    with ch2:
        _rolling_chart("PINN P(skid) (live)", buf_t, buf_skid, 0.65, AMBER,
                       "Probability", "Warning threshold 0.65")

# ── SOS log ──────────────────────────────────────────────────────────────────

if st.session_state.live_alerts:
    st.markdown("---")
    st.markdown(
        f'<div style="color:{RED};font-weight:700;margin-bottom:0.5rem;">🔴 SOS Event Log</div>',
        unsafe_allow_html=True,
    )
    for entry in reversed(st.session_state.live_alerts[-10:]):
        bg = "#1A0505" if is_dark else "#FFF5F5"
        st.markdown(
            f'<div style="background:{bg};border:1px solid {RED}44;border-radius:2px;'
            f'padding:0.5rem 1rem;margin-bottom:0.4rem;font-size:0.85rem;color:{c["TEXT"]};">'
            f'⚡ {entry}</div>',
            unsafe_allow_html=True,
        )

# ── Auto-refresh ──────────────────────────────────────────────────────────────

if st.session_state.live_running:
    time.sleep(refresh_ms / 1000)
    st.rerun()
