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

# قاموس الترجمة الموحد
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
        'lang_btn': "🌐 English"
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
        'lang_btn': "🌐 العربية"
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
# 3. نظام تسجيل الدخول (Login)
# =========================================
# الباسورد لـ mohamed هو: 123456
credentials = {
    "usernames": {
        "mohamed": {
            "name": "Mohamed",
            "password": "$2b$12$LQv3c1yqBW5l4Y6x2L1M8e8jM2lM9vJk7hM5sFQ9x9Q4mV8L2zY5K"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials, 
    "vpcsolar_cookie", 
    "abcdef", 
    cookie_expiry_days=30
)

# حل مشكلة ValueError بتحديد الـ location بشكل صريح
name, authentication_status, username = authenticator.login(location="main")

if authentication_status == False:
    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
elif authentication_status == None:
    st.warning("برجاء تسجيل الدخول للمتابعة")
elif authentication_status:

    # --- SIDEBAR (القائمة الجانبية) ---
    with st.sidebar:
        try:
            st.image("logo.png", width=150)
        except:
            st.write("☀️ VPC Solar")
        
        st.write(f"👤 {L['welcome']} {name}")
        
        # زر تبديل اللغة
        if st.button(L['lang_btn']):
            st.session_state.lang = 'en' if st.session_state.lang == 'ar' else 'ar'
            st.rerun()
            
        page = st.radio("القائمة / Menu", [L['calc'], L['comp'], L['orders'], L['contact']])
        authenticator.logout(L['logout'], "sidebar")

    # --- الصفحة الرئيسية: حاسبة الطاقة ---
    if page == L['calc']:
        st.title(L['calc'])
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input("إجمالي الأحمال (وات)", min_value=10, value=1000)
            hours = st.number_input("ساعات التشغيل", min_value=1, value=5)
        with col2:
            voltage = st.selectbox("جهد النظام", [12, 24, 48])
            
        daily_energy = power * hours
        st.subheader("📊 النتائج")
        st.metric(label="الاستهلاك اليومي", value=f"{daily_energy} Wh")
        
        if st.button(L['save']):
            try:
                db.collection("solar_calculations").add({
                    "user": username,
                    "power_w": power,
                    "daily_energy": daily_energy,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success(L['success'])
            except Exception as e:
                st.error(f"Error saving: {e}")

    # --- صفحة شركات التركيب ---
    elif page == L['comp']:
        st.title(L['comp'])
        companies = [
            {"name": "شمس أكتوبر", "loc": "6 أكتوبر", "rate": "⭐ 4.9"},
            {"name": "إيجيبت سولار", "loc": "القاهرة", "rate": "⭐ 4.7"}
        ]
        for c in companies:
            with st.expander(f"📍 {c['name']}"):
                st.write(f"الموقع: {c['loc']}")
                st.write(f"التقييم: {c['rate']}")
                st.button(f"طلب معاينة من {c['name']}")

    # --- صفحة طلباتي (عرض من Firestore) ---
    elif page == L['orders']:
        st.title(L['orders'])
        docs = db.collection("solar_calculations").where("user", "==", username).stream()
        for doc in docs:
            d = doc.to_dict()
            st.info(f"✅ حساب قدرة: {d.get('daily_energy')} Wh | التاريخ: {d.get('timestamp')}")

    # --- صفحة تواصل معنا ---
    elif page == L['contact']:
        st.title(L['contact'])
        with st.form("contact_form"):
            msg = st.text_area("رسالتك أو استفسارك")
            if st.form_submit_button("إرسال"):
                db.collection("messages").add({
                    "user": username,
                    "message": msg,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("تم الإرسال بنجاح!")

# --- Footer ---
st.markdown("---")
st.caption("VPC Solar Pro © 2026")
