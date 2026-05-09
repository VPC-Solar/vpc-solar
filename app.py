import streamlit as st
import streamlit_authenticator as stauth
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
        'calc': "حاسبة الطاقة",
        'comp': "شركات التركيب",
        'orders': "طلباتي",
        'contact': "تواصل معنا",
        'logout': "تسجيل خروج",
        'save': "حفظ الحسابات",
        'success': "تم الحفظ بنجاح"
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
        'success': "Saved Successfully"
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
    st.error(f"خطأ في قاعدة البيانات: {e}")

# =========================================
# 3. نظام تسجيل الدخول (Login)
# =========================================
# ملحوظة: الباسورد '123456' هو الـ Hash المكتوب تحت
credentials = {
    "usernames": {
        "mohamed": {
            "name": "Mohamed",
            "password": "$2b$12$LQv3c1yqBW5l4Y6x2L1M8e8jM2lM9vJk7hM5sFQ9x9Q4mV8L2zY5K" # كلمة السر 123456
        }
    }
}

authenticator = stauth.Authenticate(credentials, "vpcsolar_cookie", "abcdef", 30)
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
elif authentication_status == None:
    st.warning("برجاء تسجيل الدخول")
elif authentication_status:

    # --- SIDEBAR ---
    with st.sidebar:
        try:
            st.image("logo.png", width=150)
        except: pass
        
        st.write(f"{L['welcome']} {name}")
        
        if st.button("🌐 English" if st.session_state.lang == 'ar' else "🌐 العربية"):
            st.session_state.lang = 'en' if st.session_state.lang == 'ar' else 'ar'
            st.rerun()
            
        page = st.radio("Menu", [L['calc'], L['comp'], L['orders'], L['contact']])
        authenticator.logout(L['logout'], "sidebar")

    # --- صفحات التطبيق ---
    if page == L['calc']:
        st.title(L['calc'])
        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input("القدرة (Watt)", value=1000)
            hours = st.number_input("الساعات", value=5)
        with col2:
            voltage = st.selectbox("الجهد", [12, 24, 48])
            
        res = power * hours
        st.metric("الاستهلاك", f"{res} Wh")
        
        if st.button(L['save']):
            db.collection("solar_calculations").add({
                "user": username,
                "res": res,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(L['success'])

    elif page == L['comp']:
        st.title(L['comp'])
        st.info("📍 قائمة الشركات المعتمدة (KarmSolar, Cairo Solar)")

    elif page == L['orders']:
        st.title(L['orders'])
        docs = db.collection("solar_calculations").where("user", "==", username).stream()
        for doc in docs:
            st.write(f"✅ طلب بتاريخ: {doc.to_dict().get('timestamp')}")

    elif page == L['contact']:
        st.title(L['contact'])
        with st.form("contact"):
            msg = st.text_area("رسالتك")
            if st.form_submit_button("Send"):
                db.collection("messages").add({"user": username, "msg": msg})
                st.success("Sent!")
