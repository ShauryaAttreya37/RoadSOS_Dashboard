import html

import requests
import streamlit as st

from roadsos_app.modules.ai_context import build_incident_context
from roadsos_app.modules.location import init_location_state, render_location_sidebar
from roadsos_app.modules.ui import (
    AMBER,
    GREEN,
    RED,
    alert_banner,
    get_colors,
    get_theme,
    inject_global_css,
    markdown_to_html,
    micon,
    page_header,
    render_theme_toggle,
    sidebar_brand,
)


st.set_page_config(page_title="RoadSoS | AI Assistant", page_icon=":material/sports_motorsports:", layout="wide")
inject_global_css()
init_location_state()
sidebar_brand()
render_theme_toggle()
render_location_sidebar()

c = get_colors()
is_dark = get_theme() == "dark"


SYSTEM_PROMPT = """
You are RoadSoS AI — a road safety expert, first-aid guide, and legal advisor for road accident situations in India.
You help accident victims, bystanders, and emergency responders. You know:
- WHO and Indian Red Cross first-aid protocols for road crashes
- Indian traffic laws and rights of accident victims (Motor Vehicles Act)
- How to guide bystanders step by step in an emergency
- When to call 108 (ambulance), 100 (police), 112 (unified)
Keep answers concise, actionable, and calm. Use numbered steps for procedures.
For crash first-aid, speak to a bystander unless the user clearly says they are the rider.
Never advise moving a potentially head/spine-injured rider unless fire, traffic, water, or another immediate danger makes staying in place unsafe.
Use the rider profile, emergency contact, local numbers, and coordinates when they are available.
Do not invent consciousness, bleeding, breathing, or other clinical signs that the user did not provide; say they are unknown.
If consciousness or breathing status is not supplied, the ambulance handoff must say "consciousness unknown" and "breathing unknown".
Do not use words like unconscious, unresponsive, not breathing, or severe bleeding unless the user explicitly supplied that observation.
"""

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "openrouter/auto"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"


def render_user(message: str) -> None:
    bg = "#1A0808" if is_dark else "#FFF5F5"
    border = RED + "44"
    st.markdown(
        f"""
<div style="display:flex;justify-content:flex-end;margin:10px 0;">
  <div style="background:{bg};border:1px solid {border};color:{c["TEXT"]};padding:12px 18px;border-radius:2px;
       max-width:70%;font-size:0.9rem;font-family:'Inter';line-height:1.6;position:relative;">
    <div style="position:absolute;top:-1px;right:-1px;width:6px;height:6px;background:{RED};"></div>
    {markdown_to_html(message)}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_ai(message: str) -> None:
    st.markdown(
        f"""
<div style="display:flex;gap:12px;margin:10px 0;align-items:flex-start;">
  <div style="background:{GREEN};color:#000000;border-radius:50%;width:34px;height:34px;display:flex;
       align-items:center;justify-content:center;flex-shrink:0;">{micon("smart_toy", size=19, color="#000000", fill=True)}</div>
  <div style="background:{c["CARD_BG"]};border:1px solid {c["BORDER"]};border-left:3px solid {GREEN};
       padding:12px 18px;border-radius:2px;max-width:75%;font-size:0.9rem;
       color:{c["TEXT"]};line-height:1.6;font-family:'Inter';position:relative;overflow:hidden;">
    <div style="position:absolute;top:-1px;right:-1px;width:6px;height:6px;background:{GREEN};"></div>
    {markdown_to_html(message)}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def get_anthropic_client():
    try:
        import anthropic
    except ImportError:
        return None, "The anthropic package is not installed. Run pip install -r roadsos_app/requirements.txt."

    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        return None, "ANTHROPIC_API_KEY is missing from .streamlit/secrets.toml."
    return anthropic.Anthropic(api_key=api_key), None


def ask_claude() -> str:
    client, error = get_anthropic_client()
    if error:
        return (
            f"{error}\n\n"
            "Emergency fallback: call 112 immediately for serious crashes. Do not move the rider unless the scene is unsafe."
        )

    try:
        system_prompt = f"{SYSTEM_PROMPT}\n\n{build_incident_context()}"
        with client.messages.stream(
            model=DEFAULT_ANTHROPIC_MODEL,
            max_tokens=512,
            system=system_prompt,
            messages=st.session_state.messages,
        ) as stream:
            return st.write_stream(stream.text_stream)
    except Exception as exc:
        return (
            f"RoadSoS AI could not reach Claude: {exc}\n\n"
            "1. Call 112 or the local ambulance number immediately.\n"
            "2. Do not move the rider unless the scene is unsafe.\n"
            "3. Check breathing and severe bleeding.\n"
            "4. Keep the rider warm and still.\n"
            "5. Share GPS location and medical details with responders."
        )


def get_openrouter_config() -> tuple[str | None, str, str | None]:
    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        model = st.secrets.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
    except Exception:
        api_key = None
        model = DEFAULT_OPENROUTER_MODEL
    if not api_key:
        return None, model, "OPENROUTER_API_KEY is missing from .streamlit/secrets.toml."
    return api_key, model, None


def ask_openrouter() -> str:
    api_key, model, error = get_openrouter_config()
    if error:
        return (
            f"{error}\n\n"
            "Emergency fallback: call 112 immediately for serious crashes. Do not move the rider unless the scene is unsafe."
        )

    try:
        import json as _json
        system_prompt = f"{SYSTEM_PROMPT}\n\n{build_incident_context()}"

        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://roadsos.local",
                "X-Title": "RoadSoS",
            },
            json={
                "model": model,
                "messages": [{"role": "system", "content": system_prompt}, *st.session_state.messages],
                "max_tokens": 600,
                "stream": True,
            },
            stream=True,
            timeout=(6, 60),
        )
        response.raise_for_status()

        def _token_stream():
            for raw_line in response.iter_lines():
                if not raw_line:
                    continue
                line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = _json.loads(payload)
                    delta = chunk["choices"][0].get("delta", {})
                    token = delta.get("content") or ""
                    if token:
                        yield token
                except Exception:
                    continue

        return st.write_stream(_token_stream())
    except Exception as exc:
        return (
            f"RoadSoS AI could not reach OpenRouter: {exc}\n\n"
            "1. Call 112 or the local ambulance number immediately.\n"
            "2. Do not move the rider unless the scene is unsafe.\n"
            "3. Check breathing and severe bleeding.\n"
            "4. Keep the rider warm and still.\n"
            "5. Share GPS location and medical details with responders."
        )


