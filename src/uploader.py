import pandas as pd
import streamlit as st
import numpy as np

def detect_columns(df):
    date_cols = []
    numeric_cols = []
    categorical_cols = []
    text_cols = []
    id_cols = []
    
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
        elif df[col].dtype == 'object':
            try:
                # Fast parse attempt
                pd.to_datetime(df[col].dropna().head(10), format='mixed', errors='raise')
                date_cols.append(col)
            except (ValueError, TypeError):
                pass
                
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
            
        if df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(df[col]):
            n_unique = df[col].nunique()
            if n_unique == len(df):
                id_cols.append(col)
            elif n_unique < 50:
                categorical_cols.append(col)
            else:
                text_cols.append(col)
                
    return {
        "date_cols": date_cols,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "text_cols": text_cols,
        "id_cols": id_cols
    }

def show_mapping_ui(df, detected):
    st.subheader("Map Your Data Columns")
    
    with st.form("column_mapping"):
        col1, col2 = st.columns(2)
        
        with col1:
            date_col = st.selectbox("Date column*", ["None"] + detected["date_cols"], 
                                    index=1 if detected["date_cols"] else 0)
            revenue_col = st.selectbox("Revenue column*", ["None"] + detected["numeric_cols"],
                                       index=1 if detected["numeric_cols"] else 0)
            profit_col = st.selectbox("Profit column", ["None"] + detected["numeric_cols"],
                                      index=2 if len(detected["numeric_cols"]) > 1 else 0)
            quantity_col = st.selectbox("Quantity column", ["None"] + detected["numeric_cols"],
                                      index=3 if len(detected["numeric_cols"]) > 2 else 0)
            discount_col = st.selectbox("Discount column", ["None"] + detected["numeric_cols"])
            
        with col2:
            cat_opts = ["None"] + detected["categorical_cols"] + detected["text_cols"]
            category_col = st.selectbox("Category column", cat_opts, index=1 if len(cat_opts) > 1 else 0)
            sub_category_col = st.selectbox("Sub-category column", cat_opts, index=2 if len(cat_opts) > 2 else 0)
            region_col = st.selectbox("Region/Location col", cat_opts)
            
            text_id_opts = ["None"] + detected["text_cols"] + detected["id_cols"] + detected["categorical_cols"]
            product_col = st.selectbox("Product Name column", text_id_opts)
            customer_col = st.selectbox("Customer ID column", text_id_opts)
            segment_col = st.selectbox("Customer Segment", cat_opts)
            
        st.markdown("### Data Preview")
        st.dataframe(df.head(5), use_container_width=True)
            
        submitted = st.form_submit_button("Confirm & Analyse →", type="primary")
        if submitted:
            if date_col == "None" or revenue_col == "None":
                st.error("Your CSV needs at least one date column and one revenue (numeric) column.")
                return None
                
            col_map = {
                "_date": date_col,
                "_revenue": revenue_col,
                "_profit": profit_col if profit_col != "None" else None,
                "_quantity": quantity_col if quantity_col != "None" else None,
                "_discount": discount_col if discount_col != "None" else None,
                "_category": category_col if category_col != "None" else None,
                "_subcategory": sub_category_col if sub_category_col != "None" else None,
                "_region": region_col if region_col != "None" else None,
                "_product": product_col if product_col != "None" else None,
                "_customer_id": customer_col if customer_col != "None" else None,
                "_segment": segment_col if segment_col != "None" else None
            }
            return col_map
    return None
