import streamlit as st
import streamlit_authenticator as stauth
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

        creds = service_account.Credentials.from_service_account_info(
            key_dict
        )

        db = firestore.Client(
            credentials=creds,
            project=key_dict["project_id"]
        )

except Exception as e:

    st.error(f"Firestore Error: {e}")

# =========================================
# LOGIN SYSTEM
# =========================================

names = ["Mohamed", "Ahmed"]

usernames = ["mohamed", "ahmed"]

passwords = ["123456", "abcdef"]

hashed_passwords = stauth.Hasher.hash_passwords(passwords)

authenticator = stauth.Authenticate(
    {
        "usernames": {
            usernames[i]: {
                "name": names[i],
                "password": hashed_passwords[i]
            }
            for i in range(len(usernames))
        }
    },
    "vpcsolar",
    "abcdef",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login(
    "Login",
    "main"
)

# =========================================
# LOGIN CHECK
# =========================================

if authentication_status == False:

    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

elif authentication_status == None:

    st.warning("من فضلك سجل الدخول")

elif authentication_status:

    # =========================================
    # CUSTOM CSS
    # =========================================

    st.markdown("""
    <style>

    .main {
        direction: rtl;
        text-align: right;
    }

    section[data-testid="stSidebar"] {
        direction: rtl;
    }

    .stButton > button {
        background-color: #00BFFF;
        color: white;
        border-radius: 12px;
        height: 50px;
        width: 100%;
        border: none;
        font-size: 18px;
        font-weight: bold;
    }

    .stButton > button:hover {
        background-color: #0099cc;
    }

    </style>
    """, unsafe_allow_html=True)

    # =========================================
    # LOAD LOGO
    # =========================================

    logo = Image.open("logo.png")

    # =========================================
    # SIDEBAR
    # =========================================

    with st.sidebar:

        st.image(logo, width=180)

        st.title("☀️ VPC Solar")

        st.write(f"Welcome {name}")

        authenticator.logout("Logout", "sidebar")

        page = st.radio(
            "القائمة",
            [
                "الرئيسية",
                "حاسبة الطاقة الشمسية",
                "شركات التركيب",
                "خطط المتابعة",
                "تواصل معنا"
            ]
        )

    # =========================================
    # HOME PAGE
    # =========================================

    if page == "الرئيسية":

        st.title("☀️ VPC Solar")

        st.subheader("Smart Solar Solutions")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("## 🏠 الأنظمة السكنية")

            st.write(
                "حلول متكاملة لتشغيل المنازل بالطاقة الشمسية."
            )

            st.button("استكشف الأنظمة السكنية")

        with col2:

            st.markdown("## 🚜 الأنظمة الزراعية")

            st.write(
                "أنظمة ري وطلمبات تعمل بالطاقة الشمسية."
            )

            st.button("استكشف الأنظمة الزراعية")

    # =========================================
    # SOLAR CALCULATOR
    # =========================================

    elif page == "حاسبة الطاقة الشمسية":

        st.title("⚡ حاسبة الطاقة الشمسية")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:

            power = st.number_input(
                "إجمالي الأحمال (وات)",
                min_value=100,
                value=1000
            )

            hours = st.number_input(
                "عدد ساعات التشغيل",
                min_value=1,
                value=5
            )

        with col2:

            voltage = st.selectbox(
                "جهد النظام",
                [12, 24, 48]
            )

            battery_backup = st.slider(
                "عدد ساعات البطارية الاحتياطية",
                1,
                24,
                5
            )

        # =========================================
        # CALCULATIONS
        # =========================================

        daily_energy = power * hours

        inverter_size = int(power * 1.25)

        panel_count = max(
            1,
            round(daily_energy / (400 * 5))
        )

        battery_capacity = int(
            (daily_energy * battery_backup)
            / (voltage * 0.8)
        )

        estimated_price = (
            panel_count * 5000
            + inverter_size * 2
        )

        st.markdown("---")

        st.subheader("📊 النتائج")

        r1, r2, r3, r4 = st.columns(4)

        r1.metric(
            "الاستهلاك اليومي",
            f"{daily_energy} Wh"
        )

        r2.metric(
            "قدرة الإنفرتر",
            f"{inverter_size} W"
        )

        r3.metric(
            "عدد الألواح",
            f"{panel_count}"
        )

        r4.metric(
            "البطاريات",
            f"{battery_capacity} Ah"
        )

        st.success(
            f"💰 السعر التقريبي: {estimated_price:,} جنيه"
        )

        # =========================================
        # CHART
        # =========================================

        data = pd.DataFrame({
            "Component": [
                "Inverter",
                "Panels",
                "Battery"
            ],
            "Value": [
                inverter_size,
                panel_count,
                battery_capacity
            ]
        })

        fig = px.bar(
            data,
            x="Component",
            y="Value",
            title="System Components"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # =========================================
        # SAVE DATA
        # =========================================

        if st.button("حفظ الحسابات"):

            try:

                db.collection(
                    "solar_calculations"
                ).add({

                    "user": username,
                    "power": power,
                    "hours": hours,
                    "daily_energy": daily_energy,
                    "inverter": inverter_size,
                    "panels": panel_count,
                    "battery": battery_capacity,

                    "timestamp":
                    firestore.SERVER_TIMESTAMP
                })

                st.success(
                    "تم حفظ البيانات بنجاح"
                )

            except Exception as e:

                st.error(e)

    # =========================================
    # COMPANIES PAGE
    # =========================================

    elif page == "شركات التركيب":

        st.title("🏢 شركات التركيب")

        companies = [

            {
                "name": "شمس أكتوبر",
                "rating": "⭐ 4.9",
                "location": "6 أكتوبر"
            },

            {
                "name": "إيجيبت سولار",
                "rating": "⭐ 4.7",
                "location": "القاهرة"
            },

            {
                "name": "النيل للطاقة",
                "rating": "⭐ 4.8",
                "location": "الجيزة"
            }

        ]

        for comp in companies:

            with st.container(border=True):

                st.subheader(comp["name"])

                st.write(comp["rating"])

                st.write(comp["location"])

                st.button(
                    f"طلب تركيب - {comp['name']}"
                )

    # =========================================
    # MONITORING PAGE
    # =========================================

    elif page == "خطط المتابعة":

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

    # =========================================
    # CONTACT PAGE
    # =========================================

    elif page == "تواصل معنا":

        st.title("📞 تواصل معنا")

        with st.form("contact_form"):

            name_input = st.text_input("الاسم")

            email = st.text_input("البريد الإلكتروني")

            message = st.text_area("رسالتك")

            submit = st.form_submit_button(
                "إرسال"
            )

            if submit:

                try:

                    db.collection(
                        "messages"
                    ).add({

                        "name": name_input,
                        "email": email,
                        "message": message,

                        "timestamp":
                        firestore.SERVER_TIMESTAMP
                    })

                    st.success(
                        "تم إرسال الرسالة بنجاح"
                    )

                except Exception as e:

                    st.error(e)

    # =========================================
    # FOOTER
    # =========================================

    st.markdown("---")

    st.caption("VPC Solar © 2026")
