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
from src.queries import summary_stats, monthly_revenue_mom, revenue_by_category, revenue_by_region, pareto_analysis
from src.insights import generate_rule_insights, generate_ai_insights

st.set_page_config(page_title="Overview - RetailPulse", page_icon="📊", layout="wide")
apply_custom_theme()

if 'df' not in st.session_state or st.session_state.df is None or 'col_map' not in st.session_state or st.session_state.col_map is None:
    st.switch_page("main.py")
    st.stop()

col_map = st.session_state.col_map
db_path = getattr(st.session_state, 'db_path', None)
if not db_path:
    st.switch_page('main.py')
    st.stop()

st.sidebar.title(f"RetailPulse | {st.session_state.dataset_name}")
if st.sidebar.button("Upload new dataset"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("main.py")

mapped_count = sum(1 for v in col_map.values() if v is not None)
st.sidebar.caption(f"Data Quality: {mapped_count}/{len(col_map)} columns mapped")

st.markdown(f"<h2>{st.session_state.dataset_name} — Overview</h2>", unsafe_allow_html=True)

stats = summary_stats(db_path, col_map)
if not stats.empty:
    s = stats.iloc[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: st.metric("Total Revenue", format_currency(s['total_revenue']))
    if col_map.get('_profit'):
        with c2: st.metric("Total Profit", format_currency(s['total_profit']))
        if s['total_revenue'] and s['total_revenue'] != 0:
             with c3: st.metric("Profit Margin %", format_pct(s['total_profit'] / s['total_revenue']))
    with c4: st.metric("Total Records", format_number(s['total_orders']))
    with c5: st.metric("Avg Value", format_currency(s['avg_order_value']))
    with c6: st.metric("Date Range", f"{str(s['min_date'])[:10]} to {str(s['max_date'])[:10]}")

st.markdown("---")

mom_df = monthly_revenue_mom(db_path, col_map)
if not mom_df.empty:
    fig1 = px.line(mom_df, x="month", y="revenue", title="Monthly Revenue Trend", template="plotly_dark", color_discrete_sequence=["#00D4AA"])
    fig1.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827")
    st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

c_left, c_right = st.columns(2)
cat_df = revenue_by_category(db_path, col_map)

with c_left:
    if cat_df is not None and not cat_df.empty:
        fig_cat = px.bar(cat_df.head(10), x="_category", y="revenue", title="Revenue by Category", template="plotly_dark", color_discrete_sequence=["#F59E0B"])
        fig_cat.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827")
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("Category column not mapped")

with c_right:
    if cat_df is not None and not cat_df.empty and col_map.get('_profit'):
        fig_mar = px.bar(cat_df.head(10), x="_category", y=["revenue", "profit"], barmode="group", title="Revenue vs Profit", template="plotly_dark", color_discrete_sequence=["#00D4AA", "#F43F5E"])
        fig_mar.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827")
        st.plotly_chart(fig_mar, use_container_width=True)
    else:
         st.info("Profit or Category column not mapped")

st.markdown("---")
st.subheader("Insights")
insight_mode = st.radio("Mode", ["Rule-based", "AI-powered"], horizontal=True)

if insight_mode == "Rule-based":
    queries = {"mom": mom_df, "category": cat_df, "pareto": pareto_analysis(db_path, col_map)}
    ins = generate_rule_insights(st.session_state.df, col_map, queries)
    for i in ins:
        st.markdown(f"<div class='insight-card {i['type']}'><b>{i['icon']}</b> {i['text']}</div>", unsafe_allow_html=True)
else:
    s_text = f"Records: {stats.iloc[0]['total_orders']}, Revenue: {stats.iloc[0]['total_revenue']}, Date Range: {stats.iloc[0]['min_date']} to {stats.iloc[0]['max_date']}"
    ins = generate_ai_insights(s_text)
    for i in ins:
        st.markdown(f"<div class='insight-card {i['type']}'><b>{i['icon']}</b> {i['text']} <span style='float:right;font-size:0.8em;color:#00D4AA'>Powered by AI</span></div>", unsafe_allow_html=True)

with st.expander("View Raw Data"):
    st.dataframe(st.session_state.df.head(100))
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="data.csv")
