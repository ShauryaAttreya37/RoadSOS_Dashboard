import html
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from roadsos_app.modules.emergency_numbers import get_emergency_numbers
from roadsos_app.modules.config import get_secret
from roadsos_app.modules.location import has_location, init_location_state, render_location_sidebar
from roadsos_app.modules.nearby_services import CACHE_SCHEMA_VERSION, count_total_contacts, eta_minutes, fetch_nearby_services
from roadsos_app.modules.offline_cache import cache_age_hours, clear_cache, is_cache_fresh
from roadsos_app.modules.road_intelligence import (
    MAX_ROAD_RADIUS_M,
    build_road_state_deck,
    fetch_live_traffic,
    fetch_road_network,
    fetch_weather_advisory,
    traffic_summary,
)
from roadsos_app.modules.translator import tr
from roadsos_app.modules.ui import (
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
    "trauma_centre": {
        "icon": "emergency",
        "title": "Trauma Centres",
        "desc": "Emergency-capable hospitals and mapped trauma centres for time-critical crash care.",
        "empty": "No trauma centre is mapped within this radius. Check nearby hospitals and call the local ambulance number shown above.",
    },
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
        "empty": "No police stations found. Call the local police emergency number shown above.",
    },
    "fire_station": {
        "icon": "local_fire_department",
        "title": "Fire & Rescue",
        "desc": "Fire brigade and rescue stations for extrication and fire response.",
        "empty": "No fire stations found. Call the local fire emergency number shown above.",
    },
    "ambulance": {
        "icon": "emergency",
        "title": "Ambulance & Emergency Dispatch",
        "desc": "Mapped ambulance points and emergency-hospital dispatch fallbacks. Call to confirm availability.",
        "empty": "No ambulance or emergency dispatch points found. Call the local ambulance number shown above.",
    },
    "vehicle_rescue": {
        "icon": "directions_car",
        "title": "Vehicle Rescue & Towing",
        "desc": "Towing services and roadside assistance for crash vehicle recovery.",
        "empty": "No towing services found nearby.",
    },
    "puncture_shop": {
        "icon": "build",
        "title": "Puncture & Repair Shops",
        "desc": "Tyre repair shops, garages, and vehicle repair centres.",
        "empty": "No repair shops found nearby.",
    },
    "showroom": {
        "icon": "storefront",
        "title": "Vehicle Showrooms",
        "desc": "Mapped car and motorcycle showrooms for vehicle support and recovery coordination.",
        "empty": "No vehicle showrooms found nearby.",
    },
}


@st.cache_data(ttl=86400, show_spinner=False)
def cached_services(lat: float, lon: float, radius_m: int, _google_maps_api_key: str | None, country_code: str = "XX") -> dict:
    return fetch_nearby_services(lat, lon, radius_m, _google_maps_api_key, country_code=country_code)


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
    <span style="font-size:1.15rem;font-weight:800;color:{c["TEXT"]};margin-left:8px;font-family:'Outfit';text-transform:uppercase;letter-spacing:0.06em;vertical-align:middle;">{tr(meta['title'])}</span>
    <div style="color:{c["MUTED"]};font-size:0.85rem;margin-top:5px;font-family:'Inter';">{tr(meta['desc'])}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        search = st.text_input(
            f"{tr('Filter')} {tr(meta['title'])}",
            placeholder=f"{tr('Filter')} {tr(meta['title']).lower()}...",
            key=f"search_{category}",
            label_visibility="collapsed",
        )
        if search:
            items = [item for item in items if search.lower() in item["name"].lower()]

        if not items:
            placeholder_card(tr(meta["empty"]))
            return

        if max_results != "All" and len(items) > int(max_results):
            st.caption(f"{tr('Showing the nearest')} {max_results} {tr('of')} {len(items)} {tr('results. Select All in Search Controls to render every listing.')}")
            items = items[: int(max_results)]

        cols = st.columns(3)
        for idx, svc in enumerate(items):
            distance = svc.get("distance_km")
            eta_min = svc.get("eta_min") or (eta_minutes(float(distance)) if distance is not None else None)
            svc = {**svc, "eta_min": eta_min}
            with cols[idx % 3]:
                service_card(**svc)


