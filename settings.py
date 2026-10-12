"""Server-only configuration from environment variables or Streamlit secrets."""
import os


def setting(name, default=None):
    value = os.getenv(name)
    if value is not None:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        return default


def positive_int(name, default):
    value = int(setting(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return value


def enabled(name, default=False):
    return str(setting(name, default)).lower() in {"true", "1", "yes"}
