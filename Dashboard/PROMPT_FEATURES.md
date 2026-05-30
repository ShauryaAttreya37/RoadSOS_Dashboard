# RoadSoS — Features Prompt
## Auto-Location · PINN-Driven First Aid · Service Navigation

Feed this into Codex alongside PROMPT.md and PROMPT_UI.md.

---

## 1. Auto Location Detection

The app must detect the user's location automatically on load — no manual lat/lon entry required. Use a two-tier approach:

### Tier 1 — Browser Geolocation (most accurate)

Use the `streamlit-js-eval` package to call the browser's native geolocation API:

```python
# requirements.txt: add streamlit-js-eval>=0.1.7
from streamlit_js_eval import get_geolocation

def get_browser_location():
    loc = get_geolocation()
    if loc and "coords" in loc:
        return loc["coords"]["latitude"], loc["coords"]["longitude"]
    return None, None
```

Call this once on page load and store result in `st.session_state.lat`, `st.session_state.lon`.

### Tier 2 — IP Geolocation Fallback

If browser geolocation is denied or unavailable, fall back to IP-based location using the free `ipapi.co` API:

```python
import requests

def get_ip_location():
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        data = r.json()
        return (
            float(data["latitude"]),
            float(data["longitude"]),
            data.get("country_code", "IN"),
            data.get("city", ""),
            data.get("country_name", "India"),
        )
    except Exception:
        # Hard fallback: Bangalore, India (demo location from blueprint)
        return 12.9716, 77.5946, "IN", "Bengaluru", "India"
```

### Location State Management

```python
# In app.py or each page, at top:
if "lat" not in st.session_state:
    lat, lon, country_code, city, country_name = get_ip_location()
    st.session_state.lat = lat
    st.session_state.lon = lon
    st.session_state.country_code = country_code
    st.session_state.city = city
    st.session_state.country_name = country_name
    st.session_state.location_source = "IP"

# Show location pill in sidebar
st.sidebar.markdown(f"""
<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;
     padding:8px 12px;font-size:0.8rem;margin-bottom:1rem;">
    📍 <b style="color:#F0F6FC;">{st.session_state.city}</b>
    <span style="color:#8B949E;"> · {st.session_state.country_name}</span><br>
    <span style="color:#8B949E;font-size:0.72rem;">
        {st.session_state.lat:.4f}, {st.session_state.lon:.4f}
        · via {st.session_state.location_source}
    </span>
</div>
""", unsafe_allow_html=True)

# Manual override (collapsed by default)
with st.sidebar.expander("🔧 Override Location"):
    st.session_state.lat = st.number_input("Latitude", value=st.session_state.lat, format="%.4f")
    st.session_state.lon = st.number_input("Longitude", value=st.session_state.lon, format="%.4f")
```

---

## 2. Nearby Services — Section Navigation

### Page Structure: `pages/2_Nearby_Services.py`

The page has two parts: a **persistent top strip** (location + emergency numbers + search) and a **sectioned body** with one section per service category. Navigation is via Streamlit tabs at the top of the body — each tab is a full dedicated section, not a filtered list.

### Auto-fetch on load

```python
# Fetch immediately using auto-detected location — no button press needed
lat = st.session_state.lat
lon = st.session_state.lon
radius = st.sidebar.slider("Search radius", 1, 20, 5, format="%d km") * 1000

@st.cache_data(ttl=86400, show_spinner=False)
def cached_services(lat, lon, radius):
    return fetch_nearby_services(lat, lon, radius)

with st.spinner("📡 Finding nearby services..."):
    services = cached_services(round(lat, 3), round(lon, 3), radius)
```

### Section definitions

Build exactly these 5 tabs. Each tab title includes a live count badge:

```python
counts = {cat: len(services.get(cat, [])) for cat in
          ["hospital", "police", "ambulance", "vehicle_rescue", "puncture_shop"]}

tab_labels = [
    f"🏥 Hospitals & Trauma ({counts['hospital']})",
    f"🚔 Police ({counts['police']})",
    f"🚑 Ambulance ({counts['ambulance']})",
    f"🚗 Vehicle Rescue ({counts['vehicle_rescue']})",
    f"🔧 Puncture & Repair ({counts['puncture_shop']})",
]

tabs = st.tabs(tab_labels)
```

### Per-section content

Each tab renders:
1. A **section header** with icon, title, and a one-line description of what this section covers
2. A **search filter** (text input, filters cards in this tab only)
3. A **3-column card grid** using `service_card()` from PROMPT_UI.md
4. An **empty state** if no results

