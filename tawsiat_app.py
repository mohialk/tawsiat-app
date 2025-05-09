import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="نظام التوصيات - Polygon", layout="centered")
st.markdown("<h1 style='text-align: center;'>📈 نظام التوصيات الشرعي للأسهم الأمريكية</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>بيانات مباشرة من Polygon.io</h4>", unsafe_allow_html=True)
st.divider()

API_KEY = "1dJxO4BEMIx170XvzTpNWdD7C7m76UuW"

stocks = {
    "AAPL": "استثمار",
    "NVDA": "استثمار",
    "LLY": "استثمار",
    "V": "استثمار",
    "MA": "استثمار",
    "ORCL": "مضاربة",
    "AI": "مضاربة"
}

selected = st.selectbox("📌 اختر السهم", options=list(stocks.keys()))

def fetch_polygon_data(ticker):
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=180)
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{from_date}/{to_date}?adjusted=true&sort=asc&limit=120&apiKey={API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return pd.DataFrame()
    data = r.json().get("results", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df['t'] = pd.to_datetime(df['t'], unit='ms')
    df.set_index('t', inplace=True)
    df.rename(columns={'c': 'Close', 'v': 'Volume'}, inplace=True)
    return df

def analyze_investment(df):
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df = df.dropna()
    df['Signal'] = df['Close'] < df['EMA50']
    return df

def analyze_trade(df):
    df['EMA9'] = df['Close'].ewm(span=9).mean()
    df['VolumeMA20'] = df['Volume'].rolling(20).mean()
    df = df.dropna()
    df['Signal'] = (df['Volume'] > 1.5 * df['VolumeMA20']) & (df['Close'] > df['EMA9'])
    return df

df = fetch_polygon_data(selected)

if df.empty:
    st.error("❌ لا توجد بيانات كافية للسهم حالياً.")
else:
    if stocks[selected] == "استثمار":
        result = analyze_investment(df)
        mode = "📊 استثماري (توصية يومية)"
    else:
        result = analyze_trade(df)
        mode = "⚡ مضاربة (توصية لحظية)"

    latest = result.iloc[-1]
    signal = latest['Signal']
    price = latest['Close']

    st.markdown(f"### 🧾 تحليل السهم: `{selected}`")
    st.markdown(f"**النوع:** {mode}")
    st.markdown(f"**السعر الحالي:** `{price:.2f}` دولار")

    if signal:
        st.success("✅ توجد إشارة دخول حالياً")
    else:
        st.warning("🚫 لا توجد إشارة دخول حالياً")

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(result['Close'], label='الإغلاق اليومي', linewidth=2)
    if 'EMA50' in result.columns:
        ax.plot(result['EMA50'], label='EMA50', linestyle='--')
    if 'EMA9' in result.columns:
        ax.plot(result['EMA9'], label='EMA9', linestyle='--')
    ax.set_title(f"سعر السهم: {selected}", fontsize=14)
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)
