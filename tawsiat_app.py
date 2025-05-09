
# واجهة احترافية - نظام توصيات مقسم استثمار / مضاربة - Streamlit
# تمهيد لبناء البطاقات والربط الكامل مع Polygon + NewsAPI + Google RSS

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

st.set_page_config(page_title="توصيات الأسهم الشرعية", layout="wide")
st.title("📊 نظام التوصيات الشرعي - واجهة احترافية")

API_KEY = "YOUR_API_KEY_HERE"  # Polygon
NEWS_API_KEY = "9071a77124c3425ab844422c724a93b5"  # NewsAPI

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

def fetch_news(ticker):
    results = []

    # NewsAPI
    url_api = f"https://newsapi.org/v2/everything?q={ticker}&sortBy=publishedAt&pageSize=1&apiKey={NEWS_API_KEY}"
    r1 = requests.get(url_api)
    if r1.status_code == 200:
        articles = r1.json().get("articles", [])
        if articles:
            article = articles[0]
            title = article['title']
            url = article['url']
            desc = article['description'] or ""
            sentiment = "🔴 سلبي" if any(word in desc.lower() for word in ["downgrade", "lawsuit", "loss", "decline", "drop", "cut"]) else "🟢 إيجابي"
            results.append((title, url, sentiment))

    # Google News RSS
    from xml.etree import ElementTree as ET
    rss_url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
    r2 = requests.get(rss_url)
    if r2.status_code == 200:
        root = ET.fromstring(r2.content)
        items = root.findall(".//item")
        if items:
            title = items[0].find("title").text
            url = items[0].find("link").text
            desc = items[0].find("description").text if items[0].find("description") is not None else ""
            sentiment = "🔴 سلبي" if any(word in desc.lower() for word in ["downgrade", "lawsuit", "loss", "decline", "drop", "cut"]) else "🟢 إيجابي"
            results.append((title, url, sentiment))

    return results

def analyze_stock(df, mode):
    df['EMA'] = df['Close'].ewm(span=50 if mode=="استثمار" else 9).mean()
    close = df['Close'].iloc[-1]
    ema = df['EMA'].iloc[-1]
    signal = close > ema if mode=="مضاربة" else close < ema
    stop = round(close * (0.95 if mode=="استثمار" else 0.97), 2)
    targets = [round(close * r, 2) for r in [1.03, 1.06, 1.10]]
    duration = "أسبوعين - شهر" if mode == "استثمار" else "1-3 أيام"
    reason = "كسر متوسط EMA" if signal else "دون متوسط EMA بدون اختراق"
    confidence = 0
    if signal:
        confidence += 50
        if mode == "استثمار" and close < ema * 0.98:
            confidence += 25
        if mode == "مضاربة" and df['Volume'].iloc[-1] > df['Volume'].rolling(20).mean().iloc[-1]:
            confidence += 25
    return signal, targets, stop, duration, reason, confidence, df.index[-1].date()

for mode in ["استثمار", "مضاربة"]:
    st.header(f"{'👑' if mode=='استثمار' else '⚡'} أسهم {mode}")
    valid_signals = []
    invalid_signals = []
    for symbol in stocks[mode]:
        df = fetch_data(symbol)
        if df.empty:
            invalid_signals.append((symbol, None, None))
            continue
        signal, targets, stop, dur, reason, confidence, last_date = analyze_stock(df, mode)
        news_items = fetch_news(symbol)
        if signal:
            valid_signals.append((symbol, df, targets, stop, dur, reason, confidence, last_date, news_items))
        else:
            invalid_signals.append((symbol, df, last_date, news_items))

    if valid_signals:
        st.subheader("✅ أسهم صالحة للدخول")
        cols = st.columns(len(valid_signals))
        for i, (symbol, df, targets, stop, dur, reason, confidence, last_date, news_items) in enumerate(valid_signals):
            with cols[i]:
                st.markdown(f"### {symbol}")
                st.metric(label="📈 السعر الحالي", value=f"${df['Close'].iloc[-1]:.2f}")
                st.markdown(f"**📅 تاريخ البيانات:** {last_date}")
                st.markdown(f"**🧭 نوع التوصية:** {mode}")
                st.markdown(f"**✅ إشارة دخول:** نعم")
                st.markdown(f"🎯 الأهداف:")
                for idx, t in enumerate(targets, 1):
                    st.markdown(f"- 🎯 هدف {idx}: {t}")
                st.markdown(f"🛑 وقف الخسارة: {stop}")
                st.markdown(f"⏱ المدة المتوقعة: {dur}")
                st.markdown(f"🧠 السبب: {reason}")
                st.markdown(f"💡 مؤشر الثقة: `{confidence}%`")
                if news_items:
                    for title, url, sentiment in news_items:
                        st.markdown(f"**📢 خبر:** [{title}]({url}) – {sentiment}")

    if invalid_signals:
        st.subheader("🚫 أسهم غير صالحة للدخول")
        cols = st.columns(len(invalid_signals))
        for i, (symbol, df, last_date, news_items) in enumerate(invalid_signals):
            with cols[i]:
                st.markdown(f"### {symbol}")
                if df is None:
                    st.error(f"❌ لا توجد بيانات حالياً لـ {symbol}")
                else:
                    st.metric(label="📈 السعر الحالي", value=f"${df['Close'].iloc[-1]:.2f}")
                    st.markdown(f"**📅 تاريخ البيانات:** {last_date}")
                    st.markdown(f"**🧭 نوع التوصية:** {mode}")
                    st.markdown("**✅ إشارة دخول:** لا")
                    if news_items:
                        for title, url, sentiment in news_items:
                            st.markdown(f"**📢 خبر:** [{title}]({url}) – {sentiment}")