def render_road_intelligence(lat: float, lon: float, radius_m: int, services: dict) -> None:
    st.markdown("---")
    st.subheader(tr("3D Road Vicinity Intelligence"))
    st.caption(
        tr("Optional operational view of verified nearby road topology, current weather exposure, and live traffic signals. Emergency contacts above stay available while this heavier layer is loaded.")
    )
    if not st.toggle(
        tr("Load live 3D road intelligence"),
        key="road_intelligence_enabled",
        help=tr("Loads OpenStreetMap road topology, current Open-Meteo conditions, and optional TomTom traffic."),
    ):
        placeholder_card(tr("Emergency contacts are ready. Enable the live 3D layer when road and traffic context is needed."))
        return

    map_view_mode = st.radio(
        tr("Map view"),
        [tr("Road Map"), tr("3D Operations")],
        horizontal=True,
        help=tr("Use Road Map for navigation clarity or 3D Operations for elevated traffic and incident signals."),
    )

    road_radius_m = min(radius_m, MAX_ROAD_RADIUS_M)
    tomtom_key = get_secret("TOMTOM_API_KEY")
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
    <b style="color:{risk_color};">{tr("WEATHER-DERIVED ROAD ADVISORY")}: {tr(weather["risk"])}</b>
    <span style="color:{c["MUTED"]};"> &nbsp; {tr(weather["advisory"])}</span><br>
    <span style="font-size:0.8rem;color:{c["MUTED"]};">
        {tr("Open-Meteo observation")} {html.escape(weather["observed_at"])} &nbsp; | &nbsp;
        {weather["temperature_c"]:.1f} C &nbsp; | &nbsp;
        {tr("precipitation")} {weather["precipitation_mm"]:.1f} mm &nbsp; | &nbsp;
        {tr("wind")} {weather["wind_kmh"]:.1f} km/h
    </span>
