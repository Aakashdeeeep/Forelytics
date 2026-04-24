import datetime
import sqlite3
import streamlit as st
import pandas as pd
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import apply_custom_theme
from src.uploader import detect_columns, show_mapping_ui
from src.ingest import ingest_to_sqlite

st.set_page_config(page_title="RetailPulse", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")
apply_custom_theme()

if 'db_path' not in st.session_state:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'retailpulse.db')
    st.session_state.db_path = DB_PATH

if 'df' not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #00D4AA; font-size: 4rem; margin-top: 5vh;'>RetailPulse</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #e2e8f0; font-size: 1.2rem; margin-bottom: 5vh;'>Upload any CSV dataset and get instant AI-powered analytics</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style='display: flex; justify-content: space-around; margin-bottom: 2rem;'>
                <span style='background: #111827; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #00D4AA; font-size: 0.9rem;'>Smart Column Detection</span>
                <span style='background: #111827; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #F59E0B; font-size: 0.9rem;'>AI Insights</span>
                <span style='background: #111827; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #6366F1; font-size: 0.9rem;'>ML Forecasting</span>
            </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Drop your dataset here", type=['csv'])
        
        if st.button("Try with sample data →", use_container_width=True):
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            DATA_PATH = os.path.join(BASE_DIR, "..", "data", "superstore.csv")
            if os.path.exists(DATA_PATH):
                st.session_state.df = pd.read_csv(DATA_PATH, encoding="latin1")
                st.session_state.dataset_name = "Superstore Sample"
                st.rerun()
            else:
                st.error("Sample dataset not found in data/ folder. Please upload a file.")
                
        if uploaded_file is not None:
            st.session_state.df = pd.read_csv(uploaded_file)
            st.session_state.dataset_name = uploaded_file.name
            st.toast(f"Successfully loaded {uploaded_file.name}")
            st.rerun()

if 'df' in st.session_state and 'col_map' not in st.session_state:
    st.markdown("---")
    df = st.session_state.df
    st.info(f"Loaded **{st.session_state.dataset_name}** | {df.shape[0]:,} rows, {df.shape[1]:,} columns")
    
    detected = detect_columns(df)
    col_map = show_mapping_ui(df, detected)
    
    if col_map:
        with st.spinner("Ingesting and optimizing data..."):
            row_count, schema, ts = ingest_to_sqlite(df, col_map, st.session_state.db_path)
            st.session_state.col_map = col_map
            st.toast("Data ingested successfully!")
            st.switch_page("pages/1_overview.py")