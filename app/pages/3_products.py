import sqlite3
import datetime
import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.utils import apply_custom_theme, format_currency, format_pct, format_number
from src.ingest import get_connection
from src.queries import top_items, pareto_analysis, run_query

st.set_page_config(page_title="Products - RetailPulse", page_icon="📦", layout="wide")
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

st.markdown(f"<h2>{st.session_state.dataset_name} — Products & Categories</h2>", unsafe_allow_html=True)

if not col_map.get("_product") and not col_map.get("_category"):
    st.warning("Map a Product or Category column to unlock this page")
    if st.button("Re-map Columns"):
        st.session_state.pop("col_map")
        st.switch_page("main.py")
    st.stop()

if col_map.get("_product"):
    pareto_df = pareto_analysis(db_path, col_map)
    if pareto_df is not None and not pareto_df.empty:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Unique Products", format_number(len(pareto_df)))
        
        st.markdown("---")
        
        plot_df = pareto_df.head(50)
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Bar(x=plot_df['_product'], y=plot_df['revenue'], name='Revenue', marker_color='#00D4AA'))
        fig_pareto.add_trace(go.Scatter(x=plot_df['_product'], y=plot_df['cumulative_pct']*100, name='Cumulative %', yaxis='y2', line=dict(color='#F59E0B')))
        
        fig_pareto.update_layout(
            title="Pareto Analysis (Top 50 Products)",
            template="plotly_dark",
            plot_bgcolor="#111827", paper_bgcolor="#111827",
            yaxis=dict(title="Revenue"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105])
        )
        st.plotly_chart(fig_pareto, use_container_width=True)

        st.markdown("---")
        n_slider = st.slider("Top N Products to view", 5, 50, 10)
        top_prod_df = top_items(db_path, col_map, '_product', n=n_slider)
        st.dataframe(top_prod_df, use_container_width=True)
        st.download_button("Download CSV", data=top_prod_df.to_csv(index=False).encode('utf-8'), file_name="top_products.csv")

if col_map.get("_category") and col_map.get("_profit"):
    q = "SELECT _category, SUM(_revenue) as rev, SUM(_profit) as prof FROM facts WHERE _category IS NOT NULL GROUP BY 1"
    df_cat = run_query(db_path, q)
    if not df_cat.empty:
        df_cat['margin'] = df_cat['prof'] / df_cat['rev']
        
        st.markdown("---")
        st.subheader("Category Margins")
        
        df_cat['color'] = df_cat['margin'].apply(lambda x: '#00D4AA' if x > 0 else '#F43F5E')
        fig_margin = go.Figure(go.Bar(
            x=df_cat['margin']*100, y=df_cat['_category'], orientation='h', 
            marker_color=df_cat['color']
        ))
        fig_margin.update_layout(title="Category Profit Margin %", template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827")
        st.plotly_chart(fig_margin, use_container_width=True)
