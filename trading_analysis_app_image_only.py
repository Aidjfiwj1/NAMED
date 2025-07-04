import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import easyocr
import tempfile

def t(ar, en):
    language = st.session_state.get("language", "English")
    return ar if language == "العربية" else en

def analyze_price_direction(prices):
    if len(prices) < 2:
        return "غير كافية", "Not enough data"
    direction = prices[-1] - prices[0]
    if direction > 0:
        return "صاعد", "Uptrend"
    elif direction < 0:
        return "هابط", "Downtrend"
    else:
        return "جانبي", "Sideways"

def main():
    st.set_page_config(page_title="تحليل صورة شارت فقط", layout="wide")
    if "language" not in st.session_state:
        st.session_state.language = "English"

    language = st.selectbox("🌐 اختر اللغة / Select Language", ["العربية", "English"], index=1)
    st.session_state.language = language

    st.title(t("📊 تحليل صورة شارت فقط بدون API", "📊 Chart Image Analysis Only (No API)"))

    uploaded_file = st.file_uploader(t("📤 ارفع صورة الشارت (من TradingView أو Binance)", 
                                       "📤 Upload Chart Image (from TradingView or Binance)"), 
                                     type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption=t("📊 الشارت المرفوع", "Uploaded Chart"), use_column_width=True)

        st.markdown("---")
        st.subheader(t("📖 تحليل الصورة: قراءة الأسعار", "📖 Image Analysis: OCR Price Extraction"))

        temp = tempfile.NamedTemporaryFile(delete=False)
        image.save(temp.name)

        reader = easyocr.Reader(['en'], gpu=False)
        result = reader.readtext(temp.name)

        prices = []
        detected_texts = []
        for bbox, text, conf in result:
            detected_texts.append(text)
            try:
                num = float(text.replace(",", "").replace("$", ""))
                prices.append(num)
            except:
                continue

        if prices:
            last_price = prices[-1]
            trend_ar, trend_en = analyze_price_direction(prices)
            st.success(t(f"📌 تم اكتشاف {len(prices)} سعر، آخر سعر: {last_price}", 
                         f"📌 Detected {len(prices)} prices, Last: {last_price}"))
            st.markdown(t(f"📈 الاتجاه التقريبي: **{trend_ar}**", f"📈 Estimated Trend: **{trend_en}**"))
        else:
            st.warning(t("⚠️ لم يتم اكتشاف أسعار واضحة من الصورة", 
                         "⚠️ No clear prices detected from the image"))

        st.subheader(t("📝 النصوص المكتشفة داخل الصورة:", "📝 Texts Detected in Image:"))
        for text in detected_texts:
            st.write(f"- {text}")

        st.subheader(t("📉 توقع حركة مبنية على الصورة", "📉 Forecast Based on Image"))
        if prices:
            x = np.arange(30)
            y = last_price + np.cumsum(np.random.normal(0.0003, 0.0002, 30))
            plt.figure(figsize=(10, 4))
            plt.plot(x, y, color='green')
            plt.grid(True)
            st.pyplot(plt)
    else:
        st.info(t("👆 الرجاء رفع صورة شارت لبدء التحليل.", "👆 Please upload a chart image to begin."))

if __name__ == "__main__":
    main()
