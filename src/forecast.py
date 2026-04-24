import pandas as pd
import numpy as np
import streamlit as st
import sqlite3
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from src.queries import run_query

def get_monthly_revenue_ts(db_path):
    q = """
    SELECT strftime('%Y-%m-01', _date) as ds, SUM(_revenue) as y
    FROM facts WHERE _date IS NOT NULL
    GROUP BY 1 ORDER BY 1
    """
    df = run_query(db_path, q)
    df["ds"] = pd.to_datetime(df["ds"])
    return df

def create_xgb_features(df):
    d = df.copy()
    d['month'] = d['ds'].dt.month
    d['quarter'] = d['ds'].dt.quarter
    d['is_q4'] = (d['quarter'] == 4).astype(int)
    d['lag_1'] = d['y'].shift(1)
    d['lag_2'] = d['y'].shift(2)
    d['lag_3'] = d['y'].shift(3)
    d['rolling_mean_3'] = d['y'].rolling(window=3).mean()
    d['rolling_std_3'] = d['y'].rolling(window=3).std()
    d['growth_rate'] = (d['y'] - d['lag_1']) / (d['lag_1'] + 1e-5)
    return d.dropna()

@st.cache_resource
def train_evaluate_models(db_path):
    df = get_monthly_revenue_ts(db_path)
    if len(df) < 12:
        return None, None, None, {"error": "Insufficient data"}
    
    metrics = {"Prophet": {}, "XGBoost": {}}
    try:
        train_size = int(len(df) * 0.8)
        train_df, test_df = df.iloc[:train_size], df.iloc[train_size:]
        
        from prophet import Prophet
        m_eval = Prophet(yearly_seasonality=True)
        m_eval.fit(train_df)
        forecast_eval = m_eval.predict(test_df[['ds']])
        
        metrics["Prophet"]["MAE"] = mean_absolute_error(test_df['y'], forecast_eval['yhat'])
        metrics["Prophet"]["MAPE"] = mean_absolute_percentage_error(test_df['y'], forecast_eval['yhat'])
        metrics["Prophet"]["RMSE"] = mean_squared_error(test_df['y'], forecast_eval['yhat'], squared=False)
    except Exception as e:
        pass

    try:
        xgb_df = create_xgb_features(df)
        if len(xgb_df) > 5:
            X = xgb_df.drop(columns=['ds', 'y'])
            y = xgb_df['y']
            
            xgb = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
            xgb.fit(X, y)
            
            train_size_xgb = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:train_size_xgb], X.iloc[train_size_xgb:]
            y_train, y_test = y.iloc[:train_size_xgb], y.iloc[train_size_xgb:]
            xgb_eval = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
            xgb_eval.fit(X_train, y_train)
            preds = xgb_eval.predict(X_test)
            
            metrics["XGBoost"]["MAE"] = mean_absolute_error(y_test, preds)
            metrics["XGBoost"]["MAPE"] = mean_absolute_percentage_error(y_test, preds)
            metrics["XGBoost"]["RMSE"] = mean_squared_error(y_test, preds, squared=False)
    except Exception:
        pass

    try:
        from prophet import Prophet
        m_final = Prophet(yearly_seasonality=True)
        m_final.fit(df)
    except Exception as e:
        m_final = None
        
    xgb_final = None
    xgb_df_final = create_xgb_features(df)
    if len(xgb_df_final) > 5:
         xgb_final = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
         xgb_final.fit(xgb_df_final.drop(columns=['ds', 'y']), xgb_df_final['y'])

    return m_final, xgb_final, xgb_df_final, metrics

def forecast_future_prophet(model, months):
    future = model.make_future_dataframe(periods=months, freq='MS')
    forecast = model.predict(future)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(months)

def forecast_future_xgboost(model, feature_df, months):
    last_known = feature_df.iloc[-1].copy()
    forecasts = []
    current_date = last_known['ds']
    current_y = last_known['y']
    
    lag_1, lag_2, lag_3 = current_y, last_known['lag_1'], last_known['lag_2']
    
    for _ in range(months):
        next_month = current_date + pd.DateOffset(months=1)
        row = pd.DataFrame([{
            'month': next_month.month,
            'quarter': next_month.quarter,
            'is_q4': 1 if next_month.quarter == 4 else 0,
            'lag_1': lag_1,
            'lag_2': lag_2,
            'lag_3': lag_3,
            'rolling_mean_3': np.mean([lag_1, lag_2, lag_3]),
            'rolling_std_3': np.std([lag_1, lag_2, lag_3]),
            'growth_rate': (lag_1 - lag_2) / (lag_2 + 1e-5)
        }])
        pred = model.predict(row)[0]
        forecasts.append({'ds': next_month, 'yhat': pred, 'yhat_lower': pred * 0.85, 'yhat_upper': pred * 1.15})
        
        lag_3, lag_2, lag_1 = lag_2, lag_1, pred
        current_date = next_month
        
    return pd.DataFrame(forecasts)
    
def get_feature_importance(model, feature_names):
    imp = pd.DataFrame({'feature': feature_names, 'importance': model.feature_importances_})
    return imp.sort_values('importance', ascending=False)
