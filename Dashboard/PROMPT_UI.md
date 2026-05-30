# RoadSoS — UI Build Prompt
## Streamlit Frontend with Custom Aesthetic

---

## Design Identity

**NOT** a copy of the sample. Build a distinct RoadSoS visual identity:

| Property | Value |
|---|---|
| Base theme | Dark — charcoal/deep navy backgrounds |
| Primary accent | `#E53935` (emergency red) |
| Secondary accent | `#FF8F00` (amber — warning state) |
| Success | `#00C853` (green — safe / open) |
| Background | `#0D1117` (page), `#161B22` (cards), `#21262D` (inputs) |
| Text primary | `#F0F6FC` |
| Text muted | `#8B949E` |
| Card style | Rounded corners (12px), subtle red-glow border on hover, no drop shadows — use borders instead |
| Font | System font stack — no Google Fonts imports needed |
| Icons | Unicode emoji only — no icon libraries |

**Feel:** A dark-mode ops dashboard. Think mission control, not consumer app. Clean, data-dense, authoritative. The red is reserved for emergencies — don't overuse it.

---

## Global CSS — Inject in Every Page

Every Streamlit page must start with:

```python
import streamlit as st

st.set_page_config(page_title="RoadSoS", page_icon="🪖", layout="wide")

st.markdown("""
<style>
/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0D1117;
    color: #F0F6FC;
}
[data-testid="stSidebar"] {
    background-color: #0D1117;
    border-right: 1px solid #30363D;
}
[data-testid="stSidebar"] * { color: #F0F6FC !important; }

/* ── Remove Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Buttons ── */
.stButton > button {
    background: #E53935;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
    transition: background 0.2s;
}
.stButton > button:hover { background: #B71C1C; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #21262D !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    color: #F0F6FC !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1rem;
}
[data-testid="metric-container"] label { color: #8B949E !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161B22;
    border-radius: 10px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #8B949E;
    border-radius: 8px;
    border: none;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #E53935 !important;
    color: #FFFFFF !important;
}

/* ── Divider ── */
hr { border-color: #30363D; }
</style>
""", unsafe_allow_html=True)
```

---

## Reusable HTML Components

Define these as Python functions returning `st.markdown(html, unsafe_allow_html=True)`.

### `service_card(name, category, distance_km, eta_min, phone, status="OPEN 24×7", status_type="24x7")`

