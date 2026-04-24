import sqlite3
import pandas as pd
import streamlit as st

@st.cache_data
def run_query(db_path, query):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return pd.read_sql_query(query, conn)
    return pd.read_sql_query(query, _conn)

def summary_stats(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    rev_col = "_revenue"
    prof_col = "_profit" if col_map.get("_profit") else "NULL"
    date_col = "_date"
    
    q = f"""
    SELECT 
        SUM({rev_col}) as total_revenue,
        SUM({prof_col}) as total_profit,
        COUNT(*) as total_orders,
        MIN({date_col}) as min_date,
        MAX({date_col}) as max_date,
        AVG({rev_col}) as avg_order_value
    FROM facts
    """
    return run_query(db_path, q)

def monthly_revenue_mom(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    q = """
    WITH monthly AS (
        SELECT strftime('%Y-%m', _date) as month, SUM(_revenue) as revenue
        FROM facts 
        WHERE _date IS NOT NULL
        GROUP BY 1
    )
    SELECT month, revenue,
           LAG(revenue) OVER (ORDER BY month) as prev_revenue,
           (revenue - LAG(revenue) OVER (ORDER BY month)) / NULLIF(LAG(revenue) OVER (ORDER BY month), 0) as mom_pct
    FROM monthly
    """
    return run_query(db_path, q)

def rolling_avg(db_path, col_map, window=3):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    q = f"""
    WITH monthly AS (
        SELECT strftime('%Y-%m', _date) as month, SUM(_revenue) as revenue
        FROM facts WHERE _date IS NOT NULL GROUP BY 1
    )
    SELECT month, revenue,
           AVG(revenue) OVER (ORDER BY month ROWS BETWEEN {window-1} PRECEDING AND CURRENT ROW) as rolling_avg
    FROM monthly
    """
    return run_query(db_path, q)

def top_items(db_path, col_map, col='_product', n=10):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get(col):
        return None
    prof_col = "_profit" if col_map.get('_profit') else "NULL"
    qty_col = "_quantity" if col_map.get('_quantity') else "NULL"
    q = f"""
    SELECT {col} as item, SUM(_revenue) as revenue, SUM({prof_col}) as profit, SUM({qty_col}) as quantity
    FROM facts WHERE {col} IS NOT NULL
    GROUP BY 1
    ORDER BY revenue DESC
    LIMIT {n}
    """
    return run_query(db_path, q)

def revenue_by_category(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get("_category"):
        return None
    prof_col = "_profit" if col_map.get('_profit') else "NULL"
    q = f"""
    SELECT _category, SUM(_revenue) as revenue, SUM({prof_col}) as profit
    FROM facts WHERE _category IS NOT NULL
    GROUP BY 1 ORDER BY revenue DESC
    """
    return run_query(db_path, q)

def revenue_by_region(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get("_region"):
        return None
    prof_col = "_profit" if col_map.get('_profit') else "NULL"
    qty_col = "_quantity" if col_map.get('_quantity') else "NULL"
    q = f"""
    SELECT _region, SUM(_revenue) as revenue, SUM({prof_col}) as profit, SUM({qty_col}) as orders
    FROM facts WHERE _region IS NOT NULL
    GROUP BY 1 ORDER BY revenue DESC
    """
    return run_query(db_path, q)

def discount_profit_impact(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get("_discount") or not col_map.get("_profit"):
        return None
    q = """
    SELECT _discount, AVG(_profit) as avg_profit, SUM(_revenue) as total_revenue
    FROM facts WHERE _discount IS NOT NULL
    GROUP BY 1 ORDER BY _discount
    """
    return run_query(db_path, q)

def customer_ltv(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get("_customer_id"):
        return None
    q = """
    SELECT _customer_id, MIN(_date) as first_purchase, MAX(_date) as last_purchase,
           COUNT(*) as orders, SUM(_revenue) as ltv
    FROM facts WHERE _customer_id IS NOT NULL
    GROUP BY 1 ORDER BY ltv DESC
    """
    return run_query(db_path, q)

def segment_breakdown(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get("_segment"):
        return None
    q = """
    SELECT _segment, COUNT(DISTINCT _customer_id) as customers, SUM(_revenue) as revenue
    FROM facts WHERE _segment IS NOT NULL
    GROUP BY 1 ORDER BY revenue DESC
    """
    return run_query(db_path, q)

def quarterly_yoy_growth(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    q = """
    WITH quarters AS (
        SELECT strftime('%Y', _date) || '-Q' || ((cast(strftime('%m', _date) as integer) + 2) / 3) as quarter_str,
               strftime('%Y', _date) as year,
               ((cast(strftime('%m', _date) as integer) + 2) / 3) as qtr,
               SUM(_revenue) as revenue
        FROM facts WHERE _date IS NOT NULL GROUP BY 1, 2, 3
    )
    SELECT q1.quarter_str, q1.revenue,
           q2.revenue as prev_year_revenue,
           (q1.revenue - q2.revenue) / NULLIF(q2.revenue, 0) as yoy_growth
    FROM quarters q1
    LEFT JOIN quarters q2 ON q1.year = cast(cast(q2.year as integer) + 1 as text) AND q1.qtr = q2.qtr
    ORDER BY q1.quarter_str
    """
    return run_query(db_path, q)

def pareto_analysis(db_path, col_map):
    if col_map.get('_date') is None or col_map.get('_revenue') is None:
        return None
    if not col_map.get("_product"):
        return None
    q = """
    WITH prod_rev AS (
        SELECT _product, SUM(_revenue) as revenue FROM facts WHERE _product IS NOT NULL GROUP BY 1
    ),
    ranked AS (
        SELECT _product, revenue, SUM(revenue) OVER() as total_revenue,
               SUM(revenue) OVER(ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_revenue
        FROM prod_rev
    )
    SELECT _product, revenue, running_revenue / total_revenue as cumulative_pct
    FROM ranked ORDER BY revenue DESC
    """
    return run_query(db_path, q)
