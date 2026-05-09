import streamlit as st
import json
from google.oauth2 import service_account
from google.cloud import firestore

# 1. إعداد الاتصال بـ Firebase Firestore
# الكود ده بيقرأ المفتاح الجديد اللي حطيناه في Streamlit Secrets كـ "نص" (String)
try:
    if "textkey" in st.secrets:
        # تحويل النص لقاموس JSON لضمان عدم حدوث أخطاء في التنسيق أو الـ JWT
        key_dict = json.loads(st.secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=key_dict["project_id"])
    else:
        st.error("خطأ: مفتاح 'textkey' غير موجود في إعدادات Secrets.")
except Exception as e:
    st.error(f"فشل الاتصال بقاعدة البيانات: {e}")

# 2. إعدادات واجهة التطبيق
st.set_page_config(
    page_title="VPC Solar",
    page_icon="☀️",
    layout="wide"
)

# تخصيص التصميم (CSS) لدعم الواجهة من اليمين لليسار (RTL)
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stMetricValue"] { font-size: 25px; }
    section[data-testid="stSidebar"] { direction: rtl; }
    button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# ===== SIDEBAR (القائمة الجانبية) =====
with st.sidebar:
    import os
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    
    st.title("☀️ VPC Solar")
    st.write("نظام الطاقة الشمسية المتكامل")
    
    page = st.radio(
        "انتقل إلى:",
        ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "خطط المتابعة", "تواصل معنا"]
    )

# ===== صفحة الرئيسية =====
if page == "الرئيسية":
    st.title("☀️ VPC Solar")
    st.subheader("حلول الطاقة الشمسية الذكية لمستقبل أفضل")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏠 الأنظمة السكنية")
        st.write("توفير حتى 100% من فاتورة الكهرباء المنزلية.")
        if st.button("استكشف الأنظمة السكنية"):
            st.info("سيتم إضافة التفاصيل قريباً")
            
    with col2:
        st.markdown("### 🚜 الأنظمة الزراعية")
        st.write("حلول ري متكاملة تعمل بالطاقة الشمسية.")
        if st.button("استكشف الأنظمة الزراعية"):
            st.info("سيتم إضافة التفاصيل قريباً")

# ===== صفحة حاسبة الطاقة الشمسية =====
elif page == "حاسبة الطاقة الشمسية":
    st.title("⚡ حاسبة الطاقة الشمسية الدقيقة")
    
    with st.expander("📝 أدخل بيانات أحمالك هنا", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input("إجمالي قدرة الأجهزة (وات/Watt)", min_value=10, value=1000)
            hours = st.number_input("ساعات التشغيل المطلوبة يومياً", min_value=1, value=6)
        with col2:
            voltage = st.selectbox("جهد النظام (Volt)", [12, 24, 48])
            safety = 1.25

    # العمليات الحسابية
    daily_energy = power * hours
    inverter_size = power * safety
    panel_count = round(daily_energy / (400 * 5))
    battery_capacity = round((daily_energy * 1) / (voltage * 0.8))

    st.markdown("---")
    st.subheader("📊 المواصفات الفنية المطلوبة:")
    
    res1, res2, res3 = st.columns(3)
    res1.metric("قدرة الإنفيرتر", f"{int(inverter_size)} W")
    res2.metric("عدد الألواح (400W)", f"{panel_count} ألواح")
    res3.metric("سعة البطاريات", f"{battery_capacity} Ah")
    
    if st.button("حفظ هذه الحسابات"):
        try:
            db.collection("solar_calculations").add({
                "power_w": power,
                "hours": hours,
                "daily_energy_wh": daily_energy,
                "inverter_w": inverter_size,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("تم حفظ البيانات في Firestore بنجاح!")
        except Exception as e:
            st.error(f"خطأ في الحفظ: {e}")

# ===== صفحة تواصل معنا =====
elif page == "تواصل معنا":
    st.title("📞 تواصل مع فريق VPC Solar")
    
    with st.form("contact_form"):
        name = st.text_input("الاسم بالكامل")
        email = st.text_input("البريد الإلكتروني")
        msg = st.text_area("رسالتك")
        submit_button = st.form_submit_button("إرسال")

        if submit_button:
            if name and email and msg:
                try:
                    # حفظ الرسالة في مجموعة (messages)
                    db.collection("messages").add({
                        "name": name,
                        "email": email,
                        "message": msg,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success(f"شكراً يا {name}، تم إرسال رسالتك بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الإرسال: {e}")
            else:
                st.warning("برجاء إكمال جميع الحقول.")

# ===== باقي الصفحات =====
elif page == "شركات التركيب":
    st.title("🏢 شركات التركيب المعتمدة")
    companies = [
        {"الاسم": "شمس أكتوبر للمقاولات", "التقييم": "⭐ 4.9", "الموقع": "6 أكتوبر"},
        {"الاسم": "إيجيبت سولار", "التقييم": "⭐ 4.7", "الموقع": "القاهرة"},
        {"الاسم": "النيل للطاقة", "التقييم": "⭐ 4.8", "الموقع": "الجيزة"}
    ]
    for comp in companies:
        st.markdown(f"**{comp['الاسم']}** | {comp['التقييم']} | {comp['الموقع']}")
        st.divider()

elif page == "خطط المتابعة":
    st.title("📡 أنظمة المتابعة والتحكم")
    st.write("نقدم حلولاً برمجية لمتابعة إنتاج محطتك عبر الإنترنت.")

# ===== FOOTER =====
st.markdown("---")
st.caption("VPC Solar © 2026 | تطوير م/ أبو سعد")
