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
# 🔐 DYNAMIC LOGIN SYSTEM
# =========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    
    user_in = st.text_input("اسم المستخدم")
    pass_in = st.text_input("كلمة المرور", type="password")

    if st.button("Login"):
        # الدخول الافتراضي للمطور
        if user_in == "mohamed" and pass_in == "123456":
            st.session_state.logged_in = True
            st.session_state.username = user_in
            st.rerun()
        else:
            try:
                # التحقق من قاعدة بيانات المستخدمين
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
        background-color: #00BFFF;
        color: white;
        border-radius: 12px;
        height: 50px;
        width: 100%;
        border: none;
        font-size: 18px;
        font-weight: bold;
    }
    .stButton > button:hover { background-color: #0099cc; }
    </style>
    """, unsafe_allow_html=True)

    # تحميل اللوجو
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

        page = st.radio(
            "القائمة",
            ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "خطط المتابعة", "تواصل معنا", "إنشاء حساب"]
        )

    # --- صفحات التطبيق ---
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
            power = st.number_input("إجمالي الأحمال (وات)", min_value=100, value=1000)
            hours = st.number_input("عدد ساعات التشغيل", min_value=1, value=5)
        with col2:
            voltage = st.selectbox("جهد النظام (Volt)", [12, 24, 48])
            battery_backup = st.slider("عدد ساعات البطارية الاحتياطية", 1, 24, 5)

        # --- المعادلات التقنية الدقيقة ---
        # إضافة معامل فقد 20% لضمان كفاءة النظام
        daily_energy = (power * hours) / 0.8 
        # قدرة الإنفرتر مع معامل أمان 25% (لتحمل تيار البدء)
        inverter_size = int(power * 1.25)
        # عدد الألواح (بافتراض لوح 400 وات ومتوسط سطوع شمس 5 ساعات)
        panel_count = max(1, round(daily_energy / (400 * 5)))
        # سعة البطارية مع مراعاة عمق التفريغ 50% للبطاريات الجل
        battery_capacity = int((daily_energy * (battery_backup/hours)) / (voltage * 0.5))
        # تقدير سعري مبدئي
        estimated_price = (panel_count * 6500 + inverter_size * 5 + battery_capacity * 40)

        st.markdown("---")
        st.subheader("📊 النتائج")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("الاستهلاك اليومي", f"{int(daily_energy)} Wh")
        r2.metric("قدرة الإنفرتر", f"{inverter_size} W")
        r3.metric("عدد الألواح (400W)", f"{panel_count}")
        r4.metric("البطاريات المطلوبة", f"{battery_capacity} Ah")

        st.success(f"💰 السعر التقريبي للمكونات الأساسية: {estimated_price:,} جنيه")

        # الرسم البياني
        data = pd.DataFrame({
            "Component": ["Inverter (W)", "Panels (Qty)", "Battery (Ah)"],
            "Value": [inverter_size, panel_count, battery_capacity]
        })
        fig = px.bar(data, x="Component", y="Value", title="مواصفات النظام المقترح", color="Component")
        st.plotly_chart(fig, use_container_width=True)

        if st.button("حفظ الحسابات في ملفك"):
            try:
                db.collection("solar_calculations").add({
                    "user": username,
                    "power": power,
                    "hours": hours,
                    "daily_energy": daily_energy,
                    "inverter": inverter_size,
                    "panels": panel_count,
                    "battery": battery_capacity,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("تم حفظ الحسابات بنجاح في قاعدة البيانات")
            except Exception as e:
                st.error(f"فشل الحفظ: {e}")

    elif page == "شركات التركيب":
        st.title("🏢 شركات التركيب المعتمدة")
        companies = [
            {"name": "شمس أكتوبر", "rating": "⭐ 4.9", "location": "6 أكتوبر - المنطقة الصناعية"},
            {"name": "إيجيبت سولار", "rating": "⭐ 4.7", "location": "القاهرة - التجمع"},
            {"name": "النيل للطاقة", "rating": "⭐ 4.8", "location": "الجيزة - الدقي"}
        ]
        for comp in companies:
            with st.container(border=True):
                st.subheader(comp["name"])
                st.write(f"التقييم: {comp['rating']}")
                st.write(f"الموقع: {comp['location']}")
                st.button(f"طلب معاينة من {comp['name']}")

    elif page == "خطط المتابعة":
        st.title("📡 أنظمة المتابعة الذكية (IoT)")
        st.info("هذه الخدمة تتيح لك مراقبة إنتاج توربينات الرياح وألواح الطاقة الشمسية لحظة بلحظة.")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("خطة المتابعة الأساسية")
            st.write("✔ تنبيهات الأعطال عبر التطبيق")
            st.write("✔ تقرير إنتاج شهري")
            st.button("تفعيل الخدمة الأساسية")
        with col2:
            st.subheader("خطة المتابعة المتقدمة")
            st.write("✔ لوحة تحكم لحظية (Live Dashboard)")
            st.write("✔ تحليل الاهتزازات وصيانة تنبؤية")
            st.button("اشترك في الخطة المتقدمة")

    elif page == "تواصل معنا":
        st.title("📞 تواصل مع فريق VPC Solar")
        with st.form("contact_form"):
            name_input = st.text_input("الاسم بالكامل")
            email = st.text_input("البريد الإلكتروني")
            message = st.text_area("كيف يمكننا مساعدتك؟")
            submit = st.form_submit_button("إرسال الرسالة")
            if submit:
                try:
                    db.collection("messages").add({
                        "name": name_input, "email": email, "message": message,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("شكراً لتواصلك معنا، سيقوم فريقنا بالرد عليك قريباً.")
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")

    elif page == "إنشاء حساب":
        st.title("📝 إنشاء حساب مستخدم جديد")
        with st.form("register_form"):
            new_username = st.text_input("اختر اسم المستخدم")
            new_email = st.text_input("البريد الإلكتروني")
            new_password = st.text_input("كلمة المرور", type="password")
            submit_register = st.form_submit_button("إتمام التسجيل")

            if submit_register:
                try:
                    users_ref = db.collection("users")
                    query = users_ref.where("username", "==", new_username).stream()
                    if any(query):
                        st.error("عذراً، اسم المستخدم هذا محجوز بالفعل.")
                    else:
                        users_ref.add({
                            "username": new_username,
                            "email": new_email,
                            "password": new_password,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("مبروك! تم إنشاء حسابك بنجاح 🔥")
                except Exception as e:
                    st.error(f"فشل التسجيل: {e}")

    st.markdown("---")
    st.caption("VPC Solar Ecosystem Pro © 2026 | تطوير المهندس أبو سعد")
