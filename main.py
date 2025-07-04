import streamlit as st
import pandas as pd
import requests
import ta
import numpy as np

st.set_page_config(page_title="📊 تحليل شموع وتوقعات متقدمة مع نقاط دخول", layout="centered")
st.title("📈 تحليل الشموع مع Entry, Stoploss و R/R")

def fetch_klines(symbol, interval, limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    df.set_index("open_time", inplace=True)
    return df

def calculate_kdj(df, n=14, k_period=3, d_period=3):
    low_min = df['low'].rolling(window=n).min()
    high_max = df['high'].rolling(window=n).max()
    rsv = (df['close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(com=k_period-1, adjust=False).mean()
    d = k.ewm(com=d_period-1, adjust=False).mean()
    j = 3 * k - 2 * d
    df['K'] = k
    df['D'] = d
    df['J'] = j
    return df

def analyze_data(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['ema'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df = calculate_kdj(df)
    df.dropna(inplace=True)
    return df

def predict_candle(df):
    latest = df.iloc[-1]
    if (latest['rsi'] < 30 and latest['macd'] > latest['macd_signal'] and latest['J'] < 20):
        return "صعود (شراء)"
    elif (latest['rsi'] > 70 and latest['macd'] < latest['macd_signal'] and latest['J'] > 80):
        return "هبوط (بيع)"
    else:
        return "تثبيت (انتظار)"

def calculate_trade_levels(df, risk_percent=0.5, rr_ratio=3):
    # Entry price = آخر سعر إغلاق
    entry = df['close'].iloc[-1]

    # وقف الخسارة = أقل سعر خلال آخر 5 شموع ناقص نسبة مخاطرة (risk_percent)
    stoploss = df['low'].iloc[-5:].min() * (1 - risk_percent / 100)

    # جني الأرباح = Entry + (Entry - Stoploss) * rr_ratio
    take_profit = entry + (entry - stoploss) * rr_ratio

    # حساب نسبة المخاطرة إلى المكافأة
    risk = entry - stoploss
    reward = take_profit - entry
    rr = reward / risk if risk != 0 else np.nan

    return entry, stoploss, take_profit, rr

symbol = st.text_input("اسم العملة (مثال: BTCUSDT):", value="BTCUSDT")
interval = st.selectbox("اختر الفاصل الزمني:", ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"])
limit = st.slider("عدد الشموع للتحميل:", 50, 500, 100)

if st.button("تحميل وتحليل البيانات"):
    try:
        df = fetch_klines(symbol, interval, limit)
        df = analyze_data(df)
        st.success("✅ تم تحميل وتحليل البيانات!")

        st.subheader("آخر بيانات الشموع")
        st.dataframe(df.tail(10))

        st.subheader("الرسم البياني للسعر (Close)")
        st.line_chart(df['close'])

        st.subheader("مؤشرات فنية")
        st.line_chart(df[['rsi', 'ema', 'macd', 'macd_signal', 'K', 'D', 'J']])

        st.subheader("تحليل الشموع وتوصية التداول")
        recommendation = predict_candle(df)
        st.markdown(f"### 🔮 التوقع للشمعة القادمة: **{recommendation}**")

        entry, stoploss, take_profit, rr = calculate_trade_levels(df)
        st.markdown(f"**نقطة الدخول (Entry):** {entry:.4f}")
        st.markdown(f"**وقف الخسارة (Stoploss):** {stoploss:.4f}")
        st.markdown(f"**جني الأرباح (Take Profit):** {take_profit:.4f}")
        st.markdown(f"**نسبة المخاطرة إلى المكافأة (R/R):** {rr:.2f}")

    except Exception as e:
        st.error(f"حدث خطأ: {e}")