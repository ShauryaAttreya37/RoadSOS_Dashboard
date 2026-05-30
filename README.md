# RoadSoS

RoadSoS is a smart-helmet emergency and predictive safety prototype for the IIT Madras Road Safety Hackathon 2026. The Streamlit command center combines helmet PINN simulations, rider-aware AI assistance, emergency medical handoff, browser location detection, and nearby-service discovery.

## App

The deployable application lives in `roadsos_app`.

```powershell
python -m pip install -r requirements.txt
streamlit run roadsos_app/app.py
```

## Streamlit Community Cloud

Create an app from this repository with:

- Branch: `main`
- Main file path: `roadsos_app/app.py`
- Python version: `3.12`

Paste the required keys into the Streamlit Cloud secrets field. Never commit `.streamlit/secrets.toml`.

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENROUTER_MODEL = "openrouter/auto"

# Optional integrations
ANTHROPIC_API_KEY = "sk-ant-..."
TOMTOM_API_KEY = "your-tomtom-traffic-api-key"
GOOGLE_MAPS_API_KEY = "your-google-maps-platform-key"
```

OpenStreetMap powers nearby-service discovery without a paid key. A server-side Google Maps Platform key with Places API (New) access enriches live trauma-centre, ambulance, towing, repair, and showroom coverage. TomTom enables live traffic overlays, and either OpenRouter or Anthropic enables hosted AI responses.

The hosted app keeps rider medical data in the active Streamlit session only. Runtime logs, caches, local profiles, and secrets are excluded from version control.

## Model Notebook

The PINN architecture notebook is included at `roadsos_app/notebooks/RoadSoS_PINN_Model.ipynb`.
