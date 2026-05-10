import streamlit as st
import json
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import firestore
from PIL import Image

# =========================================
# 1. CONFIG & SETTINGS
# =========================================
st.set_page_config(page_title="VPC Solar", page_icon="☀️", layout="wide")

# =========================================
# 2. FIREBASE CONNECTION
# =========================================
try:
    if "textkey" in st.secrets:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=key_dict["project_id"])
except Exception as e:
    st.error(f"Firestore Error: {e}")

# =========================================
# 3. 🌐 MULTI-LANGUAGE DICTIONARY
# =========================================
texts = {
    'ar': {
        'welcome': "مرحباً بك", 'logout': "خروج", 'menu': "القائمة",
        'home': "الرئيسية", 'calc': "حاسبة الطاقة الشمسية", 'comp': "شركات التركيب",
        'plans': "خطط المتابعة", 'contact': "تواصل معنا", 'reg': "إنشاء حساب",
        'login_title': "🔐 تسجيل الدخول", 'user_label': "اسم المستخدم",
        'pass_label': "كلمة المرور", 'login_btn': "دخول",
        'error_msg': "اسم المستخدم أو كلمة المرور غير صحيحة",
        'sys_results': "📊 نتائج النظام المتوقعة"
    },
    'en': {
        'welcome': "Welcome", 'logout': "Logout", 'menu': "Menu",
        'home': "Home", 'calc': "Solar Calculator", 'comp': "Installers",
        'plans': "Monitoring Plans", 'contact': "Contact Us", 'reg': "Register",
        'login_title': "🔐 Login", 'user_label': "Username",
        'pass_label': "Password", 'login_btn': "Login",
        'error_msg': "Invalid username or password",
        'sys_results': "📊 Expected System Results"
    }
}

if 'lang' not in st.session_state: st.session_state.lang = 'ar'
L = texts[st.session_state.lang]

# =========================================
# 4. 🔐 DYNAMIC LOGIN SYSTEM
# =========================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

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
                    if doc.to_dict().get("password") == pass_in:
                        st.session_state.logged_in = True
                        st.session_state.username = user_in
                        found = True
                        st.rerun()
                if not found: st.error(L['error_msg'])
            except: st.error("Database Connection Error")
    st.stop()

# =========================================
# 5. MAIN APP UI (After Login)
# =========================================
username = st.session_state.username
direction = "rtl" if st.session_state.lang == 'ar' else "ltr"

st.markdown(f"""
<style>
    .main {{ direction: {direction}; text-align: {"right" if direction=="rtl" else "left"}; }}
    section[data-testid="stSidebar"] {{ direction: {direction}; }}
    .stButton > button {{ background-color: #00BFFF; color: white; border-radius: 10px; width: 100%; }}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("☀️ VPC Solar")
    st.write(f"{L['welcome']}: {username}")
    
    # تبديل اللغة
    lang_choice = st.selectbox("Language / اللغة", ["العربية", "English"], index=0 if st.session_state.lang == 'ar' else 1)
    st.session_state.lang = 'ar' if lang_choice == "العربية" else 'en'
    
    if st.button(L['logout']):
        st.session_state.logged_in = False
        st.rerun()
    
    st.markdown("---")
    page = st.radio(L['menu'], [L['home'], L['calc'], L['comp'], L['plans'], L['contact'], L['reg']])

# --- PAGES CONTENT ---
if page == L['home']:
    st.title(f"🏠 {L['home']}")
    st.subheader("VPC Solar Ecosystem")
    col1, col2 = st.columns(2)
    with col1:
        st.info("Residential Systems / الأنظمة السكنية")
        st.button("Explore Residential")
    with col2:
        st.success("Agricultural Systems / الأنظمة الزراعية")
        st.button("Explore Agricultural")

elif page == L['calc']:
    st.title(f"⚡ {L['calc']}")
    col1, col2 = st.columns(2)
    with col1:
        load = st.number_input("Total Load (Watts) / الأحمال", 100, 50000, 1000)
        h = st.number_input("Operating Hours / ساعات التشغيل", 1, 24, 5)
    with col2:
        v = st.selectbox("System Voltage / جهد النظام", [12, 24, 48])
    
    if st.button("Calculate / احسب الآن"):
        daily = load * h
        panels = round(daily / 400)
        st.divider()
        st.subheader(L['sys_results'])
        c1, c2 = st.columns(2)
        c1.metric("Daily Energy", f"{daily} Wh")
        c2.metric("Approx. Panels (400W)", f"{panels}")

elif page == L['comp']:
    st.title(f"🏢 {L['comp']}")
    st.write("Current verified companies in 6th of October City:")
    st.table(pd.DataFrame({
        "Company": ["Shams October", "VPC Partners", "Egypt Solar"],
        "Location": ["Industrial Zone", "Degla Palms", "Smart Village"],
        "Rating": ["5/5", "4.8/5", "4.5/5"]
    }))

elif page == L['plans']:
    st.title(f"📡 {L['plans']}")
    st.warning("IoT Monitoring is coming soon to your dashboard.")

elif page == L['contact']:
    st.title(f"📞 {L['contact']}")
    with st.form("c_form"):
        st.text_input("Name")
        st.text_area("Message")
        st.form_submit_button("Send")

elif page == L['reg']:
    st.title(f"📝 {L['reg']}")
    with st.form("reg_form"):
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")
        if st.form_submit_button("Register"):
            db.collection("users").add({"username": u, "password": p})
            st.success("Account Created!")

st.markdown("---")
st.caption("VPC Solar Pro © 2026")
