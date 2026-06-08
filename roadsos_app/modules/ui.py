from __future__ import annotations

import html
import math
import re
from urllib.parse import quote_plus

import streamlit as st
from roadsos_app.modules.translator import tr, LANGUAGES


# Color Constants
RED = "#E53935"
AMBER = "#FF8F00"
GREEN = "#76B900"

# Theme Colors
THEMES = {
    "dark": {
        "PAGE_BG": "#050505",
        "CARD_BG": "#0F1115",
        "INPUT_BG": "#161B22",
        "BORDER": "#22252A",
        "TEXT": "#F0F6FC",
        "MUTED": "#8B949E",
        "DIVIDER": "#22252A",
        "SUBTLE_BORDER": "#22252A",
        "SC_BADGE_BG": "18",
        "SC_BADGE_BORDER": "33",
        "EN_STRIP_BG": "#150808",
        "EN_STRIP_BORDER": "#E5393533",
        "BTN_DIR_BORDER": "#22252A",
        "BTN_DIR_HOVER_BORDER": "#F0F6FC",
        "CHIP_BG": "#161B22",
        "GLASS_BG": "rgba(15, 17, 21, 0.8)",
    },
    "light": {
        "PAGE_BG": "#F8F9FA",
        "CARD_BG": "#FFFFFF",
        "INPUT_BG": "#FFFFFF",
        "BORDER": "#DEE2E6",
        "TEXT": "#1A1D21",
        "MUTED": "#6C757D",
        "DIVIDER": "#DEE2E6",
        "SUBTLE_BORDER": "#E9ECEF",
        "SC_BADGE_BG": "0D",
        "SC_BADGE_BORDER": "20",
        "EN_STRIP_BG": "#FFF5F5",
        "EN_STRIP_BORDER": "#FEB2B2",
        "BTN_DIR_BORDER": "#DEE2E6",
        "BTN_DIR_HOVER_BORDER": "#1A1D21",
        "CHIP_BG": "#E9ECEF",
        "GLASS_BG": "rgba(255, 255, 255, 0.8)",
    },
}


def get_theme() -> str:
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    return st.session_state.theme


def get_colors() -> dict[str, str]:
    return THEMES[get_theme()]


def toggle_theme() -> None:
    st.session_state.theme = "light" if get_theme() == "dark" else "dark"
    st.rerun()


def micon(
    name: str,
    size: int = 20,
    color: str | None = None,
    fill: bool = False,
    weight: int = 600,
) -> str:
    """Return an inline Material Symbols (Rounded) icon as an HTML span.

    Use inside any raw-HTML context (st.markdown/st.html with unsafe_allow_html).
    For native Streamlit widget labels (st.tabs, st.button) use ':material/<name>:'.
    """
    col = color or "currentColor"
    fill_v = 1 if fill else 0
    return (
        f'<span class="material-symbols-rounded" style="'
        f"font-size:{size}px;color:{col};line-height:1;vertical-align:middle;"
        f"font-variation-settings:'FILL' {fill_v},'wght' {weight},'GRAD' 0,'opsz' {size};"
        f'">{name}</span>'
    )


def markdown_to_html(text: str) -> str:
    """Surgical Markdown to HTML converter for custom UI boxes."""
    if not text:
        return ""

    # Escape HTML first
    safe = html.escape(text)

    # Headers (### Header)
    safe = re.sub(r"^### (.*?)$", r'<h3 style="margin:1rem 0 0.5rem;font-size:1.1rem;font-family:\'Outfit\';text-transform:uppercase;letter-spacing:0.04em;">\1</h3>', safe, flags=re.MULTILINE)
    safe = re.sub(r"^## (.*?)$", r'<h3 style="margin:1.2rem 0 0.6rem;font-size:1.2rem;font-family:\'Outfit\';text-transform:uppercase;letter-spacing:0.04em;">\1</h3>', safe, flags=re.MULTILINE)
    safe = re.sub(r"^# (.*?)$", r'<h2 style="margin:1.5rem 0 0.8rem;font-size:1.4rem;font-family:\'Outfit\';text-transform:uppercase;letter-spacing:0.04em;">\1</h2>', safe, flags=re.MULTILINE)

    # Bold (**text**)
    safe = re.sub(r"\*\*(.*?)\*\*", f"<b style='color:{GREEN};font-weight:700;'>\\1</b>", safe)

    # Bullet points (* or -)
    def repl_list(match):
        items = match.group(0).strip().split("\n")
        html_items = "".join([f"<li style='margin-bottom:0.4rem;'>{re.sub(r'^[\*\-]\s+', '', item)}</li>" for item in items])
        return f"<ul style='margin:0.8rem 0;padding-left:1.4rem;list-style-type:square;'>{html_items}</ul>"

    safe = re.sub(r"((?:^[\*\-]\s+.*(?:\n|$))+)", repl_list, safe, flags=re.MULTILINE)

    # Numbered points (1.)
    def repl_num_list(match):
        items = match.group(0).strip().split("\n")
        html_items = "".join([f"<li style='margin-bottom:0.4rem;'>{re.sub(r'^\d+\.\s+', '', item)}</li>" for item in items])
        return f"<ol style='margin:0.8rem 0;padding-left:1.4rem;'>{html_items}</ol>"

    safe = re.sub(r"((?:^\d+\.\s+.*(?:\n|$))+)", repl_num_list, safe, flags=re.MULTILINE)

    # Newlines
    safe = safe.replace("\n", "<br>")

    return safe


def inject_global_css() -> None:
    c = get_colors()
    is_dark = get_theme() == "dark"

    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