```python
def service_card(name, category=None, distance_km=None, eta_min=None, phone=None,
                 status="OPEN 24×7", status_type="24x7"):
    status_color = "#00C853" if "24" in status else "#FF8F00"
    category_line = f'<div class="sc-cat">{category}</div>' if category else ""
    maps_url = f"https://www.google.com/maps/search/{name.replace(' ', '+')}"
    phone_href = f"tel:{phone}" if phone else "#"
    st.markdown(f"""
    <div class="svc-card">
        <div class="sc-header">
            <div>
                <div class="sc-name">{name}</div>
                {category_line}
            </div>
            <span class="sc-badge" style="background:{status_color}22;color:{status_color};
                  border:1px solid {status_color}44;">{status}</span>
        </div>
        <div class="sc-meta">
            <span>📍 {distance_km} km</span>
            <span>⏱ ETA {eta_min} min</span>
            <span>📞 {phone}</span>
        </div>
        <div class="sc-actions">
            <a href="{phone_href}" class="btn-call">📞 Call Now</a>
            <a href="{maps_url}" target="_blank" class="btn-dir">🗺 Directions</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

Card CSS (add to global block):
```css
.svc-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.svc-card:hover { border-color: #E53935; }
.sc-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem; }
.sc-name { font-size: 1rem; font-weight: 700; color: #F0F6FC; }
.sc-cat { font-size: 0.78rem; color: #8B949E; margin-top: 2px; }
.sc-badge { font-size: 0.7rem; font-weight: 600; padding: 3px 8px; border-radius: 20px; white-space: nowrap; }
.sc-meta { display: flex; gap: 1.2rem; font-size: 0.82rem; color: #8B949E; margin-bottom: 0.8rem; flex-wrap: wrap; }
.sc-actions { display: flex; gap: 0.6rem; }
.btn-call {
    background: #E53935; color: #fff; padding: 7px 16px; border-radius: 8px;
    text-decoration: none; font-size: 0.85rem; font-weight: 600;
}
.btn-call:hover { background: #B71C1C; }
.btn-dir {
    background: transparent; color: #F0F6FC; padding: 7px 16px;
    border: 1px solid #30363D; border-radius: 8px;
    text-decoration: none; font-size: 0.85rem; font-weight: 600;
}
.btn-dir:hover { border-color: #8B949E; }
```

### `emergency_number_strip(country_name, numbers_dict)`

```python
def emergency_number_strip(country_name, numbers):
    items = "".join([
        f'<div class="en-item"><div class="en-num">{v}</div><div class="en-label">{k.title()}</div></div>'
        for k, v in numbers.items()
    ])
    st.markdown(f"""
    <div class="en-strip">
        <div class="en-title">⚡ Quick Emergency Numbers — {country_name}</div>
        <div class="en-row">{items}</div>
    </div>
    """, unsafe_allow_html=True)
```

CSS:
```css
.en-strip {
    background: #1A0A0A;
    border: 1px solid #E5393544;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 1.5rem 0;
}
.en-title { color: #E53935; font-weight: 700; margin-bottom: 1rem; font-size: 0.95rem; }
.en-row { display: flex; gap: 1.5rem; flex-wrap: wrap; }
.en-item { text-align: center; }
.en-num { font-size: 2rem; font-weight: 800; color: #E53935; line-height: 1; }
.en-label { font-size: 0.75rem; color: #8B949E; margin-top: 4px; }
```

### `page_header(title, subtitle, badge_text=None, badge_color="#00C853")`

```python
def page_header(title, subtitle, badge_text=None, badge_color="#00C853"):
    badge_html = ""
    if badge_text:
        badge_html = f'<span style="background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}55;font-size:0.72rem;font-weight:700;padding:3px 10px;border-radius:20px;margin-left:12px;vertical-align:middle;">{badge_text}</span>'
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
        <h1 style="color:#F0F6FC;margin:0;font-size:1.8rem;">
            {title}{badge_html}
        </h1>
        <p style="color:#8B949E;margin:4px 0 0 0;font-size:0.9rem;">{subtitle}</p>
    </div>
    <hr style="border-color:#30363D;margin-bottom:1.5rem;">
    """, unsafe_allow_html=True)
```

### `alert_banner(level, message)`

```python
def alert_banner(level, message):
    # level: "crash" | "warning" | "safe"
    config = {
        "crash":   ("#E53935", "#1A0505", "🔴", "CRASH DETECTED — SOS FIRED"),
        "warning": ("#FF8F00", "#1A1200", "🟡", "SKID WARNING — HAPTIC ALERT"),
        "safe":    ("#00C853", "#051A0D", "🟢", "SAFE — NORMAL RIDING"),
    }
    color, bg, icon, label = config[level]
    st.markdown(f"""
    <div style="background:{bg};border:1px solid {color}44;border-left:4px solid {color};
         border-radius:10px;padding:1rem 1.4rem;margin-bottom:1.5rem;
         display:flex;align-items:center;gap:0.8rem;">
        <span style="font-size:1.4rem;">{icon}</span>
        <div>
            <div style="color:{color};font-weight:800;font-size:1rem;">{label}</div>
            <div style="color:#8B949E;font-size:0.85rem;margin-top:2px;">{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

### `stat_card(label, value, unit="", color="#F0F6FC")`

```python
def stat_card(label, value, unit, color="#F0F6FC"):
    st.markdown(f"""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
         padding:1rem 1.2rem;text-align:center;">
        <div style="font-size:0.75rem;color:#8B949E;text-transform:uppercase;
             letter-spacing:0.05em;margin-bottom:6px;">{label}</div>
        <div style="font-size:2rem;font-weight:800;color:{color};line-height:1;">
            {value}<span style="font-size:1rem;font-weight:400;color:#8B949E;"> {unit}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
```

---

## Page: Nearby Services (`pages/2_Nearby_Services.py`)

**Layout:**

```
[page_header] "📍 Nearby Services" | LIVE badge

[Sidebar]
  Country selector (flag + name)
  Radius slider (1–20 km)
  Lat / Lon inputs
  [Fetch Services button]
  ──────────────────────
  Cache status line

[Main area top]
  [emergency_number_strip]

[Contact count row — 4 stat_cards in columns]
  Hospitals | Police | Ambulance | Vehicle

[Tabs: 🏥 Hospitals & Trauma | 🚔 Police | 🚑 Ambulance | 🚗 Vehicle Rescue]
  Each tab: 3-column grid of service_cards
  If no data: dark placeholder card "No services found in this radius"
```

**Search bar** — filter cards by name within active tab:
```python
search = st.text_input("", placeholder="🔍  Search services by name...",
                        key="svc_search")
# Filter displayed cards by search.lower() in name.lower()
```

**3-column grid** using `st.columns(3)` — distribute cards round-robin across columns.

**Sidebar country selector:**
```python
countries = {"🇮🇳 India": "IN", "🇺🇸 USA": "US", "🇬🇧 UK": "GB",
             "🇦🇪 UAE": "AE", "🇦🇺 Australia": "AU", "🇩🇪 Germany": "DE",
             "🇸🇬 Singapore": "SG", "🇯🇵 Japan": "JP", "🇫🇷 France": "FR"}
selected = st.sidebar.selectbox("Country", list(countries.keys()), index=0)
country_code = countries[selected]
```

**Cache status line** in sidebar:
```python
if is_cache_fresh(cache_key):
    age = cache_age_hours(cache_key)
    st.sidebar.markdown(f"✅ **Cached** ({age:.1f} hrs ago)")
else:
    st.sidebar.markdown("🌐 **Live fetch**")
```

---

## Page: PINN Dashboard (`pages/1_PINN_Dashboard.py`)

**Layout:**

```
[page_header] "🪖 Helmet Intelligence" | TraumaSense AI v1.0 badge

[Sidebar]
  Scenario: Normal Riding / Oil Patch / Crash
  Duration: slider
  ──────────────────────
  Rider Profile (expander)
    Name, Blood Group, Allergies, Emergency Contact
  ──────────────────────
  [Run Simulation button]

[alert_banner]  ← top of main area, full width

[4 stat_cards in columns]
  Peak Accel | P(skid) max | HIC15 | Injury

[2 matplotlib plots side by side]
  Left: Resultant acceleration over time
        plt.style.use("dark_background"), fig bg #0D1117
        Red line at 6g, label "Impact threshold"
  Right: PINN P(skid) over time
        Orange line at 0.65, label "Warning threshold"

[Expander: "⚙ Train / Retrain PINN"]
  Shows epoch progress bar + loss plot when training
```

**Plot style template:**
```python
plt.style.use("dark_background")
fig, ax = plt.subplots(figsize=(7, 3))
fig.patch.set_facecolor("#0D1117")
ax.set_facecolor("#161B22")
ax.tick_params(colors="#8B949E")
ax.xaxis.label.set_color("#8B949E")
ax.yaxis.label.set_color("#8B949E")
for spine in ax.spines.values():
    spine.set_edgecolor("#30363D")
ax.grid(color="#30363D", linewidth=0.5)
# Plot data
ax.plot(t, values, color="#E53935", linewidth=1.5)
ax.axhline(threshold, color="#FF8F00", linewidth=1, linestyle="--", label="Threshold")
ax.legend(facecolor="#161B22", edgecolor="#30363D", labelcolor="#F0F6FC")
st.pyplot(fig, use_container_width=True)
plt.close(fig)
```

---

## Page: Emergency Profile (`pages/3_Emergency_Profile.py`)

**Layout:**

```
[page_header] "🪪 Rider Profile & First Aid"

[Two columns 1:1]

Left col — Form:
  Name (text input)
  Blood Group (selectbox — all 8 types)
  Allergies (text input)
  Medical Conditions (text area)
  Emergency Contact (text input, +91...)
  [Save Profile button]

Right col — Live preview card:
  Dark card with rider initials avatar (large circle, red bg)
  Name, blood group badge, allergies chip
  Emergency contact with 📞 icon

[SOS Packet Preview — code block]
  st.code(json.dumps(sos_packet, indent=2), language="json")

[First Aid Instructions — dark card]
  Rendered markdown with WHO motorcycle crash protocol

[QR Code — centered]
  Generated from: https://roadsos.app/rider/{rider_id}
  White QR on dark background (#161B22)
  Caption: "Scan for emergency medical info"
```

**Blood group badge** (in profile card):
```python
def blood_badge(bg):
    st.markdown(f"""
    <span style="background:#E5393522;color:#E53935;border:1px solid #E5393544;
         font-size:0.9rem;font-weight:800;padding:4px 12px;border-radius:20px;">
        {bg}
    </span>
    """, unsafe_allow_html=True)
```

---

## Page: RoadSoS AI (`pages/4_AI_Assistant.py`)

Chat interface. Powered by the Anthropic API (use `anthropic` package, key from `st.secrets["ANTHROPIC_API_KEY"]`).

**System prompt for the AI:**
```
You are RoadSoS AI — a road safety expert, first-aid guide, and legal advisor for road accident situations in India.
You help accident victims, bystanders, and emergency responders. You know:
- WHO and Indian Red Cross first-aid protocols for road crashes
- Indian traffic laws and rights of accident victims (Motor Vehicles Act)
- How to guide bystanders step by step in an emergency
- When to call 108 (ambulance), 100 (police), 112 (unified)
Keep answers concise, actionable, and calm. Use numbered steps for procedures.
```

**Layout:**
```
[page_header] "🤖 RoadSoS AI" | "Powered by Claude" badge (amber)

[Subtitle] "Road safety expert · First-aid guide · Legal advisor"

[Chat message history — scrollable]
  User messages: right-aligned, red bubble (#E53935 bg)
  AI messages: left-aligned, dark card (#161B22), subtle left border #E53935

[Suggested prompts — shown only when no messages yet]
  Row of clickable pills:
    "What do I do if I witness an accident?"
    "Signs of internal bleeding?"
    "Can police refuse to help?"
    "How to stabilize a crash victim?"

[Input row at bottom]
  st.chat_input("Ask about first aid, legal rights, emergency procedures...")
```

**Message rendering:**
```python
# User bubble
st.markdown(f"""
<div style="display:flex;justify-content:flex-end;margin:8px 0;">
  <div style="background:#E53935;color:#fff;padding:10px 16px;border-radius:16px 16px 4px 16px;
       max-width:70%;font-size:0.9rem;">{message}</div>
</div>
""", unsafe_allow_html=True)

# AI bubble
st.markdown(f"""
<div style="display:flex;gap:10px;margin:8px 0;align-items:flex-start;">
  <div style="background:#E53935;border-radius:50%;width:32px;height:32px;display:flex;
       align-items:center;justify-content:center;flex-shrink:0;font-size:0.9rem;">🤖</div>
  <div style="background:#161B22;border:1px solid #30363D;border-left:3px solid #E53935;
       padding:10px 16px;border-radius:4px 16px 16px 16px;max-width:75%;font-size:0.9rem;
       color:#F0F6FC;">{message}</div>
</div>
""", unsafe_allow_html=True)
```

**Streaming response:**
```python
with anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"]).messages.stream(
    model="claude-haiku-4-5-20251001",
    max_tokens=512,
    system=SYSTEM_PROMPT,
    messages=st.session_state.messages,
) as stream:
    response = st.write_stream(stream.text_stream)
```

---

## Sidebar Navigation (app.py)

```python
st.sidebar.markdown("""
<div style="text-align:center;padding:1rem 0 0.5rem;">
    <div style="font-size:2rem;">🪖</div>
    <div style="font-weight:800;font-size:1.1rem;color:#F0F6FC;">RoadSoS</div>
    <div style="font-size:0.7rem;color:#8B949E;letter-spacing:0.1em;">
        DETECTION BEFORE DIAGNOSIS
    </div>
</div>
<hr style="border-color:#30363D;margin:0.8rem 0;">
""", unsafe_allow_html=True)
```

---

## requirements.txt

```
streamlit>=1.35.0
torch>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
pandas>=2.0.0
requests>=2.31.0
qrcode[pil]>=7.4.0
Pillow>=10.0.0
anthropic>=0.25.0
```

---

## Run

```bash
streamlit run roadsos_app/app.py
```

For AI page, add to `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## What NOT to do

- No white backgrounds anywhere
- No Streamlit default blue buttons — override all with red via CSS
- No light-mode matplotlib plots — always `dark_background` style
- No Google Fonts imports
- No external icon libraries
- No Lorem Ipsum placeholder text — use real RoadSoS content
- Do not use `st.success()` / `st.warning()` / `st.error()` — use the custom `alert_banner()` instead
- Do not use `st.table()` — use card grids
