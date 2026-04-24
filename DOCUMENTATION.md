# RetailPulse: Complete Project Documentation

## 1. Executive Summary

**RetailPulse** is a production-grade, dynamic sales analytics web application built entirely in Python using the **Streamlit** framework. It acts as an automated Data Analyst, transforming raw CSV sales or transactional data into interactive, deeply analytical dashboards.

**What it does:** 
It allows a user to upload *any* raw transactional dataset (e.g., e-commerce orders, retail store sales). It intelligently guesses the semantic meaning of the columns (which one is a date? revenue? customer ID?) and provides a UI for the user to confirm. Once confirmed, it ingests this data into an optimized embedded SQLite database, runs complex SQL queries to calculate metrics, and renders beautiful, state-of-the-art Plotly charts across multiple curated dashboards (Overview, Regional, Products, Customers). It also includes a Machine Learning engine to forecast future revenue.

**Why it's unique:** 
Instead of being hardcoded to a specific dataset (like the classic Superstore dataset), RetailPulse uses a strict `col_map` pattern to dynamically generate SQL. If a user uploads a dataset lacking "Region" data, the app intelligently adapts by locking the Regional dashboard but continuing to function perfectly everywhere else.

---

## 2. Architecture & Data Flow (How It Works)

RetailPulse follows a multi-tier, modular architecture to ensure scalability, caching, and clean code separation. 

### Step-by-Step Data Flow:
1. **Upload Phase (`src/uploader.py`):** The user provides a CSV. Pandas temporarily loads this file into memory. A smart heuristic engine analyses column names and data types (e.g., looking for the word "date", checking if numeric columns are continuous or categorical) to auto-propose mappings.
2. **Column Mapping:** The user reviews and finalizes the mapping. The mapping links the app's internal semantic variables (e.g., `_date`, `_revenue`, `_profit`) to the user's actual column names.
3. **ETL & SQLite Ingestion (`src/ingest.py`):** Once mapped, the raw DataFrame is renamed, type-casted securely (dates to ISO strings, strings to standard categories), and dumped into a highly optimized SQLite database file (`retailpulse.db`) inside a table called `facts`. Indexes are placed on crucial filtering columns (Date, Category, Region) for blazing-fast query resolution.
4. **Dynamic SQL Querying (`src/queries.py`):** The app never touches the raw Pandas DataFrame for heavy lifting. Instead, when a page loads, it builds abstract SQL text based on the `col_map` and pushes the computation down to the SQLite engine. Streamlit's `@st.cache_data` caches the result sets so switching between pages is instantaneous.
5. **Visualization (`app/pages/`):** Streamlit consumes these curated, aggregated data chunks from SQLite and paints responsive Plotly charts on top of a custom, fully-styled CSS framework ("Dark Luxury Analytics" theme).

---

## 3. Core Modules Overview 

### `app/main.py`
The gateway to the application. It handles routing and checking `st.session_state`. If raw data is not mapped, it prompts the user with the Dropzone and Mapping UI. If data *is* mapped, it forcefully routes the user to the `Overview` page.

### `app/pages/` (The UI Views)
*   **`1_overview.py`**: A macro-level dashboard showing total business health—Key Performance Indicators (KPIs), Time Series trends, and top-level AI insights.
*   **`2_regional.py`**: A breakdown of geographic performance using Plotly Choropleth Maps and heatmaps.
*   **`3_products.py`**: An item-level profitability layout displaying Pareto curves (80/20 rule) and Category Profit Margins.
*   **`4_customers.py`**: Tracks Unique Customers, Customer Lifetime Value (CLTV), Cohort Retention, and spending segments.
*   **`5_forecast.py`**: The Machine Learning view. Attempts to fit an XGBoost or Facebook Prophet model to historical data to predict 3 to 12 months into the future.

