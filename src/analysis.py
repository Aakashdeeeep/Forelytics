import sqlite3
import pandas as pd
import numpy as np
import scipy.stats as stats
import streamlit as st

def outlier_detection(df, col_map):
    outliers = {}
    for col in ["_revenue", "_profit"]:
        if col_map.get(col) and col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(series) < 10: continue
            q1, q3 = np.percentile(series, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            outliers[col] = series[(series < lower_bound) | (series > upper_bound)].count()
    return outliers

def correlation_matrix(df, col_map):
    numeric_cols = [col for col in ["_revenue", "_profit", "_quantity", "_discount"] 
                    if col_map.get(col) and col in df.columns]
    if len(numeric_cols) > 1:
        return df[numeric_cols].apply(pd.to_numeric, errors='coerce').corr()
    return None

def discount_significance(df, col_map):
    if not col_map.get("_discount") or not col_map.get("_profit"):
        return None
    disc = pd.to_numeric(df["_discount"], errors='coerce')
    prof = pd.to_numeric(df["_profit"], errors='coerce')
    mask = disc.notna() & prof.notna()
    if sum(mask) < 10: return None
    
    no_disc = prof[mask & (disc == 0)]
    has_disc = prof[mask & (disc > 0)]
    
    if len(no_disc) > 5 and len(has_disc) > 5:
        stat, pval = stats.ttest_ind(no_disc, has_disc, equal_var=False)
        return {"t_stat": stat, "p_value": pval, "significant": pval < 0.05}
    return None

def cohort_analysis(df, col_map):
    if not col_map.get("_customer_id") or not col_map.get("_date"):
        return None
    d = df.copy()
    d["_date"] = pd.to_datetime(d["_date"], errors='coerce')
    d = d.dropna(subset=["_date", "_customer_id"])
    if len(d) == 0: return None
    
    d["CohortMonth"] = d.groupby("_customer_id")["_date"].transform("min").dt.to_period("M")
    d["OrderMonth"] = d["_date"].dt.to_period("M")
    
    d_grp = d.groupby(["CohortMonth", "OrderMonth"]).agg(n_customers=("_customer_id", "nunique")).reset_index()
    d_grp["Period"] = (d_grp.OrderMonth - d_grp.CohortMonth).apply(lambda x: x.n)
    
    cohort_pivot = d_grp.pivot_table(index="CohortMonth", columns="Period", values="n_customers")
    if not cohort_pivot.empty and 0 in cohort_pivot.columns:
        cohort_sizes = cohort_pivot.iloc[:, 0]
        retention = cohort_pivot.divide(cohort_sizes, axis=0)
        return retention
    return None

def category_seasonality(df, col_map):
    if not col_map.get("_category") or not col_map.get("_date"):
        return None
    d = df.copy()
    d["_date"] = pd.to_datetime(d["_date"], errors='coerce')
    d["month"] = d["_date"].dt.month
    cat_month = d.groupby(["_category", "month"])["_revenue"].sum().unstack()
    return cat_month
