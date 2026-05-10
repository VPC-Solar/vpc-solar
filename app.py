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

# تهيئة حالة الصفحة إذا لم تكن موجودة
if "page" not in st.session_state:
    st.session_state.page = "الرئيسية"

# =========================================
# 🔐 DYNAMIC LOGIN & REGISTER SYSTEM
# =========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("☀️ مرحباً بك في VPC Solar")
    
    tab_login, tab_signup = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب جديد"])

    with tab_login:
        user_in = st.text_input("اسم المستخدم", key="login_user")
        pass_in = st.text_input("كلمة المرور", type="password", key="login_pass")

        if st.button("تسجيل الدخول", use_container_width=True):
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
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
                except Exception as e:
                    st.error(f"خطأ: {e}")

    with tab_signup:
        new_username = st.text_input("اختر اسم مستخدم", key="reg_user")
        new_email = st.text_input("البريد الإلكتروني", key="reg_email")
        new_password = st.text_input("اختر كلمة مرور", type="password", key="reg_pass")
        
        if st.button("إنشاء الحساب", use_container_width=True):
            if new_username and new_password:
                try:
                    users_ref = db.collection("users")
                    query = users_ref.where("username", "==", new_username).stream()
                    if any(query):
                        st.error("اسم المستخدم موجود بالفعل")
                    else:
                        users_ref.add({
                            "username": new_username, "email": new_email,
                            "password": new_password, "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("تم إنشاء الحساب بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")
    st.stop()

# =========================================
# MAIN APP (بعد تسجيل الدخول)
# =========================================
if st.session_state.logged_in:
    username = st.session_state.username

    # تحسين الـ CSS لإخفاء حدود الأزرار وجعلها تبدو كقائمة احترافية
    st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    section[data-testid="stSidebar"] { direction: rtl; }
    
    /* تصميم أزرار القائمة الجانبية */
    .stSidebar [data-testid="stButton"] button {
        background-color: transparent;
        color: white;
        border: none;
        text-align: right;
        font-size: 18px;
        width: 100%;
        justify-content: flex-start;
        padding: 10px 0px;
    }
    .stSidebar [data-testid="stButton"] button:hover {
        color: #00BFFF;
        background-color: rgba(255, 255, 255, 0.1);
    }
    
    /* زر تسجيل الخروج بلون مختلف في الأسفل */
    .logout-btn button {
        color: #FF4B4B !important;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("☀️ VPC Solar")
        st.write(f"مرحباً بك: **{username}**")
        st.markdown("---")
        
        # تحويل القائمة إلى أزرار بدلاً من Radio
        if st.button("🏠 الرئيسية"):
            st.session_state.page = "الرئيسية"
            st.rerun()
        if st.button("⚡ حاسبة الطاقة الشمسية"):
            st.session_state.page = "حاسبة الطاقة الشمسية"
            st.rerun()
        if st.button("🏢 شركات التركيب"):
            st.session_state.page = "شركات التركيب"
            st.rerun()
        if st.button("📡 خطط المتابعة"):
            st.session_state.page = "خطط المتابعة"
            st.rerun()
        if st.button("📞 تواصل معنا"):
            st.session_state.page = "تواصل معنا"
            st.rerun()

        # زر تسجيل الخروج في الأسفل
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 تسجيل الخروج", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- صفحات التطبيق بناءً على الاختيار ---
    page = st.session_state.page

    if page == "الرئيسية":
        st.title("☀️ VPC Solar")
        st.subheader("Smart Solar Solutions")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("## 🏠 الأنظمة السكنية")
            st.button("استكشف الأنظمة السكنية")
        with col2:
            st.markdown("## 🚜 الأنظمة الزراعية")
            st.button("استكشف الأنظمة الزراعية")

    elif page == "حاسبة الطاقة الشمسية":
        st.title("⚡ حاسبة الطاقة الشمسية")
        power = st.number_input("إجمالي الأحمال (وات)", min_value=100, value=1000)
        hours = st.number_input("عدد ساعات التشغيل", min_value=1, value=5)
        # ... (باقي كود الحاسبة كما هو)
        st.info("قم بإدخال البيانات لحساب النظام المناسب لك.")

    elif page == "شركات التركيب":
        st.title("🏢 شركات التركيب")
        # ... (كود الشركات)

    elif page == "خطط المتابعة":
        st.title("📡 خطط المتابعة والصيانة")
        # ... (كود الخطط)

    elif page == "تواصل معنا":
        st.title("📞 تواصل معنا")
        # ... (كود التواصل)

    st.markdown("---")
    st.caption("VPC Solar © 2026")
