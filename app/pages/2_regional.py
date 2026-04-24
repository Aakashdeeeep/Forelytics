import sqlite3
import datetime
import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.utils import apply_custom_theme, format_currency, format_pct, format_number
from src.ingest import get_connection
from src.queries import revenue_by_region

st.set_page_config(page_title="Regional - RetailPulse", page_icon="🌍", layout="wide")
apply_custom_theme()

if 'df' not in st.session_state or st.session_state.df is None or 'col_map' not in st.session_state or st.session_state.col_map is None:
    st.switch_page("main.py")
    st.stop()

col_map = st.session_state.col_map
db_path = getattr(st.session_state, 'db_path', None)
if not db_path:
    st.switch_page('main.py')
    st.stop()

if st.sidebar.button("Upload new dataset"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("main.py")

st.markdown(f"<h2>{st.session_state.dataset_name} — Regional Analysis</h2>", unsafe_allow_html=True)

if not col_map.get("_region"):
    st.warning("Map a Region column to unlock this page")
    if st.button("Re-map Columns"):
        st.session_state.pop("col_map")
        st.switch_page("main.py")
    st.stop()

reg_df = revenue_by_region(db_path, col_map)
if reg_df is None or reg_df.empty:
    st.info("No regional data available.")
    st.stop()

top_regions = reg_df.head(6)
cols = st.columns(len(top_regions))
for i, row in top_regions.iterrows():
    with cols[i]:
        st.metric(row['_region'], format_currency(row['revenue']))

st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    fig_bar = px.bar(reg_df.head(15), x="revenue", y="_region", orientation='h', title="Revenue by Region", 
                     template="plotly_dark", color_discrete_sequence=["#00D4AA"])
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor="#111827", paper_bgcolor="#111827")
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    if col_map.get('_category'):
        q = f"SELECT _region, _category, SUM(_revenue) as revenue FROM facts WHERE _region IS NOT NULL AND _category IS NOT NULL GROUP BY 1, 2"
        heat_df = run_query(db_path, q)
        heat_pivot = heat_df.pivot(index="_region", columns="_category", values="revenue").fillna(0)
        fig_heat = px.imshow(heat_pivot, aspect="auto", title="Region × Category Heatmap", template="plotly_dark", color_continuous_scale="Teal")
        fig_heat.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Map a Category column to see Regional Category Heatmap")

st.markdown("---")
st.subheader("Region Comparison")
st.dataframe(reg_df, use_container_width=True)
csv = reg_df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", data=csv, file_name="regions.csv")
