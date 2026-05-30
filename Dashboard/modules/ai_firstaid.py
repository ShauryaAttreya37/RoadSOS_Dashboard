from __future__ import annotations

import streamlit as st
import requests

from modules.ai_context import build_incident_context


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "openrouter/auto"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"


def generate_firstaid(
    hic15: float,
    bric: float,
    injury_label: str,
    peak_accel_g: float,
    skid_preceded: bool,
    scenario: str,
    blood_group: str = "Unknown",
    allergies: str = "None",
    rider_name: str | None = None,
    conditions: str | None = None,
    emergency_contact: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
    city: str | None = None,
    country_name: str | None = None,
    country_code: str | None = None,
    location_source: str | None = None,
) -> str:
    incident_context = build_incident_context(
        rider_name=rider_name,
        blood_group=blood_group,
        allergies=allergies,
        conditions=conditions,
        emergency_contact=emergency_contact,
        lat=lat,
        lon=lon,
        city=city,
        country_name=country_name,
        country_code=country_code,
        location_source=location_source,
    )
    prompt = f"""
You are a trauma first-aid advisor. A motorcycle crash has been detected by the RoadSoS helmet system.
{incident_context}

You are instructing a bystander at the crash scene, not the injured rider.
Do not tell the rider to move, stand, walk, remove the helmet, eat, or drink.
Only tell the bystander to move the rider if fire, traffic, water, or another immediate danger makes staying in place unsafe.
Do not invent consciousness, bleeding, breathing, or other clinical signs that are not in the prompt; report them as unknown.
If consciousness or breathing status is not supplied, the ambulance handoff must say "consciousness unknown" and "breathing unknown".
Do not use words like unconscious, unresponsive, not breathing, or severe bleeding unless the prompt explicitly supplied that observation.

The on-board PINN model has produced these biomechanical measurements:

- Head Injury Criterion (HIC15): {hic15:.0f} (threshold: 700 moderate, 1000 severe)
- Brain Rotational Injury (BrIC): {bric:.3f} (threshold: 1.0 severe)
- Computed injury severity: {injury_label}
- Peak impact acceleration: {peak_accel_g:.1f} g
- Skid preceded crash: {"Yes" if skid_preceded else "No"}
- Crash scenario: {scenario}
- Rider blood group: {blood_group}
- Known allergies: {allergies}

Based on ONLY these measurements and the RoadSoS incident context, give a bystander exactly 5 numbered steps they must take RIGHT NOW.
Be direct. Use simple words. Each step must be one sentence. Prioritise by urgency.
Do NOT give generic advice — tailor every step to the severity level above.
End with one line: what to tell the ambulance when they call the local ambulance number.
Format as markdown with bold step numbers.
"""
    # 1. Try Anthropic if key is present
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if api_key:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=DEFAULT_ANTHROPIC_MODEL,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text
    except Exception:
        pass

    # 2. Try OpenRouter if key is present
    try:
        return _generate_openrouter_firstaid(prompt)
    except Exception:
        pass

    # 3. Fallback to static logic
    return _fallback_firstaid(hic15, bric, injury_label, peak_accel_g, skid_preceded, blood_group, allergies)


def _generate_openrouter_firstaid(prompt: str) -> str:
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not configured.")

    model = st.secrets.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    response = requests.post(
        OPENROUTER_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://roadsos.local",
            "X-Title": "RoadSoS",
        },
        json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 400},
        timeout=(4, 30),
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"].get("content", "")
    if not content.strip():
        raise RuntimeError("OpenRouter returned an empty response.")
    return content


def _fallback_firstaid(
    hic15: float,
    bric: float,
    injury_label: str,
    peak_accel_g: float,
    skid_preceded: bool,
    blood_group: str,
    allergies: str,
) -> str:
    if injury_label == "SEVERE":
        severity_action = "Treat this as a severe head or spine injury and do not move the rider unless the scene is unsafe."
    elif injury_label == "MODERATE":
        severity_action = "Keep the rider still and watch closely for confusion, vomiting, worsening headache, or drowsiness."
    else:
        severity_action = "Keep the rider seated or lying still and reassess symptoms every few minutes."

    skid_line = "Tell responders a skid likely preceded the crash." if skid_preceded else "Tell responders no clear skid warning preceded the impact."
    return (
        f"**1.** Call ambulance service now and report HIC15 {hic15:.0f}, BrIC {bric:.3f}, peak impact {peak_accel_g:.1f} g, and severity {injury_label}.\n"
        f"**2.** {severity_action}\n"
        "**3.** Check breathing and heavy bleeding, and apply firm direct pressure to any severe bleeding with clean cloth.\n"
        f"**4.** Share medical details: blood group {blood_group}, allergies {allergies or 'None'}, and the RoadSoS crash profile.\n"
        f"**5.** {skid_line}\n\n"
        "Tell the ambulance: motorcycle crash with helmet PINN injury metrics, suspected head trauma risk, exact GPS location, blood group, and allergies."
    )
