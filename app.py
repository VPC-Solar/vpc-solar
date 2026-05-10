import streamlit as st
import json
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import firestore
from PIL import Image

# =========================================
# PAGE CONFIG
# =========================================
st.set_page_config(
    page_title="VPC Solar",
    page_icon="☀️",
    layout="wide"
)

# =========================================
# FIREBASE CONNECTION
# =========================================
try:
    if "textkey" in st.secrets:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=key_dict["project_id"])
except Exception as e:
    st.error(f"Firestore Error: {e}")

# =========================================
# 🌐 LANGUAGE DICTIONARY (قاموس اللغات)
# =========================================
texts = {
    'ar': {
        'welcome': "مرحباً بك",
        'logout': "تسجيل الخروج",
        'menu': "القائمة",
        'home': "الرئيسية",
        'calc': "حاسبة الطاقة الشمسية",
        'comp': "شركات التركيب",
        'plans': "خطط المتابعة",
        'contact': "تواصل معنا",
        'reg': "إنشاء حساب",
        'login_title': "🔐 تسجيل الدخول",
        'user_label': "اسم المستخدم",
        'pass_label': "كلمة المرور",
        'login_btn': "دخول",
        'error_msg': "اسم المستخدم أو كلمة المرور غير صحيحة"
    },
    'en': {
        'welcome': "Welcome",
        'logout': "Logout",
        'menu': "Menu",
        'home': "Home",
        'calc': "Solar Calculator",
        'comp': "Installers",
        'plans': "Monitoring Plans",
        'contact': "Contact Us",
        'reg': "Register",
        'login_title': "🔐 Login",
        'user_label': "Username",
        'pass_label': "Password",
        'login_btn': "Login",
        'error_msg': "Invalid username or password"
    }
}

# تهيئة اللغة الافتراضية (عربي)
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

# اختصار للوصول للنصوص بسهولة
L = texts[st.session_state.lang]

# =========================================
# 🔐 DYNAMIC LOGIN SYSTEM
# =========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title(L['login_title'])
    
    user_in = st.text_input(L['user_label'])
    pass_in = st.text_input(L['pass_label'], type="password")

    if st.button(L['login_btn']):
        if user_in == "mohamed" and pass_in == "123456":
            st.session_state.logged_in = True
            st.session_state.username = user_in
            st.rerun()
        else:
            try:
                users_ref = db.collection("users")
                query = users_ref.where("username", "==", user_in).stream()
                found = False
                for doc in query:
                    user_data = doc.to_dict()
                    if user_data.get("password") == pass_in:
                        st.session_state.logged_in = True
                        st.session_state.username = user_in
                        found = True
                        st.rerun()
                if not found:
                    st.error(L['error_msg'])
            except Exception as e:
                st.error(f"Error: {e}")
    st.stop()

# =========================================
# MAIN APP (بعد تسجيل الدخول)
# =========================================
if st.session_state.logged_in:
    username = st.session_state.username

    # ضبط التنسيق بناءً على اللغة (RTL للعربي و LTR للإنجليزي)
    direction = "rtl" if st.session_state.lang == 'ar' else "ltr"
    st.markdown(f"""
    <style>
    .main {{ direction: {direction}; text-align: {"right" if direction=="rtl" else "left"}; }}
    section[data-testid="stSidebar"] {{ direction: {direction}; }}
    .stButton > button {{
        background-color: #00BFFF;
        color: white;
        border-radius: 12px;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

    try:
        logo = Image.open("logo.png")
    except:
        logo = None

    # --- SIDEBAR ---
    with st.sidebar:
        if logo:
            st.image(logo, width=180)
        st.title("☀️ VPC Solar")
        st.write(f"{L['welcome']}: {username}")

        # زر تغيير اللغة في السايدبار
        new_lang = st.selectbox("Language / اللغة", ["العربية", "English"], index=0 if st.session_state.lang == 'ar' else 1)
        st.session_state.lang = 'ar' if new_lang == "العربية" else 'en'
        
        if st.button(L['logout']):
            st.session_state.logged_in = False
            st.rerun()

        page = st.radio(
            L['menu'],
            [L['home'], L['calc'], L['comp'], L['plans'], L['contact'], L['reg']]
        )

    # --- صفحات التطبيق (مثال لصفحة واحدة والباقي بنفس النمط) ---
    if page == L['home']:
        st.title(f"☀️ VPC Solar - {L['home']}")
        # هنا تكمل باقي محتوى الصفحات باستخدام متغيرات L['...']
