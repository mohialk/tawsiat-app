import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="نظام التوصيات الشرعي", layout="centered")
st.title("📈 نظام التوصيات الشرعي للأسهم الأمريكية")

stocks = {
    "AAPL": "استثمار",
    "NVDA": "استثمار",
    "LLY": "استثمار",
    "V": "استثمار",
    "MA": "استثمار",
    "ORCL": "مضاربة",
    "AI": "مضاربة"
}

selected = st.selectbox("اختر السهم", options=list(stocks.keys()))

@st.cache_data
def load_data(symbol):
    return yf.download(symbol, period="6mo", interval="1d")

data = load_data(selected)

def analyze_investment(data):
    if 'Close' not in data.columns or data.empty:
        return pd.DataFrame()
    data = data.copy()
    data['EMA50'] = data['Close'].ewm(span=50).mean()
    if 'EMA50' in data.columns:
        data = data[data['EMA50'].notna()]
        data['Signal'] = data['Close'] < data['EMA50']
    else:
        data['Signal'] = False
    return data

def analyze_trade(data):
    if 'Close' not in data.columns or 'Volume' not in data.columns or data.empty:
        return pd.DataFrame()
    data = data.copy()
    data['EMA9'] = data['Close'].ewm(span=9).mean()
    data['VolumeMA20'] = data['Volume'].rolling(20).mean()
    if 'EMA9' in data.columns and 'VolumeMA20' in data.columns:
        data = data[data['EMA9'].notna() & data['VolumeMA20'].notna()]
        data['Signal'] = (data['Volume'] > 1.5 * data['VolumeMA20']) & (data['Close'] > data['EMA9'])
    else:
        data['Signal'] = False
    return data

result = pd.DataFrame()
mode = ""

if selected in stocks:
    if stocks[selected] == "استثمار":
        result = analyze_investment(data)
        mode = "📊 استثماري (توصية يومية)"
    elif stocks[selected] == "مضاربة":
        result = analyze_trade(data)
        mode = "⚡ مضاربة (توصية لحظية)"

if result.empty or 'Signal' not in result.columns:
    st.error("⚠️ لا توجد بيانات كافية لتحليل هذا السهم حالياً.")
else:
    latest = result.iloc[-1]
    signal = latest['Signal']

    st.subheader("🔍 تحليل السهم: " + selected)
    st.markdown(f"**النوع:** {mode}")
    st.markdown(f"**السعر الحالي:** {latest['Close']:.2f} دولار")

    if signal:
        st.success("✅ توجد إشارة دخول حالياً")
    else:
        st.warning("🚫 لا توجد إشارة دخول حالياً")

    fig, ax = plt.subplots()
    ax.plot(result['Close'], label='سعر الإغلاق')
    if 'EMA50' in result.columns:
        ax.plot(result['EMA50'], label='EMA50', linestyle='--')
    if 'EMA9' in result.columns:
        ax.plot(result['EMA9'], label='EMA9', linestyle='--')
    ax.set_title(f"السهم: {selected}")
    ax.legend()
    st.pyplot(fig)
