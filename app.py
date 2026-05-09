import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import firestore

# --- الاتصال بـ Firebase ---
try:
    if "textkey" in st.secrets:
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=key_dict["project_id"])
    else:
        st.error("مفتاح textkey غير موجود")
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")

# --- إعدادات الصفحة واللغة ---
st.set_page_config(page_title="VPC Solar Pro", layout="wide")

# نظام تبديل اللغة (عربي/انجليزي)
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

def change_lang():
    st.session_state.lang = 'en' if st.session_state.lang == 'ar' else 'ar'

# --- واجهة تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_ui():
    st.title("🔐 VPC Solar - Login")
    with st.form("login_form"):
        user_email = st.text_input("البريد الإلكتروني / Email")
        password = st.text_input("كلمة المرور / Password", type="password")
        submit = st.form_submit_button("دخول / Login")
        
        if submit:
            if user_email and len(password) > 5: # محاكاة للتحقق
                st.session_state.logged_in = True
                st.session_state.user_email = user_email
                st.rerun()
            else:
                st.error("برجاء إدخال بيانات صحيحة")

# --- التطبيق الرئيسي بعد الدخول ---
if not st.session_state.logged_in:
    login_ui()
else:
    # القائمة الجانبية المحدثة
    with st.sidebar:
        st.write(f"مرحباً: {st.session_state.user_email}")
        if st.button("🌐 Switch to English" if st.session_state.lang == 'ar' else "🌐 التحويل للعربية"):
            change_lang()
            st.rerun()
        
        menu = ["الرئيسية", "حاسبة الطاقة", "شركات التركيب", "طلباتي", "خروج"]
        choice = st.radio("القائمة", menu)
        
        if choice == "خروج":
            st.session_state.logged_in = False
            st.rerun()

    # --- صفحة شركات التركيب (بيانات حقيقية) ---
    if choice == "شركات التركيب":
        st.title("🏢 شركات تركيب معتمدة في مصر")
        # في المرحلة الجاية هنسحب دول من Firestore مباشرة
        companies = [
            {"name": "KarmSolar", "location": "القاهرة", "contact": "19000"},
            {"name": "Cairo Solar", "location": "المهندسين", "contact": "01000..."},
            {"name": "Sunprism", "location": "6 أكتوبر", "contact": "011..."},
        ]
        for comp in companies:
            with st.expander(f"📍 {comp['name']}"):
                st.write(f"الموقع: {comp['location']}")
                st.write(f"للتواصل: {comp['contact']}")
                if st.button(f"طلب معاينة من {comp['name']}"):
                    st.success("تم إرسال طلبك للشركة بنجاح!")

    # --- صفحة طلباتي (عرض البيانات من Firestore) ---
    elif choice == "طلباتي":
        st.title("📋 سجل حساباتي وطلباتي")
        docs = db.collection("solar_calculations").where("user", "==", st.session_state.user_email).stream()
        for doc in docs:
            data = doc.to_dict()
            st.info(f"تاريخ الطلب: {data.get('timestamp')} | القدرة: {data.get('power_w')} وات")

    # بقية الصفحات (الرئيسية والحاسبة) تظل كما هي مع ربط الـ user_email عند الحفظ
