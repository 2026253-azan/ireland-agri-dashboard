# 🇮🇪 Ireland Agricultural Analytics Dashboard

> **MSc Data Analytics · CCT College Dublin · 2026**

An interactive Streamlit dashboard analysing Ireland's agricultural sector using FAOSTAT data (2010–2023), benchmarked against France and Germany.

## 🔗 Live App
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

---

## 📊 Dashboard Sections

| Section | Content |
|---------|---------|
| 🏷️ KPI Cards | At-a-glance 2023 metrics |
| 🌾 Crop Trends | Ireland vs France vs Germany |
| 🐄 Livestock | Per-animal subplot |
| 🧪 Pesticides | Volume + intensity |
| ⚖️ Trade | Export/Import area chart + balance |
| 🔮 ARIMA Forecast | 5-year outlook 2024–2028 |
| 🤖 ML Comparison | Linear / RF / GB metrics |
| 💬 Sentiment | News polarity analysis |
| 🗺️ Heatmap | Normalised indicator heatmap |
| 📋 Data Table | Full Ireland panel + CSV download |

---

## 🚀 Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ireland-agri-dashboard.git
cd ireland-agri-dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

---

## 🛠️ Tech Stack
- **Python** · **Streamlit** · **Plotly**
- **scikit-learn** (Random Forest, Gradient Boosting, Linear Regression)
- **statsmodels** (ARIMA forecasting)
- **TextBlob** (sentiment analysis)

## 📦 Data
FAOSTAT — Food and Agriculture Organization of the United Nations  
License: CC BY-NC-SA 3.0 IGO

---

## 📝 Key Findings

1. **Ireland is a net agricultural exporter** — consistent trade surplus across 2010–2023
2. **Cattle dominates** Irish livestock, unlike France/Germany (poultry-heavy)
3. **Low pesticide intensity** — Ireland uses ~2.8 kg/ha vs France's ~4.8 kg/ha
4. **Exports projected to grow** through 2028 per ARIMA model
5. **Gradient Boosting outperforms** baseline ML models (R² ≈ 0.9+)

## 💡 Policy Recommendations

1. Scale up tillage crops — reduce cereal import dependency
2. Leverage livestock export advantage — cattle is Ireland's core strength
3. Maintain low pesticide use — market as sustainable/green brand
4. Invest in dairy processing — high-value dairy exports show strongest trajectory
5. CAP alignment — align with EU sustainability targets to secure future funding
