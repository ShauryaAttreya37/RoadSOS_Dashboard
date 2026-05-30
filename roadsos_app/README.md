# RoadSoS Streamlit App

RoadSoS combines helmet PINN simulations with location-aware emergency routing, nearby-service discovery, medical QR handoff, and rider-aware AI assistance.

## Run Locally

From the repository root:

```powershell
python -m pip install -r requirements.txt
streamlit run roadsos_app/app.py
```

Create `.streamlit/secrets.toml` in the repository root when AI or optional map integrations are needed:

```toml
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENROUTER_MODEL = "openrouter/auto"

# Optional integrations
ANTHROPIC_API_KEY = "sk-ant-..."
TOMTOM_API_KEY = "your-tomtom-traffic-api-key"
GOOGLE_MAPS_API_KEY = "your-google-maps-platform-key"
```

Browser geolocation uses `streamlit-js-eval`. If the browser denies permission, RoadSoS falls back to IP geolocation and then to manual coordinates. The resolved location is reused across pages for the active Streamlit session; use **Detect Location Again** in the sidebar to request a fresh fix.

Nearby services use OpenStreetMap Overpass data with a 24-hour runtime cache. Add a server-side `GOOGLE_MAPS_API_KEY` with Places API (New) access to enrich live trauma-centre, hospital, police, fire, ambulance, towing, puncture-shop, repair, and showroom contacts. The **Refresh Live Data** action bypasses the runtime cache, while expired cached contacts remain available as an offline fallback if live providers fail. TomTom can add live traffic flow and incidents. Emergency contact cards render before the optional 3D road-intelligence layer; enable that layer on demand when road topology, weather, and traffic context are needed. Rider medical profile data remains session-scoped on hosted Streamlit deployments.

For production Google Places enrichment, enable Places API (New), store the key only in Streamlit secrets, restrict the key to Places API (New), and add server IP restrictions when the deployment has stable outbound IP addresses.

## Model Notebook

The model notebook is available at `notebooks/RoadSoS_PINN_Model.ipynb`. It documents the 6-axis IMU PINN architecture, physical constraints, skid probability, and injury metrics.
