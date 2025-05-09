import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

st.set_page_config(page_title="توصيات الأسهم الشرعية", layout="wide")
st.title("📊 نظام التوصيات الشرعي - واجهة احترافية")

API_KEY = "1dJxO4BEMIx170XvzTpNWdD7C7m76UuW"

stocks = {
    "استثمار": ["AAPL", "NVDA", "LLY", "V", "MA"],
    "مضاربة": ["ORCL", "AI"]
}

def fetch_data(ticker):
    end = datetime.now().date()
    start = end - timedelta(days=180)
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start}/{end}?adjusted=true&sort=asc&limit=120&apiKey={API_KEY}"
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

def analyze_stock(df, mode):
    df['EMA'] = df['Close'].ewm(span=50 if mode == "استثمار" else 9).mean()
    signal = df['Close'].iloc[-1] > df['EMA'].iloc[-1] if mode == "مضاربة" else df['Close'].iloc[-1] < df['EMA'].iloc[-1]
    stop = round(df['Close'].iloc[-1] * (0.95 if mode == "استثمار" else 0.97), 2)
    target1 = round(df['Close'].iloc[-1] * 1.03, 2)
    target2 = round(df['Close'].iloc[-1] * 1.06, 2)
    target3 = round(df['Close'].iloc[-1] * 1.10, 2)
    duration = "أسبوعين - شهر" if mode == "استثمار" else "1-3 أيام"
    reason = "كسر متوسط EMA" if signal else "دون متوسط EMA بدون اختراق"
    return signal, target1, target2, target3, stop, duration, reason

for mode in ["استثمار", "مضاربة"]:
    st.header(f"{'👑' if mode == 'استثمار' else '⚡'} أسهم {mode}")
    cols = st.columns(len(stocks[mode]))
    for i, symbol in enumerate(stocks[mode]):
        with cols[i]:
            df = fetch_data(symbol)
            if df.empty:
                st.error(f"❌ لا توجد بيانات حالياً لـ {symbol}")
                continue
            signal, t1, t2, t3, stop, dur, reason = analyze_stock(df, mode)
            st.markdown(f"### {symbol}")
            st.metric(label="📈 السعر الحالي", value=f"${df['Close'].iloc[-1]:.2f}")
            st.markdown(f"**🧭 نوع التوصية:** {mode}")
            st.markdown(f"**✅ إشارة دخول:** {'نعم' if signal else 'لا'}")
            st.markdown(f"🎯 الأهداف: {t1}, {t2}, {t3}")
            st.markdown(f"🛑 وقف الخسارة: {stop}")
            st.markdown(f"⏱ المدة المتوقعة: {dur}")
            st.markdown(f"🧠 السبب: {reason}")
