import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from modules.ai_firstaid import generate_firstaid
from modules.emergency_numbers import get_emergency_numbers
from modules.inference import load_model, run_inference
from modules.location import has_location, init_location_state, render_location_sidebar
from modules.profile_store import load_profile
from modules.simulation import simulate_crash, simulate_normal, simulate_oil_patch
from modules.train import train_default
from modules.ui import (
    AMBER,
    GREEN,
    RED,
    alert_banner,
    get_colors,
    get_theme,
    inject_global_css,
    markdown_to_html,
    page_header,
    render_theme_toggle,
    saas_metric,
    sidebar_brand,
)


st.set_page_config(page_title="RoadSoS | Helmet Intelligence", page_icon="🪖", layout="wide")
inject_global_css()
init_location_state()
sidebar_brand()
render_theme_toggle()
render_location_sidebar()

c = get_colors()
is_dark = get_theme() == "dark"

plt.style.use("dark_background")


SEVERITY_COLORS = {
    "SEVERE": (RED, "#1F0808" if is_dark else "#FFF5F5"),
    "MODERATE": (AMBER, "#1F1408" if is_dark else "#FFFBF5"),
    "LOW": (GREEN, "#081F0D" if is_dark else "#F7FFF7"),
}


def styled_plot(title: str, x, y, line_color: str, threshold: float, threshold_label: str, ylabel: str):
    fig, ax = plt.subplots(figsize=(7, 3))
    
    # Pure dark theme surfaces (enforcing dark mode per RULE[AGENTS.md])
    fig.patch.set_facecolor("#050505")
    ax.set_facecolor("#0F1115")
    
    ax.tick_params(colors="#8B949E", labelsize=8)
    ax.xaxis.label.set_color("#8B949E")
    ax.yaxis.label.set_color("#8B949E")
    
    # Grid lines - high-precision, sharp, dark oscilloscope grids
    ax.grid(color="#1F232B", linewidth=0.5, linestyle="-", alpha=0.8)
    
    # Neon glowing signal lines (double line rendering)
    # Glow layer (wider, highly-translucent line)
    ax.plot(x, y, color=line_color, linewidth=4.0, alpha=0.35)
    # Primary telemetry trace (sharp foreground line)
    ax.plot(x, y, color=line_color, linewidth=1.5)
    
    # Gradient/backlighting area fill-under signal path
    ax.fill_between(x, y, 0, color=line_color, alpha=0.08)
    
    # Warning/impact threshold line with amber neon glow
    ax.axhline(threshold, color=AMBER, linewidth=1.0, linestyle="--", label=threshold_label)
    
    # Title & Labeling
    ax.set_title(title.upper(), color="#F0F6FC", pad=12, fontsize=10, fontweight="bold", fontfamily="sans-serif")
    ax.set_xlabel("TIME (S)", fontsize=8, fontweight="bold")
    ax.set_ylabel(ylabel.upper(), fontsize=8, fontweight="bold")
    
    for spine in ax.spines.values():
        spine.set_edgecolor("#22252A")
        
    ax.legend(facecolor="#0F1115", edgecolor="#22252A", labelcolor="#F0F6FC", fontsize=8)
    
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def run_selected_scenario(scenario: str, duration: int) -> dict:
    scenario_map = {
        "Normal Riding": (simulate_normal, {"duration": duration, "seed": 42}, 50),
        "Oil Patch": (simulate_oil_patch, {"duration": duration, "seed": 43}, 50),
        "Crash": (simulate_crash, {"duration": min(duration, 10), "seed": 44}, 1000),
    }
    sim_fn, kwargs, fs = scenario_map[scenario]
    result = run_inference(sim_fn, kwargs, fs=fs)
    result["scenario"] = scenario
    return result