def ask_ai(provider: str) -> str:
    if provider == "OpenRouter":
        return ask_openrouter()
    return ask_claude()


def provider_options() -> list[str]:
    """Order providers so one with a configured key is selected by default."""
    configured: list[str] = []
    others: list[str] = []
    for name, secret_key in (("OpenRouter", "OPENROUTER_API_KEY"), ("Claude", "ANTHROPIC_API_KEY")):
        try:
            has_key = bool(st.secrets.get(secret_key))
        except Exception:
            has_key = False
        (configured if has_key else others).append(name)
    return configured + others


with st.sidebar:
    ai_provider = st.selectbox("AI Provider", provider_options())

provider_badge = ai_provider
page_header("RoadSoS AI Assistant", "Road safety expert · First-aid guide · Legal advisor", f"Powered by {provider_badge}", AMBER, icon="smart_toy")

if "messages" not in st.session_state:
    st.session_state.messages = []

if ai_provider == "OpenRouter":
    _, _, setup_error = get_openrouter_config()
else:
    client, setup_error = get_anthropic_client()
    del client
if setup_error:
    alert_banner("warning", setup_error)

if not st.session_state.messages:
    prompt_cols = st.columns(4)
    suggestions = [
        "What do I do if I witness an accident?",
        "Signs of internal bleeding?",
        "Can police refuse to help?",
        "How to stabilize a crash victim?",
    ]
    for idx, suggestion in enumerate(suggestions):
        with prompt_cols[idx]:
            if st.button(suggestion, key=f"suggestion_{idx}", use_container_width=True):
                st.session_state.pending_prompt = suggestion

chat_html = f"""
<div class="saas-card" style="min-height:360px; margin-top:1.2rem; display:flex; flex-direction:column; gap:16px; position:relative; overflow:hidden;">
  <div class="saas-card-accent" style="background:{GREEN} !important;"></div>
"""

if not st.session_state.messages:
    chat_html += f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; flex:1; min-height:300px; color:{c["MUTED"]}; font-family:'Inter'; font-size:0.9rem;">
        <span style="margin-bottom:1rem;">{micon("smart_toy", size=52, color=GREEN, fill=True)}</span>
        <span style="font-family:'Outfit'; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:{c["TEXT"]};">RoadSoS AI Active</span>
        <span style="margin-top:0.4rem; opacity:0.8;">No messages yet. Ask a question or click one of the suggestions below to start!</span>
    </div>
    """
else:
    for message in st.session_state.messages:
        if message["role"] == "user":
            bg = "#1A0808" if is_dark else "#FFF5F5"
            border = RED + "44"
            chat_html += f"""
            <div style="display:flex; justify-content:flex-end; margin:5px 0;">
              <div style="background:{bg}; border:1px solid {border}; color:{c["TEXT"]}; padding:12px 18px; border-radius:8px;
                   max-width:70%; font-size:0.9rem; font-family:'Inter'; line-height:1.6; position:relative;">
                <div style="position:absolute; top:-1px; right:-1px; width:6px; height:6px; background:{RED};"></div>
                {markdown_to_html(message["content"])}
              </div>
            </div>
            """
        else:
            chat_html += f"""
            <div style="display:flex; gap:12px; margin:5px 0; align-items:flex-start;">
              <div style="background:{GREEN}; color:#000000; border-radius:50%; width:34px; height:34px; display:flex;
                   align-items:center; justify-content:center; flex-shrink:0;">{micon("smart_toy", size=19, color="#000000", fill=True)}</div>
              <div style="background:{c["PAGE_BG"]}; border:1px solid {c["BORDER"]}; border-left:3px solid {GREEN};
                   padding:12px 18px; border-radius:8px; max-width:75%; font-size:0.9rem;
                   color:{c["TEXT"]}; line-height:1.6; font-family:'Inter'; position:relative; overflow:hidden;">
                <div style="position:absolute; top:-1px; right:-1px; width:6px; height:6px; background:{GREEN};"></div>
                {markdown_to_html(message["content"])}
              </div>
            </div>
            """
chat_html += "</div>"
st.html(chat_html)

incoming = st.chat_input("Ask about first aid, legal rights, emergency procedures...")
if not incoming and st.session_state.get("pending_prompt"):
    incoming = st.session_state.pop("pending_prompt")

if incoming:
    st.session_state.messages.append({"role": "user", "content": incoming})
    render_user(incoming)
    response = ask_ai(ai_provider)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
