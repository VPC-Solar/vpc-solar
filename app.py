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
# LOGIN SYSTEM
# =========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "page" not in st.session_state:
    st.session_state.page = "الرئيسية"

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")

    user_in = st.text_input("اسم المستخدم")
    pass_in = st.text_input("كلمة المرور", type="password")

    if st.button("Login"):
        if user_in == "mohamed" and pass_in == "123456":
            st.session_state.logged_in = True
            st.session_state.username = user_in
            st.session_state.page = "الرئيسية"
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
                        st.session_state.page = "الرئيسية"
                        found = True
                        st.rerun()

                if not found:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
            except Exception as e:
                st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")

    st.stop()

# =========================================
# MAIN APP
# =========================================
if st.session_state.logged_in:

    username = st.session_state.username
    page = st.session_state.page

    st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    section[data-testid="stSidebar"] { direction: rtl; }

    .stButton > button {
        background-color: #00BFFF;
        color: white;
        border-radius: 12px;
        height: 50px;
        width: 100%;
        border: none;
        font-size: 16px;
        font-weight: bold;
        margin-bottom: 8px;
    }

    .stButton > button:hover {
        background-color: #0099cc;
    }
    </style>
    """, unsafe_allow_html=True)

    # logo
    try:
        logo = Image.open("logo.png")
    except:
        logo = None

    # ================= SIDEBAR =================
    with st.sidebar:
        if logo:
            st.image(logo, width=180)

        st.title("☀️ VPC Solar")
        st.write(f"مرحباً بك: {username}")

        st.markdown("## 📌 القائمة")

        if st.button("الرئيسية"):
            st.session_state.page = "الرئيسية"
        if st.button("حاسبة الطاقة الشمسية"):
            st.session_state.page = "حاسبة الطاقة الشمسية"
        if st.button("شركات التركيب"):
            st.session_state.page = "شركات التركيب"
        if st.button("خطط المتابعة"):
            st.session_state.page = "خطط المتابعة"
        if st.button("تواصل معنا"):
            st.session_state.page = "تواصل معنا"
        if st.button("إنشاء حساب"):
            st.session_state.page = "إنشاء حساب"

        st.markdown("---")

        if st.button("🚪 تسجيل الخروج"):
            st.session_state.logged_in = False
            st.rerun()

    # ================= PAGES =================

    if page == "الرئيسية":
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

    elif page == "حاسبة الطاقة الشمسية":
        st.title("⚡ حاسبة الطاقة الشمسية")
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input("إجمالي الأحمال (وات)", 100, value=1000)
            hours = st.number_input("عدد ساعات التشغيل", 1, value=5)

        with col2:
            voltage = st.selectbox("جهد النظام", [12, 24, 48])
            battery_backup = st.slider("ساعات البطارية الاحتياطية", 1, 24, 5)

        daily_energy = power * hours
        inverter_size = int(power * 1.25)
        panel_count = max(1, round(daily_energy / (400 * 5)))
        battery_capacity = int((daily_energy * battery_backup) / (voltage * 0.8))
        estimated_price = (panel_count * 5000 + inverter_size * 2)

        st.markdown("---")
        st.subheader("📊 النتائج")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("الاستهلاك", f"{daily_energy} Wh")
        c2.metric("الإنفرتر", f"{inverter_size} W")
        c3.metric("الألواح", panel_count)
        c4.metric("البطاريات", battery_capacity)

        st.success(f"💰 السعر التقريبي: {estimated_price:,} جنيه")

        df = pd.DataFrame({
            "Component": ["Inverter", "Panels", "Battery"],
            "Value": [inverter_size, panel_count, battery_capacity]
        })

        fig = px.bar(df, x="Component", y="Value")
        st.plotly_chart(fig, use_container_width=True)

    elif page == "شركات التركيب":
        st.title("🏢 شركات التركيب")

        companies = [
            {"name": "شمس أكتوبر", "rating": "⭐ 4.9", "location": "6 أكتوبر"},
            {"name": "إيجيبت سولار", "rating": "⭐ 4.7", "location": "القاهرة"},
            {"name": "النيل للطاقة", "rating": "⭐ 4.8", "location": "الجيزة"}
        ]

        for comp in companies:
            with st.container():
                st.subheader(comp["name"])
                st.write(comp["rating"])
                st.write(comp["location"])
                st.button(f"طلب تركيب - {comp['name']}")

    elif page == "خطط المتابعة":
        st.title("📡 خطط المتابعة")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Basic")
            st.write("✔ تنبيهات أعطال")
            st.write("✔ تقارير شهرية")
            st.button("اشترك")

        with col2:
            st.subheader("Premium")
            st.write("✔ دعم 24/7")
            st.write("✔ زيارات صيانة")
            st.button("اشترك Premium")

    elif page == "تواصل معنا":
        st.title("📞 تواصل معنا")

        with st.form("contact"):
            name = st.text_input("الاسم")
            email = st.text_input("الإيميل")
            msg = st.text_area("الرسالة")

            if st.form_submit_button("إرسال"):
                db.collection("messages").add({
                    "name": name,
                    "email": email,
                    "message": msg,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("تم الإرسال")

    elif page == "إنشاء حساب":
        st.title("📝 إنشاء حساب")

        with st.form("register"):
            new_user = st.text_input("اسم المستخدم")
            new_email = st.text_input("الإيميل")
            new_pass = st.text_input("كلمة المرور", type="password")

            if st.form_submit_button("إنشاء"):
                users_ref = db.collection("users")
                query = users_ref.where("username", "==", new_user).stream()

                if any(query):
                    st.error("اسم المستخدم موجود")
                else:
                    users_ref.add({
                        "username": new_user,
                        "email": new_email,
                        "password": new_pass,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("تم إنشاء الحساب")

    st.markdown("---")
    st.caption("VPC Solar © 2026")
