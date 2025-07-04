import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta
import easyocr
from PIL import Image
import tempfile
import requests

st.set_page_config(page_title="🔥 محلل تداول ذكي بالصور", layout="wide")

def ocr_detect_prices(image):
    reader = easyocr.Reader(['en'], gpu=False)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
        image.convert("RGB").save(temp.name, format="JPEG")
        result = reader.readtext(temp.name)
    prices = []
    texts = []
    for _, text, _ in result:
        texts.append(text)
        try:
            prices.append(float(text.replace(",", "").replace("$", "")))
        except:
            continue
    return prices, texts

def fetch_klines(symbol, interval, limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qav", "trades", "tb_base_vol", "tb_qav", "ignore"
        ])
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        df["time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df
    except:
        return None

def generate_recommendation(df):
    close = df["close"]
    rsi = ta.momentum.RSIIndicator(close).rsi()
    macd = ta.trend.MACD(close).macd_diff()
    ma20 = close.rolling(window=20).mean()
    signal = ""
    if rsi.iloc[-1] < 30 and macd.iloc[-1] > 0 and close.iloc[-1] > ma20.iloc[-1]:
        signal = "✅ شراء (فرصة صعود قوية)"
    elif rsi.iloc[-1] > 70 and macd.iloc[-1] < 0 and close.iloc[-1] < ma20.iloc[-1]:
        signal = "❌ بيع (احتمال هبوط)"
    else:
        signal = "🔁 انتظر (لا توجد فرصة واضحة الآن)"
    return signal, rsi, macd, ma20

st.title("📊 محلل تداول ذكي بالصور + بيانات Binance")

symbol = st.text_input("🔹 اسم العملة (مثال: BTCUSDT)", value="BTCUSDT").upper()
timeframe = st.selectbox("⏱️ اختر الفريم الزمني", ["1m", "3m", "5m", "15m", "1h", "4h", "1d"], index=4)

uploaded_file = st.file_uploader("📤 ارفع صورة الشارت (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="📸 الصورة التي تم رفعها", use_column_width=True)

    with st.expander("📖 نتيجة تحليل الصورة (OCR)"):
        prices, texts = ocr_detect_prices(image)
        if prices:
            st.success(f"✅ تم اكتشاف {len(prices)} سعر | آخر سعر: {prices[-1]}")
        else:
            st.warning("⚠️ لم يتم العثور على أسعار من الصورة")
        for t in texts:
            st.write(f"- {t}")

    st.markdown("---")
    st.subheader("📈 تحليل فني فعلي من Binance")

    df = fetch_klines(symbol, timeframe)
    if df is None:
        st.error("❌ فشل في جلب بيانات العملة، تأكد من الاسم الصحيح")
    else:
        recommendation, rsi, macd, ma = generate_recommendation(df)
        st.success(f"📌 التوصية: {recommendation}")

        entry = df["close"].iloc[-1]
        stop = round(entry * 0.97, 5)
        take = round(entry * 1.05, 5)
        rr = round((take - entry) / (entry - stop), 2)

        st.markdown(f"🔹 سعر الدخول: **{entry}**")
        st.markdown(f"🔻 وقف الخسارة: **{stop}**")
        st.markdown(f"🎯 جني الأرباح: **{take}**")
        st.markdown(f"📊 نسبة R/R: **{rr}**")

        st.markdown("---")
        st.subheader("📉 الرسم البياني مع المؤشرات")

        fig, ax = plt.subplots(figsize=(10,4))
        ax.plot(df["time"], df["close"], label="السعر", color="blue")
        ax.plot(df["time"], ma, label="MA20", color="orange")
        ax.set_title(f"الرسم البياني لـ {symbol}")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        st.markdown("🔎 المؤشرات الفنية:")
        st.line_chart(pd.DataFrame({"RSI": rsi, "MACD": macd}, index=df["time"]))

else:
    st.info("👆 ارفع صورة شارت ليبدأ التحليل.")

