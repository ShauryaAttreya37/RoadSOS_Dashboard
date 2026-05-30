from __future__ import annotations

from typing import Any

import streamlit as st


def get_secret(name: str, default: Any = None) -> Any:
    """Return an optional Streamlit secret without requiring a secrets file."""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default
