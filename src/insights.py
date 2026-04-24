import pandas as pd
import numpy as np
import streamlit as st
import anthropic
import os
from src.utils import format_currency, format_pct

def generate_rule_insights(df, col_map, queries):
    insights = []
    if "mom" in queries and not queries["mom"].empty:
        mom = queries["mom"].iloc[-1]
        pct = mom["mom_pct"]
        if pd.notna(pct):
            if pct > 0:
                insights.append({"text": f"Revenue grew by {format_pct(pct)} month-over-month.", "type": "positive", "icon": "↑"})
            elif pct < 0:
                insights.append({"text": f"Revenue declined by {format_pct(abs(pct))} month-over-month.", "type": "negative", "icon": "↓"})
            
    if "category" in queries and not queries["category"].empty:
        top_cat = queries["category"].iloc[0]
        insights.append({"text": f"Top category is {top_cat['_category']} with {format_currency(top_cat['revenue'])} revenue.", "type": "positive", "icon": "↑"})
        
    if "pareto" in queries and not queries["pareto"].empty:
        pareto = queries["pareto"]
        p_count = len(pareto)
        p_20 = int(p_count * 0.2) or 1
        cum_rev = pareto.iloc[p_20 - 1]["cumulative_pct"]
        insights.append({"text": f"Top 20% of products drive {format_pct(cum_rev)} of total revenue.", "type": "neutral", "icon": "→"})
        
    if not insights:
        insights.append({"text": "Insufficient data to generate rule-based insights.", "type": "neutral", "icon": "→"})
        
    return insights

@st.cache_data
def generate_ai_insights(df_summary):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return [{"text": "AI Insights unavailable (requires ANTHROPIC_API_KEY). Running fallback...", "type": "neutral", "icon": "⚠"}]
        
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""You are a senior data analyst. Given this dataset summary, generate 5 specific, 
quantified business insights with actionable recommendations. Be concise. Start each with an emoji.
Dataset: {df_summary}"""
    
    try:
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text
        insights = []
        for line in text.strip().split('\n'):
            if line.strip():
                insights.append({"text": line.strip(), "type": "neutral", "icon": "✨"})
        return insights[:5]
    except Exception as e:
        return [{"text": f"AI Insights failed: {str(e)}", "type": "negative", "icon": "⚠"}]
