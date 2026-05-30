# RoadSoS — Hackathon TODO

## What the judges require (from problem statement 1.3)

The tool must provide **location-based access** to nearby:
- Trauma centres & hospitals
- Ambulance services
- Vehicle rescue / towing services
- Police stations
- Nearest puncture shops & showrooms
- Emergency contacts

### Evaluation criteria
1. Reliability and data accuracy
2. Number of contacts fetched
3. **Offline functionality**
4. Innovation & additional features
5. Information integration across countries (global applicability)

---

## What we already have ✅

- [x] PINN model for crash prediction (synthetic data, training loop, inference)
- [x] TinyML crash classifier concept (1D-CNN, INT8)
- [x] LoRa mesh network design (433 MHz, 3 km range)
- [x] Solar charging subsystem spec
- [x] Hardware BOM (ESP32-S3, ICM-42688-P, SIM7600, NEO-6M)
- [x] Emergency response flow (t=0 to t=12s)
- [x] Streamlit dashboard (skid probability, HIC15, BrIC, alerts)
- [x] Pitch deck (`SmartHelmet.pptx`)
- [x] Report (`RoadSoS_Report.docx`, `RoadSoS_Submission_2.docx`)
- [x] HTML presentation (`RoadSoS_Pitch.html`)
- [x] Plots for normal / oil patch / crash scenarios (dark mode)

---

## What is MISSING (gaps vs. judging criteria) ❌

### 1. Location-based nearby services (CORE requirement — not implemented)
- [ ] Integrate a location/maps API (OpenStreetMap/Overpass or Google Places) to fetch **nearest** hospitals, police stations, ambulance services
- [ ] Add **towing services**, puncture shops, and showrooms to the fetched contact types
- [ ] Show distance + contact number for each result
- [ ] Show number of contacts fetched (judge metric #2)

### 2. Offline functionality (explicit judging criterion)
- [ ] Cache nearby service data locally (SQLite or JSON) so it works without internet
- [ ] Implement fallback: if no network, serve cached results with timestamp
- [ ] Document or demo the offline scenario in the submission

### 3. Global applicability
- [ ] Switch from India-only hardcoding (108, local APIs) to country-aware service numbers
- [ ] Use an international emergency number dataset or OSM tags that work globally
- [ ] Mention this in the pitch / report explicitly

### 4. Evaluation criteria coverage gaps
- [ ] **Reliability & data accuracy**: explain/show data source quality (OSM live vs. cached)
- [ ] **Number of contacts**: show a count metric in the dashboard — e.g. "12 services found within 5 km"
- [ ] **Information integration across countries**: add a country-selector demo or table of emergency numbers by country

### 5. Demo / submission polish
- [ ] Add the location-based services feature to the Streamlit dashboard (new tab or section)
- [ ] Update the pitch deck to include the location-services screen / flow
- [ ] Update the report to cover the offline caching and global number features
- [ ] Add a live demo script / README showing how to run the full stack

---

## Priority order (1 day budget)

| Priority | Task | Est. time |
|----------|------|-----------|
| 🔴 P1 | Build location-based nearby services feature (OSM Overpass API) | 3–4 h |
| 🔴 P1 | Add offline caching (cache to local JSON/SQLite on first fetch) | 1–2 h |
| 🟡 P2 | Integrate into Streamlit dashboard (new "Nearby Services" tab) | 1 h |
| 🟡 P2 | Add country-aware emergency numbers table | 1 h |
| 🟢 P3 | Update pitch deck slides to show new feature | 30 min |
| 🟢 P3 | Update report with offline + global sections | 30 min |
