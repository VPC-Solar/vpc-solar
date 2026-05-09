import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import firestore

# --- 1. الاتصال بـ Firebase ---
try:
    if "textkey" in st.secrets:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=key_dict["project_id"])
    else:
        st.error("مفتاح textkey غير موجود في Secrets")
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")

# --- 2. إعدادات الصفحة واللغة ---
st.set_page_config(page_title="VPC Solar Pro", page_icon="☀️", layout="wide")

if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

# قاموس النصوص للترجمة
texts = {
    'ar': {
        'title': "☀️ VPC Solar Pro",
        'home': "الرئيسية",
        'calc': "حاسبة الطاقة",
        'companies': "شركات التركيب",
        'orders': "طلباتي",
        'logout': "خروج",
        'welcome': "مرحباً بك في مستقبل الطاقة",
        'login_btn': "دخول",
        'calc_res': "النتائج الفنية:",
        'save_btn': "حفظ الحسابات"
    },
    'en': {
        'title': "☀️ VPC Solar Pro",
        'home': "Home",
        'calc': "Solar Calculator",
        'companies': "Installers",
        'orders': "My Orders",
        'logout': "Logout",
        'welcome': "Welcome to the future of energy",
        'login_btn': "Login",
        'calc_res': "Technical Results:",
        'save_btn': "Save Calculations"
    }
}

L = texts[st.session_state.lang]

# --- 3. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(L['title'])
    with st.form("login_form"):
        email = st.text_input("البريد الإلكتروني / Email")
        password = st.text_input("كلمة المرور / Password", type="password")
        if st.form_submit_button(L['login_btn']):
            if email and len(password) > 5:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.warning("أدخل إيميل وباسورد صحيح")
    st.stop()

# --- 4. القائمة الجانبية ---
with st.sidebar:
    st.title(L['title'])
    st.write(f"👤 {st.session_state.user_email}")
    
    if st.button("🌐 English" if st.session_state.lang == 'ar' else "🌐 العربية"):
        st.session_state.lang = 'en' if st.session_state.lang == 'ar' else 'ar'
        st.rerun()

    menu = [L['home'], L['calc'], L['companies'], L['orders'], L['logout']]
    choice = st.radio("القائمة", menu)

if choice == L['logout']:
    st.session_state.logged_in = False
    st.rerun()

# --- 5. الصفحات ---

# صفحة الرئيسية
if choice == L['home']:
    st.title(L['home'])
    st.subheader(L['welcome'])
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.info("🏠 أنظمة سكنية")
    with col2:
        st.success("🚜 أنظمة زراعية")

# صفحة حاسبة الطاقة (اللي كانت ناقصة)
elif choice == L['calc']:
    st.title(L['calc'])
    col1, col2 = st.columns(2)
    with col1:
        power = st.number_input("القدرة (وات)", value=1000)
        hours = st.number_input("ساعات التشغيل", value=5)
    with col2:
        voltage = st.selectbox("الجهد", [12, 24, 48])
    
    daily_energy = power * hours
    st.divider()
    st.subheader(L['calc_res'])
    st.metric("إنتاج اليوم", f"{daily_energy} Wh")
    
    if st.button(L['save_btn']):
        db.collection("solar_calculations").add({
            "user": st.session_state.user_email,
            "power_w": power,
            "daily_energy": daily_energy,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        st.success("تم الحفظ بنجاح!")

# صفحة الشركات
elif choice == L['companies']:
    st.title(L['companies'])
    st.write("📍 قائمة الشركات المعتمدة:")
    st.info("KarmSolar - Cairo Solar - Sunprism")

# صفحة طلباتي
elif choice == L['orders']:
    st.title(L['orders'])
    docs = db.collection("solar_calculations").where("user", "==", st.session_state.user_email).stream()
    for doc in docs:
        d = doc.to_dict()
        st.write(f"📅 {d.get('timestamp')} - القدرة: {d.get('power_w')}W")

st.markdown("---")
st.caption("VPC Solar © 2026")
