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
from src.queries import customer_ltv, segment_breakdown
from src.analysis import cohort_analysis

st.set_page_config(page_title="Customers - RetailPulse", page_icon="👥", layout="wide")
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

st.markdown(f"<h2>{st.session_state.dataset_name} — Customer Insights</h2>", unsafe_allow_html=True)

if not col_map.get("_customer_id"):
    st.warning("Map a Customer column to unlock this page")
    if st.button("Re-map Columns"):
        st.session_state.pop("col_map")
        st.switch_page("main.py")
    st.stop()

ltv_df = customer_ltv(db_path, col_map)
c1, c2, c3, c4 = st.columns(4)

with c1: st.metric("Unique Customers", format_number(len(ltv_df)))
with c2: 
    repeat_rate = len(ltv_df[ltv_df['orders'] > 1]) / len(ltv_df) if len(ltv_df) else 0
    st.metric("Repeat Rate %", format_pct(repeat_rate))
with c3: st.metric("Avg LTV", format_currency(ltv_df['ltv'].mean() if len(ltv_df) else 0))

seg_df = segment_breakdown(db_path, col_map)
with c4:
    if seg_df is not None and not seg_df.empty:
        st.metric("Top Segment", seg_df.iloc[0]['_segment'])
    else:
        st.metric("Top Segment", "N/A")

st.markdown("---")
c_left, c_right = st.columns(2)
with c_left:
    if seg_df is not None and not seg_df.empty:
        fig_seg = px.bar(seg_df, x="revenue", y="_segment", orientation='h', title="Revenue by Segment", 
                         template="plotly_dark", color_discrete_sequence=["#00D4AA"])
        fig_seg.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827", yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.info("Map a Segment column to view segmentation.")

with c_right:
    if not ltv_df.empty:
        fig_ltv = px.histogram(ltv_df, x="ltv", nbins=50, title="LTV Distribution", 
                               template="plotly_dark", color_discrete_sequence=["#6366F1"])
        fig_ltv.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827")
        st.plotly_chart(fig_ltv, use_container_width=True)

st.markdown("---")
cohort = cohort_analysis(st.session_state.df, col_map)
if cohort is not None:
    st.subheader("Cohort Retention Heatmap")
    cohort.index = cohort.index.astype(str)
    fig_cohort = px.imshow(cohort, aspect="auto", title="Cohort Retention %", 
                           template="plotly_dark", color_continuous_scale="Blues")
    fig_cohort.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827")
    st.plotly_chart(fig_cohort, use_container_width=True)
else:
    st.info("Insufficient data for cohort analysis (needs _customer_id and _date).")

st.markdown("---")
st.subheader("Top 20 Customers")
top20 = ltv_df.head(20)
st.dataframe(top20, use_container_width=True)
st.download_button("Download Top 20 Customers", data=top20.to_csv(index=False).encode(), file_name="top_customers.csv")