Section header definitions:
```python
SECTION_META = {
    "hospital": {
        "icon": "🏥", "title": "Hospitals & Trauma Centres",
        "desc": "Emergency departments, ICUs, and trauma centres sorted by distance.",
        "empty": "No hospitals found within this radius. Try increasing the search range."
    },
    "police": {
        "icon": "🚔", "title": "Police Stations",
        "desc": "Nearest police stations for accident reporting and legal assistance.",
        "empty": "No police stations found. Call 100 (India) directly."
    },
    "ambulance": {
        "icon": "🚑", "title": "Ambulance Services",
        "desc": "Government and private ambulance dispatch points.",
        "empty": "No ambulance stations found. Call 108 (India) directly."
    },
    "vehicle_rescue": {
        "icon": "🚗", "title": "Vehicle Rescue & Towing",
        "desc": "Towing services and roadside assistance for crash vehicle recovery.",
        "empty": "No towing services found nearby."
    },
    "puncture_shop": {
        "icon": "🔧", "title": "Puncture Shops & Showrooms",
        "desc": "Tyre repair shops and authorised service centres.",
        "empty": "No repair shops found nearby."
    },
}
```

Section render function:
```python
def render_section(tab, category, services_dict):
    items = services_dict.get(category, [])
    meta = SECTION_META[category]
    with tab:
        st.markdown(f"""
        <div style="margin-bottom:1rem;">
            <span style="font-size:1.3rem;">{meta['icon']}</span>
            <span style="font-size:1.1rem;font-weight:700;color:#F0F6FC;
                  margin-left:8px;">{meta['title']}</span>
            <div style="color:#8B949E;font-size:0.85rem;margin-top:4px;">
                {meta['desc']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        search = st.text_input("", placeholder=f"🔍  Filter {meta['title'].lower()}...",
                                key=f"search_{category}")
        if search:
            items = [i for i in items if search.lower() in i["name"].lower()]

        if not items:
            st.markdown(f"""
            <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;
                 padding:2rem;text-align:center;color:#8B949E;">
                {meta['empty']}
            </div>
            """, unsafe_allow_html=True)
            return

        cols = st.columns(3)
        for i, svc in enumerate(items):
            with cols[i % 3]:
                service_card(**svc)
```

### Top strip (above tabs, always visible)

```python
# Emergency numbers strip — auto-populated from detected country
numbers = get_emergency_numbers(st.session_state.country_code)
emergency_number_strip(st.session_state.country_name, numbers)

# Summary metric row
c1, c2, c3, c4, c5 = st.columns(5)
total = count_total_contacts(services)
with c1: stat_card("Total Services", total, "found", "#F0F6FC")
with c2: stat_card("Hospitals", counts["hospital"], "nearby", "#E53935")
with c3: stat_card("Police", counts["police"], "nearby", "#4FC3F7")
with c4: stat_card("Ambulance", counts["ambulance"], "nearby", "#FF8F00")
with c5: stat_card("Repair", counts["puncture_shop"] + counts["vehicle_rescue"], "nearby", "#00C853")
```

### Overpass query — add vehicle rescue and puncture

Extend the Overpass query in `modules/nearby_services.py`:

```python
OVERPASS_TAGS = {
    "hospital":       [('amenity', 'hospital'), ('amenity', 'clinic'),
                       ('amenity', 'doctors'), ('healthcare', 'hospital')],
    "police":         [('amenity', 'police')],
    "ambulance":      [('emergency', 'ambulance_station'),
                       ('amenity', 'ambulance_station')],
    "vehicle_rescue": [('amenity', 'vehicle_inspection'),
                       ('emergency', 'rescue')],
    "puncture_shop":  [('shop', 'tyres'), ('shop', 'car_repair'),
                       ('shop', 'motorcycle_repair'), ('shop', 'car')],
}
```

ETA calculation (add to `haversine` module):
```python
# Rough ETA based on average urban speed of 30 km/h
def eta_minutes(distance_km: float) -> int:
    return max(1, round(distance_km / 30 * 60))
```

---

## 3. PINN-Driven AI First Aid

### Concept

When the PINN runs inference on a crash scenario, it produces:
- `hic15` — head impact severity score
- `bric` — brain rotational injury score
- `injury_label` — LOW / MODERATE / SEVERE
- `P_skid` max — whether a skid preceded the crash
- `scenario` — normal / oil_patch / crash
- `peak_accel_g` — peak resultant acceleration

These outputs are passed to Claude (Haiku) to generate **specific, contextual first-aid instructions** for that exact crash severity — not generic tips.

### Module: `modules/ai_firstaid.py`

