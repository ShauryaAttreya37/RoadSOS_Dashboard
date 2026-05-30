# RoadSoS — Master Build Prompt
## For Claude Code / OpenAI Codex / Any AI Coding Agent

---

## Project Context

**RoadSoS** is a smart helmet + emergency services platform built for the IIT Madras Road Safety Hackathon 2026 (Problem Statement 3). The system has two layers:

1. **Helmet intelligence layer** — A Physics-Informed Neural Network (PINN) that predicts skid probability and crash severity from IMU data, and a TinyML crash classifier that confirms impacts. Both run on an ESP32-S3. A Python simulation + Streamlit dashboard demonstrates this.

2. **Location-based emergency services layer** — Fetches nearest hospitals, ambulance services, police stations, towing services, and puncture shops using the user's GPS coordinates. Caches everything offline. Works globally. This layer is MISSING and must be built.

**The entire deliverable is a Streamlit multi-page app.** All logic lives in `.py` files. No Jupyter notebooks for production code. The existing notebook (`HelmetSOS.ipynb`) is only a reference — port its content into clean `.py` modules.

All plots must use **dark mode** (matplotlib dark background style).

---

## Repository Layout to Create

Build the following folder structure inside the project root (`C:\Users\shaur\OneDrive\Documents\Projects\IITM HACKATHON\`):

```
roadsos_app/
├── app.py                          # Streamlit entry point — run this
├── pages/
│   ├── 1_PINN_Dashboard.py         # Helmet AI dashboard (port from notebook)
│   ├── 2_Nearby_Services.py        # Location-based services finder
│   └── 3_Emergency_Profile.py      # Rider medical profile + QR page
├── modules/
│   ├── __init__.py
│   ├── simulation.py               # IMU data simulation (normal / oil / crash)
│   ├── pinn_model.py               # RoadSoSPINN model class + IMUNormaliser
│   ├── injury_metrics.py           # HIC15, BrIC, injury_label functions
│   ├── losses.py                   # pinn_loss, residual_vehicle, residual_biomechanics
│   ├── train.py                    # train() function, saves roadsos_pinn.pt
│   ├── inference.py                # run_inference(), load_model()
│   ├── nearby_services.py          # OSM Overpass API fetcher
│   ├── offline_cache.py            # JSON cache read/write with timestamp
│   └── emergency_numbers.py        # Country → emergency number lookup table
├── data/
│   └── cache/                      # Auto-created; stores offline JSON caches
├── artifacts/
│   └── roadsos_pinn.pt             # Trained model checkpoint (generated on first run)
├── requirements.txt
└── README.md
```

---

## Module Specs

### `modules/simulation.py`

Port the three simulation functions from `HelmetSOS.ipynb` exactly:

- `simulate_normal(duration, fs, seed)` → returns dict with keys `t, ax, ay, az, gx, gy, gz, v, theta, mu, P_skid, scenario`
- `simulate_oil_patch(duration, fs, seed, patch_start)` → same keys, scenario=1
- `simulate_crash(duration, fs, seed, crash_time)` → same keys, scenario=2
- `build_dataset(n_seeds_each)` → returns `X_raw (N,7), Y_raw (N,3), meta (N,2)` arrays

Use **only** `numpy` and `scipy`. No torch here.

---

### `modules/pinn_model.py`

Port from notebook:

```python
class RoadSoSPINN(nn.Module):
    # 7 inputs: [t, ax, ay, az, gx, gy, gz]
    # 6 outputs: [v, theta, mu_eff, x_brain, y_brain, z_brain]
    # default: hidden_layers=6, hidden_width=128, activation=tanh
    # xavier init, sigmoid on mu_eff output
    def forward(self, x): ...
    def out(self, x): ...   # returns dict of named outputs

class IMUNormaliser:
    def fit_transform(self, X): ...
    def transform(self, X): ...
    def inverse_transform(self, X): ...
```

---

### `modules/injury_metrics.py`

Port from notebook:

```python
CONSTANTS = {
    "HIC_LOW": 700, "HIC_HIGH": 1000,
    "BRIC_X": 66.3, "BRIC_Y": 56.5, "BRIC_Z": 42.2,
    "MU_DRY": 0.75, "MU_WET": 0.45, "MU_OIL": 0.15,
    "M_TOTAL": 225.0, "G": 9.81, "WHEELBASE": 1.35,
    "M_BRAIN": 1.4, "K_BRAIN": 2.1e4, "C_BRAIN": 85.0,
}

def compute_hic15(ax, ay, az, fs, window_ms=15) -> float: ...
def compute_bric(gx, gy, gz) -> float: ...
def injury_label(hic, bric) -> str:  # "LOW" | "MODERATE" | "SEVERE"
    ...
def skid_probability(mu_eff_array) -> np.ndarray:
    # P_sk = clip((MU_WET - mu_eff) / MU_WET, 0, 1)
    ...
```

---

### `modules/losses.py`

Port physics residuals and PINN loss from notebook:

```python
def residual_vehicle(outs, x) -> tuple[Tensor, Tensor]:
    # R_v = M_TOTAL * dv_dt + mu_eff * M_TOTAL * G
    # R_theta = dtheta_dt - v * sin(theta) / WHEELBASE
    ...

def residual_biomechanics(outs, x) -> Tensor:
    # Kelvin-Voigt for x_brain, y_brain, z_brain
    ...

def pinn_loss(model, x_batch, y_batch, lam={"data":1.0, "vehicle":0.1, "bio":0.05}):
    # returns total_loss, data_loss, vehicle_loss, bio_loss
    ...
```

---

### `modules/train.py`

```python
def train(model, X_raw, Y_raw, epochs=3000, lr=1e-3, batch=512,
          lam=None, save_path="artifacts/roadsos_pinn.pt") -> dict:
    # Adam + CosineAnnealingLR + grad clip 1.0
    # saves checkpoint: {model_state, norm_mean, norm_std, Y_mean, Y_std}
    # returns history dict: {total, data, vehicle, bio} loss lists
    ...
```

---

### `modules/inference.py`

```python
@st.cache_resource
def load_model(path="artifacts/roadsos_pinn.pt"):
    # loads checkpoint, reconstructs model + normaliser
    ...

def run_inference(sim_fn, sim_kwargs, fs=50):
    # runs simulation → normalise → forward pass → extract outputs
    # returns: t, ax, ay, az, gx, gy, gz, mu_pred, P_skid, hic15, bric, label
    ...
```

---

### `modules/nearby_services.py`

This is the **most important missing module**. Fetch nearby emergency services using the OpenStreetMap Overpass API (free, no API key needed).

```python
import requests, json, math
from modules.offline_cache import load_cache, save_cache

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

SERVICE_QUERIES = {
    "hospital":       'node["amenity"="hospital"]',
    "clinic":         'node["amenity"="clinic"]',
    "police":         'node["amenity"="police"]',
    "fire_station":   'node["amenity"="fire_station"]',
    "ambulance":      'node["emergency"="ambulance_station"]',
    "towing":         'node["amenity"="vehicle_inspection"]',  # fallback
    "puncture_shop":  'node["shop"="tyres"]',
    "car_showroom":   'node["shop"="car"]',
}

def fetch_nearby_services(lat: float, lon: float, radius_m: int = 5000) -> dict:
    """
    Fetch all service categories within radius_m metres of (lat, lon).
    Returns dict: { category: [ {name, lat, lon, distance_km, phone, address}, ... ] }
    Results are sorted by distance ascending.
    Tries cache first; falls back to live Overpass query; saves result to cache.
    Cache key: f"{lat:.3f}_{lon:.3f}_{radius_m}"
    Cache TTL: 24 hours
    """
    ...

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Returns distance in km."""
    ...

def build_overpass_query(lat, lon, radius_m) -> str:
    """Builds a single combined Overpass QL query for all service types."""
    ...

def count_total_contacts(services: dict) -> int:
    """Returns total number of unique service contacts found."""
    return sum(len(v) for v in services.values())
```

**Overpass query pattern** (use `[out:json][timeout:25]`):
```
[out:json][timeout:25];
(
  node["amenity"="hospital"](around:5000,LAT,LON);
  node["amenity"="police"](around:5000,LAT,LON);
  node["emergency"="ambulance_station"](around:5000,LAT,LON);
  node["shop"="tyres"](around:5000,LAT,LON);
  node["amenity"="fire_station"](around:5000,LAT,LON);
  node["shop"="car"](around:5000,LAT,LON);
);
out body;
```

Parse `element["tags"]` for `name`, `phone`/`contact:phone`, `addr:full`/`addr:street`.

---

### `modules/offline_cache.py`

```python
import json, os, time
from pathlib import Path

CACHE_DIR = Path("data/cache")
CACHE_TTL_SECONDS = 86400  # 24 hours

def cache_path(key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{key}.json"

def load_cache(key: str) -> dict | None:
    """Returns cached data if exists and not expired, else None."""
    ...

def save_cache(key: str, data: dict) -> None:
    """Saves data with timestamp."""
    ...

def is_cache_fresh(key: str) -> bool: ...

def cache_age_hours(key: str) -> float: ...
```

---

### `modules/emergency_numbers.py`

```python
# International emergency contact numbers by country ISO code
EMERGENCY_NUMBERS = {
    "IN": {"ambulance": "108", "police": "100", "fire": "101", "unified": "112"},
    "US": {"ambulance": "911", "police": "911", "fire": "911", "unified": "911"},
    "GB": {"ambulance": "999", "police": "999", "fire": "999", "unified": "112"},
    "AU": {"ambulance": "000", "police": "000", "fire": "000", "unified": "112"},
    "DE": {"ambulance": "112", "police": "110", "fire": "112", "unified": "112"},
    "FR": {"ambulance": "15",  "police": "17",  "fire": "18",  "unified": "112"},
    "JP": {"ambulance": "119", "police": "110", "fire": "119", "unified": "112"},
    "CN": {"ambulance": "120", "police": "110", "fire": "119", "unified": "120"},
    "BR": {"ambulance": "192", "police": "190", "fire": "193", "unified": "192"},
    "ZA": {"ambulance": "10177","police": "10111","fire": "10177","unified": "112"},
    # ... add more countries
}

def get_emergency_numbers(country_code: str) -> dict:
    """Returns emergency numbers for the given ISO country code. Defaults to 112."""
    return EMERGENCY_NUMBERS.get(country_code.upper(),
           {"ambulance": "112", "police": "112", "fire": "112", "unified": "112"})

def all_countries() -> list[str]:
    return sorted(EMERGENCY_NUMBERS.keys())
```

---

## Streamlit Pages

### `app.py` — Entry Point

```python
import streamlit as st

st.set_page_config(
    page_title="RoadSoS",
    page_icon="🪖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🪖 RoadSoS — Smart Helmet Emergency System")
st.markdown("""
**Predict** dangerous riding · **Detect** crashes · **Alert** emergency services · **Warn** nearby riders
""")

st.info("Use the sidebar to navigate between modules.")
```

---

### `pages/1_PINN_Dashboard.py` — Helmet AI

Port the Streamlit dashboard from `HelmetSOS.ipynb` into this file. All matplotlib plots must use `plt.style.use("dark_background")`.

**Sidebar controls:**
- Scenario selector: Normal Riding / Oil Patch / Crash
- Simulation duration (slider, 5–30 s)
- Rider profile: blood group, allergies, emergency contact

**Main panel layout (3 columns):**
- Col 1: Resultant acceleration plot (dark mode, red 6g threshold line)
- Col 2: PINN P(skid) over time (dark mode, orange 0.65 threshold line)
- Col 3: Scorecard — HIC15, BrIC, Injury Severity (metric cards)

**Alert banner** (full width, above plots):
- 🔴 `CRASH DETECTED — SOS FIRED` (if crash or accel > 6g)
- 🟡 `SKID WARNING — HAPTIC ALERT` (if P_skid > 0.65)
- 🟢 `SAFE — NORMAL RIDING`

**Training section** (expander at bottom):
- Button: "Train / Retrain PINN"
- Shows live loss plot when training runs
- Saves `artifacts/roadsos_pinn.pt`

---

### `pages/2_Nearby_Services.py` — Location Services (BUILD THIS)

This page satisfies the core hackathon requirement.

**Sidebar controls:**
- Country selector (dropdown, ISO codes from `emergency_numbers.py`)
- Radius slider: 1 km – 20 km (default 5 km)
- Manual lat/lon inputs (text inputs, pre-filled with demo Bangalore coords: 12.9716, 77.5946)
- "Use Demo Location" button (Bangalore NH-44, the blueprint scenario location)
- "Fetch Services" button

**Main panel:**

**Section 1 — Emergency Numbers Card**
Show a styled card with the country's emergency numbers:
```
🚑 Ambulance: 108    🚔 Police: 100    🔥 Fire: 101    📞 Unified: 112
```

**Section 2 — Services Found**
After fetch:
- Metric at top: `📍 {N} services found within {radius} km`
- Tabs for each service category: Hospitals | Police | Ambulance | Towing | Puncture Shops | Showrooms
- Each tab shows a table: Name | Distance (km) | Phone | Address
- Table sorted by distance ascending

**Section 3 — Offline Status**
- Show cache status: `✅ Cached (2.3 hrs ago)` or `🌐 Live fetch`
- Button: "Clear Cache"

**Section 4 — Data Source Note**
`Data sourced from OpenStreetMap via Overpass API. Cache refreshes every 24 hours for offline use.`

---

### `pages/3_Emergency_Profile.py` — Rider Profile & QR

**Form inputs:**
- Rider name, blood group (dropdown: A+/A-/B+/B-/O+/O-/AB+/AB-), allergies, medical conditions, emergency contact number

**Output:**
- Rider card preview (styled markdown)
- SOS packet preview (JSON code block):
```json
{
  "type": "CRASH_ALERT",
  "severity": "HIGH",
  "lat": 12.9716,
  "lon": 77.5946,
  "blood_group": "O+",
  "allergies": "Penicillin",
  "emergency_contact": "+91XXXXXXXXXX",
  "timestamp": "2026-05-29T18:22:10"
}
```
- First-aid instructions card (rendered markdown, WHO/Red Cross guidelines)
- QR code image generated from the rider's emergency URL using the `qrcode` library

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
```

---

## Style Rules (apply everywhere)

1. **All matplotlib plots**: `plt.style.use("dark_background")` before every figure. Background `#0e1117`, accent colors: red `#ff4b4b`, orange `#ffa500`, green `#00c853`.
2. **Streamlit theme**: Use `st.set_page_config(layout="wide")`. Prefer `st.columns()` over vertical stacking.
3. **No hardcoded India-only logic** in `nearby_services.py` or `emergency_numbers.py` — both must be country-agnostic.
4. **Cache before live fetch** — always check cache first in `fetch_nearby_services()`.
5. **`@st.cache_resource`** on `load_model()`, **`@st.cache_data`** on expensive data fetches.
6. **No pyngrok** — the app runs locally via `streamlit run roadsos_app/app.py`.

---

## Run Instructions

```bash
cd "C:\Users\shaur\OneDrive\Documents\Projects\IITM HACKATHON"
pip install -r roadsos_app/requirements.txt
streamlit run roadsos_app/app.py
```

First run auto-trains the PINN and saves the checkpoint. Subsequent runs load from cache.

---

## Documentation Task

After building all `.py` files, update `SmartHelmetSOS_Documentation.docx` with these sections:

1. **System Overview** — two-layer architecture (helmet AI + location services)
2. **Module Reference** — one subsection per `.py` file: purpose, inputs, outputs, key functions
3. **PINN Architecture** — model diagram, physics residuals, loss function, training config
4. **Injury Metrics** — HIC15 formula, BrIC formula, injury scoring
5. **Location Services** — Overpass API query structure, supported service types, offline caching strategy
6. **Emergency Numbers** — table of all countries with their numbers
7. **Evaluation Criteria Coverage** — map each judging criterion to the feature that addresses it:
   - Reliability & accuracy → OSM data + cache freshness
   - Number of contacts → count metric on page 2
   - Offline functionality → `offline_cache.py` + 24h TTL
   - Innovation → PINN + physics-informed prediction
   - Global applicability → country selector + international numbers
8. **How to Run** — setup, training, dashboard launch
9. **Hardware BOM** — from blueprint (ESP32-S3, ICM-42688-P, Ra-02, SIM7600, NEO-6M, solar film)
10. **Deployment Roadmap** — Week 0–2 hackathon → Month 3 pilot → Year 1 B2B

---

## Priority Build Order

1. `modules/simulation.py` + `modules/pinn_model.py` + `modules/injury_metrics.py` + `modules/losses.py` + `modules/train.py` + `modules/inference.py`
2. `pages/1_PINN_Dashboard.py` (port existing notebook dashboard)
3. `modules/offline_cache.py` + `modules/emergency_numbers.py` + `modules/nearby_services.py`
4. `pages/2_Nearby_Services.py` (the core missing feature)
5. `pages/3_Emergency_Profile.py`
6. `app.py`
7. `requirements.txt`
8. Update `SmartHelmetSOS_Documentation.docx`
