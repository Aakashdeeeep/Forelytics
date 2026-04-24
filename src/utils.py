import streamlit as st
import pandas as pd

COLOR_PALETTE = ["#00D4AA", "#F59E0B", "#6366F1", "#F43F5E", "#10B981", "#8B5CF6"]

def format_currency(value):
    if value is None or pd.isna(value):
        return "$0.00"
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value/1_000:.2f}K"
    return f"${value:.2f}"

def format_pct(value):
    if value is None or pd.isna(value):
        return "0.0%"
    return f"{value * 100:.1f}%"

def format_number(value):
    if value is None or pd.isna(value):
        return "0"
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value/1_000:.2f}K"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value)}"
        return f"{value:.2f}"
    return str(value)

def get_delta_color(value):
    if value is None or pd.isna(value):
        return "off"
    if value > 0:
        return "normal"
    elif value < 0:
        return "inverse"
    return "off"

def apply_custom_theme():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.markdown("<style>/* CSS Not found */</style>", unsafe_allow_html=True)
