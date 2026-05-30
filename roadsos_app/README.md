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

Browser geolocation uses `streamlit-js-eval`. If the browser denies permission, RoadSoS falls back to IP geolocation and then to manual coordinates.

Nearby services use OpenStreetMap Overpass data with a 24-hour runtime cache. Google Maps can enrich the service list, and TomTom can add live traffic flow and incidents. Rider medical profile data remains session-scoped on hosted Streamlit deployments.
