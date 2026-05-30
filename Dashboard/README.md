# RoadSoS Streamlit App

RoadSoS combines the existing helmet PINN dashboard with a global emergency-service lookup layer.

## Run

```powershell
cd "C:\Users\shaur\OneDrive\Documents\Projects\IITM HACKATHON"
pip install -r roadsos_app\requirements.txt
streamlit run roadsos_app\app.py
```

For the RoadSoS AI page, create `.streamlit/secrets.toml` in the project root:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
OPENROUTER_API_KEY = "sk-or-v1-..."
OPENROUTER_MODEL = "openai/gpt-4o-mini"
```

`ANTHROPIC_API_KEY` is used for direct Claude calls. `OPENROUTER_API_KEY` enables the OpenRouter chat endpoint for testing, and `OPENROUTER_MODEL` can be changed to any model ID available in your OpenRouter account.

Browser geolocation uses `streamlit-js-eval`. If the browser denies location permission, RoadSoS falls back to IP geolocation. If both fail, the app asks for a real manual coordinate instead of using mock/demo coordinates.

## Location Services

The nearby-services page uses OpenStreetMap Overpass API and writes 24-hour JSON caches to `roadsos_app/data/cache`.
