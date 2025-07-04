# NAMED 
st.set_page_config(page_title="تحليل ذكي للشارت", layout="wide")
st.title("📈 تحليل تداول ذكي من صورة شارت")

# اختيار اللغة
language = st.selectbox("🌐 اختر اللغة / Select Language", ["العربية", "English"])

def t(ar, en):
    return ar if language == "العربية" else en

st.markdown(t(
    \"\"\"
👋 مرحبًا بك في أداة تحليل الشموع الذكية  
ارفع صورة شارت من أي منصة وسنقوم بتحليل الاتجاه والتوصية بصفقة بيع أو شراء.
\"\"\",
    \"\"\"
👋 Welcome to the Smart Candlestick Analyzer  
Upload a chart image and we'll detect patterns, trend, and suggest Buy/Sell entries.
\"\"\"
))
