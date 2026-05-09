import streamlit as st
import json
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import firestore
from PIL import Image

# =========================================
# 1. إعدادات الصفحة واللغة
# =========================================
st.set_page_config(page_title="VPC Solar Pro", page_icon="☀️", layout="wide")

if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

# قاموس الترجمة
texts = {
    'ar': {
        'title': "☀️ VPC Solar Pro",
        'welcome': "مرحباً",
        'calc': "حاسبة الطاقة الشمسية",
        'comp': "شركات التركيب",
        'orders': "طلباتي",
        'contact': "تواصل معنا",
        'logout': "تسجيل خروج",
        'save': "حفظ الحسابات",
        'success': "تم حفظ البيانات بنجاح",
        'lang_btn': "🌐 English",
        'login_title': "تسجيل الدخول",
        'user_label': "اسم المستخدم",
        'pass_label': "كلمة المرور",
        'login_btn': "دخول"
    },
    'en': {
        'title': "☀️ VPC Solar Pro",
        'welcome': "Welcome",
        'calc': "Solar Calculator",
        'comp': "Installers",
        'orders': "My Orders",
        'contact': "Contact Us",
        'logout': "Logout",
        'save': "Save Data",
        'success': "Data saved successfully",
        'lang_btn': "🌐 العربية",
        'login_title': "Login",
        'user_label': "Username",
        'pass_label': "Password",
        'login_btn': "Login"
    }
}
L = texts[st.session_state.lang]

# =========================================
# 2. الاتصال بـ Firebase (Firestore)
# =========================================
try:
    if "textkey" in st.secrets:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=key_dict["project_id"])
except Exception as e:
    st.error(f"Firestore Error: {e}")

# =========================================
# 3. نظام تسجيل الدخول (Simple & Secure)
# =========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(L['login_title'])
    with st.form("login_form"):
        user_input = st.text_input(L['user_label'])
        pass_input = st.text_input(L['pass_label'], type="password")
        if st.form_submit_button(L['login_btn']):
            if user_input == "mohamed" and pass_input == "123456":
                st.session_state.logged_in = True
                st.session_state.username = user_input
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
    st.stop()

# =========================================
# 4. التطبيق الرئيسي (بعد الدخول)
# =========================================

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("logo.png", width=150)
    except:
        st.title("☀️ VPC Solar")
    
    st.write(f"👤 {L['welcome']} {st.session_state.username}")
    
    if st.button(L['lang_btn']):
        st.session_state.lang = 'en' if st.session_state.lang == 'ar' else 'ar'
        st.rerun()
        
    page = st.radio("القائمة / Menu", [L['calc'], L['comp'], L['orders'], L['contact']])
    
    if st.button(L['logout']):
        st.session_state.logged_in = False
        st.rerun()

# --- حاسبة الطاقة الشمسية ---
if page == L['calc']:
    st.title(L['calc'])
    col1, col2 = st.columns(2)
    with col1:
        power = st.number_input("إجمالي الأحمال (وات)", min_value=10, value=1000)
        hours = st.number_input("ساعات التشغيل", min_value=1, value=5)
    with col2:
        voltage = st.selectbox("جهد النظام", [12, 24, 48])
        
    daily_energy = power * hours
    st.metric("الاستهلاك اليومي", f"{daily_energy} Wh")
    
    if st.button(L['save']):
        db.collection("solar_calculations").add({
            "user": st.session_state.username,
            "daily_energy": daily_energy,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        st.success(L['success'])

# --- صفحة الشركات ---
elif page == L['comp']:
    st.title(L['comp'])
    st.info("📍 قائمة الشركات المعتمدة (KarmSolar, Cairo Solar, Sunprism)")

# --- صفحة طلباتي ---
elif page == L['orders']:
    st.title(L['orders'])
    docs = db.collection("solar_calculations").where("user", "==", st.session_state.username).stream()
    for doc in docs:
        d = doc.to_dict()
        st.info(f"✅ حساب قدرة: {d.get('daily_energy')} Wh | التاريخ: {d.get('timestamp')}")

# --- تواصل معنا ---
elif page == L['contact']:
    st.title(L['contact'])
    with st.form("contact"):
        msg = st.text_area("رسالتك")
        if st.form_submit_button("إرسال"):
            db.collection("messages").add({
                "user": st.session_state.username,
                "message": msg,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("تم الإرسال!")

st.markdown("---")
st.caption("VPC Solar Pro © 2026")
