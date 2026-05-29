# 🇮🇪 Ireland Agricultural Analytics Dashboard

**CCT College Dublin · MSc Data Analytics · 2026**

An interactive Streamlit dashboard analysing Irish agricultural data (2010–2023)
sourced from FAOSTAT, comparing Ireland against France and Germany.

## Features
- KPI Summary Cards
- Crop Production Trends (interactive, filterable)
- Livestock Stocks (Cattle, Sheep, Pigs, Chickens)
- Pesticide Usage (Volume & Intensity)
- Agricultural Trade Analysis
- ARIMA 5-Year Forecast (2024–2028)
- ML Model Performance (Linear Regression, Random Forest, Gradient Boosting)
- Sentiment Analysis of News Headlines
- Normalised Indicator Heatmap
- Full Data Table with search
- Evidence-Based Policy Recommendations

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud (Free)

1. Push this folder to a **public GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **New app** → select your repo → set `app.py` as the main file
5. Click **Deploy** — you'll get a public link like:
   `https://your-app-name.streamlit.app`

## Data Source
FAOSTAT — Food and Agriculture Organization of the United Nations
License: CC BY-NC-SA 3.0 IGO
