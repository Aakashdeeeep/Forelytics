import sqlite3
import pandas as pd
import streamlit as st
import datetime

@st.cache_resource
def get_connection(db_path):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

def ingest_to_sqlite(df, col_map, db_path):
    conn = get_connection(db_path)
    
    df_ingest = df.copy()
    if col_map.get("_date"):
        df_ingest[col_map["_date"]] = pd.to_datetime(df_ingest[col_map["_date"]], format='mixed', errors='coerce')
    
    rename_dict = {}
    for col in df_ingest.columns:
        rename_dict[col] = f"_raw_{col}"
    df_ingest = df_ingest.rename(columns=rename_dict)
    
    indexes_to_create = []
    for std_name, orig_name in col_map.items():
        if orig_name and pd.notna(orig_name):
            df_ingest[std_name] = df_ingest[f"_raw_{orig_name}"]
            if std_name in ["_date", "_category", "_region", "_segment"]:
                indexes_to_create.append(std_name)
    
    if "_date" in df_ingest.columns:
        df_ingest["_date"] = df_ingest["_date"].dt.strftime('%Y-%m-%d %H:%M:%S')
        
    df_ingest.to_sql("facts", conn, if_exists="replace", index=False)
    
    cursor = conn.cursor()
    for col in indexes_to_create:
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{col} ON facts ({col})")
    conn.commit()
    
    row_count = len(df_ingest)
    table_schema = df_ingest.columns.tolist()
    ingest_timestamp = datetime.datetime.now().isoformat()
    
    return row_count, table_schema, ingest_timestamp
