import html

import streamlit as st

from modules.emergency_numbers import get_emergency_numbers
from modules.location import has_location, init_location_state, render_location_sidebar
from modules.nearby_services import CACHE_SCHEMA_VERSION, count_total_contacts, eta_minutes, fetch_nearby_services
from modules.offline_cache import cache_age_hours, clear_cache, is_cache_fresh
from modules.road_intelligence import (
    MAX_ROAD_RADIUS_M,
    build_road_state_deck,
    fetch_live_traffic,
    fetch_road_network,
    fetch_weather_advisory,
    traffic_summary,
)
from modules.ui import (
    AMBER,
    GREEN,
    RED,
    emergency_number_strip,
    get_colors,
    get_theme,
    inject_global_css,
    micon,
    page_header,
    placeholder_card,
    render_theme_toggle,
    service_card,
    sidebar_brand,
    stat_card,
)


st.set_page_config(page_title="RoadSoS | Nearby Services", page_icon=":material/sports_motorsports:", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
init_location_state()
sidebar_brand()
render_theme_toggle()
render_location_sidebar()

c = get_colors()
is_dark = get_theme() == "dark"


SECTION_META = {
    "hospital": {
        "icon": "local_hospital",
        "title": "Hospitals & Clinics",
        "desc": "Mapped hospitals, clinics, and doctors sorted by distance.",
        "empty": "No hospitals or clinics found within this radius. Try increasing the search range.",
    },
    "police": {
        "icon": "local_police",
        "title": "Police Stations",
        "desc": "Nearest police stations for accident reporting and legal assistance.",
        "empty": "No police stations found. Call 100 (India) directly.",
    },
    "fire_station": {
        "icon": "local_fire_department",
        "title": "Fire & Rescue",
        "desc": "Fire brigade and rescue stations for extrication and fire response.",
        "empty": "No fire stations found. Call 101 (India) directly.",
    },
    "ambulance": {
        "icon": "emergency",
        "title": "Ambulance & Emergency Dispatch",
        "desc": "Mapped ambulance points and emergency-hospital dispatch fallbacks. Call to confirm availability.",
        "empty": "No ambulance or emergency dispatch points found. Call 108 (India) directly.",
    },
    "vehicle_rescue": {
        "icon": "directions_car",
        "title": "Vehicle Rescue & Towing",
        "desc": "Towing services and roadside assistance for crash vehicle recovery.",
        "empty": "No towing services found nearby.",
    },
    "puncture_shop": {
        "icon": "build",
        "title": "Puncture Shops & Showrooms",
        "desc": "Tyre repair shops and authorised service centres.",
        "empty": "No repair shops found nearby.",
    },
}


@st.cache_data(ttl=86400, show_spinner=False)
def cached_services(lat: float, lon: float, radius_m: int, _google_maps_api_key: str | None) -> dict:
    return fetch_nearby_services(lat, lon, radius_m, _google_maps_api_key)


@st.cache_data(ttl=900, show_spinner=False)
def cached_road_network(lat: float, lon: float, radius_m: int) -> list[dict]:
    return fetch_road_network(lat, lon, radius_m)


@st.cache_data(ttl=300, show_spinner=False)
def cached_weather_advisory(lat: float, lon: float) -> dict:
    return fetch_weather_advisory(lat, lon)


@st.cache_data(ttl=120, show_spinner=False)
def cached_live_traffic(lat: float, lon: float, radius_m: int, _api_key: str | None) -> dict:
    roads = cached_road_network(lat, lon, radius_m)
    return fetch_live_traffic(lat, lon, radius_m, roads, _api_key)


def render_section(tab, category: str, services_dict: dict) -> None:
    items = list(services_dict.get(category, []))
    meta = SECTION_META[category]
    with tab:
        st.markdown(
            f"""
<div style="margin-bottom:1.2rem;">
    {micon(meta['icon'], size=28, color=GREEN, fill=True)}
    <span style="font-size:1.15rem;font-weight:800;color:{c["TEXT"]};margin-left:8px;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.06em;vertical-align:middle;">{meta['title']}</span>
    <div style="color:{c["MUTED"]};font-size:0.85rem;margin-top:5px;font-family:'Inter';">{meta['desc']}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        search = st.text_input(
            f"Filter {meta['title']}",
            placeholder=f"Filter {meta['title'].lower()}...",
            key=f"search_{category}",
            label_visibility="collapsed",
        )
        if search:
            items = [item for item in items if search.lower() in item["name"].lower()]

        if not items:
            placeholder_card(meta["empty"])
            return

        if max_results != "All" and len(items) > int(max_results):
            st.caption(f"Showing the nearest {max_results} of {len(items)} results. Select All in Search Controls to render every listing.")
            items = items[: int(max_results)]

        cols = st.columns(3)
        for idx, svc in enumerate(items):
            svc = {**svc, "eta_min": svc.get("eta_min") or eta_minutes(float(svc.get("distance_km", 0)))}
            with cols[idx % 3]:
                service_card(**svc)


with st.sidebar:
    st.header("Search Controls")
    radius_km = st.slider("Search radius", 1, 20, 5, format="%d km")
    max_results = st.selectbox("Results per category", [12, 24, 48, "All"], index=1)
    service_provider_key = "google" if st.secrets.get("GOOGLE_MAPS_API_KEY") else "osm"
    cache_key = (
        f"{CACHE_SCHEMA_VERSION}_{service_provider_key}_{float(st.session_state.lat):.3f}_{float(st.session_state.lon):.3f}_{radius_km * 1000}"
        if has_location()
        else ""
    )
    if cache_key and is_cache_fresh(cache_key):
        st.markdown(f":material/check_circle: **Cached** ({cache_age_hours(cache_key):.1f} hrs ago)")
    else:
        st.markdown(":material/public: **Live fetch**")

    if st.button("Refresh Live Data", type="primary", use_container_width=True):
        cached_services.clear()
        cached_road_network.clear()
        cached_weather_advisory.clear()
        cached_live_traffic.clear()
        st.rerun()
    if st.button("Clear Cache", use_container_width=True):
        clear_cache()
        cached_services.clear()
        cached_road_network.clear()
        cached_weather_advisory.clear()
        cached_live_traffic.clear()
        st.rerun()


page_header(
    "Nearby Emergency Services",
    "Auto-detected location, emergency numbers, and nearby service navigation.",
    "LIVE",
    GREEN,
    icon="location_on",
)

numbers = get_emergency_numbers(st.session_state.get("country_code", "XX"))
emergency_number_strip(st.session_state.get("country_name", "Unknown"), numbers)

if not has_location():
    st.warning(
        "No real coordinates are available yet. Allow browser location permission or enter coordinates in the sidebar to fetch nearby services."
    )
    st.stop()

with st.spinner("Finding nearby services..."):
    try:
        lat = round(float(st.session_state.lat), 3)
        lon = round(float(st.session_state.lon), 3)
        radius_m = radius_km * 1000
        google_maps_api_key = st.secrets.get("GOOGLE_MAPS_API_KEY")
        services = cached_services(lat, lon, radius_m, google_maps_api_key)
        service_error = None
    except Exception as exc:
        services = {"hospital": [], "police": [], "fire_station": [], "ambulance": [], "vehicle_rescue": [], "puncture_shop": []}
        service_error = str(exc)

if service_error:
    st.markdown(
        f"""
<div style="background:{"#1A1200" if is_dark else "#FFFBF5"};border:1px solid {AMBER}44;border-left:4px solid {AMBER};
     border-radius:2px;padding:1rem 1.4rem;margin-bottom:1.5rem;color:{c["TEXT"]};font-family:'Inter';">
    Live service lookup failed: {service_error}
</div>
""",
        unsafe_allow_html=True,
    )

category_order = ["hospital", "police", "fire_station", "ambulance", "vehicle_rescue", "puncture_shop"]
counts = {cat: len(services.get(cat, [])) for cat in category_order}
total = count_total_contacts(services)
service_provider = str((services.get("_meta") or {}).get("provider", "OpenStreetMap"))

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    stat_card("Total Services", total, "found", c["TEXT"])
with c2:
    stat_card("Hospitals", counts["hospital"], "nearby", RED)
with c3:
    stat_card("Police", counts["police"], "nearby", "#4FC3F7")
with c4:
    stat_card("Fire & Rescue", counts["fire_station"], "nearby", "#FF6E40")
with c5:
    stat_card("Ambulance", counts["ambulance"], "nearby", AMBER)
with c6:
    stat_card("Repair", counts["puncture_shop"] + counts["vehicle_rescue"], "nearby", GREEN)

if not st.secrets.get("GOOGLE_MAPS_API_KEY"):
    st.info(
        "Service coverage currently uses OpenStreetMap. Add GOOGLE_MAPS_API_KEY to enrich every category with "
        "Google Places results, including service-area ambulance and towing providers that may not have mapped storefronts."
    )
else:
    st.caption(f"Nearby service provider coverage: {service_provider}.")
    service_warnings = list((services.get("_meta") or {}).get("warnings") or [])
    if service_warnings:
        st.warning("Some Google Places enrichment requests could not be completed. Available verified results are shown.")

st.markdown("---")
st.subheader("3D Road Vicinity Intelligence")
st.caption(
    "Operational view of verified nearby road topology, current weather exposure, and live traffic signals. "
    "Weather exposure is an advisory, not a pavement inspection."
)
map_view_mode = st.radio(
    "Map view",
    ["Road Map", "3D Operations"],
    horizontal=True,
    help="Use Road Map for navigation clarity or 3D Operations for elevated traffic and incident signals.",
)

road_radius_m = min(radius_m, MAX_ROAD_RADIUS_M)
tomtom_key = st.secrets.get("TOMTOM_API_KEY")
road_error = None
weather_error = None
traffic_error = None

with st.spinner("Loading verified road topology and live vicinity signals..."):
    try:
        roads = cached_road_network(lat, lon, road_radius_m)
    except Exception as exc:
        roads = []
        road_error = str(exc)
    try:
        weather = cached_weather_advisory(lat, lon)
    except Exception as exc:
        weather = None
        weather_error = str(exc)
    try:
        traffic = cached_live_traffic(lat, lon, road_radius_m, tomtom_key)
    except Exception as exc:
        traffic = {
            "configured": bool(tomtom_key),
            "source": "TomTom Traffic unavailable",
            "flows": [],
            "incidents": [],
            "updated_at": None,
            "errors": [str(exc)],
        }
        traffic_error = str(exc)

summary = traffic_summary(traffic)
rm1, rm2, rm3, rm4, rm5 = st.columns(5)
with rm1:
    stat_card("Road Segments", len(roads), "OSM verified", "#8B949E")
with rm2:
    stat_card("Live Flow Samples", summary["flows"], "TomTom", GREEN if summary["flows"] else "#8B949E")
with rm3:
    stat_card("Congested", summary["congested"], "segments", AMBER if summary["congested"] else GREEN)
with rm4:
    stat_card("Incidents", summary["incidents"], "live", RED if summary["incidents"] else GREEN)
with rm5:
    stat_card("Closures", summary["closures"], "live", RED if summary["closures"] else GREEN)

if weather:
    risk_color = RED if weather["risk"] == "HIGH" else AMBER if weather["risk"] == "ELEVATED" else GREEN
    st.markdown(
        f"""
<div style="background:{c["CARD_BG"]};border:1px solid {risk_color}44;border-left:4px solid {risk_color};
     border-radius:6px;padding:1rem 1.2rem;margin:1rem 0;color:{c["TEXT"]};font-family:'Inter';">
    <b style="color:{risk_color};">WEATHER-DERIVED ROAD ADVISORY: {weather["risk"]}</b>
    <span style="color:{c["MUTED"]};"> &nbsp; {weather["advisory"]}</span><br>
    <span style="font-size:0.8rem;color:{c["MUTED"]};">
        Open-Meteo observation {html.escape(weather["observed_at"])} &nbsp; | &nbsp;
        {weather["temperature_c"]:.1f} C &nbsp; | &nbsp;
        precipitation {weather["precipitation_mm"]:.1f} mm &nbsp; | &nbsp;
        wind {weather["wind_kmh"]:.1f} km/h
    </span>
</div>
""",
        unsafe_allow_html=True,
    )
elif weather_error:
    st.warning(f"Current weather advisory is unavailable: {weather_error}")

st.pydeck_chart(
    build_road_state_deck(lat, lon, roads, traffic, map_view_mode, services=services),
    width="stretch",
    height=610,
    key=f"roadsos-map-v4-{lat:.3f}-{lon:.3f}",
)

if not traffic["configured"]:
    st.info(
        "Live traffic flow and incident towers are ready but disabled until TOMTOM_API_KEY is added. "
        "The visible road network is real OpenStreetMap topology and the advisory uses current Open-Meteo observations."
    )
elif traffic_error or traffic.get("errors"):
    st.warning("Some TomTom live traffic requests could not be completed. Available live signals are shown.")
else:
    st.caption(f"TomTom live traffic refreshed at {traffic['updated_at']} UTC.")

st.caption(
    "Map legend: basemap roads = CARTO with OpenStreetMap data; green/amber/red elevated corridors = TomTom live flow; "
    "red towers = TomTom incidents; blue marker = rider GPS. Use 3D Operations to inspect elevated live signals. "
    "Radar radius is capped at 5 km for fast refreshes."
)

st.markdown("---")
st.subheader("Nearby Emergency Contacts")

tab_labels = [
    f":material/local_hospital: Hospitals ({counts['hospital']})",
    f":material/local_police: Police ({counts['police']})",
    f":material/local_fire_department: Fire & Rescue ({counts['fire_station']})",
    f":material/emergency: Ambulance ({counts['ambulance']})",
    f":material/directions_car: Towing ({counts['vehicle_rescue']})",
    f":material/build: Repair ({counts['puncture_shop']})",
]
tabs = st.tabs(tab_labels)

for tab, category in zip(tabs, category_order):
    render_section(tab, category, services)

st.markdown("---")
st.caption(
    "Emergency contacts: OpenStreetMap via Overpass API with 24-hour offline cache. "
    "Road topology: OpenStreetMap. Weather: Open-Meteo current conditions. Optional live traffic: TomTom Traffic."
)
