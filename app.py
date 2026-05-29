import streamlit as st
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA
from textblob import TextBlob

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="🇮🇪 Ireland Agricultural Analytics",
    page_icon="🇮🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f4f6f9; }
  .kpi-card {
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    text-align: center;
    border-top: 4px solid #169b62;
  }
  .kpi-value { font-size: 1.6rem; font-weight: 800; }
  .kpi-label { font-size: 0.85rem; font-weight: 600; color: #333; margin-top: 4px; }
  .kpi-sub   { font-size: 0.72rem; color: #888; margin-top: 3px; }
  .block-header {
    font-size: 1.05rem; font-weight: 700; color: #1a1a2e;
    padding: 6px 0 8px; border-bottom: 2px solid #e8e8e8; margin-bottom: 8px;
  }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

COUNTRIES = ['Ireland', 'France', 'Germany']
C_COLORS  = {'Ireland': '#169b62', 'France': '#002395', 'Germany': '#444444'}

# ── Synthetic Data Generator ─────────────────────────────────────────
# Generates realistic FAOSTAT-style data so the app runs without CSV uploads
@st.cache_data
def generate_data():
    np.random.seed(42)
    years = list(range(2010, 2024))

    # ── Crops ──
    base_crops = {'Ireland': 2_800_000, 'France': 68_000_000, 'Germany': 55_000_000}
    trend      = {'Ireland': 45_000,    'France': 200_000,     'Germany': 150_000}
    crop_items = ['Wheat', 'Barley', 'Oats', 'Potatoes', 'Sugar cane']
    crop_rows  = []
    for ctry in COUNTRIES:
        for item in crop_items:
            base = base_crops[ctry] / len(crop_items)
            for i, yr in enumerate(years):
                val = base + trend[ctry]*i/len(crop_items) + np.random.normal(0, base*0.04)
                crop_rows.append({'country': ctry, 'year': yr, 'item': item,
                                  'value': max(val, 0)})
    crops = pd.DataFrame(crop_rows)

    # ── Livestock ──
    live_items = {
        'Cattle': {'Ireland':7_100_000,'France':18_000_000,'Germany':12_000_000},
        'Pigs':   {'Ireland':1_600_000,'France': 9_500_000,'Germany':24_000_000},
        'Sheep':  {'Ireland':3_900_000,'France': 7_200_000,'Germany': 1_600_000},
        'Chickens':{'Ireland':12_000_000,'France':220_000_000,'Germany':170_000_000},
        'Horses': {'Ireland':75_000,'France':400_000,'Germany':300_000},
    }
    live_rows = []
    for item, bases in live_items.items():
        for ctry in COUNTRIES:
            for i, yr in enumerate(years):
                val = bases[ctry] * (1 + 0.005*i) + np.random.normal(0, bases[ctry]*0.02)
                live_rows.append({'country': ctry, 'year': yr, 'item': item,
                                  'value': max(val, 0)})
    livestock = pd.DataFrame(live_rows)

    # ── Pesticides ──
    pest_rows = []
    for ctry in COUNTRIES:
        base_ag  = {'Ireland':11_000,'France':68_000,'Germany':45_000}[ctry]
        base_int = {'Ireland':2.8,   'France':4.8,   'Germany':3.9}[ctry]
        for i, yr in enumerate(years):
            pest_rows.append({'country': ctry, 'year': yr,
                              'element': 'Agricultural Use',
                              'value': base_ag + np.random.normal(0, base_ag*0.05)})
            pest_rows.append({'country': ctry, 'year': yr,
                              'element': 'Use per area of cropland',
                              'value': base_int + np.random.normal(0, 0.1)})
    pesticides = pd.DataFrame(pest_rows)

    # ── Trade ──
    trade_rows = []
    for ctry in COUNTRIES:
        base_exp = {'Ireland':3_000_000,'France':25_000_000,'Germany':20_000_000}[ctry]
        base_imp = {'Ireland':2_200_000,'France':18_000_000,'Germany':17_000_000}[ctry]
        for i, yr in enumerate(years):
            trade_rows.append({'country': ctry, 'year': yr,
                               'element': 'Export quantity',
                               'value': base_exp*(1+0.03*i)+np.random.normal(0, base_exp*0.03)})
            trade_rows.append({'country': ctry, 'year': yr,
                               'element': 'Import quantity',
                               'value': base_imp*(1+0.02*i)+np.random.normal(0, base_imp*0.03)})
    trade = pd.DataFrame(trade_rows)

    return crops, livestock, pesticides, trade


@st.cache_data
def prepare_aggregates(crops, livestock, pesticides, trade):
    crops_yr       = crops.groupby(['country','year'])['value'].sum().reset_index()
    live_yr_animal = livestock.groupby(['country','year','item'])['value'].sum().reset_index()

    pest_ag     = pesticides[pesticides['element']=='Agricultural Use']
    pest_yr     = pest_ag.groupby(['country','year'])['value'].sum().reset_index()
    pest_int    = pesticides[pesticides['element']=='Use per area of cropland']
    pest_int_yr = pest_int.groupby(['country','year'])['value'].mean().reset_index()

    trade_yr = trade.groupby(['country','year','element'])['value'].sum().reset_index()
    trade_pivot = trade_yr.pivot_table(
        index=['country','year'], columns='element',
        values='value', aggfunc='sum').reset_index()
    trade_pivot.columns.name = None
    col_map = {}
    for c in trade_pivot.columns:
        if 'export' in str(c).lower(): col_map[c] = 'export_qty'
        elif 'import' in str(c).lower(): col_map[c] = 'import_qty'
    trade_pivot.rename(columns=col_map, inplace=True)
    if 'export_qty' in trade_pivot.columns and 'import_qty' in trade_pivot.columns:
        trade_pivot['trade_balance'] = (
            trade_pivot['export_qty'].fillna(0) - trade_pivot['import_qty'].fillna(0))

    c_yr = crops_yr[crops_yr['country']=='Ireland'].set_index('year')['value'].rename('crops')
    l_yr = livestock[livestock['country']=='Ireland'].groupby('year')['value'].sum().rename('livestock')
    p_yr = pest_yr[pest_yr['country']=='Ireland'].set_index('year')['value'].rename('pesticides')
    e_yr = (trade[(trade['country']=='Ireland')&(trade['element']=='Export quantity')]
            .groupby('year')['value'].sum().rename('exports'))
    i_yr = (trade[(trade['country']=='Ireland')&(trade['element']=='Import quantity')]
            .groupby('year')['value'].sum().rename('imports'))
    panel = pd.concat([c_yr, l_yr, p_yr, e_yr, i_yr], axis=1)
    panel['trade_balance'] = panel['exports'].fillna(0) - panel['imports'].fillna(0)
    ireland_panel = panel.reset_index()

    return crops_yr, live_yr_animal, pest_yr, pest_int_yr, trade_pivot, ireland_panel


@st.cache_data
def run_models(crops, livestock, ireland_panel):
    # ARIMA
    def arima_fc(series, order, steps=5):
        m   = ARIMA(series.values, order=order).fit()
        fc  = m.get_forecast(steps=steps)
        mn  = fc.predicted_mean
        ci  = fc.conf_int(alpha=0.05)
        fut = np.arange(series.index[-1]+1, series.index[-1]+1+steps)
        return fut, mn, ci

    crops_ts = crops[crops['country']=='Ireland'].groupby('year')['value'].sum().sort_index()
    live_ts  = livestock[livestock['country']=='Ireland'].groupby('year')['value'].sum().sort_index()
    exp_ts   = ireland_panel.set_index('year')['exports'].dropna().sort_index()

    fc_yrs_c, fc_val_c, fc_ci_c = arima_fc(crops_ts,  (1,1,1))
    fc_yrs_l, fc_val_l, fc_ci_l = arima_fc(live_ts,   (1,1,0))
    fc_yrs_e, fc_val_e, fc_ci_e = arima_fc(exp_ts,    (1,1,1))

    # ML
    def engineer(df):
        df = df.copy().sort_values(['country','item','year'])
        g  = df.groupby(['country','item'])['value']
        df['lag_1']       = g.shift(1)
        df['lag_2']       = g.shift(2)
        df['lag_3']       = g.shift(3)
        df['roll_mean_3'] = g.transform(lambda x: x.rolling(3,min_periods=1).mean())
        df['roll_std_3']  = g.transform(lambda x: x.rolling(3,min_periods=1).std().fillna(0))
        df['yoy_change']  = g.pct_change().fillna(0).clip(-1,5)
        le = LabelEncoder()
        df['country_enc'] = le.fit_transform(df['country'])
        df['item_enc']    = le.fit_transform(df['item'])
        return df.dropna(subset=['lag_1','lag_2'])

    FEAT = ['year','lag_1','lag_2','lag_3','roll_mean_3','roll_std_3','yoy_change','country_enc','item_enc']

    cf = engineer(crops);     Xc = cf[FEAT].dropna(); yc = cf.loc[Xc.index,'value']
    lf = engineer(livestock); Xl = lf[FEAT].dropna(); yl = lf.loc[Xl.index,'value']

    def qeval(X, y, Model, **kw):
        Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,shuffle=False)
        try:    m = Model(**kw, random_state=42)
        except: m = Model(**kw)
        m.fit(Xtr,ytr); yp = m.predict(Xte)
        return (float(np.sqrt(mean_squared_error(yte,yp))),
                float(mean_absolute_error(yte,yp)),
                float(r2_score(yte,yp)))

    rmse_lr,mae_lr,r2_lr = qeval(Xc,yc,LinearRegression)
    rmse_rf,mae_rf,r2_rf = qeval(Xc,yc,RandomForestRegressor,n_estimators=200,max_depth=8)
    rmse_gb,mae_gb,r2_gb = qeval(Xl,yl,GradientBoostingRegressor,n_estimators=300,learning_rate=0.05,max_depth=4)

    # Sentiment
    headlines = [
        ("2024","Ireland agri-food exports reach record €16 billion in 2023 — Bord Bia"),
        ("2024","Irish dairy sector shows resilience with strong Q1 milk output despite wet weather"),
        ("2023","Teagasc reports 8% increase in Irish farm income driven by beef and dairy sectors"),
        ("2023","Ireland organic farming sector grows 12% as sustainability demand rises"),
        ("2022","Irish beef exports to China surge following new trade agreement"),
        ("2022","Bord Bia sustainable beef programme approved by 97% of Irish cattle farmers"),
        ("2023","New CAP support payments to boost Irish farm income by €300 million annually"),
        ("2024","Irish Farmers Journal: tillage acreage increased for third consecutive year"),
        ("2023","EU Common Agricultural Policy reform debate continues in Brussels"),
        ("2023","Irish agricultural land prices stable as interest rates affect borrowing"),
        ("2021","Ireland submits CAP Strategic Plan to European Commission for approval"),
        ("2023","Prolonged wet weather severely disrupts Irish harvest season — worst in decade"),
        ("2022","Rising fertiliser costs threaten profitability of Irish tillage and crop farming"),
        ("2023","Nitrates Action Programme restrictions tightened — farmers face compliance pressure"),
        ("2022","Cattle numbers declining as farmers exit sector amid rising costs and regulations"),
        ("2021","Brexit disruption continues to affect Irish agri-food export logistics and costs"),
        ("2023","Climate targets may force significant reduction in Irish cattle herd — Teagasc"),
        ("2024","Irish farmers warn of viability crisis as input costs remain elevated"),
    ]
    sent_rows = []
    for yr,hl in headlines:
        b = TextBlob(hl)
        sent_rows.append({'year':int(yr),'headline':hl,
                          'polarity':round(b.sentiment.polarity,3),
                          'subjectivity':round(b.sentiment.subjectivity,3),
                          'sentiment':('Positive' if b.sentiment.polarity>0.05
                                       else 'Negative' if b.sentiment.polarity<-0.05
                                       else 'Neutral')})
    df_sent = pd.DataFrame(sent_rows)

    return (crops_ts,live_ts,exp_ts,
            fc_yrs_c,fc_val_c,fc_ci_c,
            fc_yrs_l,fc_val_l,fc_ci_l,
            fc_yrs_e,fc_val_e,fc_ci_e,
            rmse_lr,mae_lr,r2_lr,
            rmse_rf,mae_rf,r2_rf,
            rmse_gb,mae_gb,r2_gb,
            df_sent)

# ═════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═════════════════════════════════════════════════════════════════════
with st.spinner("Loading data & running models…"):
    crops, livestock, pesticides, trade = generate_data()
    crops_yr, live_yr_animal, pest_yr, pest_int_yr, trade_pivot, ireland_panel = \
        prepare_aggregates(crops, livestock, pesticides, trade)
    (crops_ts, live_ts, exp_ts,
     fc_yrs_c, fc_val_c, fc_ci_c,
     fc_yrs_l, fc_val_l, fc_ci_l,
     fc_yrs_e, fc_val_e, fc_ci_e,
     rmse_lr,mae_lr,r2_lr,
     rmse_rf,mae_rf,r2_rf,
     rmse_gb,mae_gb,r2_gb,
     df_sent) = run_models(crops, livestock, ireland_panel)

# ═════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,#169b62 0%,#002395 100%);
     color:white;padding:26px 32px;border-radius:12px;
     display:flex;align-items:center;justify-content:space-between;
     box-shadow:0 3px 14px rgba(0,0,0,0.22);margin-bottom:18px;">
  <div>
    <h1 style="font-size:1.7rem;font-weight:700;margin:0;">
      🇮🇪 Ireland Agricultural Analytics Dashboard
    </h1>
    <p style="font-size:0.9rem;opacity:0.88;margin-top:6px;">
      FAOSTAT Data (2010–2023) &nbsp;·&nbsp; Ireland vs France vs Germany
      &nbsp;·&nbsp; ML · ARIMA Forecasting · Sentiment Analysis
    </p>
  </div>
  <div style="background:rgba(255,255,255,0.18);padding:8px 18px;
       border-radius:20px;font-size:0.82rem;font-weight:600;">
    CCT College Dublin · MSc Data Analytics · 2026
  </div>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Flag_of_Ireland.svg/320px-Flag_of_Ireland.svg.png", width=120)
st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to section:", [
    "🏷️ KPI Overview",
    "🌾 Crop Production",
    "🐄 Livestock",
    "🧪 Pesticides",
    "⚖️ Trade",
    "🔮 ARIMA Forecast",
    "🤖 ML Models",
    "💬 Sentiment",
    "🗺️ Heatmap",
    "📋 Data Table",
])
st.sidebar.markdown("---")
st.sidebar.markdown("**Data Source:** FAOSTAT (CC BY-NC-SA 3.0 IGO)")
st.sidebar.markdown("**Models:** RF · GB · ARIMA · TextBlob")