/* Professional Icon System — Material Symbols Rounded */
.material-symbols-rounded {{
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal !important;
    font-style: normal !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    display: inline-block !important;
    -webkit-font-smoothing: antialiased !important;
    font-feature-settings: 'liga' !important;
    vertical-align: middle;
}}

/* Status badge colours (no animation) */
.pulse-green, .pulse-amber, .pulse-red {{ /* intentionally empty — animations removed */ }}

/* Base */
html, body, [data-testid="stAppViewContainer"] {{
    background-color: {c["PAGE_BG"]} !important;
    color: {c["TEXT"]} !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
[data-testid="stSidebar"] {{
    background-color: {c["PAGE_BG"]} !important;
    border-right: 1px solid {c["BORDER"]} !important;
}}
[data-testid="stSidebar"] * {{ color: {c["TEXT"]} !important; }}
.block-container {{ padding-top: 1rem; max-width: 1400px; padding-left: 3rem; padding-right: 3rem; }}

/* Remove ALL Streamlit chrome including the header strip */
#MainMenu, footer, header,
[data-testid="stAppDeployButton"],
[data-testid="stToolbar"],
[data-testid="stHeader"] {{
    display: none !important;
    height: 0 !important;
    visibility: hidden !important;
}}
[data-testid="stSidebarCollapseButton"] {{
    display: none !important;
}}

/* Sidebar nav labels — hide filename text, inject clean product names via ::after */
[data-testid="stSidebarNav"] li a p {{
    font-size: 0 !important;
    line-height: 0 !important;
}}
[data-testid="stSidebarNav"] li a p::after {{
    font-size: 0.92rem !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    color: inherit !important;
    line-height: 1.4 !important;
}}
[data-testid="stSidebarNav"] li:nth-child(1) a p::after {{ content: "Command Center"; }}
[data-testid="stSidebarNav"] li:nth-child(2) a p::after {{ content: "Helmet Intelligence"; }}
[data-testid="stSidebarNav"] li:nth-child(3) a p::after {{ content: "Nearby Services"; }}
[data-testid="stSidebarNav"] li:nth-child(4) a p::after {{ content: "Rider Profile & SOS"; }}
[data-testid="stSidebarNav"] li:nth-child(5) a p::after {{ content: "RoadSoS AI Assistant"; }}
[data-testid="stSidebarNav"] li:nth-child(6) a p::after {{ content: "Live Helmet Stream"; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {c["PAGE_BG"]}; }}
::-webkit-scrollbar-thumb {{
    background: {GREEN}44;
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{ background: {GREEN}99; }}

/* Uniform column gap across the whole app */
[data-testid="stHorizontalBlock"] {{
    gap: 1rem !important;
    align-items: stretch !important;
}}
[data-testid="column"] {{
    min-width: 0 !important;
}}

/* Vertical spacing between Streamlit elements */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlock"] > div {{
    margin-bottom: 0.75rem !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Outfit', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 800 !important;
    margin-bottom: 1rem !important;
}}

/* Buttons */
.stButton > button {{
    background: {GREEN} !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 0.7rem 1.4rem !important;
    transition: background 0.15s ease !important;
    width: 100% !important;
}}
.stButton > button:hover {{ background: #88d000 !important; }}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div,
.stNumberInput input {{
    background: {c["INPUT_BG"]} !important;
    border: 1px solid {c["BORDER"]} !important;
    border-radius: 6px !important;
    color: {c["TEXT"]} !important;
    font-family: 'Inter', sans-serif !important;
    padding: 10px 14px !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {{
    border-color: {GREEN} !important;
    outline: none !important;
}}
.stSlider [data-baseweb="slider"] div {{ color: {GREEN} !important; }}

/* Toggles: keep the track, knob, and label visible in both themes */
[data-testid="stCheckbox"] {{
    background: {c["CARD_BG"]} !important;
    border: 1px solid {c["BORDER"]} !important;
    border-radius: 8px !important;
    padding: 0.85rem 1rem !important;
}}
[data-testid="stCheckbox"] [data-testid="stWidgetLabel"] p {{
    color: {c["TEXT"]} !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
}}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input[type="checkbox"] + div {{
    background-color: {c["MUTED"]} !important;
    border: 1px solid {c["BORDER"]} !important;
    box-shadow: inset 0 0 0 1px {c["BORDER"]} !important;
}}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input[type="checkbox"]:checked + div {{
    background-color: {GREEN} !important;
    border-color: {GREEN} !important;
    box-shadow: inset 0 0 0 1px {GREEN} !important;
}}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input[type="checkbox"] + div > div {{
    background-color: {c["CARD_BG"]} !important;
    border: 1px solid {c["TEXT"]}44 !important;
}}
[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > input[type="checkbox"]:focus-visible + div {{
    outline: 3px solid {GREEN}55 !important;
    outline-offset: 2px !important;
}}

/* Metrics */
[data-testid="metric-container"] {{
    position: relative !important;
    background: {c["CARD_BG"]} !important;
    border: 1px solid {c["BORDER"]} !important;
    border-radius: 8px !important;
    padding: 1.2rem !important;
    overflow: hidden !important;
}}
[data-testid="metric-container"]::before {{
    content: "" !important;
    position: absolute !important;
    top: 0; left: 0 !important;
    width: 3px !important;
    height: 100% !important;
    background: {GREEN} !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: {c["CARD_BG"]} !important;
    border-radius: 8px !important;
    gap: 6px !important;
    padding: 5px !important;
    border: 1px solid {c["BORDER"]} !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {c["MUTED"]} !important;
    border-radius: 6px !important;
    border: none !important;
    font-family: 'Outfit', sans-serif !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    font-weight: 700 !important;
    font-size: 0.83rem !important;
    padding: 10px 20px !important;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: {GREEN} !important; }}
.stTabs [aria-selected="true"] {{
    background: {GREEN} !important;
    color: #000000 !important;
}}

/* Divider */
hr {{ border-color: {c["DIVIDER"]} !important; margin: 1.5rem 0 !important; }}

/* Cards — flat, no lift animations */
.saas-card, .profile-card, .svc-card, .ai-insight-card {{
    background: {c["CARD_BG"]} !important;
    border: 1px solid {c["BORDER"]} !important;
    border-radius: 10px !important;
    padding: 1.2rem !important;
    position: relative !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
}}
.saas-card:hover, .profile-card:hover, .svc-card:hover {{ border-color: {GREEN}66 !important; }}

/* Left accent stripe */
.saas-card-accent, .profile-card::before, .svc-card::before, .ai-insight-card::before {{
    content: "" !important;
    position: absolute !important;
    top: 0; left: 0 !important;
    width: 3px !important;
    height: 100% !important;
    background: {GREEN} !important;
}}

.sc-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 0.8rem; margin-bottom: 1rem; }}
.sc-name {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
    color: {c["TEXT"]} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
}}
.sc-cat {{ font-size: 0.8rem !important; color: {c["MUTED"]} !important; margin-top: 3px !important; }}
.sc-badge {{
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 4px 10px !important;
    border-radius: 4px !important;
}}
.sc-meta {{ display: flex; gap: 1.2rem; font-size: 0.85rem; color: {c["MUTED"]}; margin-bottom: 1rem; flex-wrap: wrap; }}
.sc-actions {{ display: flex; gap: 0.7rem; flex-wrap: wrap; margin-top: auto; }}

/* CTAs */
.btn-call {{
    background: {GREEN} !important; color: #000 !important;
    padding: 9px 18px !important; border-radius: 6px !important;
    text-decoration: none !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.82rem !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.07em !important;
    flex: 1 !important; text-align: center !important;
    transition: background 0.15s !important;
}}
.btn-call:hover {{ background: #88d000 !important; }}
.btn-dir {{
    background: {c["INPUT_BG"]} !important; color: {c["TEXT"]} !important;
    padding: 9px 18px !important;
    border: 1px solid {c["BORDER"]} !important; border-radius: 6px !important;
    text-decoration: none !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.82rem !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.07em !important;
    flex: 1 !important; text-align: center !important;
    transition: border-color 0.15s !important;
}}
.btn-dir:hover {{ border-color: {GREEN} !important; color: {GREEN} !important; }}

/* Emergency strip */
.en-strip {{
    background: {c["CARD_BG"]} !important;
    border: 1px solid {RED}44 !important;
    border-left: 5px solid {RED} !important;
    border-radius: 10px !important;
    padding: 1.2rem 1.5rem !important;
    margin: 1.5rem 0 !important;
}}
.en-title {{
    font-family: 'Outfit', sans-serif !important;
    color: {RED} !important; font-weight: 800 !important;
    margin-bottom: 1rem !important; font-size: 1rem !important;
    text-transform: uppercase !important; letter-spacing: 0.1em !important;
}}

/* Stat cards */
.saas-metric-label {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.75rem !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.1em !important;
    color: {c["MUTED"]} !important; margin-bottom: 0.6rem !important;
}}
.saas-metric-value {{
    font-family: 'Outfit', sans-serif !important;
    font-size: 2.2rem !important; font-weight: 800 !important; line-height: 1 !important;
}}
.saas-metric-unit {{
    font-size: 0.95rem !important; font-weight: 500 !important;
    color: {c["MUTED"]} !important; margin-left: 5px !important;
}}

/* AI insight card — no glassmorphism */
.ai-insight-card {{
    background: {c["CARD_BG"]} !important;
    border: 1px solid {GREEN}33 !important;
}}
.ai-insight-header {{
    display: flex !important; align-items: center !important; gap: 0.8rem !important;
    margin-bottom: 1.2rem !important;
    border-bottom: 1px solid {c["DIVIDER"]} !important; padding-bottom: 0.8rem !important;
}}

/* Alert banners — flat */
.saas-alert-banner {{
    border-radius: 10px !important;
    padding: 1.2rem 1.6rem !important;
    position: relative !important;
}}

/* Profile Avatar */
.profile-avatar {{
    width: 80px; height: 80px; border-radius: 12px;
    background: {GREEN} !important; color: #000000 !important;
    display: inline-flex !important; align-items: center !important; justify-content: center !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.8rem !important; font-weight: 800 !important; margin-bottom: 1.5rem !important;
    box-shadow: 0 4px 12px {GREEN}44 !important;
}}

.chip {{
    background: {c["INPUT_BG"]} !important;
    color: {c["TEXT"]} !important;
    border: 1px solid {c["BORDER"]} !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    margin-right: 8px !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )

    components_html_code = """
<script>
(function() {
  const doc = window.parent.document;
  if (window.frameElement) {
    window.frameElement.style.display = "none";
    const controllerContainer = window.frameElement.closest('[data-testid="stElementContainer"]');
    if (controllerContainer) controllerContainer.style.display = "none";
  }
  
  // 1. Sidebar Toggle Button Integration
  const existingToggle = doc.getElementById("roadsos-sidebar-toggle");
  if (existingToggle) existingToggle.remove();

  const toggleBtn = doc.createElement("button");
  toggleBtn.id = "roadsos-sidebar-toggle";
  toggleBtn.type = "button";
  toggleBtn.title = "Toggle sidebar";
  toggleBtn.setAttribute("aria-label", "RoadSoS toggle sidebar");
  toggleBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size:22px;">menu</span>';
  toggleBtn.style.cssText = [
    "position: fixed",
    "top: 16px",
    "left: 16px",
    "width: 40px",
    "height: 40px",
    "display: inline-flex",
    "align-items: center",
    "justify-content: center",
    "z-index: 2147483647",
    "border: 1px solid PLOT_BORDER",
    "border-radius: 8px",
    "background: PLOT_CARD_BG",
    "color: PLOT_GREEN",
    "font-size: 22px",
    "font-weight: 800",
    "line-height: 1",
    "cursor: pointer",
    "box-shadow: 0 6px 18px rgba(0, 0, 0, 0.22)",
    "transition: border-color 0.15s"
  ].join(";");

  const findNativeToggle = () => {
    const candidates = Array.from(doc.querySelectorAll("button"));
    return candidates.find((el) => {
      if (el.id === "roadsos-sidebar-toggle") return false;
      const label = (el.getAttribute("aria-label") || "").toLowerCase();
      const text = (el.textContent || "").toLowerCase();
      const testid = (el.getAttribute("data-testid") || el.closest("[data-testid]")?.getAttribute("data-testid") || "").toLowerCase();
      return label.includes("sidebar") ||
        testid.includes("sidebarcollapsebutton") ||
        text.includes("keyboard_double_arrow_left") ||
        text.includes("keyboard_double_arrow_right");
    });
  };

  toggleBtn.addEventListener("mouseenter", () => {
    toggleBtn.style.borderColor = "PLOT_GREEN";
    toggleBtn.style.background = "PLOT_GREEN22";
    toggleBtn.style.borderColor = "PLOT_GREEN";
    toggleBtn.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.3)";
  });
  toggleBtn.addEventListener("mouseleave", () => {
    toggleBtn.style.borderColor = "PLOT_BORDER";
    toggleBtn.style.background = "PLOT_CARD_BG";
    toggleBtn.style.borderColor = "PLOT_BORDER";
    toggleBtn.style.boxShadow = "0 4px 12px rgba(0, 0, 0, 0.2)";
  });
  toggleBtn.addEventListener("click", () => {
    const native = findNativeToggle();
    if (native) native.click();
  });

  doc.body.appendChild(toggleBtn);

  // 2. Product-ready page titles and sidebar menu labels
  const pageLabels = {
    "/": "Command Center",
    "/PINN_Dashboard": "Helmet Intelligence",
    "/Nearby_Services": "Nearby Services",
    "/Emergency_Profile": "Rider Profile & SOS",
    "/AI_Assistant": "RoadSoS AI Assistant",
    "/Live_Dashboard": "Live Helmet Stream"
  };
  const cleanPath = (value) => {
    const path = new URL(value, window.parent.location.origin).pathname.replace(/\\/+$/, "");
    return path || "/";
  };
  const currentPath = cleanPath(window.parent.location.href);
  const activePageLabel = pageLabels[currentPath] || "Command Center";

  const updateNavigationLabels = () => {
    doc.querySelectorAll('[data-testid="stSidebarNav"] a[href]').forEach((link) => {
      const label = pageLabels[cleanPath(link.href)];
      if (!label) return;
      const paragraph = link.querySelector("p");
      if (paragraph && paragraph.textContent !== label) paragraph.textContent = label;
      link.setAttribute("aria-label", label);
      link.setAttribute("title", label);
    });
    doc.title = "RoadSoS | " + activePageLabel;
  };
  updateNavigationLabels();
  setTimeout(updateNavigationLabels, 250);
  setTimeout(updateNavigationLabels, 1000);
  new MutationObserver(updateNavigationLabels).observe(doc.body, { childList: true, subtree: true });


  // 3. Persistent Floating Global Chatbot
  const chatExisting = doc.getElementById("roadsos-global-chatbot");
  if (chatExisting) chatExisting.remove();

  const chatbotContainer = doc.createElement("div");
  chatbotContainer.id = "roadsos-global-chatbot";
  chatbotContainer.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 2147483647;
    font-family: 'Inter', -apple-system, sans-serif;
  `;

  // Create Chatbot Button
  const chatbotBtn = doc.createElement("button");
  chatbotBtn.id = "roadsos-chatbot-toggle";
  chatbotBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size:26px;">smart_toy</span>';
  chatbotBtn.style.cssText = `
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: #0F1115;
    border: 2px solid PLOT_GREEN;
    color: PLOT_GREEN;
    font-size: 26px;
    cursor: pointer;
    box-shadow: 0 0 16px rgba(118, 185, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: border-color 0.15s;
  `;

  chatbotBtn.addEventListener("mouseenter", () => {
    chatbotBtn.style.borderColor = "#95df00";
  });
  chatbotBtn.addEventListener("mouseleave", () => {
    chatbotBtn.style.borderColor = "PLOT_GREEN";
    chatbotBtn.style.boxShadow = "0 0 16px rgba(118, 185, 0, 0.4)";
  });

  // Create Chat Window Overlay
  const chatWindow = doc.createElement("div");
  chatWindow.id = "roadsos-chatbot-window";
  chatWindow.style.cssText = `
    position: absolute;
    bottom: 72px;
    right: 0;
    width: 360px;
    height: 480px;
    background: #050505;
    border: 1px solid #22252A;
    border-radius: 12px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.6);
    display: none;
    flex-direction: column;
    overflow: hidden;
    transition: border-color 0.15s;
  `;

  // Use the canonical clean-route label so navigation and companion context
  // always describe the same active Streamlit page.
  const pageName = activePageLabel;

  // Header element
  const header = doc.createElement("div");
  header.style.cssText = `
    padding: 16px;
    background: #0F1115;
    border-bottom: 1px solid #22252A;
    display: flex;
    align-items: center;
    justify-content: space-between;
  `;
  header.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <span style="width: 8px; height: 8px; border-radius: 50%; background: PLOT_GREEN; box-shadow: 0 0 8px PLOT_GREEN;"></span>
      <b style="color: #F0F6FC; font-size: 0.9rem; font-family: 'Outfit', sans-serif; text-transform: uppercase; letter-spacing: 0.05em;">RoadSoS Companion</b>
    </div>
    <span style="font-size: 0.72rem; color: #8B949E; border: 1px solid #22252A; padding: 2px 8px; border-radius: 4px; font-weight: 600; display:inline-flex; align-items:center; gap:4px;"><span class="material-symbols-rounded" style="font-size:14px;">description</span>` + pageName + `</span>
  `;

  // Messages historical scroll area
  const messagesArea = doc.createElement("div");
  messagesArea.style.cssText = `
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  `;
  
  messagesArea.innerHTML = `
    <div style="display: flex; gap: 8px; align-items: flex-start;">
      <div style="background: PLOT_GREEN; color: #000000; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 800;"><span class="material-symbols-rounded" style="font-size:15px;color:#000;">smart_toy</span></div>
      <div style="background: #0F1115; border: 1px solid #22252A; border-left: 2px solid PLOT_GREEN; padding: 10px 14px; border-radius: 6px; font-size: 0.82rem; color: #F0F6FC; line-height: 1.45; max-width: 80%;">
        Hello! I am your RoadSoS global assistant. I see you are currently on the <b>` + pageName + `</b> page. How can I help you?
      </div>
    </div>
  `;

  // Message input bar
  const inputContainer = doc.createElement("div");
  inputContainer.style.cssText = `
    padding: 12px;
    background: #0F1115;
    border-top: 1px solid #22252A;
    display: flex;
    gap: 8px;
  `;

  const textInput = doc.createElement("input");
  textInput.type = "text";
  textInput.placeholder = "Open secure AI assistant...";
  textInput.style.cssText = `
    flex: 1;
    background: #161B22;
    border: 1px solid #22252A;
    border-radius: 6px;
    color: #F0F6FC;
    font-size: 0.82rem;
    padding: 8px 12px;
    outline: none;
    transition: all 0.2s ease;
  `;
  textInput.addEventListener("focus", () => {
    textInput.style.borderColor = "PLOT_GREEN";
    textInput.style.boxShadow = "0 0 8px rgba(118, 185, 0, 0.3)";
  });
  textInput.addEventListener("blur", () => {
    textInput.style.borderColor = "#22252A";
    textInput.style.boxShadow = "none";
  });

  const sendBtn = doc.createElement("button");
  sendBtn.innerHTML = '<span class="material-symbols-rounded" style="font-size:18px;color:#000;">send</span>';
  sendBtn.style.cssText = `
    background: PLOT_GREEN;
    border: none;
    border-radius: 6px;
    width: 32px;
    height: 32px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
  `;
  sendBtn.addEventListener("mouseenter", () => {
    sendBtn.style.background = "#95df00";
  });
  sendBtn.addEventListener("mouseleave", () => {
    sendBtn.style.background = "PLOT_GREEN";
  });

  inputContainer.appendChild(textInput);
  inputContainer.appendChild(sendBtn);

  chatWindow.appendChild(header);
  chatWindow.appendChild(messagesArea);
  chatWindow.appendChild(inputContainer);

  chatbotContainer.appendChild(chatbotBtn);
  chatbotContainer.appendChild(chatWindow);
  doc.body.appendChild(chatbotContainer);

  // Toggle Action
  chatbotBtn.addEventListener("click", () => {
    const isVisible = chatWindow.style.display === "flex";
    chatWindow.style.display = isVisible ? "none" : "flex";
    if (!isVisible) {
      setTimeout(() => textInput.focus(), 50);
    }
  });

  // API Config
  const apiKey = "PLOT_API_KEY";
  const provider = "PLOT_PROVIDER";
  const openrouterModel = "PLOT_MODEL";
  const chatHistory = [];

  const addMessage = (role, text) => {
    const bubble = doc.createElement("div");
    bubble.style.cssText = `
      display: flex;
      gap: 8px;
      align-items: flex-start;
      margin: 4px 0;
      justify-content: ` + (role === "user" ? "flex-end" : "flex-start") + `;
    `;
    
    if (role === "user") {
      bubble.innerHTML = `
        <div style="background: #1A0808; border: 1px solid rgba(229, 57, 53, 0.25); padding: 10px 14px; border-radius: 6px; font-size: 0.82rem; color: #F0F6FC; line-height: 1.45; max-width: 80%; position: relative;">
          <div style="position: absolute; top: -1px; right: -1px; width: 4px; height: 4px; background: #E53935;"></div>
          ` + text.replace(/</g, "&lt;").replace(/>/g, "&gt;") + `
        </div>
      `;
    } else {
      bubble.innerHTML = `
        <div style="background: PLOT_GREEN; color: #000000; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 800;"><span class="material-symbols-rounded" style="font-size:15px;color:#000;">smart_toy</span></div>
        <div style="background: #0F1115; border: 1px solid #22252A; border-left: 2px solid PLOT_GREEN; padding: 10px 14px; border-radius: 6px; font-size: 0.82rem; color: #F0F6FC; line-height: 1.45; position: relative;">
          <div style="position: absolute; top: -1px; right: -1px; width: 4px; height: 4px; background: PLOT_GREEN;"></div>
          ` + text + `
        </div>
      `;
    }
    messagesArea.appendChild(bubble);
    messagesArea.scrollTop = messagesArea.scrollHeight;
  };

  const handleSend = async () => {
    const val = textInput.value.trim();
    if (!val) return;
    textInput.value = "";
    addMessage("user", val);
    addMessage("assistant", "Opening the secure RoadSoS AI Assistant...");
    setTimeout(() => {
      window.parent.location.href = "/AI_Assistant";
    }, 350);
    return;

    const typingBubble = doc.createElement("div");
    typingBubble.id = "roadsos-typing-indicator";
    typingBubble.style.cssText = "display: flex; gap: 8px; align-items: center; color: #8B949E; font-size: 0.78rem; padding-left: 32px; margin: 4px 0;";
    typingBubble.innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px;"><span class="material-symbols-rounded" style="font-size:14px;">bolt</span> RoadSoS AI is thinking...</span>`;
    messagesArea.appendChild(typingBubble);
    messagesArea.scrollTop = messagesArea.scrollHeight;

    try {
      const pageContexts = {
        "Command Center": "The user is currently viewing the Command Center page, which acts as the operations dashboard showing live status and mission modules.",
        "Helmet Intelligence": "The user is viewing Helmet Intelligence. It runs normal, oil-patch, and crash simulations, displays biomechanical head-injury scores (HIC15 and BrIC), and renders telemetry graphs.",
        "Nearby Services": "The user is viewing the Nearby Emergency Services search. It displays Hospital, Police, and Towing contact cards from OSM live queries.",
        "Rider Profile & SOS": "The user is viewing Rider Profile & SOS. It configures blood group, allergies, conditions, emergency contact details, and a scannable QR handoff for responders.",
        "RoadSoS AI Assistant": "The user is viewing the RoadSoS AI Assistant, where they can ask contextual first-aid and Indian road-accident procedure questions.",
        "Live Helmet Stream": "The user is viewing Live Helmet Stream, which has rolling IMU telemetry, real-time skid prediction, and an active SOS incident log."
      };
      
      const systemPrompt = "You are the RoadSoS Global AI Companion. Keep replies brief, calm, and highly action-oriented. Answer the user based on the app features and context.\\nContext: " + (pageContexts[pageName] || "");
      
      let reply = "";
      if (provider === "openrouter") {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
          method: "POST",
          headers: {
            "Authorization": "Bearer " + apiKey,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            model: openrouterModel || "openrouter/auto",
            messages: [
              { role: "system", content: systemPrompt },
              ...chatHistory
            ],
            max_tokens: 250
          })
        });
        if (!response.ok) throw new Error("HTTP " + response.status);
        const data = await response.json();
        reply = data.choices[0].message.content;
      } else {
        const response = await fetch("https://api.anthropic.com/v1/messages", {
          method: "POST",
          headers: {
            "x-api-key": apiKey,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "anthropic-dangerous-direct-browser-access": "true"
          },
          body: JSON.stringify({
            model: "claude-3-5-haiku-20241022",
            max_tokens: 250,
            system: systemPrompt,
            messages: chatHistory
          })
        });
        if (!response.ok) throw new Error("HTTP " + response.status);
        const data = await response.json();
        reply = data.content[0].text;
      }
      
      const indicator = doc.getElementById("roadsos-typing-indicator");
      if (indicator) indicator.remove();
      
      addMessage("assistant", reply);
      chatHistory.push({ role: "assistant", content: reply });
    } catch (err) {
      const indicator = doc.getElementById("roadsos-typing-indicator");
      if (indicator) indicator.remove();
      addMessage("assistant", "Error connecting to AI: " + err.message + "\\n\\nGuidance: Stay calm. In case of head trauma, do not move the patient unless immediate danger is present.");
    }
  };

  sendBtn.addEventListener("click", handleSend);
  textInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleSend();
  });

})();
</script>
"""

    components_html_code = components_html_code.replace("PLOT_GREEN", GREEN)
    components_html_code = components_html_code.replace("PLOT_BORDER", c["BORDER"])
    components_html_code = components_html_code.replace("PLOT_CARD_BG", c["CARD_BG"])
    
    components_html_code = components_html_code.replace("PLOT_API_KEY", "")
    components_html_code = components_html_code.replace("PLOT_PROVIDER", "none")
    components_html_code = components_html_code.replace("PLOT_MODEL", "")

    st.html(
        components_html_code,
        unsafe_allow_javascript=True,
    )



def sidebar_brand() -> None:
    c = get_colors()
    st.sidebar.markdown(
        f"""
<div style="text-align:center;padding:1.5rem 0 1rem;">
    <div style="text-shadow: 0 0 20px {GREEN}33;">{micon("sports_motorsports", size=46, color=GREEN, fill=True)}</div>
    <div style="font-weight:800;font-size:1.5rem;color:{c["TEXT"]};font-family:'Outfit';letter-spacing:0.15em;text-transform:uppercase;margin-top:0.6rem;">RoadSoS</div>
    <div style="font-size:0.7rem;color:{GREEN};letter-spacing:0.2em;font-family:'Outfit';font-weight:700;text-transform:uppercase;margin-top:0.2rem;">
        DETECTION BEFORE DIAGNOSIS
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Global Language Selection Dropdown (100 languages)
    if "selected_language" not in st.session_state:
        st.session_state.selected_language = "English"

    lang_options = list(LANGUAGES.keys())
    try:
        current_index = lang_options.index(st.session_state.selected_language)
    except ValueError:
        current_index = 0

    selected_lang = st.sidebar.selectbox(
        "🌐 Language / भाषा",
        options=lang_options,
        index=current_index,
        key="lang_selector_widget"
    )

    if selected_lang != st.session_state.selected_language:
        st.session_state.selected_language = selected_lang
        st.rerun()

    st.sidebar.markdown(
        f'<hr style="border-color:{c["DIVIDER"]};margin:1rem 0;">',
        unsafe_allow_html=True,
    )


def page_header(
    title: str,
    subtitle: str,
    badge_text: str | None = None,
    badge_color: str = GREEN,
    icon: str | None = None,
) -> None:
    c = get_colors()
    icon_html = ""
    if icon:
        icon_html = (
            f'<span style="margin-right:14px;vertical-align:middle;">'
            f'{micon(icon, size=34, color=GREEN, fill=True)}</span>'
        )
    badge_html = ""
    if badge_text:
        pulse_class = "pulse-green"
        if badge_color == RED:
            pulse_class = "pulse-red"
        elif badge_color == AMBER:
            pulse_class = "pulse-amber"
        badge_html = (
            f'<span class="{pulse_class}" style="background:{badge_color}18;color:{badge_color};border:1px solid {badge_color}33;'
            "font-family:'Outfit';font-size:0.75rem;font-weight:700;padding:6px 16px;border-radius:8px;"
            'margin-left:16px;vertical-align:middle;text-transform:uppercase;letter-spacing:0.1em;display:inline-block;">'
            f"{html.escape(tr(badge_text))}"
            "</span>"
        )
    st.markdown(
        f"""
<div style="margin-bottom:2rem;">
    <h1 style="color:{c["TEXT"]};margin:0;font-size:2.2rem;font-family:'Outfit';font-weight:800;text-transform:uppercase;letter-spacing:0.08em;display:inline-block;vertical-align:middle;">
        {icon_html}{html.escape(tr(title))}
    </h1>
    {badge_html}
    <p style="color:{c["MUTED"]};margin:10px 0 0 0;font-size:1rem;font-family:'Inter';font-weight:400;opacity:0.9;">{html.escape(tr(subtitle))}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def alert_banner(level: str, message: str) -> None:
    c = get_colors()
    is_dark = get_theme() == "dark"
    config = {
        "crash": (RED, "#1F0808" if is_dark else "#FFF5F5", "crisis_alert", "CRASH DETECTED — SOS FIRED"),
        "warning": (AMBER, "#1F1408" if is_dark else "#FFFBF5", "warning", "SKID WARNING — HAPTIC ALERT"),
        "safe": (GREEN, "#081F0D" if is_dark else "#F7FFF7", "verified_user", "SAFE — NORMAL RIDING"),
    }
    color, bg, icon_name, label = config[level]
    icon = micon(icon_name, size=26, color=color, fill=True)
    pulse_class = "pulse-green" if level == "safe" else "pulse-red" if level == "crash" else "pulse-amber"
    st.markdown(
        f"""
<div class="saas-alert-banner {pulse_class}" style="background:{bg}; border: 1px solid {color}33;">
    <div style="position:absolute;top:0;left:0;width:100%;height:100%;background:linear-gradient(90deg, {color}08 0%, transparent 100%);pointer-events:none;"></div>
    <div class="saas-alert-icon" style="color:{color}; border: 2px solid {color}22; background: {color}11;">{icon}</div>
    <div class="saas-alert-content">
        <div class="saas-alert-title" style="color:{color};">{html.escape(tr(label))}</div>
        <div class="saas-alert-desc">{html.escape(tr(message))}</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def saas_metric(label: str, value: str | int | float, unit: str = "", color: str | None = None) -> None:
    c = get_colors()
    display_color = color if color else c["TEXT"]
    st.markdown(
        f"""
<div class="saas-card">
    <div class="saas-card-accent" style="background:{display_color} !important;"></div>
    <div class="saas-metric-label">{html.escape(tr(label))}</div>
    <div class="saas-metric-value" style="color:{display_color} !important;">
        {html.escape(tr(str(value)))}<span class="saas-metric-unit">{html.escape(tr(unit))}</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str | int | float, unit: str = "", color: str | None = None) -> None:
    saas_metric(label, value, unit, color)


def emergency_number_strip(country_name: str, numbers: dict[str, str]) -> None:
    items = "".join(
        f'<a href="tel:{html.escape(v, quote=True)}" class="en-item" style="flex:1; min-width:100px; text-decoration:none;">'
        f'<div class="en-num" style="color:{RED}; font-size:2.4rem;">{html.escape(v)}</div>'
        f'<div class="en-label" style="font-size:0.8rem;">{html.escape(k.title())}</div>'
        "</a>"
        for k, v in numbers.items()
    )
    st.markdown(
        f"""
<div class="en-strip">
    <div class="en-title">{micon("bolt", size=22, color=RED, fill=True)} Quick Emergency Numbers — {html.escape(country_name)}</div>
    <div class="en-row" style="display:flex; justify-content:space-between; text-align:center;">{items}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def global_sos_card(country_name: str, profile: dict[str, object]) -> None:
    c = get_colors()
    sos_number = str(profile["unified"])
    coverage = str(profile["coverage"])
    note = str(profile["note"])
    fallback = bool(profile["is_mobile_fallback"])
    status_color = AMBER if fallback else RED
    st.sidebar.markdown(
        f"""
<div style="background:{c["CARD_BG"]};border:1px solid {status_color}55;border-left:4px solid {status_color};
     border-radius:12px;padding:14px 16px;margin:0 0 1rem;box-shadow:0 4px 12px rgba(0,0,0,0.16);">
  <div style="color:{status_color};font-family:'Outfit';font-size:0.72rem;font-weight:800;
       letter-spacing:0.1em;text-transform:uppercase;">{micon("sos", size=18, color=status_color, fill=True)} {tr("Global SOS")}</div>
  <div style="color:{c["TEXT"]};font-size:1.55rem;font-weight:900;font-family:'Outfit';margin:0.25rem 0;">
    {html.escape(sos_number)}
  </div>
  <div style="color:{c["MUTED"]};font-size:0.75rem;line-height:1.45;font-family:'Inter';">
    {html.escape(tr(country_name))} · {html.escape(tr(coverage))}<br>{html.escape(tr(note))}
  </div>
  <a href="tel:{html.escape(sos_number, quote=True)}" class="btn-call"
     style="display:block;text-align:center;margin-top:0.8rem;padding:9px 10px;border-radius:6px;text-decoration:none;">
    {micon("call", size=17)} {tr("Call SOS")} {html.escape(sos_number)}
  </a>
</div>
""",
        unsafe_allow_html=True,
    )


def service_card(
    name: str,
    category: str | None = None,
    distance_km: float | None = None,
    eta_min: int | None = None,
    phone: str | None = None,
    address: str | None = None,
    status: str = "OPEN 24x7",
    status_type: str = "24x7",
    lat: float | None = None,
    lon: float | None = None,
    maps_url: str | None = None,
    **_: object,
) -> None:
    del status_type
    c = get_colors()
    status_color = GREEN if "24" in status else AMBER
    safe_name = html.escape(name)
    category_line = f'<div class="sc-cat">{html.escape(tr(category))}</div>' if category else ""
    query = f"{lat},{lon}" if lat is not None and lon is not None else name
    directions_url = html.escape(maps_url or f"https://www.google.com/maps/search/{quote_plus(str(query))}", quote=True)
    phone_clean = "" if not phone or phone == "Not listed" else phone
    phone_href = f"tel:{phone_clean}" if phone_clean else "#"
    phone_label = html.escape(tr(phone if phone else "Not listed"))
    address_line = ""
    if address and address != "Not listed":
        address_line = f'<div class="sc-cat" style="margin:0.5rem 0 1.2rem; font-family:\'Inter\'; opacity:0.8; line-height:1.5;">{html.escape(tr(address))}</div>'
    distance_label = "--" if distance_km is None else f"{distance_km:.2f}"
    eta_label = "--" if eta_min is None else str(eta_min)
    st.html(
        f"""<div class="svc-card">
<div class="sc-header">
<div>
<div class="sc-name">{safe_name}</div>
{category_line}
</div>
<span class="sc-badge" style="background:{status_color}18; color:{status_color}; border:1px solid {status_color}33;">{html.escape(tr(status))}</span>
</div>
<div class="sc-meta">
<div style="display:flex; align-items:center; gap:6px;">{micon("location_on", size=18, color=GREEN)} <b>{distance_label}</b> km</div>
<div style="display:flex; align-items:center; gap:6px;">{micon("schedule", size=18, color=GREEN)} <b>{eta_label}</b> min</div>
<div style="display:flex; align-items:center; gap:6px;">{micon("call", size=18, color=GREEN)} {phone_label}</div>
</div>
{address_line}
<div class="sc-actions">
<a href="{phone_href}" class="btn-call">{micon("call", size=17)} {tr("Call Now")}</a>
<a href="{directions_url}" target="_blank" class="btn-dir">{micon("directions", size=17)} {tr("Directions")}</a>
</div>
</div>"""
    )


def placeholder_card(message: str) -> None:
    st.markdown(f'<div class="placeholder-card" style="padding:3rem !important; opacity:0.8; border-radius:12px;">{html.escape(tr(message))}</div>', unsafe_allow_html=True)


def blood_badge(bg: str) -> str:
    c = get_colors()
    bg_hex = RED + (c["SC_BADGE_BG"])
    border_hex = RED + (c["SC_BADGE_BORDER"])
    return (
        f'<span style="background:{bg_hex};color:{RED};border:1px solid {border_hex};'
        "font-family:'Outfit';font-size:0.85rem;font-weight:800;padding:6px 16px;border-radius:8px;"
        'text-transform:uppercase;letter-spacing:0.05em;">'
        f"{html.escape(bg)}</span>"
    )


def initials(name: str) -> str:
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "RS"
    return "".join(part[0].upper() for part in parts[:2])



def eta_from_distance(distance_km: float | None) -> int | None:
    if distance_km is None:
        return None
    return max(2, int(math.ceil(distance_km / 28 * 60)))


def location_pill(lat: float, lon: float, city: str, country_name: str, source: str) -> None:
    c = get_colors()
    st.sidebar.markdown(
        f"""
<div style="background:{c["CARD_BG"]}; border: 1px solid {c["BORDER"]}; border-radius: 12px;
     padding: 16px 20px; font-size: 0.85rem; margin-bottom: 1.5rem; position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    <div style="position:absolute; top:0; left:0; width:4px; height:100%; background:{GREEN}; z-index:10;"></div>
    <div style="display: flex; align-items: flex-start; gap: 10px;">
        {micon("location_on", size=22, color=GREEN, fill=True)}
        <div>
            <b style="color:{c["TEXT"]}; font-family:'Outfit'; text-transform:uppercase; letter-spacing:0.05em; font-size:1rem;">{html.escape(city or "Detected location")}</b><br>
            <span style="color:{c["MUTED"]}; font-weight:500;">{html.escape(country_name or "Unknown")}</span>
        </div>
    </div>
    <div style="color:{c["MUTED"]}; font-size:0.75rem; font-family:'Inter'; margin-top:12px; padding-top:12px; border-top:1px solid {c["DIVIDER"]}; opacity:0.8;">
        <b>{lat:.4f}, {lon:.4f}</b><br>via <span style="color:{GREEN}; font-weight:700;">{html.escape(source)}</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_theme_toggle() -> None:
    theme = get_theme()
    label = ":material/dark_mode: Dark Mode" if theme == "light" else ":material/light_mode: Light Mode"
    if st.sidebar.button(label, use_container_width=True):
        toggle_theme()