</div>
""",
            unsafe_allow_html=True,
        )
    elif weather_error:
        st.warning(f"Current weather advisory is unavailable: {weather_error}")

    if road_error:
        st.warning(f"Road topology is unavailable: {road_error}")

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


with st.sidebar:
    st.header(tr("Search Controls"))
    radius_km = st.slider(tr("Search radius"), 1, 20, 5, format="%d km")
    max_results = st.selectbox(tr("Results per category"), [12, 24, 48, "All"], index=1)
    service_provider_key = "google" if get_secret("GOOGLE_MAPS_API_KEY") else "osm"
    cache_key = (
        f"{CACHE_SCHEMA_VERSION}_{service_provider_key}_{float(st.session_state.lat):.3f}_{float(st.session_state.lon):.3f}_{radius_km * 1000}"
        if has_location()
        else ""
    )
    if cache_key and is_cache_fresh(cache_key):
        st.markdown(f":material/check_circle: **{tr('Cached')}** ({cache_age_hours(cache_key):.1f} {tr('hrs ago')})")
    else:
        st.markdown(f":material/public: **{tr('Live fetch')}**")

    if st.button(tr("Refresh Live Data"), type="primary", use_container_width=True):
        st.session_state["_force_service_refresh"] = True
        cached_services.clear()
        cached_road_network.clear()
        cached_weather_advisory.clear()
        cached_live_traffic.clear()
        st.rerun()
    if st.button(tr("Clear Cache"), use_container_width=True):
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
        tr("No real coordinates are available yet. Allow browser location permission or enter coordinates in the sidebar to fetch nearby services.")
    )
    st.stop()

with st.spinner("Finding nearby services..."):
    try:
        lat = round(float(st.session_state.lat), 3)
        lon = round(float(st.session_state.lon), 3)
        radius_m = radius_km * 1000
        google_maps_api_key = get_secret("GOOGLE_MAPS_API_KEY")
        country_code = str(st.session_state.get("country_code", "XX"))
        force_service_refresh = bool(st.session_state.pop("_force_service_refresh", False))
        services = (
            fetch_nearby_services(lat, lon, radius_m, google_maps_api_key, force_refresh=True, country_code=country_code)
            if force_service_refresh
            else cached_services(lat, lon, radius_m, google_maps_api_key, country_code)
        )
        service_error = None
    except Exception as exc:
        services = {category: [] for category in SECTION_META}
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

category_order = list(SECTION_META)
counts = {cat: len(services.get(cat, [])) for cat in category_order}
total = count_total_contacts(services)
service_meta = dict(services.get("_meta") or {})
service_provider = str(service_meta.get("provider", "OpenStreetMap"))

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    stat_card("Unique Contacts", total, "found", c["TEXT"])
with c2:
    stat_card("Trauma Centres", counts["trauma_centre"], "nearby", RED)
with c3:
    stat_card("Hospitals", counts["hospital"], "nearby", RED)
with c4:
    stat_card("Police", counts["police"], "nearby", "#4FC3F7")
with c5:
    stat_card("Ambulance", counts["ambulance"], "nearby", AMBER)

c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card("Fire & Rescue", counts["fire_station"], "nearby", "#FF6E40")
with c2:
    stat_card("Towing", counts["vehicle_rescue"], "nearby", GREEN)
with c3:
    stat_card("Puncture & Repair", counts["puncture_shop"], "nearby", GREEN)
with c4:
    stat_card("Showrooms", counts["showroom"], "nearby", GREEN)

if service_meta.get("source") == "stale_cache":
    st.warning(
        f"Live service providers are unavailable. Showing offline cached contacts from "
        f"{float(service_meta.get('age_hours') or 0):.1f} hours ago."
    )
elif service_meta.get("source") == "emergency_numbers_fallback":
    st.warning(
        "Map data could not be loaded and no offline cache exists. Showing hardcoded emergency "
        "numbers for your country — call them directly for dispatch to your location."
    )
if service_meta.get("auto_expanded_to_m"):
    expanded_km = int(service_meta["auto_expanded_to_m"]) // 1000
    st.info(
        f"Sparse results at {radius_km} km — automatically expanded search to {expanded_km} km to find more contacts."
    )

if not get_secret("GOOGLE_MAPS_API_KEY"):
    st.info(
        "Service coverage currently uses OpenStreetMap. Add GOOGLE_MAPS_API_KEY to enrich every category with "
        "Google Places results, including service-area ambulance and towing providers that may not have mapped storefronts."
    )
else:
    st.caption(f"Nearby service provider coverage: {service_provider}.")
    service_warnings = list(service_meta.get("warnings") or [])
    if service_warnings:
        st.warning("Some Google Places enrichment requests could not be completed. Available verified results are shown.")

st.markdown("---")
st.subheader(tr("Nearby Emergency Contacts"))

tab_labels = [
    f":material/emergency: {tr('Trauma Centres')} ({counts['trauma_centre']})",
    f":material/local_hospital: {tr('Hospitals')} ({counts['hospital']})",
    f":material/local_police: {tr('Police')} ({counts['police']})",
    f":material/local_fire_department: {tr('Fire & Rescue')} ({counts['fire_station']})",
    f":material/emergency: {tr('Ambulance')} ({counts['ambulance']})",
    f":material/directions_car: {tr('Towing')} ({counts['vehicle_rescue']})",
    f":material/build: {tr('Repair')} ({counts['puncture_shop']})",
    f":material/storefront: {tr('Showrooms')} ({counts['showroom']})",
]
tabs = st.tabs(tab_labels)

for tab, category in zip(tabs, category_order):
    render_section(tab, category, services)

render_road_intelligence(lat, lon, radius_m, services)

st.markdown("---")
st.caption(
    "Emergency contacts: OpenStreetMap via Overpass API with 24-hour offline cache. "
    "Road topology: OpenStreetMap. Weather: Open-Meteo current conditions. Optional live traffic: TomTom Traffic."
)