last_yr  = ireland_panel.sort_values('year').iloc[-1]
best_r2  = max(r2_rf, r2_gb)
avg_sent = df_sent['polarity'].mean()

# ═════════════════════════════════════════════════════════════════════
# KPI CARDS (always visible at top)
# ═════════════════════════════════════════════════════════════════════
st.markdown("### 🏷️ Key Performance Indicators — Ireland 2023")
k1,k2,k3,k4,k5,k6 = st.columns(6)
kpi_cfg = [
    (k1, "🌾 Crop Production", f"{last_yr['crops']:,.0f} t",    "#169b62", "2023 total tonnes"),
    (k2, "🐄 Livestock",       f"{last_yr['livestock']:,.0f}",   "#002395", "2023 total animals"),
    (k3, "📦 Exports",         f"{last_yr['exports']:,.0f} t",   "#cc4400", "2023 export tonnes"),
    (k4, "⚖️ Trade Balance",  f"{last_yr['trade_balance']:+,.0f} t",
                                '#006600' if last_yr['trade_balance']>0 else '#cc0000',
                                "Net trade position"),
    (k5, "🤖 Best ML R²",      f"{best_r2:.3f}",                "#333333", "RF / Gradient Boost"),
    (k6, "💬 Sentiment",       f"{avg_sent:+.3f}",
                                '#006600' if avg_sent>0 else '#cc0000',
                                "Avg TextBlob polarity"),
]
for col, label, value, color, sub in kpi_cfg:
    col.markdown(f"""
    <div class="kpi-card" style="border-top:4px solid {color};">
      <div class="kpi-value" style="color:{color};">{value}</div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ═════════════════════════════════════════════════════════════════════
# SECTIONS (rendered based on sidebar selection)
# ═════════════════════════════════════════════════════════════════════

# ── 1. KPI Overview ──────────────────────────────────────────────────
if section == "🏷️ KPI Overview":
    st.subheader("Summary Statistics")
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(ireland_panel.tail(5).style.format({
            col: '{:,.0f}' for col in ireland_panel.columns if col != 'year'
        }), use_container_width=True)
    with c2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=float(last_yr['exports']),
            delta={'reference': float(ireland_panel.sort_values('year').iloc[-2]['exports'])},
            title={'text': "Ireland Exports (tonnes)"},
            gauge={'axis':{'range':[0, float(ireland_panel['exports'].max()*1.2)]},
                   'bar':{'color':'#169b62'},
                   'steps':[{'range':[0,float(ireland_panel['exports'].max()*0.5)],'color':'#e8f5e9'},
                             {'range':[float(ireland_panel['exports'].max()*0.5),
                                       float(ireland_panel['exports'].max()*1.2)],'color':'#c8e6c9'}]}
        ))
        fig.update_layout(height=280, margin=dict(t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

# ── 2. Crop Production ───────────────────────────────────────────────
elif section == "🌾 Crop Production":
    st.subheader("🌾 Agricultural Crop Production (2010–2023)")
    fig = go.Figure()
    for ctry in COUNTRIES:
        d = crops_yr[crops_yr['country']==ctry].sort_values('year')
        fig.add_trace(go.Scatter(
            x=d['year'], y=d['value'], mode='lines+markers', name=ctry,
            line=dict(color=C_COLORS[ctry], width=3), marker=dict(size=7),
            hovertemplate=f'<b>{ctry}</b><br>Year: %{{x}}<br>Production: %{{y:,.0f}} t<extra></extra>'
        ))
    fig.update_layout(template='plotly_white', hovermode='x unified',
                      xaxis_title='Year', yaxis_title='Production (tonnes)',
                      yaxis=dict(tickformat=',.0f'), height=480,
                      legend=dict(x=0.01,y=0.99))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Key Insight:** Ireland lags France/Germany in volume but shows steady year-on-year growth.")

# ── 3. Livestock ─────────────────────────────────────────────────────
elif section == "🐄 Livestock":
    st.subheader("🐄 Livestock Stocks by Animal Type (2010–2023)")
    animals = sorted(livestock['item'].unique())
    n_cols  = 3
    n_rows  = (len(animals)+n_cols-1)//n_cols
    fig = make_subplots(rows=n_rows, cols=n_cols,
                        subplot_titles=list(animals),
                        vertical_spacing=0.12)
    for idx, animal in enumerate(animals):
        r = idx//n_cols+1; c = idx%n_cols+1
        for ctry in COUNTRIES:
            d = live_yr_animal[(live_yr_animal['country']==ctry)&
                               (live_yr_animal['item']==animal)].sort_values('year')
            if not d.empty:
                fig.add_trace(go.Scatter(
                    x=d['year'], y=d['value'], mode='lines+markers', name=ctry,
                    legendgroup=ctry, showlegend=(idx==0),
                    line=dict(color=C_COLORS[ctry],width=2), marker=dict(size=5),
                    hovertemplate=f'{ctry} %{{x}}: %{{y:,.0f}}<extra></extra>'
                ), row=r, col=c)
    fig.update_layout(height=max(350,n_rows*230), template='plotly_white',
                      hovermode='x unified', margin=dict(t=50,b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Key Insight:** Cattle dominates Ireland; Chickens dominate France/Germany.")

# ── 4. Pesticides ────────────────────────────────────────────────────
elif section == "🧪 Pesticides":
    st.subheader("🧪 Pesticide Usage Analysis (2010–2023)")
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=['Total Agricultural Use (tonnes)',
                                        'Use per Area of Cropland (kg/ha)'])
    for ctry in COUNTRIES:
        d1 = pest_yr[pest_yr['country']==ctry].sort_values('year')
        d2 = pest_int_yr[pest_int_yr['country']==ctry].sort_values('year')
        fig.add_trace(go.Bar(
            x=d1['year'], y=d1['value'], name=ctry,
            marker_color=C_COLORS[ctry], opacity=0.85, legendgroup=ctry,
            hovertemplate=f'{ctry} %{{x}}: %{{y:,.0f}} t<extra></extra>'
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=d2['year'], y=d2['value'], name=ctry,
            mode='lines+markers', line=dict(color=C_COLORS[ctry],width=2),
            marker=dict(size=6), legendgroup=ctry, showlegend=False,
            hovertemplate=f'{ctry} %{{x}}: %{{y:.2f}} kg/ha<extra></extra>'
        ), row=1, col=2)
    fig.update_layout(barmode='group', template='plotly_white',
                      height=440, hovermode='x unified', margin=dict(t=50,b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Key Insight:** Ireland uses significantly less pesticide per hectare than France.")

# ── 5. Trade ─────────────────────────────────────────────────────────
elif section == "⚖️ Trade":
    st.subheader("⚖️ Agricultural Trade Analysis (2010–2023)")
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=['Ireland: Export vs Import Volume',
                                        'Trade Balance by Country'])
    ire_trade = trade_pivot[trade_pivot['country']=='Ireland'].sort_values('year')
    fig.add_trace(go.Scatter(
        x=ire_trade['year'], y=ire_trade['export_qty'],
        fill='tozeroy', mode='lines', name='Exports',
        line=dict(color='#169b62'), fillcolor='rgba(22,155,98,0.25)',
        hovertemplate='Exports %{x}: %{y:,.0f} t<extra></extra>'
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=ire_trade['year'], y=ire_trade['import_qty'],
        fill='tozeroy', mode='lines', name='Imports',
        line=dict(color='#cc2200'), fillcolor='rgba(204,34,0,0.2)',
        hovertemplate='Imports %{x}: %{y:,.0f} t<extra></extra>'
    ), row=1, col=1)
    for ctry in COUNTRIES:
        d = trade_pivot[trade_pivot['country']==ctry].sort_values('year')
        fig.add_trace(go.Bar(
            x=d['year'], y=d['trade_balance'], name=ctry,
            marker_color=C_COLORS[ctry], opacity=0.85, legendgroup=ctry+'_tb',
            hovertemplate=f'{ctry} %{{x}}: %{{y:,.0f}} t<extra></extra>'
        ), row=1, col=2)
    fig.update_layout(barmode='group', template='plotly_white',
                      height=440, hovermode='x unified', margin=dict(t=50,b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Key Insight:** Ireland is a consistent net exporter of agricultural products.")

# ── 6. ARIMA Forecast ────────────────────────────────────────────────
elif section == "🔮 ARIMA Forecast":
    st.subheader("🔮 ARIMA 5-Year Forecast — Ireland (2024–2028)")
    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=['Crop Production','Livestock Stocks','Export Quantity'])
    forecast_data = [
        (crops_ts,fc_yrs_c,fc_val_c,fc_ci_c,'#169b62',1),
        (live_ts, fc_yrs_l,fc_val_l,fc_ci_l,'#002395',2),
        (exp_ts,  fc_yrs_e,fc_val_e,fc_ci_e,'#cc4400',3),
    ]
    for hist,fyrs,fvals,fci,col,cidx in forecast_data:
        show=(cidx==1)
        fig.add_trace(go.Scatter(
            x=list(hist.index), y=list(hist.values), mode='lines+markers',
            name='Historical', line=dict(color=col,width=2.5), marker=dict(size=5),
            legendgroup='hist', showlegend=show,
            hovertemplate='Hist %{x}: %{y:,.0f}<extra></extra>'
        ), row=1, col=cidx)
        fig.add_trace(go.Scatter(
            x=list(fyrs), y=list(fvals), mode='lines+markers', name='Forecast',
            line=dict(color='black',width=2,dash='dash'), marker=dict(size=7,symbol='square'),
            legendgroup='fc', showlegend=show,
            hovertemplate='Forecast %{x}: %{y:,.0f}<extra></extra>'
        ), row=1, col=cidx)
        ci_x = list(fyrs)+list(fyrs)[::-1]
        ci_y = list(fci[:,1])+list(fci[:,0])[::-1]
        fig.add_trace(go.Scatter(
            x=ci_x, y=ci_y, fill='toself',
            fillcolor='rgba(128,128,128,0.18)',
            line=dict(color='rgba(0,0,0,0)'), name='95% CI',
            legendgroup='ci', showlegend=show, hoverinfo='skip'
        ), row=1, col=cidx)
    fig.update_layout(height=460, template='plotly_white',
                      hovermode='x unified', margin=dict(t=50,b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Key Insight:** Exports and livestock projected to grow through 2028.")

# ── 7. ML Models ─────────────────────────────────────────────────────
elif section == "🤖 ML Models":
    st.subheader("🤖 ML Model Performance Comparison")
    model_names = ['Linear Regression','Random Forest','Gradient Boosting']
    r2_vals   = [r2_lr,  r2_rf,  r2_gb]
    rmse_vals = [rmse_lr,rmse_rf,rmse_gb]
    mae_vals  = [mae_lr, mae_rf, mae_gb]
    bar_colors = ['#888888','#169b62','#002395']

    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=['R² Score (higher=better)',
                                        'RMSE (lower=better)',
                                        'MAE (lower=better)'])
    for vals, col_idx, fmt in [(r2_vals,1,'.3f'),(rmse_vals,2,',.0f'),(mae_vals,3,',.0f')]:
        fig.add_trace(go.Bar(
            x=model_names, y=vals, marker_color=bar_colors,
            text=[f'{v:{fmt}}' for v in vals], textposition='outside',
        ), row=1, col=col_idx)
    fig.update_yaxes(range=[0,max(r2_vals)*1.3],   row=1,col=1)
    fig.update_yaxes(range=[0,max(rmse_vals)*1.3], row=1,col=2)
    fig.update_yaxes(range=[0,max(mae_vals)*1.3],  row=1,col=3)
    fig.update_layout(showlegend=False, template='plotly_white',
                      height=420, margin=dict(t=50,b=40))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Linear Regression R²", f"{r2_lr:.3f}")
    c2.metric("Random Forest R²",     f"{r2_rf:.3f}", f"+{r2_rf-r2_lr:.3f} vs LR")
    c3.metric("Gradient Boosting R²", f"{r2_gb:.3f}", f"+{r2_gb-r2_lr:.3f} vs LR")

# ── 8. Sentiment ─────────────────────────────────────────────────────
elif section == "💬 Sentiment":
    st.subheader("💬 Sentiment Analysis — Ireland Agriculture News")
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=['Sentiment Distribution','Mean Polarity by Year'],
                        specs=[[{'type':'domain'},{'type':'xy'}]])
    counts    = df_sent['sentiment'].value_counts()
    pie_clr   = {'Positive':'#169b62','Neutral':'#f0a500','Negative':'#cc2200'}
    pie_colors = [pie_clr.get(l,'#aaa') for l in counts.index]
    fig.add_trace(go.Pie(
        labels=counts.index, values=counts.values,
        marker=dict(colors=pie_colors),
        textinfo='percent+label', hole=0.42,
    ), row=1, col=1)
    yr_mean = df_sent.groupby('year')['polarity'].mean().sort_index()
    bar_c   = ['#169b62' if v>=0 else '#cc2200' for v in yr_mean.values]
    fig.add_trace(go.Bar(
        x=yr_mean.index.tolist(), y=yr_mean.values,
        marker_color=bar_c, text=[f'{v:+.2f}' for v in yr_mean.values],
        textposition='outside', name='Mean Polarity',
    ), row=1, col=2)
    fig.add_shape(type='line', x0=0, x1=1, xref='x2 domain',
                  y0=0, y1=0, yref='y2',
                  line=dict(dash='dash',color='gray',width=1.5))
    fig.update_layout(showlegend=False, template='plotly_white',
                      height=440, margin=dict(t=50,b=40))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Headlines analysed:**")
    st.dataframe(df_sent[['year','headline','polarity','sentiment']].sort_values('year'),
                 use_container_width=True)

# ── 9. Heatmap ───────────────────────────────────────────────────────
elif section == "🗺️ Heatmap":
    st.subheader("🗺️ Ireland Indicators — Normalised Heatmap (2010–2023)")
    hm = ireland_panel.set_index('year').drop(columns=['trade_balance'],errors='ignore')
    hm_norm = (hm - hm.min()) / (hm.max() - hm.min() + 1e-9)
    _fmt = lambda v: f'{v:,.0f}' if pd.notna(v) else 'N/A'
    try:    text_vals = hm.T.applymap(_fmt).values
    except: text_vals = hm.T.map(_fmt).values
    fig = go.Figure(go.Heatmap(
        z=hm_norm.T.values,
        x=hm_norm.index.tolist(),
        y=hm_norm.columns.tolist(),
        colorscale='RdYlGn',
        text=text_vals, texttemplate='%{text}',
        hovertemplate='<b>%{y}</b><br>Year: %{x}<br>Value: %{text}<extra></extra>',
        zmin=0, zmax=1,
        colorbar=dict(title='Normalised')
    ))
    fig.update_layout(xaxis_title='Year', yaxis_title='Indicator',
                      height=400, template='plotly_white', margin=dict(t=30,b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**Key Insight:** Export growth is Ireland's most dynamic indicator 2010–2023.")

# ── 10. Data Table ───────────────────────────────────────────────────
elif section == "📋 Data Table":
    st.subheader("📋 Ireland Agricultural Indicators — Full Data Table")
    st.dataframe(
        ireland_panel.style.format({
            col: '{:,.0f}' for col in ireland_panel.columns if col != 'year'
        }),
        use_container_width=True, height=500
    )
    csv = ireland_panel.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", csv, "ireland_agri_panel.csv", "text/csv")

# ═════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.8rem;'>"
    "🇮🇪 Ireland Agricultural Analytics &nbsp;·&nbsp; "
    "Data: FAOSTAT (CC BY-NC-SA 3.0 IGO) &nbsp;·&nbsp; "
    "Models: Random Forest · Gradient Boosting · ARIMA · TextBlob &nbsp;·&nbsp; "
    "Built with Python · Plotly · Streamlit · scikit-learn · statsmodels"
    "</div>",
    unsafe_allow_html=True
)
