import sqlite3
import datetime
import streamlit as st
import pandas as pd
import sys
import os
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.utils import apply_custom_theme, format_currency
from src.ingest import get_connection
from src.queries import run_query
from src.forecast import train_evaluate_models, forecast_future_prophet, forecast_future_xgboost, get_feature_importance

st.set_page_config(page_title="Forecast - RetailPulse", page_icon="🔮", layout="wide")
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

st.markdown(f"<h2>{st.session_state.dataset_name} — ML Revenue Forecasting</h2>", unsafe_allow_html=True)

if not col_map.get("_date") or not col_map.get("_revenue"):
    st.warning("Date and Revenue required for forecasting.")
    st.stop()

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    model_choice = st.radio("Model", ["Prophet (Best for Seasonality)", "XGBoost (Best for Trends)"])
with c2:
    horizon = st.select_slider("Forecast Horizon (Months)", options=[3, 6, 12], value=6)
with c3:
    st.write("")
    st.write("")
    generate = st.button("Generate Forecast", type="primary", use_container_width=True)

if check_run := generate or 'forecast_result' in st.session_state:
    if generate:
        with st.spinner("Training models & evaluating..."):
            m_prophet, m_xgb, xgb_df, metrics_eval = train_evaluate_models(db_path)
            if m_prophet is None and m_xgb is None:
                st.error("Both models failed or insufficient data. Need 1+ years.")
                st.stop()
                
            st.session_state.m_prophet = m_prophet
            st.session_state.m_xgb = m_xgb
            st.session_state.xgb_df = xgb_df
            st.session_state.metrics_eval = metrics_eval
            st.session_state.forecast_result = True
            st.toast("Forecasting complete!")

    m_prophet = st.session_state.get('m_prophet')
    m_xgb = st.session_state.get('m_xgb')
    metrics_eval = st.session_state.get('metrics_eval')
    xgb_df = st.session_state.get('xgb_df')

    recent_sql = "SELECT strftime('%Y-%m-01', _date) as ds, SUM(_revenue) as y FROM facts WHERE _date IS NOT NULL GROUP BY 1 ORDER BY 1"
    historical = run_query(db_path, recent_sql)
    historical['ds'] = pd.to_datetime(historical['ds'])

    if "Prophet" in model_choice:
        if m_prophet is None:
            st.warning("Prophet failed. Falling back to XGBoost.")
            forecast = forecast_future_xgboost(m_xgb, xgb_df, horizon)
        else:
            try:
                forecast = forecast_future_prophet(m_prophet, horizon)
            except Exception as e:
                st.warning("Prophet failed during prediction. Falling back to XGBoost.")
                forecast = forecast_future_xgboost(m_xgb, xgb_df, horizon)
    else:
        if m_xgb is None:
            st.warning("XGBoost failed. Falling back to Prophet.")
            try:
                forecast = forecast_future_prophet(m_prophet, horizon)
            except Exception as e:
                st.error("Both models failed during prediction.")
                st.stop()
        else:
            forecast = forecast_future_xgboost(m_xgb, xgb_df, horizon)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historical['ds'], y=historical['y'], name="Actual", line=dict(color="#00D4AA", width=3)))
    
    fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], name="Forecast", line=dict(color="#F59E0B", width=3, dash='dash')))
    
    if "yhat_lower" in forecast.columns:
        fig.add_trace(go.Scatter(
            x=list(forecast['ds']) + list(forecast['ds'])[::-1],
            y=list(forecast['yhat_upper']) + list(forecast['yhat_lower'])[::-1],
            fill='toself',
            fillcolor='rgba(245, 158, 11, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='Confidence Interval'
        ))

    today = historical['ds'].iloc[-1]
    fig.update_layout(title="Revenue Forecast", template="plotly_dark", plot_bgcolor="#111827", paper_bgcolor="#111827")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    res_1, res_2, res_3 = st.columns(3)
    
    with res_1:
        st.subheader("Model Evaluation")
        if metrics_eval:
            metric_df = pd.DataFrame(metrics_eval).dropna(how='all').T
            st.dataframe(metric_df, use_container_width=True)
            
    with res_2:
        if "XGBoost" in model_choice and m_xgb is not None:
            st.subheader("Feature Importance")
            feat_imp = get_feature_importance(m_xgb, xgb_df.drop(columns=['ds', 'y']).columns)
            fig_imp = px.bar(feat_imp.head(5), x='importance', y='feature', orientation='h', template='plotly_dark', color_discrete_sequence=["#10B981"])
            fig_imp.update_layout(plot_bgcolor="#111827", paper_bgcolor="#111827", yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_imp, use_container_width=True)
            
    with res_3:
        st.subheader("Forecast Summary")
        next_month = forecast.iloc[0]
        st.metric("Next Month Prediction", format_currency(next_month['yhat']))
        total_pred = forecast['yhat'].sum()
        st.metric(f"{horizon}-Month Total", format_currency(total_pred))
        
    with st.expander("How does this forecast work?"):
         st.write("We use Prophet for modeling yearly seasonality and XGBoost for analyzing trends and lagged impacts. Features include recent order lags and rolling averages to simulate real-world growth.")
