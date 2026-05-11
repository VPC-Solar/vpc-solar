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

if not st.session_state.logged_in:
    st.title("☀️ مرحباً بك في VPC Solar")
    
    # إنشاء تبويبات للدخول وإنشاء الحساب في الواجهة الأمامية
    tab_login, tab_signup = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب جديد"])

    with tab_login:
        user_in = st.text_input("اسم المستخدم", key="login_user")
        pass_in = st.text_input("كلمة المرور", type="password", key="login_pass")

        if st.button("تسجيل الدخول", use_container_width=True):
            # الدخول الافتراضي للمطور
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
                        st.success("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول من التبويب الآخر.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء التسجيل: {e}")
            else:
                st.warning("يرجى إدخال اسم المستخدم وكلمة المرور")
    
    st.stop() # إيقاف التنفيذ هنا حتى يتم تسجيل الدخول

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

        # تم حذف "إنشاء حساب" من هنا لأنها أصبحت في البداية
        page = st.selectbox(
            "☰ القائمة",
            ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "خطط المتابعة"]
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

        data = pd.DataFrame({
            "Component": ["Inverter", "Panels", "Battery"],
            "Value": [inverter_size, panel_count, battery_capacity]
        })
        fig = px.bar(data, x="Component", y="Value", title="System Components")
        st.plotly_chart(fig, use_container_width=True)

        if st.button("حفظ الحسابات"):
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
                st.success("تم حفظ البيانات بنجاح")
            except Exception as e:
                st.error(e)

    elif page == "شركات التركيب":
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

    elif page == "تواصل معنا":
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

    st.markdown("---")

col1, col2 = st.columns([2,8])

with col1:
    st.caption("VPC Solar © 2026")

with col2:
    if st.button("📞 تواصل معنا"):

        st.info("""
        "تواصل معنا"
        """)
        