SEVERITY_HEADLINE = {
    "SEVERE": ("CRITICAL", "Life-threatening head and brain loading detected. Treat as major trauma and act immediately."),
    "MODERATE": ("CONCERNING", "Injury thresholds were partly crossed. The rider needs close monitoring and likely medical care."),
    "LOW": ("MINOR", "Readings stayed within safe limits — no impact or skid signature in this window."),
}


def section_title(text: str, color: str = GREEN) -> None:
    st.markdown(
        f"""
<div style="font-family:'Outfit';font-weight:800;font-size:1rem;color:{c["TEXT"]};
     text-transform:uppercase;letter-spacing:0.06em;margin:1.6rem 0 0.8rem;
     border-left:3px solid {color};padding-left:0.7rem;">{text}</div>
""",
        unsafe_allow_html=True,
    )


def info_card(title: str, body_html: str, color: str) -> None:
    st.markdown(
        f"""
<div class="saas-card" style="border-left:4px solid {color} !important; padding: 1.2rem !important; margin-bottom: 0.8rem !important;">
    <div style="color:{color};font-family:'Outfit';font-weight:800;font-size:0.72rem;
         text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.35rem;">{title}</div>
    <div style="color:{c["TEXT"]};font-size:0.86rem;line-height:1.55;font-family:'Inter';">{body_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def insight_row(icon: str, body_html: str, color: str) -> None:
    st.markdown(
        f"""
<div style="background:{c["CARD_BG"]}; border: 1px solid {c["BORDER"]}; border-left: 3px solid {color};
     border-radius: 4px; padding: 1rem; margin-bottom: 0.6rem; display: flex; gap: 0.8rem; align-items: flex-start;">
    <span style="font-size: 1.2rem;">{icon}</span>
    <span style="color:{c["TEXT"]}; font-size: 0.9rem; line-height: 1.6; font-family: 'Inter';">{body_html}</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_metric_guide(peak_accel: float, skid_max: float, result: dict) -> None:
    hic, bric = result["hic15"], result["bric"]
    cards = [
        (
            "Peak Acceleration",
            f"The head was thrown at <b>{peak_accel:.1f} g</b>. Relaxed riding sits near <b>1 g</b>; "
            "anything past the <b>6 g</b> line is a genuine impact.",
            RED if peak_accel > 6 else GREEN,
        ),
        (
            "Skid Probability",
            f"PINN estimates up to a <b>{skid_max * 100:.0f}%</b> chance the tyres lost grip. "
            "Above <b>65%</b> the bike was sliding.",
            AMBER if skid_max > 0.65 else GREEN,
        ),
        (
            "HIC15 · Head Injury",
            f"Skull/brain impact score of <b>{hic:.0f}</b>. Under <b>700</b> is safe, "
            "<b>700–1000</b> moderate, over <b>1000</b> severe.",
            RED if hic > 1000 else AMBER if hic > 700 else GREEN,
        ),
        (
            "BrIC · Brain Rotation",
            f"Rotational brain-injury index of <b>{bric:.2f}</b>. Approaching <b>1.0</b> means "
            "dangerous twisting forces on the brain.",
            RED if bric >= 1.0 else AMBER if bric >= 0.5 else GREEN,
        ),
    ]
    cols = st.columns(2)
    for idx, (title, body, color) in enumerate(cards):
        with cols[idx % 2]:
            info_card(title, body, color)


def render_graph_insights(result: dict, ares: np.ndarray, peak_accel: float, skid_max: float) -> None:
    t = np.asarray(result["t"], dtype=float)
    dt = float(t[1] - t[0]) if t.size > 1 else 0.02
    peak_time = float(t[int(np.argmax(ares))])
    skid_time = float(t[int(np.argmax(result["P_skid"]))])
    time_above = float(np.sum(ares > 6.0) * dt)

    if peak_accel > 6.0:
        insight_row(
            "🔴",
            f"Acceleration spiked to <b>{peak_accel:.1f} g</b> at <b>{peak_time:.2f}s</b> and stayed above "
            f"the 6 g impact line for <b>{time_above * 1000:.0f} ms</b> — a clear crash signature.",
            RED,
        )
    else:
        insight_row(
            "🟢",
            f"Acceleration peaked at only <b>{peak_accel:.1f} g</b>, well under the 6 g impact line — "
            "no impact event in this window.",
            GREEN,
        )

    if skid_max > 0.65:
        skid_first = skid_time < peak_time and peak_accel > 6.0
        timing = "before" if skid_first else "around"
        meaning = "a skid most likely triggered the crash" if skid_first else "the bike was losing grip"
        insight_row(
            "🟡",
            f"Skid probability reached <b>{skid_max * 100:.0f}%</b> at <b>{skid_time:.2f}s</b> "
            f"({timing} the impact) — {meaning}.",
            AMBER,
        )
    else:
        insight_row(
            "🟢",
            f"Skid probability stayed low (peak <b>{skid_max * 100:.0f}%</b>) — the tyres kept grip throughout.",
            GREEN,
        )

    word, text = SEVERITY_HEADLINE.get(result["label"], ("", ""))
    sev_color = RED if result["label"] == "SEVERE" else AMBER if result["label"] == "MODERATE" else GREEN
    insight_row("🩺", f"Overall biomechanical severity: <b>{word}</b>. {text}", sev_color)


with st.sidebar:
    st.header("Simulation Controls")
    scenario = st.selectbox("Scenario", ["Normal Riding", "Oil Patch", "Crash"])
    duration = st.slider("Duration", 5, 30, 8, format="%d sec")
    profile = load_profile()
    with st.expander("Rider Profile", expanded=True):
        blood_options = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
        rider_name = st.text_input("Name", profile["rider_name"])
        blood_group = st.selectbox(
            "Blood Group",
            blood_options,
            index=blood_options.index(profile["blood_group"]) if profile["blood_group"] in blood_options else 0,
        )
        allergies = st.text_input("Allergies", profile["allergies"])
        conditions = st.text_input("Medical Conditions", profile["conditions"])
        emergency_contact = st.text_input("Emergency Contact", profile["emergency_contact"])
        st.session_state.rider_name = rider_name
        st.session_state.blood_group = blood_group
        st.session_state.allergies = allergies
        st.session_state.conditions = conditions
        st.session_state.emergency_contact = emergency_contact
    run_clicked = st.button("Run Simulation", type="primary")

page_header("🪖 Helmet Intelligence", "PINN skid prediction and crash severity simulation.", "TraumaSense AI v1.0", AMBER)

if "last_scenario" not in st.session_state:
    st.session_state.last_scenario = scenario
if "last_duration" not in st.session_state:
    st.session_state.last_duration = duration

if (
    run_clicked
    or "pinn_result" not in st.session_state
    or st.session_state.last_scenario != scenario
    or st.session_state.last_duration != duration
):
    st.session_state["pinn_result"] = run_selected_scenario(scenario, duration)
    st.session_state.last_scenario = scenario
    st.session_state.last_duration = duration

result = st.session_state["pinn_result"]
ares = np.sqrt(result["ax"] ** 2 + result["ay"] ** 2 + result["az"] ** 2) / 9.81
peak_accel = float(ares.max())
skid_max = float(result["P_skid"].max())
crash_detected = result["scenario"] == "Crash" or peak_accel > 6.0
skid_detected = skid_max > 0.65 and not crash_detected

if crash_detected:
    alert_banner("crash", "Impact threshold crossed. Emergency packet is ready for transmission.")
elif skid_detected:
    alert_banner("warning", "Low-friction signature detected. Haptic warning should fire before loss of control.")
else:
    alert_banner("safe", "IMU stream remains below crash and skid thresholds.")

metric_cols = st.columns(4)
with metric_cols[0]:
    saas_metric("Peak Accel", f"{peak_accel:.1f}", "g", RED if peak_accel > 6 else GREEN)
with metric_cols[1]:
    saas_metric("P(skid) max", f"{skid_max:.2f}", "", AMBER if skid_max > 0.65 else GREEN)
with metric_cols[2]:
    saas_metric("HIC15", f"{result['hic15']:.0f}", "", RED if result["hic15"] > 700 else GREEN)
with metric_cols[3]:
    injury_color = RED if result["label"] == "SEVERE" else AMBER if result["label"] == "MODERATE" else GREEN
    saas_metric("Injury", result["label"], "", injury_color)

section_title("Simulation Analysis", GREEN)
render_metric_guide(peak_accel, skid_max, result)

plot_cols = st.columns(2)
with plot_cols[0]:
    styled_plot(
        "Resultant Acceleration",
        result["t"],
        ares,
        RED,
        6.0,
        "Impact threshold",
        "Acceleration (g)",
    )
with plot_cols[1]:
    styled_plot(
        "PINN P(skid)",
        result["t"],
        result["P_skid"],
        AMBER,
        0.65,
        "Warning threshold",
        "Probability",
    )

section_title("Graph Insights", AMBER)
render_graph_insights(result, ares, peak_accel, skid_max)

if crash_detected:
    st.markdown("---")
    st.markdown(
        f"""
<div style="font-size:1.1rem; font-weight:800; color:{RED}; margin-bottom:0.5rem; font-family:'Outfit'; text-transform:uppercase; letter-spacing:0.06em;">
    🩺 AI-Generated First Aid — Based on This Crash Profile
</div>
<div style="color:{c["MUTED"]}; font-size:0.85rem; margin-bottom:1.2rem; font-family:'Inter';">
    Generated using PINN biomechanical outputs (HIC15={result['hic15']:.0f}, BrIC={result['bric']:.3f}, Severity={result['label']})
</div>
""",
        unsafe_allow_html=True,
    )
    sev_word, sev_text = SEVERITY_HEADLINE.get(result["label"], ("", ""))
    sev_color = RED if result["label"] == "SEVERE" else AMBER if result["label"] == "MODERATE" else GREEN
    
    st.markdown(
        f"""
<div class="ai-insight-card">
    <div class="ai-insight-header">
        <span style="font-size: 1.5rem;">🩺</span>
        <div class="ai-insight-title">Biomechanical Severity · {sev_word}</div>
    </div>
    <div style="color:{c["TEXT"]}; font-size:0.92rem; line-height:1.6; font-family:'Inter'; margin-bottom: 1.2rem;">{sev_text}</div>
""",
        unsafe_allow_html=True,
    )
    
    cache_key = f"firstaid_{result['label']}_{int(result['hic15'])}_{int(result['bric'] * 100)}_{int(peak_accel * 10)}"
    if cache_key not in st.session_state:
        with st.spinner("🤖 Generating first-aid instructions..."):
            st.session_state[cache_key] = generate_firstaid(
                hic15=result["hic15"],
                bric=result["bric"],
                injury_label=result["label"],
                peak_accel_g=peak_accel,
                skid_preceded=bool(skid_max > 0.65),
                scenario=result["scenario"],
                rider_name=rider_name,
                blood_group=st.session_state.get("blood_group", "Unknown"),
                allergies=st.session_state.get("allergies", "None"),
                conditions=st.session_state.get("conditions", "None"),
                emergency_contact=st.session_state.get("emergency_contact", "Unknown"),
                lat=float(st.session_state.lat) if has_location() else None,
                lon=float(st.session_state.lon) if has_location() else None,
                city=str(st.session_state.get("city", "Unknown")),
                country_name=str(st.session_state.get("country_name", "Unknown")),
                country_code=str(st.session_state.get("country_code", "XX")),
                location_source=str(st.session_state.get("location_source", "Unavailable")),
            )

    st.markdown(
        f"""
    <div style="color:{c["TEXT"]}; line-height:1.7; font-size:0.95rem; font-family:'Inter';">
        {markdown_to_html(st.session_state[cache_key])}
    </div>
</div>
""",
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        ambulance = get_emergency_numbers(st.session_state.get("country_code", "XX"))["ambulance"]
        st.markdown(
            f'<a href="tel:{ambulance}" class="btn-call" style="display:block; text-align:center; padding:12px; border-radius: 4px; margin-top: 1rem;">📞 Call Ambulance ({ambulance})</a>',
            unsafe_allow_html=True,
        )
    with col2:
        if has_location():
            maps_url = (
                "https://www.google.com/maps/search/hospital+near+me/"
                f"@{float(st.session_state.lat):.6f},{float(st.session_state.lon):.6f},14z"
            )
            st.markdown(
                f'<a href="{maps_url}" target="_blank" class="btn-dir" style="display:block; text-align:center; padding:12px; border-radius: 4px; margin-top: 1rem;">🏥 Find Nearest Hospital</a>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="placeholder-card" style="text-align:center; padding:12px; margin-top:1rem; border-radius: 4px;">Enable location to find the nearest hospital.</div>',
                unsafe_allow_html=True,
            )

st.markdown(
    f"""
<div class="profile-card" style="padding:1.5rem; margin-top:1.5rem; border-radius: 8px;">
  <div style="color:{c["MUTED"]}; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem; font-family:'Outfit'; font-weight:700;">
    Rider SOS Profile
  </div>
  <div style="color:{c["TEXT"]}; font-weight:800; font-family:'Outfit'; font-size:1.2rem; text-transform:uppercase; letter-spacing:0.04em;">{rider_name}</div>
  <div style="color:{c["MUTED"]}; font-size:0.92rem; margin-top:0.4rem; font-family:'Inter';">
    Blood: <b style="color:{GREEN};">{blood_group}</b> · Allergies:
    <b style="color:{GREEN};">{allergies}</b> · Emergency:
    <b style="color:{GREEN};">{emergency_contact}</b>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

with st.expander("⚙ Train / Retrain PINN"):
    model, _, _ = load_model()
    if model is None:
        st.markdown('<div class="placeholder-card" style="border-radius: 8px;">No checkpoint found. Inference is using simulated friction until a checkpoint is trained.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="placeholder-card" style="border-radius: 8px;">Checkpoint loaded from roadsos_app/artifacts/roadsos_pinn.pt</div>', unsafe_allow_html=True)

    if st.button("Train / Retrain PINN", key="train_pinn"):
        progress = st.progress(0)
        with st.spinner("Training compact demo checkpoint..."):
            history = train_default(epochs=25)
            progress.progress(100)
        load_model.clear()
        st.markdown('<div class="placeholder-card" style="border-radius: 8px; border-color: #76B900;">Saved artifacts/roadsos_pinn.pt</div>', unsafe_allow_html=True)
        
        fig, ax = plt.subplots(figsize=(7, 3))
        fig.patch.set_facecolor("#050505")
        ax.set_facecolor("#0F1115")
        
        # Plot total loss with neon glow
        ax.plot(history["total"], color=GREEN, linewidth=4.0, alpha=0.35)
        ax.plot(history["total"], color=GREEN, linewidth=1.5, label="total")
        ax.fill_between(range(len(history["total"])), history["total"], alpha=0.08, color=GREEN)
        
        # Plot data loss with neon glow
        ax.plot(history["data"], color=AMBER, linewidth=4.0, alpha=0.35)
        ax.plot(history["data"], color=AMBER, linewidth=1.5, label="data")
        
        ax.set_yscale("log")
        ax.set_title("TRAINING LOSS", color="#F0F6FC", fontsize=10, fontweight="bold", pad=12)
        ax.tick_params(colors="#8B949E", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#22252A")
        ax.grid(color="#1F232B", linewidth=0.5, linestyle="-", alpha=0.8)
        ax.legend(facecolor="#0F1115", edgecolor="#22252A", labelcolor="#F0F6FC", fontsize=8)
        st.pyplot(fig, width="stretch")
        plt.close(fig)
