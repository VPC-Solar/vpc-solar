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
# 🔐 DYNAMIC LOGIN & REGISTER SYSTEM
# =========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "الرئيسية"

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
                st.session_state.user_role = "Admin"
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
                            st.session_state.user_role = user_data.get("role", "عميل") 
                            found = True
                            st.rerun()
                    if not found:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
                except Exception as e:
                    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

    with tab_signup:
        new_username = st.text_input("اختر اسم مستخدم", key="reg_user")
        new_email = st.text_input("البريد الإلكتروني", key="reg_email")
        new_password = st.text_input("اختر كلمة مرور", type="password", key="reg_pass")
        
        account_type = st.radio("سجل كـ:", ["عميل", "شركة تركيبات"], key="account_role")
        
        company_details = {}
        if account_type == "شركة تركيبات":
            company_details['location'] = st.selectbox("مقر الشركة الرئيسي", ["6 أكتوبر", "القاهرة", "الجيزة", "الأسكندرية"])
            company_details['bio'] = st.text_area("نبذة عن خبرات الشركة")

        if st.button("إنشاء الحساب", use_container_width=True):
            if new_username and new_password:
                try:
                    users_ref = db.collection("users")
                    if any(users_ref.where("username", "==", new_username).stream()):
                        st.error("اسم المستخدم موجود بالفعل")
                    else:
                        data = {
                            "username": new_username,
                            "email": new_email,
                            "password": new_password,
                            "role": account_type,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        }
                        if account_type == "شركة تركيبات":
                            data.update(company_details)
                        
                        users_ref.add(data)
                        st.success(f"تم إنشاء حساب {account_type} بنجاح! سجل دخولك الآن.")
                except Exception as e:
                    st.error(f"خطأ: {e}")
    st.stop()

# =========================================
# MAIN APP (بعد تسجيل الدخول)
# =========================================
if st.session_state.logged_in:
    username = st.session_state.username
    role = st.session_state.get("user_role", "عميل")

    st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    section[data-testid="stSidebar"] { direction: rtl; }
    .stButton > button {
        background-color: transparent;
        color: white;
        border-radius: 12px;
        height: 50px;
        width: 100%;
        border: 1px solid #00BFFF;
        font-size: 18px;
        font-weight: bold;
    }
    .stButton > button:hover { background-color: #0099cc; color: white; }
    </style>
    """, unsafe_allow_html=True)

    try:
        logo = Image.open("logo.png")
    except:
        logo = None

    # --- SIDEBAR (القائمة الموحدة) ---
    with st.sidebar:
        if logo:
            st.image(logo, width=180)
        st.title("☀️ VPC Solar")
        st.write(f"مرحباً بك: {username} ({role})")

        if st.button("تسجيل الخروج"):
            st.session_state.logged_in = False
            st.rerun()

        # تحديد الصفحات المتاحة حسب نوع الحساب
        if role == "شركة تركيبات":
            pages_list = ["الرئيسية", "طلبات التركيب الواردة", "ملف الشركة", "تواصل معنا"]
        elif role == "Admin":
            pages_list = ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "إدارة المستخدمين", "تواصل معنا"]
        else: # العميل
            pages_list = ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "خطط المتابعة", "تواصل معنا"]

        # حماية من خطأ index لو الصفحة الحالية مش في القائمة الجديدة
        if st.session_state.current_page not in pages_list:
            st.session_state.current_page = "الرئيسية"
            
        current_idx = pages_list.index(st.session_state.current_page)
        
        page = st.selectbox("☰ القائمة", pages_list, index=current_idx)
        st.session_state.current_page = page

    # --- معالجة الصفحات ---
    if st.session_state.current_page == "الرئيسية":
        st.title("☀️ VPC Solar")
        st.subheader("Smart Solar Solutions")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("## 🏠 الأنظمة السكنية")
            st.write("حلول متكاملة لتشغيل المنازل بالطاقة الشمسية.")
            st.button("استكشف الأنظمة السكنية")
        with col2:
            st.markdown("## 🚜 الأنظمة الزراعية")
            st.write("أنظمة ري وطلمبات تعمل بالطاقة الشمسية.")
            st.button("استكشف الأنظمة الزراعية")

    elif st.session_state.current_page == "حاسبة الطاقة الشمسية":
        st.title("⚡ حاسبة الطاقة الشمسية")
        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input("إجمالي الأحمال (وات)", min_value=100, value=1000)
            hours = st.number_input("عدد ساعات التشغيل", min_value=1, value=5)
        with col2:
            voltage = st.selectbox("جهد النظام", [12, 24, 48])
            battery_backup = st.slider("عدد ساعات البطارية الاحتياطية", 1, 24, 5)

        daily_energy = power * hours
        inverter_size = int(power * 1.25)
        panel_count = max(1, round(daily_energy / (400 * 5)))
        battery_capacity = int((daily_energy * battery_backup) / (voltage * 0.8))
        estimated_price = (panel_count * 5000 + inverter_size * 2)

        st.markdown("---")
        st.subheader("📊 النتائج")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("الاستهلاك اليومي", f"{daily_energy} Wh")
        r2.metric("قدرة الإنفرتر", f"{inverter_size} W")
        r3.metric("عدد الألواح", f"{panel_count}")
        r4.metric("البطاريات", f"{battery_capacity} Ah")
        st.success(f"💰 السعر التقريبي: {estimated_price:,} جنيه")

    elif st.session_state.current_page == "شركات التركيب":
        st.title("🏢 شركات التركيب المسجلة")
        companies = db.collection("users").where("role", "==", "شركة تركيبات").stream()
        has_companies = False
        for doc in companies:
            has_companies = True
            c = doc.to_dict()
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.subheader(c['username'])
                    st.caption(f"📍 المقر: {c.get('location', 'غير محدد')}")
                    st.write(c.get('bio', 'لا يوجد وصف متاح.'))
                with c2:
                    if st.button("طلب تسعير", key=doc.id):
                        st.success(f"تم إرسال طلبك لشركة {c['username']}")
        if not has_companies:
            st.warning("لا توجد شركات مسجلة حالياً.")

    elif st.session_state.current_page == "تواصل معنا":
        st.title("📞 تواصل معنا")
        with st.form("contact_form"):
            name_input = st.text_input("الاسم")
            email = st.text_input("البريد الإلكتروني")
            message = st.text_area("رسالتك")
            submit = st.form_submit_button("إرسال")
            if submit:
                db.collection("messages").add({
                    "name": name_input, "email": email, "message": message,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("تم إرسال الرسالة بنجاح")

    # --- Footer ---
    st.markdown("---")
    st.caption("VPC Solar © 2026 | تطوير المهندس محمد سعد الدين")
