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
                    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

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
                            "username": new_username,
                            "email": new_email,
                            "password": new_password,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء التسجيل: {e}")
            else:
                st.warning("يرجى إدخال اسم المستخدم وكلمة المرور")
    st.stop()

# =========================================
# MAIN APP (بعد تسجيل الدخول)
# =========================================
if st.session_state.logged_in:
    username = st.session_state.username

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

    # --- SIDEBAR ---
    with st.sidebar:
        if logo:
            st.image(logo, width=180)
        st.title("☀️ VPC Solar")
        st.write(f"مرحباً بك: {username}")

        if st.button("تسجيل الخروج"):
            st.session_state.logged_in = False
            st.rerun()

        # ربط القائمة بـ current_page
        pages_list = ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "خطط المتابعة"]
        # التأكد من أن الصفحة الحالية موجودة في القائمة
        current_idx = pages_list.index(st.session_state.current_page) if st.session_state.current_page in pages_list else 0
        
        page = st.selectbox(
            "☰ القائمة",
            pages_list,
            index=current_idx
        )
        st.session_state.current_page = page

    # --- صفحات التطبيق ---
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
        st.markdown("---")
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
        st.title("🏢 شركات التركيب")
        companies = [
            {"name": "شمس أكتوبر", "rating": "⭐ 4.9", "location": "6 أكتوبر"},
            {"name": "إيجيبت سولار", "rating": "⭐ 4.7", "location": "القاهرة"},
            {"name": "النيل للطاقة", "rating": "⭐ 4.8", "location": "الجيزة"}
        ]
        for comp in companies:
            with st.container(border=True):
                st.subheader(comp["name"])
                st.write(comp["rating"])
                st.write(comp["location"])
                st.button(f"طلب تركيب - {comp['name']}")

    elif st.session_state.current_page == "خطط المتابعة":
        st.title("📡 خطط المتابعة والصيانة")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Basic")
            st.write("✔ تنبيهات أعطال")
            st.write("✔ متابعة الإنتاج")
            st.write("✔ تقارير شهرية")
            st.button("اشترك الآن")
        with col2:
            st.subheader("Premium")
            st.write("✔ زيارات صيانة")
            st.write("✔ دعم 24/7")
            st.write("✔ متابعة مباشرة")
            st.button("اشترك Premium")

    elif st.session_state.current_page == "تواصل معنا":
        st.title("📞 تواصل معنا")
        with st.form("contact_form"):
            name_input = st.text_input("الاسم")
            email = st.text_input("البريد الإلكتروني")
            message = st.text_area("رسالتك")
            submit = st.form_submit_button("إرسال")
            if submit:
                try:
                    db.collection("messages").add({
                        "name": name_input, "email": email, "message": message,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("تم إرسال الرسالة بنجاح")
                except Exception as e:
                    st.error(e)

    # --- Footer ---
    st.markdown("---")
    col_btn, col_txt = st.columns([1, 8])
    with col_btn:
        if st.button("📞 تواصل معنا", key="footer_contact_btn"):
            st.session_state.current_page = "تواصل معنا"
            st.rerun()
    with col_txt:
        st.caption("VPC Solar © 2026")