### `src/` (The Business Logic)
*   `queries.py`: Holds all dynamic SQL logic. E.g., `SELECT DATE, SUM(Revenue) FROM facts...` 
*   `analysis.py`: Handles pure statistical operations (Z-Score Outlier detection, Pearson Correlation Matrices).
*   `forecast.py`: ML pipeline handling feature engineering, model training, Time Series validation, and prediction data frame creation.
*   `utils.py`: Contains formatting helpers (currency formatters) and the massive CSS injection block for the dark theme.
*   `insights.py`: A dual-engine (Rule-Based + AI LLM-Based) script that reads the aggregated stats and dynamically outputs text observations (e.g., "Revenue grew 10% this month").

---

## 4. Theoretical Foundations

RetailPulse isn't just a UI; it relies on heavily established data science and business analytics theories to provide its value. 

### A. The Pareto Principle (80/20 Rule)
**Location:** `Products Page`
**Theory:** The Pareto principle states that for many outcomes, roughly 80% of consequences come from 20% of the causes. In retail, 80% of revenue usually comes from 20% of the catalog. 
**Implementation:** The app calculates the cumulative sum of revenue per product. It plots a dual-axis chart mapping individual product revenue (bars) against the cumulative percentage of total revenue (line). This instantly reveals the "hero" products versus the "long tail" dead weight.

### B. Customer Lifetime Value (CLTV) & Cohort Analysis
**Location:** `Customers Page`
**Theory:** CLTV is a metric that estimates the total profit/revenue a business can expect from a single customer account throughout their relationship. Cohort Analysis groups customers by their acquisition date (e.g., "The March 2024 cohort") and tracks how many of them return in subsequent months to measure loyalty and churn.
**Implementation:** The app groups unique customer IDs, maps their longest date spans (Tenure), and averages their order values. Although simplified compared to a massive probabilistic model like "Buy 'Til You Die", it provides actionable segmentation (Whales vs. Churned). 

### C. Time Series Forecasting (XGBoost vs. Prophet)
**Location:** `Forecast Page`
**Theory:** Predicting the future requires decomposing the past into mathematically understandable parts: **Trend** (is the business growing?), **Seasonality** (do sales spike in November?), **Cyclicality**, and **Noise**.
*   **Prophet (Facebook):** An additive regression model. It is mathematically built to be highly robust to missing data and shifts in the trend, and it naturally models yearly and weekly seasonality using Fourier series. Prophet is a *Generalized Additive Model* (GAM).
*   **XGBoost (Extreme Gradient Boosting):** A decision-tree-based ensemble Machine Learning algorithm. It doesn't inherently understand "time". Instead, RetailPulse implements *Feature Engineering* via `forecast.py`. It creates columns for "1-month lag", "3-month rolling mean", "Month of Year", and "Growth Rate". By feeding these temporal snapshots into XGBoost, it learns the non-linear relationship of how previous months influence the next month.
**Implementation:** RetailPulse trains both simultaneously using an 80/20 Time Series Split, calculates the Mean Absolute Error (MAE), and runs a fallback mechanism. If Prophet crashes (e.g. C++ backend issues), the app gracefully defaults to the feature-engineered XGBoost pipeline.

### D. Centralized Data Architecture (OLAP Database Theory)
**Location:** `ingest.py` & `queries.py`
**Theory:** Running `.groupby()` operations on a raw 500MB Pandas CSV file in memory every time a user clicks a button will crash the server. Online Analytical Processing (OLAP) relies on indexed database schemas to resolve math quickly.
**Implementation:** By pushing the data into SQLite and using SQL `GROUP BY` and `INDEXES`, the app shifts the computational complexity from Python memory to a native C-engine database. The result is instant dashboard interactivity regardless of row count.

---

## 5. Security & Deployment Notes

*   **Temporary Data:** Uploads are currently scoped to the Streamlit `session_state` and a local SQLite file. For a true multi-tenant cloud deployment, the DB path logic must be isolated per session ID to prevent users from querying each other's data.
*   **API Security:** The AI insights require Anthropic's `claude-sonnet` API key. This is safely managed via secrets injection or environmental variables rather than hardcoded logic.

## 6. Setup & Execution

1. Ensure Python 3.9+ is installed.
2. `pip install -r requirements.txt` (Installs Streamlit, Pandas, Plotly, XGBoost, Prophet).
3. `python -m streamlit run app/main.py`
4. Access the web app via `http://localhost:8501`.
