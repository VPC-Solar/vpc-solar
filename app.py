import streamlit as st

# إعدادات واجهة التطبيق
st.set_page_config(
    page_title="VPC Solar",
    page_icon="☀️",
    layout="wide"
)

# تخصيص التصميم (CSS) لجعل الخطوط أوضح
st.markdown("""
    <style>
    .main { text-align: right; direction: rtl; }
    div[data-testid="stMetricValue"] { font-size: 25px; }
    </style>
    """, unsafe_allow_html=True)

# ===== SIDEBAR (القائمة الجانبية) =====
with st.sidebar:
    # إضافة اللوجو في القائمة الجانبية
    st.image("logo.png", width=150) # تأكد من تسمية ملف الصورة logo.png في GitHub
    st.title("☀️ VPC Solar")
    st.write("نظام الطاقة الشمسية المتكامل")
    
    page = st.radio(
        "انتقل إلى:",
        ["الرئيسية", "حاسبة الطاقة الشمسية", "شركات التركيب", "خطط المتابعة", "تواصل معنا"]
    )

# ===== الرئيسية (Home) =====
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

# ===== حاسبة الطاقة الشمسية (Solar Calculator) =====
elif page == "حاسبة الطاقة الشمسية":
    st.title("⚡ حاسبة الطاقة الشمسية الدقيقة")
    
    with st.expander("📝 أدخل بيانات أحمالك هنا", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            power = st.number_input("إجمالي قدرة الأجهزة (وات/Watt)", min_value=10, value=1000)
            hours = st.number_input("ساعات التشغيل المطلوبة يومياً", min_value=1, value=6)
        with col2:
            voltage = st.selectbox("جهد النظام (Volt)", [12, 24, 48])
            safety = 1.25 # عامل أمان لضمان كفاءة الإنفيرتر

    # الحسابات الهندسية
    daily_energy = power * hours
    inverter_size = power * safety
    panel_count = round(daily_energy / (400 * 5)) # بافتراض لوح 400 وات و5 ساعات شمس
    battery_capacity = round((daily_energy * 1) / (voltage * 0.8)) # يوم احتياط وتفريغ 80%

    st.markdown("---")
    st.subheader("📊 المواصفات الفنية المطلوبة:")
    
    res1, res2, res3 = st.columns(3)
    res1.metric("قدرة الإنفيرتر", f"{int(inverter_size)} W")
    res2.metric("عدد الألواح (400W)", f"{panel_count} ألواح")
    res3.metric("سعة البطاريات", f"{battery_capacity} Ah")
    
    st.success(f"إجمالي استهلاكك اليومي: {daily_energy} وات/ساعة")

# ===== شركات التركيب (Companies) =====
elif page == "شركات التركيب":
    st.title("🏢 شركات التركيب المعتمدة")
    st.write("قائمة بأفضل الشركات في منطقتك")
    
    companies = [
        {"الاسم": "شمس أكتوبر للمقاولات", "التقييم": "⭐ 4.9", "الموقع": "6 أكتوبر"},
        {"الاسم": "إيجيبت سولار", "التقييم": "⭐ 4.7", "الموقع": "القاهرة"},
        {"الاسم": "النيل للطاقة", "التقييم": "⭐ 4.8", "الموقع": "الجيزة"}
    ]
    
    for comp in companies:
        with st.container():
            st.markdown(f"**{comp['الاسم']}** | {comp['التقييم']} | {comp['الموقع']}")
            st.divider()

# ===== خطط المتابعة (Monitoring) =====
elif page == "خطط المتابعة":
    st.title("📡 أنظمة المتابعة والتحكم")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("الخطة الأساسية")
        st.write("- مراقبة الإنتاج لحظياً\n- تنبيهات الأعطال")
    with col2:
        st.subheader("الخطة المتقدمة")
        st.write("- تقارير شهرية مفصلة\n- دعم فني 24/7\n- زيارات صيانة دورية")

# ===== تواصل معنا (Contact) =====
elif page == "تواصل معنا":
    st.title("📞 تواصل مع فريق VPC Solar")
    name = st.text_input("الاسم بالكامل")
    email = st.text_input("البريد الإلكتروني")
    msg = st.text_area("رسالتك")
    if st.button("إرسال"):
        st.success("تم استلام رسالتك، وسنتواصل معك قريباً.")

# ===== FOOTER =====
st.markdown("---")
st.caption("VPC Solar © 2026")
