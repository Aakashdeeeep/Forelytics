# RetailPulse — Dynamic Sales Intelligence Dashboard

## Live Demo
[Streamlit Cloud URL]

## What it does
One paragraph: upload ANY CSV with sales/transactional data and instantly get
EDA, SQL analytics, statistical tests, ML forecasting, and AI-generated insights.

## Architecture
```
CSV Upload → Column Mapping → SQLite ETL → SQL Queries
                                         → Statistical Analysis
                                         → ML Forecast
                                         → Streamlit Dashboard
```

## Tech Stack table
| Tool | Purpose |
|------|---------|
| Streamlit | Web Framework & UI |
| SQLite | Embedded database for SQL analytics |
| Pandas | ETL & DataFrame manipulations |
| Prophet | ML Forecasting (Seasonal) |
| XGBoost | ML Forecasting (Tree-based) |
| Anthropic | AI Insights Generation |

## Supported CSV formats
- Any transactional/sales CSV with at least one date column and one numeric column
- Works best with: sales data, e-commerce orders, financial transactions, HR data
- Example datasets: Superstore, Online Retail UCI, Brazilian E-commerce

## Setup (5 steps)
1. git clone ...
2. pip install -r requirements.txt
3. streamlit run app/main.py
4. Upload your CSV or click "Try sample data"
5. Map your columns and explore

## Key Features
- Smart column type detection
- Dynamic SQL analytics with window functions
- Statistical hypothesis testing
- Prophet + XGBoost forecasting with comparison
- AI-powered insights via Claude API
- Works on any CSV — not just one dataset

## Skills Demonstrated
- Python, Streamlit UI/UX
- Dynamic SQL and Data Engineering
- Machine Learning models evaluation
- Statistical testing
- Prompt Engineering and GenAI
