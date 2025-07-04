import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import easyocr
import tempfile
import requests
import pandas as pd

# Binance API endpoint for klines
BINANCE_API_URL = "https://api.binance.com/api/v3/klines"

def get_binance_klines(symbol: str, interval: str, limit=100):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        response = requests.get(BINANCE_API_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        # Create DataFrame
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df
    except Exception as e:
        st.error(f"❌ خطأ في جلب بيانات Binance: {e}")
        return None

def t(ar, en):
    language = st.session_state.get("language", "English")
    return ar if language == "العربية" else en

def analyze_candle(open_price, close_price):
    # بسيط: شمعة صاعدة لو السعر اغلق اعلى من الافتتاح، هابطة بالعكس
    if close_price > open_price:
        return "صاعدة", "Bullish"
    elif close_price < open_price:
        return "هابطة", "Bearish"
    else:
        return "حيادية", "Neutral"

def main():
    st.set_page_config(page_title="تحليل تداول متقدم مع صورة", layout="wide")
    if "language" not in st.session_state:
        st.session_state.language = "English"

    language = st.selectbox("🌐 اختر اللغة / Select Language", ["العربية", "English"], index=1)
    st.session_state.language = language

    st.title(t("📊 تطبيق تحليل تداول متقدم مع صورة و Binance API", "Advanced Trading Analysis with Image and Binance API"))

    st.markdown(t(
        "اختر العملة والفريم الزمني ثم ارفع صورة الشارت للتحليل.",
        "Select symbol and timeframe, then upload a chart image for analysis."
    ))

    symbol_input = st.text_input(t("🔹 رمز العملة (مثال: BTCUSDT):", "🔹 Symbol (e.g., BTCUSDT):"), value="BTCUSDT").upper()
    timeframe = st.selectbox(t("⏰ اختر الفريم الزمني:", "⏰ Select timeframe:"), 
                             ["3m", "5m", "15m", "30m", "1h", "4h", "1d"], index=4)

    uploaded_file = st.file_uploader(t("📤 ارفع صورة الشارت", "📤 Upload Chart Image"), type=["png", "jpg", "jpeg"])

    df = get_binance_klines(symbol_input, timeframe)
    if df is None:
        st.stop()

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption=t("📊 الشارت المرفوع", "Uploaded Chart"), use_column_width=True)
        temp = tempfile.NamedTemporaryFile(delete=False)
        image.save(temp.name)

        st.markdown("---")
        st.subheader(t("📖 قراءة الأرقام والنصوص من الصورة باستخدام OCR", "📖 OCR Text Extraction from Image"))
        reader = easyocr.Reader(['en'], gpu=False)
        result = reader.readtext(temp.name)

        prices = []
        texts = []
        for bbox, text, conf in result:
            texts.append(text)
            try:
                num = float(text.replace(',', '').replace('$', ''))
                prices.append(num)
            except:
                pass

        if prices:
            last_price = prices[-1]
            st.success(t(f"📌 آخر سعر مكتشف من الصورة: {last_price}", f"📌 Last detected price from image: {last_price}"))
        else:
            last_price = df["close"].iloc[-1]
            st.warning(t("⚠️ لم يتم اكتشاف سعر واضح من الصورة، سيتم استخدام سعر Binance الحالي.", 
                         "⚠️ No clear price from image, using Binance last close price."))
            st.info(f"{t('سعر Binance الحالي:', 'Current Binance price:')} {last_price}")

        # نأخذ آخر شمعة من البيانات الحقيقية
        last_row = df.iloc[-1]
        candle_type_ar, candle_type_en = analyze_candle(last_row["open"], last_row["close"])

        st.markdown("---")
        st.subheader(t("📊 تحليل الشمعة الأخيرة من بيانات Binance", "📊 Last Candle Analysis from Binance Data"))
        st.markdown(t(f"✅ نوع الشمعة الأخيرة: **{candle_type_ar}**", f"✅ Last candle type: **{candle_type_en}**"))
        st.markdown(t(f"📈 الاتجاه العام: **{'صاعد' if last_row['close'] > last_row['open'] else 'هابط'}**",
                      f"📈 General trend: **{'Bullish' if last_row['close'] > last_row['open'] else 'Bearish'}**"))
        st.markdown(t(f"🕒 الفريم الزمني: **{timeframe}**", f"🕒 Timeframe: **{timeframe}**"))

        # التوصية
        st.subheader(t("💡 توصية التداول", "💡 Trade Recommendation"))
        entry = last_row["close"]
        sl = round(entry * 0.97, 5)
        tp = round(entry * 1.05, 5)
        st.markdown(t(f"🟢 الدخول: شراء عند {entry}", f"🟢 Entry: Buy at {entry}"))
        st.markdown(t(f"🔻 وقف الخسارة: {sl}", f"🔻 Stop Loss: {sl}"))
        st.markdown(t(f"🎯 جني الأرباح: {tp}", f"🎯 Take Profit: {tp}"))
        st.markdown(t("🔁 نسبة R/R: تقريبًا 1 : 1.6", "🔁 R/R Ratio: approx. 1 : 1.6"))

        # رسم بياني لتاريخ السعر
        st.subheader(t("📈 رسم بياني للسعر التاريخي", "📈 Historical Price Chart"))
        plt.figure(figsize=(10, 4))
        plt.plot(df["close"].astype(float).values, color='blue')
        plt.title(t(f"السعر التاريخي لـ {symbol_input}", f"Historical Price of {symbol_input}"))
        plt.grid(True)
        st.pyplot(plt)

    else:
        st.info(t("👆 الرجاء رفع صورة شارت لبدء التحليل.", "👆 Please upload a chart image to begin."))

if __name__ == "__main__":
    main()