```python
import anthropic
import streamlit as st

def generate_firstaid(
    hic15: float,
    bric: float,
    injury_label: str,       # "LOW" | "MODERATE" | "SEVERE"
    peak_accel_g: float,
    skid_preceded: bool,
    scenario: str,           # "normal" | "oil_patch" | "crash"
    blood_group: str = "Unknown",
    allergies: str = "None",
) -> str:
    """
    Generate contextual first-aid instructions from PINN outputs using Claude Haiku.
    Returns a markdown string.
    """
    prompt = f"""
You are a trauma first-aid advisor. A motorcycle crash has been detected by the RoadSoS helmet system.
The on-board PINN model has produced these biomechanical measurements:

- Head Injury Criterion (HIC15): {hic15:.0f} (threshold: 700 moderate, 1000 severe)
- Brain Rotational Injury (BrIC): {bric:.3f} (threshold: 1.0 severe)
- Computed injury severity: {injury_label}
- Peak impact acceleration: {peak_accel_g:.1f} g
- Skid preceded crash: {"Yes" if skid_preceded else "No"}
- Rider blood group: {blood_group}
- Known allergies: {allergies}

Based on ONLY these measurements, give a bystander exactly 5 numbered steps they must take RIGHT NOW.
Be direct. Use simple words. Each step must be one sentence. Prioritise by urgency.
Do NOT give generic advice — tailor every step to the severity level above.
End with one line: what to tell the ambulance when they call 108.
Format as markdown with bold step numbers.
"""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

### Integration into PINN Dashboard (`pages/1_PINN_Dashboard.py`)

After inference runs, add a **"First Aid" section** below the plots:

```python
# After run_inference() returns results
if scenario == "crash" or peak_accel_g > 6:
    st.markdown("---")
    st.markdown("""
    <div style="font-size:1rem;font-weight:700;color:#E53935;margin-bottom:0.5rem;">
        🩺 AI-Generated First Aid — Based on This Crash Profile
    </div>
    <div style="color:#8B949E;font-size:0.82rem;margin-bottom:1rem;">
        Generated by Claude using PINN biomechanical outputs (HIC15={:.0f}, BrIC={:.3f}, Severity={})
    </div>
    """.format(hic15, bric, injury_label), unsafe_allow_html=True)

    # Cache by injury params so it doesn't regenerate on every rerun
    cache_key = f"{injury_label}_{int(hic15)}_{int(bric*100)}"
    if cache_key not in st.session_state:
        with st.spinner("🤖 Generating first-aid instructions..."):
            st.session_state[cache_key] = generate_firstaid(
                hic15=hic15,
                bric=bric,
                injury_label=injury_label,
                peak_accel_g=peak_accel_g,
                skid_preceded=bool(P_skid_max > 0.65),
                scenario=scenario,
                blood_group=st.session_state.get("blood_group", "Unknown"),
                allergies=st.session_state.get("allergies", "None"),
            )

    firstaid_text = st.session_state[cache_key]

    st.markdown(f"""
    <div style="background:#0D1A0A;border:1px solid #00C85344;border-left:4px solid #00C853;
         border-radius:10px;padding:1.2rem 1.5rem;">
        {firstaid_text}
    </div>
    """, unsafe_allow_html=True)

    # Quick action buttons
    col1, col2 = st.columns(2)
    with col1:
        ambulance = get_emergency_numbers(st.session_state.country_code)["ambulance"]
        st.markdown(f'<a href="tel:{ambulance}" class="btn-call" style="display:block;text-align:center;padding:12px;">📞 Call Ambulance ({ambulance})</a>',
                    unsafe_allow_html=True)
    with col2:
        maps_url = f"https://www.google.com/maps/search/hospital+near+me/@{st.session_state.lat},{st.session_state.lon},14z"
        st.markdown(f'<a href="{maps_url}" target="_blank" class="btn-dir" style="display:block;text-align:center;padding:12px;">🏥 Find Nearest Hospital</a>',
                    unsafe_allow_html=True)
```

### Severity-colour mapping for the first-aid card border

| injury_label | Border color | Background |
|---|---|---|
| SEVERE | `#E53935` | `#1A0505` |
| MODERATE | `#FF8F00` | `#1A1200` |
| LOW | `#00C853` | `#051A0D` |

```python
SEVERITY_COLORS = {
    "SEVERE":   ("#E53935", "#1A0505"),
    "MODERATE": ("#FF8F00", "#1A1200"),
    "LOW":      ("#00C853", "#051A0D"),
}
color, bg = SEVERITY_COLORS.get(injury_label, ("#8B949E", "#161B22"))
```

---

## 4. requirements.txt (final)

```
streamlit>=1.35.0
streamlit-js-eval>=0.1.7
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

## 5. Build Order

1. `modules/nearby_services.py` — add vehicle_rescue + puncture tags, add `eta_minutes()`
2. `modules/ai_firstaid.py` — new file
3. Auto-location in `app.py` — `get_ip_location()` + session state
4. `pages/2_Nearby_Services.py` — auto-fetch, 5 tabs, section render
5. `pages/1_PINN_Dashboard.py` — add PINN-driven first-aid section after plots
6. `.streamlit/secrets.toml` — ANTHROPIC_API_KEY
