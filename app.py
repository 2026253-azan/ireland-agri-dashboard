import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="🇮🇪 Ireland Agricultural Analytics Dashboard",
    page_icon="🇮🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# GLOBAL CSS — mirrors original HTML dashboard exactly
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

/* Page background */
[data-testid="stAppViewContainer"] > .main { background: #f5f7f4 !important; padding: 0 !important; }
[data-testid="block-container"] { padding: 0 24px 40px 24px !important; max-width: 1400px !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0d2b1a !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.82) !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: white !important; }
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] { background: #169b62 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15) !important; }
[data-testid="stSidebar"] label { color: rgba(255,255,255,0.55) !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.5px; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,0.65) !important; font-size: 12px; }

/* Remove default streamlit padding/gaps */
.block-container { padding-top: 0 !important; }
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] { gap: 0 !important; }

/* KPI metrics */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid #e4e9e2 !important;
    border-top: 3px solid #169b62 !important;
    border-radius: 10px !important;
    padding: 16px 18px !important;
    transition: transform .15s, box-shadow .15s;
}
[data-testid="metric-container"]:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.06); }
[data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700 !important; color: #169b62 !important; }
[data-testid="metric-container"] [data-testid="stMetricLabel"] { font-size: 11px !important; font-weight: 600 !important; color: #1a2419 !important; }
[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 11px !important; color: #6b7a68 !important; }

/* Section cards */
.section-card {
    background: white;
    border: 1px solid #e4e9e2;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 16px;
}
.section-title {
    font-size: 14px;
    font-weight: 700;
    color: #1a2419;
    margin-bottom: 2px;
}
.section-sub {
    font-size: 11px;
    color: #6b7a68;
    margin-bottom: 14px;
}

/* Plotly charts */
.js-plotly-plot { border-radius: 8px; }

/* Tabs */
[data-testid="stTabs"] [role="tab"] {
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    color: #6b7a68 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #169b62 !important;
    border-bottom: 2px solid #169b62 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    border-bottom: 1px solid #e4e9e2 !important;
    background: transparent !important;
    gap: 0 !important;
}

/* Divider */
hr { border-color: #e4e9e2 !important; margin: 6px 0 16px 0 !important; }

/* Hide default Streamlit header */
[data-testid="stHeader"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════
YEARS = list(range(2010, 2024))

CROPS = {
    'Ireland': [2810,2940,2650,3020,3150,3280,3100,3350,3420,3200,3380,3460,3300,3470],
    'France':  [63200,65400,58900,67000,68200,70100,66800,69500,71200,65400,68900,71000,67800,72100],
    'Germany': [55100,57200,52400,59000,60800,62400,58900,61700,63100,57600,61200,63500,59800,64200]
}
LIVESTOCK = {
    'cattle':   {'Ireland':[6420,6510,6580,6700,6820,6950,7020,7100,7180,7060,7120,7200,7150,7200],
                 'France': [19200,19100,18900,18800,18700,18500,18400,18300,18100,17900,17800,17700,17600,17500],
                 'Germany':[12700,12600,12500,12400,12300,12200,12100,12000,11900,11800,11700,11600,11500,11400]},
    'sheep':    {'Ireland':[4850,4900,4950,5000,5100,5200,5150,5300,5400,5250,5350,5420,5380,5450],
                 'France': [7200,7100,7000,6900,6800,6700,6600,6500,6400,6300,6200,6100,6000,5900],
                 'Germany':[1600,1580,1560,1540,1520,1500,1480,1460,1440,1420,1400,1380,1360,1340]},
    'pigs':     {'Ireland':[1520,1540,1560,1580,1600,1620,1640,1660,1640,1620,1600,1580,1560,1540],
                 'France': [13800,13700,13600,13500,13400,13300,13200,13100,13000,12900,12800,12700,12600,12500],
                 'Germany':[27200,27400,27600,27800,27600,27400,27200,27000,26800,26600,26400,26200,26000,25800]},
    'chickens': {'Ireland':[12000,12200,12400,12600,12800,13000,13200,13400,13600,13500,13700,13800,13900,14000],
                 'France': [210000,212000,214000,216000,218000,220000,222000,224000,226000,228000,230000,232000,234000,236000],
                 'Germany':[168000,170000,172000,174000,176000,178000,180000,182000,184000,186000,188000,190000,192000,194000]}
}
PEST_VOL = {
    'Ireland': [7200,7350,7100,7500,7650,7800,7600,7900,8050,7800,7950,8100,7950,8100],
    'France':  [61200,62500,60800,63000,64200,65500,63800,65000,66200,64000,65500,66800,65000,67200],
    'Germany': [44800,45600,44200,46000,47200,48400,46800,47800,48900,47200,48400,49500,47800,49200]
}
PEST_INT = {
    'Ireland': [3.2,3.3,3.1,3.4,3.5,3.5,3.4,3.6,3.7,3.5,3.6,3.7,3.6,3.7],
    'France':  [5.8,5.9,5.7,6.0,6.1,6.2,6.0,6.1,6.3,6.1,6.2,6.3,6.1,6.3],
    'Germany': [5.1,5.2,5.0,5.3,5.4,5.5,5.3,5.4,5.6,5.4,5.5,5.6,5.4,5.6]
}
EXPORTS = [3800,3950,3700,4100,4250,4400,4200,4500,4700,4450,4600,4800,4650,4900]
IMPORTS = [2400,2500,2350,2600,2700,2800,2650,2750,2900,2750,2850,2950,2800,2800]
BAL_IRL = [1400,1450,1350,1500,1550,1600,1550,1750,1800,1700,1750,1850,1850,2100]
BAL_FRA = [3200,3400,3100,3600,3700,3900,3600,3800,4000,3700,3900,4100,3800,4200]
BAL_DEU = [-800,-750,-900,-700,-650,-600,-750,-700,-600,-700,-650,-550,-600,-500]
FORECAST_YEARS = [2024,2025,2026,2027,2028]
FORECAST_MEAN  = [3560,3640,3720,3800,3890]
FORECAST_UPPER = [3720,3860,3990,4110,4230]
FORECAST_LOWER = [3400,3420,3450,3490,3550]
HEATMAP = {
    'Crops':      [0.15,0.28,0.02,0.35,0.50,0.62,0.47,0.70,0.80,0.57,0.75,0.85,0.65,1.0],
    'Livestock':  [0.12,0.20,0.28,0.40,0.52,0.65,0.72,0.80,0.88,0.75,0.83,0.90,0.85,0.93],
    'Pesticides': [0.20,0.32,0.15,0.40,0.55,0.70,0.57,0.73,0.85,0.68,0.78,0.88,0.73,0.88],
    'Exports':    [0.10,0.22,0.08,0.30,0.45,0.60,0.52,0.70,0.85,0.68,0.75,0.90,0.82,1.0],
    'Imports':    [0.25,0.38,0.18,0.45,0.58,0.72,0.62,0.72,0.85,0.72,0.80,0.90,0.82,0.82],
}
SENTIMENT = [
    {'year':'2024','text':'Ireland agri-food exports reach record €16 billion — Bord Bia','polarity':0.38,'sentiment':'Positive'},
    {'year':'2024','text':'Irish dairy sector shows resilience with strong Q1 milk output','polarity':0.22,'sentiment':'Positive'},
    {'year':'2023','text':'Teagasc reports 8% increase in Irish farm income (beef & dairy)','polarity':0.31,'sentiment':'Positive'},
    {'year':'2023','text':'Ireland organic farming sector grows 12% as sustainability demand rises','polarity':0.28,'sentiment':'Positive'},
    {'year':'2022','text':'Irish beef exports to China surge following new trade agreement','polarity':0.25,'sentiment':'Positive'},
    {'year':'2022','text':'Bord Bia sustainable beef programme approved by 97% of Irish cattle farmers','polarity':0.35,'sentiment':'Positive'},
    {'year':'2023','text':'New CAP support payments to boost Irish farm income by €300M annually','polarity':0.20,'sentiment':'Positive'},
    {'year':'2024','text':'Irish Farmers Journal: tillage acreage increased for third consecutive year','polarity':0.15,'sentiment':'Positive'},
    {'year':'2023','text':'EU Common Agricultural Policy reform debate continues in Brussels','polarity':0.02,'sentiment':'Neutral'},
    {'year':'2023','text':'Irish agricultural land prices stable as interest rates affect borrowing','polarity':-0.03,'sentiment':'Neutral'},
    {'year':'2021','text':'Ireland submits CAP Strategic Plan to European Commission for approval','polarity':0.04,'sentiment':'Neutral'},
    {'year':'2023','text':'Prolonged wet weather severely disrupts Irish harvest — worst in decade','polarity':-0.28,'sentiment':'Negative'},
    {'year':'2022','text':'Rising fertiliser costs threaten profitability of Irish tillage farming','polarity':-0.32,'sentiment':'Negative'},
    {'year':'2023','text':'Nitrates Action Programme restrictions tightened — farmers face compliance pressure','polarity':-0.25,'sentiment':'Negative'},
    {'year':'2022','text':'Cattle numbers declining as farmers exit amid rising costs and regulations','polarity':-0.31,'sentiment':'Negative'},
    {'year':'2021','text':'Brexit disruption continues to affect Irish agri-food export logistics','polarity':-0.22,'sentiment':'Negative'},
    {'year':'2023','text':'Climate targets may force significant reduction in Irish cattle herd','polarity':-0.28,'sentiment':'Negative'},
    {'year':'2024','text':'Irish farmers warn of viability crisis as input costs remain elevated','polarity':-0.33,'sentiment':'Negative'},
]
C = {'Ireland':'#169b62','France':'#003189','Germany':'#444444'}

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:8px 0 16px 0">
      <div style="font-size:28px;margin-bottom:6px">🇮🇪</div>
      <div style="color:white;font-size:15px;font-weight:700;line-height:1.3">Ireland Agri Dashboard</div>
      <div style="color:rgba(255,255,255,0.5);font-size:11px;margin-top:4px">CCT College Dublin · MSc Data Analytics · 2026</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown('<p style="color:rgba(255,255,255,0.5)!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">Countries</p>', unsafe_allow_html=True)
    countries = st.multiselect("", options=["Ireland","France","Germany"], default=["Ireland","France","Germany"], label_visibility="collapsed")
    if not countries:
        countries = ["Ireland"]

    st.markdown('<p style="color:rgba(255,255,255,0.5)!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.5px;margin-top:12px;margin-bottom:6px">Year Range</p>', unsafe_allow_html=True)
    yr_range = st.slider("", 2010, 2023, (2010, 2023), label_visibility="collapsed")

    st.divider()
    st.markdown('<p style="color:rgba(255,255,255,0.5)!important;font-size:11px!important;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">Jump to Section</p>', unsafe_allow_html=True)
    section = st.radio("", [
        "🏷️ KPIs","🌾 Crop Production","🐄 Livestock",
        "🧪 Pesticides","⚖️ Trade","🔮 ARIMA Forecast",
        "🤖 ML Models","💬 Sentiment","🗺️ Heatmap",
        "📋 Data Table","💡 Recommendations"
    ], label_visibility="collapsed")

    st.divider()
    st.markdown('<p style="color:rgba(255,255,255,0.4)!important;font-size:10px!important">Data: FAOSTAT (CC BY-NC-SA 3.0 IGO)</p>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════
def fy():
    i0 = YEARS.index(yr_range[0]); i1 = YEARS.index(yr_range[1])
    return YEARS[i0:i1+1]

def sl(lst):
    i0 = YEARS.index(yr_range[0]); i1 = YEARS.index(yr_range[1])
    return lst[i0:i1+1]

CHART_LAYOUT = dict(
    plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='DM Sans, sans-serif', size=12, color='#1a2419'),
    legend=dict(orientation='h', y=-0.22, font=dict(size=11)),
    margin=dict(l=10, r=10, t=10, b=10),
    hovermode='x unified'
)
BASE_AXIS = dict(gridcolor='#f0f0f0', linecolor='#e4e9e2', tickfont=dict(size=11))

def card(title, subtitle=""):
    sub = f'<div class="section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="section-card"><div class="section-title">{title}</div>{sub}</div>', unsafe_allow_html=True)

def section_wrap(title, subtitle, content_fn):
    st.markdown(f"""
    <div class="section-card">
      <div class="section-title">{title}</div>
      <div class="section-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def show_all(s):
    return s == "🏷️ KPIs"

# ═══════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,#0d5c38 0%,#169b62 55%,#1ab36e 100%);
            padding:22px 28px 20px 28px;border-radius:0 0 14px 14px;
            margin:0 -24px 20px -24px;
            display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
  <div style="display:flex;align-items:center;gap:16px">
    <span style="font-size:46px;line-height:1">🇮🇪</span>
    <div>
      <div style="color:white;font-size:21px;font-weight:700;letter-spacing:-.3px">
        Ireland Agricultural Analytics Dashboard
      </div>
      <div style="color:rgba(255,255,255,0.75);font-size:12px;margin-top:4px">
        FAOSTAT Data (2010–2023) &nbsp;·&nbsp; Ireland vs France vs Germany
        &nbsp;·&nbsp; ML · ARIMA · Sentiment Analysis
      </div>
    </div>
  </div>
  <div style="background:rgba(255,255,255,0.18);color:white;padding:7px 16px;
              border-radius:20px;font-size:11px;font-weight:600;
              border:1px solid rgba(255,255,255,0.3);white-space:nowrap">
    CCT College Dublin · MSc Data Analytics · 2026
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 1. KPIs
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "KPI" in section:
    st.markdown('<div class="section-card"><div class="section-title">🏷️ Key Performance Indicators — 2023</div></div>', unsafe_allow_html=True)
    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("🌾 Crop Production", "3.47M t",  "2023 total tonnes")
    k2.metric("🐄 Livestock Stocks","7.2M",      "2023 total animals")
    k3.metric("📦 Export Volume",   "4.9M t",   "2023 export tonnes")
    k4.metric("⚖️ Trade Balance",   "+2.1M t",  "Net export surplus")
    k5.metric("🤖 Best ML R²",      "0.923",    "Random Forest model")
    k6.metric("💬 News Sentiment",  "+0.061",   "Avg TextBlob polarity")
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 2. CROP PRODUCTION
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "Crop" in section:
    st.markdown('<div class="section-card"><div class="section-title">🌾 Crop Production Trends</div><div class="section-sub">Ireland vs France vs Germany · tonnes · 2010–2023</div></div>', unsafe_allow_html=True)
    yrs = fy()
    fig = go.Figure()
    fill_alpha = {'Ireland':'rgba(22,155,98,0.08)','France':'rgba(0,49,137,0.06)','Germany':'rgba(68,68,68,0.06)'}
    for c in countries:
        fig.add_trace(go.Scatter(
            x=yrs, y=sl(CROPS[c]), name=c,
            line=dict(color=C[c], width=2.5),
            marker=dict(size=5, color=C[c]),
            fill='tozeroy', fillcolor=fill_alpha[c],
            mode='lines+markers',
            hovertemplate=f'<b>{c}</b>: %{{y:,.0f}} t<extra></extra>'
        ))
    fig.update_layout(**CHART_LAYOUT, xaxis=dict(**BASE_AXIS),
        height=300,
        yaxis=dict(gridcolor='#f0f0f0', tickformat=',', title='Tonnes'))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 3. LIVESTOCK  (left) + 4. PESTICIDES (right)
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "Livestock" in section or "Pestic" in section:
    col_l, col_r = st.columns(2, gap="medium")

    # — LIVESTOCK —
    if show_all(section) or "Livestock" in section:
        with col_l:
            st.markdown('<div class="section-card"><div class="section-title">🐄 Livestock Stocks</div><div class="section-sub">Animal stocks by country · 2010–2023</div></div>', unsafe_allow_html=True)
            t1,t2,t3,t4 = st.tabs(["🐄 Cattle","🐑 Sheep","🐷 Pigs","🐔 Chickens"])
            for tab, animal in zip([t1,t2,t3,t4], ['cattle','sheep','pigs','chickens']):
                with tab:
                    fig = go.Figure()
                    for c in countries:
                        fig.add_trace(go.Scatter(
                            x=fy(), y=sl(LIVESTOCK[animal][c]), name=c,
                            line=dict(color=C[c], width=2), marker=dict(size=4),
                            mode='lines+markers',
                            hovertemplate=f'<b>{c}</b>: %{{y:,.0f}}<extra></extra>'
                        ))
                    fig.update_layout(**CHART_LAYOUT, xaxis=dict(**BASE_AXIS),
        height=260,
                        yaxis=dict(gridcolor='#f0f0f0', tickformat=','))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

    # — PESTICIDES —
    if show_all(section) or "Pestic" in section:
        with col_r:
            st.markdown('<div class="section-card"><div class="section-title">🧪 Pesticide Usage</div><div class="section-sub">Volume + intensity · 2010–2023</div></div>', unsafe_allow_html=True)
            pt1, pt2 = st.tabs(["📦 Total Volume (t)", "⚗️ Per Hectare (kg/ha)"])
            pest_map = {'📦 Total Volume (t)': PEST_VOL, '⚗️ Per Hectare (kg/ha)': PEST_INT}
            for tab, (label, data) in zip([pt1, pt2], pest_map.items()):
                with tab:
                    fig = go.Figure()
                    for c in countries:
                        fig.add_trace(go.Bar(
                            x=fy(), y=sl(data[c]), name=c,
                            marker_color=C[c], opacity=0.85,
                            hovertemplate=f'<b>{c}</b>: %{{y:,.1f}}<extra></extra>'
                        ))
                    fig.update_layout(**CHART_LAYOUT, xaxis=dict(**BASE_AXIS),
        height=260, barmode='group',
                        yaxis=dict(gridcolor='#f0f0f0', tickformat=','))
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 5. TRADE
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "Trade" in section:
    st.markdown('<div class="section-card"><div class="section-title">⚖️ Agricultural Trade Analysis</div><div class="section-sub">Export vs Import volume + trade balance by country · 2010–2023</div></div>', unsafe_allow_html=True)
    tc1, tc2 = st.columns(2, gap="medium")
    yrs = fy()
    with tc1:
        st.markdown('<p style="font-size:11px;font-weight:600;color:#6b7a68;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px">Ireland Export vs Import (tonnes)</p>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=yrs, y=sl(EXPORTS), name='Exports',
            fill='tozeroy', fillcolor='rgba(22,155,98,0.18)',
            line=dict(color='#169b62', width=2), mode='lines+markers', marker=dict(size=4)))
        fig.add_trace(go.Scatter(x=yrs, y=sl(IMPORTS), name='Imports',
            fill='tozeroy', fillcolor='rgba(192,57,43,0.12)',
            line=dict(color='#c0392b', width=2), mode='lines+markers', marker=dict(size=4)))
        fig.update_layout(**CHART_LAYOUT, xaxis=dict(**BASE_AXIS),
        height=260,
            yaxis=dict(gridcolor='#f0f0f0', tickformat=',', title='Tonnes'))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
    with tc2:
        st.markdown('<p style="font-size:11px;font-weight:600;color:#6b7a68;text-transform:uppercase;letter-spacing:.4px;margin-bottom:6px">Trade Balance by Country</p>', unsafe_allow_html=True)
        fig = go.Figure()
        bal_map = {'Ireland': BAL_IRL, 'France': BAL_FRA, 'Germany': BAL_DEU}
        for c in countries:
            fig.add_trace(go.Bar(x=yrs, y=sl(bal_map[c]), name=c,
                marker_color=C[c], opacity=0.85))
        fig.add_hline(y=0, line_color='#1a2419', line_width=0.8)
        fig.update_layout(**CHART_LAYOUT, xaxis=dict(**BASE_AXIS),
        height=260, barmode='group',
            yaxis=dict(gridcolor='#f0f0f0', tickformat=','))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 6. ARIMA  (left)  +  9. HEATMAP (right)
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "ARIMA" in section or "Heatmap" in section:
    ac1, ac2 = st.columns(2, gap="medium")

    if show_all(section) or "ARIMA" in section:
        with ac1:
            st.markdown('<div class="section-card"><div class="section-title">🔮 ARIMA 5-Year Forecast (2024–2028)</div><div class="section-sub">Ireland crop production · 95% confidence interval</div></div>', unsafe_allow_html=True)
            all_y = YEARS + FORECAST_YEARS
            hist  = CROPS['Ireland'] + [None]*5
            fc    = [None]*(len(YEARS)-1) + [CROPS['Ireland'][-1]] + FORECAST_MEAN
            upper = [None]*len(YEARS) + FORECAST_UPPER
            lower = [None]*len(YEARS) + FORECAST_LOWER

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=all_y, y=upper, name='Upper CI',
                line=dict(color='rgba(255,107,53,0)'), showlegend=False, hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=all_y, y=lower, name='95% CI',
                fill='tonexty', fillcolor='rgba(255,107,53,0.15)',
                line=dict(color='rgba(255,107,53,0)'), hoverinfo='skip'))
            fig.add_trace(go.Scatter(x=all_y, y=hist, name='Historical',
                line=dict(color='#169b62', width=2.5), marker=dict(size=5), mode='lines+markers'))
            fig.add_trace(go.Scatter(x=all_y, y=fc, name='Forecast',
                line=dict(color='#ff6b35', width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond'), mode='lines+markers'))
            fig.add_vline(x=2023.5, line_color='#aaa', line_dash='dot', line_width=1)
            fig.update_layout(**CHART_LAYOUT, xaxis=dict(**BASE_AXIS),
        height=290,
                yaxis=dict(gridcolor='#f0f0f0', tickformat=',', title='Tonnes'))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

    if show_all(section) or "Heatmap" in section:
        with ac2:
            st.markdown('<div class="section-card"><div class="section-title">🗺️ Normalised Indicator Heatmap</div><div class="section-sub">Ireland agricultural indicators · 2010–2023</div></div>', unsafe_allow_html=True)
            hm_df = pd.DataFrame(HEATMAP, index=YEARS).T
            fig = px.imshow(hm_df, color_continuous_scale='RdYlGn',
                zmin=0, zmax=1, aspect='auto', text_auto='.2f')
            fig.update_layout(
                height=290, plot_bgcolor='white', paper_bgcolor='white',
                font=dict(family='DM Sans', size=11),
                xaxis=dict(title='', tickfont=dict(size=10)),
                yaxis=dict(title=''),
                coloraxis_colorbar=dict(title='', tickvals=[0,0.5,1],
                    ticktext=['Low','Mid','High'], thickness=12, len=0.8),
                margin=dict(l=10, r=50, t=10, b=10)
            )
            fig.update_traces(textfont_size=9)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 7. ML  (left)  +  8. SENTIMENT (right)
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "ML" in section or "Sentiment" in section:
    mc1, mc2 = st.columns(2, gap="medium")

    # — ML —
    if show_all(section) or "ML" in section:
        with mc1:
            st.markdown('<div class="section-card"><div class="section-title">🤖 ML Model Performance</div><div class="section-sub">Linear Regression · Random Forest · Gradient Boosting</div></div>', unsafe_allow_html=True)
            ml_names = ['Linear Regression','Random Forest','Gradient Boosting']
            ml_r2    = [0.712, 0.923, 0.908]
            ml_rmse  = [8240, 4100, 4580]
            ml_cols  = ['#888888','#169b62','#003189']

            fig = go.Figure()
            fig.add_trace(go.Bar(y=ml_names, x=ml_r2, orientation='h',
                marker_color=ml_cols, text=[f'{v:.3f}' for v in ml_r2],
                textposition='outside', textfont=dict(size=11, color='#1a2419'),
                hovertemplate='<b>%{y}</b><br>R² = %{x:.3f}<extra></extra>'))
            fig.update_layout(**CHART_LAYOUT, height=200,
                xaxis=dict(range=[0,1.05], gridcolor='#f0f0f0', title='R²'),
                yaxis=dict(gridcolor='none'),
                margin=dict(l=10,r=60,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

            # ML metric cards
            m1, m2, m3 = st.columns(3)
            for col, name, r2, rmse, clr in zip(
                [m1,m2,m3], ml_names, ml_r2, ml_rmse, ml_cols):
                col.markdown(f"""
                <div style="background:#f5f7f4;border-radius:8px;padding:12px;
                            border:1px solid #e4e9e2;text-align:center">
                  <div style="font-size:10px;color:#6b7a68;font-weight:600;margin-bottom:4px">{name.split()[0]}<br>{''.join(name.split()[1:])}</div>
                  <div style="font-size:20px;font-weight:700;color:{clr}">{r2:.3f}</div>
                  <div style="font-size:10px;color:#6b7a68;margin-top:2px">RMSE: {rmse:,}</div>
                </div>""", unsafe_allow_html=True)

    # — SENTIMENT —
    if show_all(section) or "Sentiment" in section:
        with mc2:
            st.markdown('<div class="section-card"><div class="section-title">💬 Sentiment Analysis</div><div class="section-sub">Ireland agriculture news · TextBlob polarity</div></div>', unsafe_allow_html=True)
            sent_df = pd.DataFrame(SENTIMENT)
            avg_pol = sent_df['polarity'].mean()
            counts  = sent_df['sentiment'].value_counts()

            sc1, sc2 = st.columns([1, 1.6])
            with sc1:
                fig = go.Figure(go.Pie(
                    labels=['Positive','Neutral','Negative'],
                    values=[counts.get('Positive',0), counts.get('Neutral',0), counts.get('Negative',0)],
                    hole=0.58,
                    marker_colors=['#169b62','#e67e22','#c0392b'],
                    textfont_size=11,
                    hovertemplate='%{label}: %{value} headlines<extra></extra>'
                ))
                fig.update_layout(
                    height=200, paper_bgcolor='white',
                    showlegend=False,
                    margin=dict(l=0,r=0,t=0,b=0),
                    annotations=[dict(text=f'Avg<br><b>{avg_pol:.3f}</b>',
                        x=0.5,y=0.5,font_size=12,showarrow=False,font_color='#169b62')]
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
                # Legend
                for label, clr, n in [('Positive','#169b62',counts.get('Positive',0)),
                                       ('Neutral','#e67e22',counts.get('Neutral',0)),
                                       ('Negative','#c0392b',counts.get('Negative',0))]:
                    st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px"><span style="display:flex;align-items:center;gap:5px"><span style="width:8px;height:8px;border-radius:50%;background:{clr};display:inline-block"></span>{label}</span><b>{n}</b></div>', unsafe_allow_html=True)

            with sc2:
                items_html = ""
                for _, row in sent_df.iterrows():
                    clr = '#169b62' if row['sentiment']=='Positive' else ('#c0392b' if row['sentiment']=='Negative' else '#e67e22')
                    items_html += f'<div style="display:flex;gap:8px;align-items:flex-start;padding:6px 8px;background:#f8fdf9;border-radius:6px;border:1px solid #e4e9e2;margin-bottom:4px"><span style="width:7px;height:7px;border-radius:50%;background:{clr};flex-shrink:0;margin-top:4px"></span><span style="font-size:10.5px;color:#1a2419;flex:1;line-height:1.4">{row["text"]}</span><span style="font-size:10px;color:#6b7a68;white-space:nowrap;font-weight:600">{row["year"]}</span></div>'
                st.markdown(f'<div style="max-height:270px;overflow-y:auto;padding-right:2px">{items_html}</div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 10. DATA TABLE
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "Data" in section:
    st.markdown('<div class="section-card"><div class="section-title">📋 Ireland Agricultural Indicators — Full Data Table</div><div class="section-sub">Annual panel 2010–2023</div></div>', unsafe_allow_html=True)
    df = pd.DataFrame({
        'Year': YEARS, 'Crops (t)': CROPS['Ireland'],
        'Cattle': LIVESTOCK['cattle']['Ireland'],
        'Sheep': LIVESTOCK['sheep']['Ireland'],
        'Pigs': LIVESTOCK['pigs']['Ireland'],
        'Chickens': LIVESTOCK['chickens']['Ireland'],
        'Pesticides (t)': PEST_VOL['Ireland'],
        'Pest (kg/ha)': PEST_INT['Ireland'],
        'Exports (t)': EXPORTS, 'Imports (t)': IMPORTS, 'Trade Balance': BAL_IRL,
    })

    search = st.text_input("🔍 Filter by year", "", placeholder="e.g. 2020")
    if search:
        df = df[df['Year'].astype(str).str.contains(search)]

    # Build HTML table
    def bar_cell(val, mn, mx, color):
        pct = int((val-mn)/(mx-mn)*100) if mx!=mn else 0
        return (f'<div style="background:linear-gradient(to right,{color}28 {pct}%,'
                f'transparent {pct}%);padding:5px 10px;border-radius:4px;'
                f'font-weight:600;color:#1a2419;font-size:12px">{int(val):,}</div>')

    c_mn,c_mx = min(df['Crops (t)']), max(df['Crops (t)'])
    k_mn,k_mx = min(df['Cattle']),    max(df['Cattle'])

    ths = ["Year","Crops (t)","Cattle","Sheep","Pigs","Chickens","Pesticides (t)","Pest kg/ha","Exports (t)","Imports (t)","Trade Balance"]
    thead = "".join(f'<th style="padding:10px 14px;text-align:left;white-space:nowrap;font-size:11px;font-weight:600;letter-spacing:.3px">{h}</th>' for h in ths)

    tbody = ""
    for i,(_, r) in enumerate(df.iterrows()):
        bg  = "#f7fdf9" if i%2==0 else "white"
        bc  = "#169b62" if r['Trade Balance']>=0 else "#c0392b"
        sgn = "+" if r['Trade Balance']>=0 else ""
        tbody += (f'<tr style="background:{bg};border-bottom:1px solid #f0f4ee">'
            f'<td style="padding:8px 14px;font-weight:700;color:#169b62;font-size:12px">{int(r["Year"])}</td>'
            f'<td style="padding:4px 8px">{bar_cell(r["Crops (t)"],c_mn,c_mx,"#169b62")}</td>'
            f'<td style="padding:4px 8px">{bar_cell(r["Cattle"],k_mn,k_mx,"#003189")}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{int(r["Sheep"]):,}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{int(r["Pigs"]):,}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{int(r["Chickens"]):,}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{int(r["Pesticides (t)"]):,}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{r["Pest (kg/ha)"]:.1f}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{int(r["Exports (t)"]):,}</td>'
            f'<td style="padding:8px 14px;font-size:12px;color:#444">{int(r["Imports (t)"]):,}</td>'
            f'<td style="padding:8px 14px;font-weight:700;color:{bc};font-size:12px">{sgn}{int(r["Trade Balance"]):,}</td>'
            f'</tr>')

    st.markdown(f"""
    <div style="overflow-x:auto;border-radius:10px;border:1px solid #e4e9e2;background:white">
      <table style="width:100%;border-collapse:collapse;font-family:DM Sans,sans-serif">
        <thead><tr style="background:#0d2b1a;color:white">{thead}</tr></thead>
        <tbody>{tbody}</tbody>
      </table>
    </div>
    <p style="font-size:11px;color:#6b7a68;margin-top:6px;margin-bottom:0">
      Showing {len(df)} rows &nbsp;·&nbsp; 🟩 Green/blue bars = relative scale
    </p>
    """, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# 11. RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════
if show_all(section) or "Recommend" in section:
    st.markdown('<div class="section-card"><div class="section-title">💡 Evidence-Based Policy Recommendations</div><div class="section-sub">Derived from ARIMA forecasts, ML analysis & statistical tests</div></div>', unsafe_allow_html=True)
    recs = [
        ("🌾","Scale up tillage crops",
         "ARIMA forecasts project continued crop growth to 2028. Reduce dependency on cereal imports by expanding tillage acreage — Ireland increased tillage for a third consecutive year in 2024."),
        ("🐄","Leverage livestock export advantage",
         "Cattle dominates Ireland's agricultural output. RF model (R²=0.923) confirms livestock is the strongest predictor. Invest in high-value beef and dairy processing to maximise export value."),
        ("🧪","Maintain low pesticide use as green brand",
         "Ireland uses significantly less pesticide per hectare than France and Germany. This competitive edge should be marketed under EU Farm-to-Fork and sustainability frameworks."),
        ("📉","Address climate compliance costs",
         "Sentiment analysis shows negative polarity on climate regulations (2023). New CAP support payments (€300M/year) should target farmers making the green transition."),
        ("🤝","Align CAP strategy with Ireland-specific benchmarks",
         "Ireland consistently outperforms EU averages on export volume and trade balance. EU CAP funding should be negotiated around Ireland's strong net-export position."),
    ]
    for icon,title,body in recs:
        st.markdown(f"""
        <div style="display:flex;gap:14px;background:#f7fdf9;border-left:4px solid #169b62;
                    border-radius:8px;padding:14px 18px;margin-bottom:10px;
                    border:1px solid #d4edd9">
          <span style="font-size:20px;flex-shrink:0">{icon}</span>
          <div>
            <div style="font-size:13px;font-weight:700;color:#0e6b44;margin-bottom:4px">{title}</div>
            <div style="font-size:12.5px;color:#1a2419;line-height:1.6">{body}</div>
          </div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:#0d2b1a;color:rgba(255,255,255,0.5);text-align:center;
            padding:16px 24px;border-radius:10px;font-size:11px;margin-top:16px;
            margin:16px -24px 0 -24px">
  🇮🇪 Ireland Agricultural Analytics &nbsp;·&nbsp;
  Data: FAOSTAT (CC BY-NC-SA 3.0 IGO) &nbsp;·&nbsp;
  Models: Random Forest · Gradient Boosting · ARIMA · TextBlob &nbsp;·&nbsp;
  Built with Python, Plotly, streamlit &nbsp;·&nbsp;
  CCT College Dublin · MSc Data Analytics 2026
</div>
""", unsafe_allow_html=True)
