import streamlit as st
import json
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import firestore
from PIL import Image
import hashlib
from datetime import datetime

# =========================================
# PAGE CONFIG
# =========================================
st.set_page_config(
    page_title="VPC Solar",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# FIREBASE CONNECTION (مع تحسين)
# =========================================
@st.cache_resource
def init_firestore():
    try:
        if "textkey" in st.secrets:
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            return firestore.Client(credentials=creds, project=key_dict["project_id"])
        return None
    except Exception as e:
        st.error(f"Firestore Error: {e}")
        return None

db = init_firestore()

# =========================================
# 🔐 AMPLIFIED SECURITY & AUTH SYSTEM
# =========================================
def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "الرئيسية"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# ADMIN HARDCODED CREDENTIALS (أكثر أماناً)
ADMIN_CREDENTIALS = {
    "mohamed": hashlib.sha256("123456".encode()).hexdigest()
}

if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .main-header { 
        font-size: 3rem; 
        text-align: center; 
        color: #00BFFF; 
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">☀️ VPC Solar Portal</h1>', unsafe_allow_html=True)
    
    tab_login, tab_signup = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب"])

    with tab_login:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### بيانات الدخول")
        with col2:
            user_in = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
            pass_in = st.text_input("🔒 كلمة المرور", type="password", placeholder="••••••••")
            
            if st.button("🚀 دخول النظام", use_container_width=True, type="primary"):
                if not user_in or not pass_in:
                    st.error("⚠️ يرجى إدخال بيانات الدخول")
                elif user_in in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[user_in] == hash_password(pass_in):
                    st.session_state.logged_in = True
                    st.session_state.username = user_in
                    st.session_state.user_role = "Admin"
                    st.session_state.user_data = {"role": "Admin"}
                    st.success("✅ تم تسجيل الدخول كمدير النظام")
                    st.rerun()
                elif db:
                    try:
                        users_ref = db.collection("users")
                        query = users_ref.where("username", "==", user_in).limit(1).stream()
                        for doc in query:
                            user_data = doc.to_dict()
                            if user_data.get("password_hash") == hash_password(pass_in):
                                st.session_state.logged_in = True
                                st.session_state.username = user_in
                                st.session_state.user_role = user_data.get("role", "عميل")
                                st.session_state.user_data = user_data
                                st.success("✅ تم تسجيل الدخول بنجاح")
                                st.rerun()
                                break
                        else:
                            st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
                    except Exception as e:
                        st.error(f"خطأ في الاتصال: {e}")

    with tab_signup:
        st.markdown("### إنشاء حساب جديد")
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("👤 اسم المستخدم", key="reg_user")
            new_email = st.text_input("📧 البريد الإلكتروني", key="reg_email")
            new_password = st.text_input("🔒 كلمة المرور", type="password", key="reg_pass")
            confirm_password = st.text_input("تأكيد كلمة المرور", type="password", key="reg_confirm")
            
        with col2:
            account_type = st.radio("نوع الحساب:", ["عميل", "شركة تركيبات"], key="account_role")
            
            company_details = {}
            if account_type == "شركة تركيبات":
                st.markdown("### بيانات الشركة")
                company_details['location'] = st.selectbox("📍 المقر الرئيسي", 
                                                         ["6 أكتوبر", "القاهرة", "الجيزة", "الأسكندرية"])
                company_details['phone'] = st.text_input("📱 رقم الهاتف")
                company_details['bio'] = st.text_area("📄 نبذة عن الشركة", height=100)

        if st.button("💾 إنشاء الحساب", use_container_width=True, type="primary"):
            if new_password != confirm_password:
                st.error("❌ كلمة المرور غير متطابقة")
            elif new_username and new_password and len(new_password) >= 6:
                if db:
                    try:
                        # فحص تكرار اسم المستخدم
                        users_ref = db.collection("users")
                        existing = users_ref.where("username", "==", new_username).limit(1).get()
                        if existing:
                            st.error("❌ اسم المستخدم موجود بالفعل")
                        else:
                            data = {
                                "username": new_username,
                                "email": new_email,
                                "password_hash": hash_password(new_password),
                                "role": account_type,
                                "created_at": firestore.SERVER_TIMESTAMP,
                                "is_active": True
                            }
                            if account_type == "شركة تركيبات" and company_details:
                                data.update(company_details)
                            
                            users_ref.add(data)
                            st.success(f"✅ تم إنشاء حساب {account_type} بنجاح!")
                            st.info("🔄 يمكنك تسجيل الدخول الآن")
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")
            else:
                st.error("⚠️ يرجى إدخال بيانات صحيحة (كلمة مرور 6 أحرف على الأقل)")
    
    st.stop()

# =========================================
# MAIN DASHBOARD
# =========================================
if st.session_state.logged_in:
    username = st.session_state.username
    role = st.session_state.user_role
    user_data = st.session_state.user_data

    # CSS محسّن
    st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; }
    section[data-testid="stSidebar"] { direction: rtl; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .stButton > button {
        background: linear-gradient(45deg, #00BFFF, #1E90FF);
        color: white;
        border: none;
        border-radius: 12px;
        height: 50px;
        font-weight: bold;
        font-size: 16px;
        box-shadow: 0 4px 15px rgba(0,191,255,0.3);
    }
    .stButton > button:hover { 
        background: linear-gradient(45deg, #0099cc, #00BFFF);
        box-shadow: 0 6px 20px rgba(0,191,255,0.4);
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar محسّن
    with st.sidebar:
        try:
            logo = Image.open("logo.png")
            st.image(logo, width=200, clamp=True)
        except:
            st.markdown("### ☀️ VPC Solar")
        
        st.markdown(f"**👤 مرحباً: {username}**")
        st.markdown(f"*🎭 الدور: {role}*")
        
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # صفحات حسب الدور
        if role == "شركة تركيبات":
            pages_list = ["الرئيسية", "طلبات التركيب", "ملف الشركة", "الإحصائيات", "تواصل"]
        elif role == "Admin":
            pages_list = ["الرئيسية", "حاسبة الطاقة", "شركات التركيب", "إدارة المستخدمين", "التقارير", "تواصل"]
        else:
            pages_list = ["الرئيسية", "حاسبة الطاقة", "شركات التركيب", "خطط المتابعة", "تواصل"]

        # ضمان الصفحة الحالية موجودة
        if st.session_state.current_page not in pages_list:
            st.session_state.current_page = "الرئيسية"
            
        current_idx = pages_list.index(st.session_state.current_page)
        selected_page = st.selectbox("📋 القائمة الرئيسية", pages_list, index=current_idx)
        st.session_state.current_page = selected_page

    # =========================================
    # صفحات محسّنة
    # =========================================
    
    if st.session_state.current_page == "الرئيسية":
        st.title("🏠 الصفحة الرئيسية")
        st.markdown("### أهلاً بك في عالم الطاقة الشمسية الذكية! ☀️")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏠 عملاء سكنيين", "1,247")
        with col2:
            st.metric("🚜 مشاريع زراعية", "89")
        with col3:
            st.metric("⚡ كيلو وات مثبت", "2.5M")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🏠 الأنظمة السكنية")
            st.info("حلول متكاملة للمنازل والشقق")
            if st.button("استكشف الحلول السكنية", use_container_width=True):
                st.session_state.current_page = "حاسبة الطاقة"
                st.rerun()
        with col2:
            st.markdown("### 🚜 الأنظمة الزراعية")
            st.info("طلمبات مياه وأنظمة ري ذكية")
            if st.button("استكشف الحلول الزراعية", use_container_width=True):
                st.balloons()

    elif st.session_state.current_page == "حاسبة الطاقة":
        st.title("⚡ حاسبة الطاقة الشمسية المتقدمة")
        
        with st.form("solar_calc"):
            col1, col2 = st.columns(2)
            with col1:
                power = st.number_input("💡 إجمالي الأحمال (وات)", min_value=100, value=1500, step=100)
                hours = st.number_input("⏰ ساعات التشغيل اليومية", min_value=1, value=6, step=1)
                voltage = st.selectbox("🔋 جهد النظام", [12, 24, 48], index=1)
            
            with col2:
                backup_days = st.slider("📅 أيام الاحتياطي", 1, 7, 3)
                efficiency = st.slider("🎛️ كفاءة النظام %", 70, 95, 85)
            
            calculate = st.form_submit_button("🧮 احسب النظام", use_container_width=True)
        
        if calculate:
            # الحسابات المتقدمة
            daily_energy = power * hours
            inverter_size = int(power * 1.25)
            panel_kw_per_day = 5  # كيلو وات ساعة لكل لوح
            panel_count = max(1, round(daily_energy / (panel_kw_per_day * 1000)))
            battery_capacity = int((daily_energy * backup_days * 1.2) / (voltage * (efficiency/100)))
            
            # التكلفة التقريبية
            panel_cost = panel_count * 4500
            inverter_cost = inverter_size * 2.5
            battery_cost = (battery_capacity // 200) * 8000
            total_cost = panel_cost + inverter_cost + battery_cost + 25000  # تكلفة التركيب
            
            st.markdown("---")
            st.subheader("📊 النتائج المتقدمة")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("⚡ الاستهلاك اليومي", f"{daily_energy:,.0f} Wh")
            col2.metric("🔌 الإنفرتر", f"{inverter_size} W")
            col3.metric("☀️ الألواح الشمسية", f"{panel_count}")
            col4.metric("🔋 سعة البطارية", f"{battery_capacity} Ah")
            
            st.success(f"💰 **التكلفة الإجمالية التقريبية: {total_cost:,.0f} جنيه مصري**")
            
            # مخطط بياني
            fig = px.pie(values=[panel_cost, inverter_cost, battery_cost, 25000],
                        names=['الألواح', 'الإنفرتر', 'البطاريات', 'التركيب'],
                        title="توزيع التكلفة")
            st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.current_page == "شركات التركيب":
        st.title("🏢 شركات التركيب المعتمدة")
        
        if db:
            companies = list(db.collection("users")
                           .where("role", "==", "شركة تركيبات")
                           .where("is_active", "==", True)
                           .stream())
            
            if companies:
                for doc in companies:
                    company = doc.to_dict()
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.markdown(f"### {company['username']}")
                            st.caption(f"📍 {company.get('location', 'غير محدد')} | 📞 {company.get('phone', 'غير محدد')}")
                            st.write(company.get('bio', 'لا توجد نبذة'))
                        
                        with col2:
                            if st.button("💬 طلب عرض أسعار", key=f"quote_{doc.id}"):
                                db.collection("quotes").add({
                                    "company_id": doc.id,
                                    "customer": st.session_state.username,
                                    "status": "جديد",
                                    "timestamp": firestore.SERVER_TIMESTAMP
                                })
                                st.success(f"✅ تم إرسال طلبك لـ {company['username']}")
                        
                        with col3:
                            if st.button("📞 اتصال", key=f"call_{doc.id}"):
                                st.info(f"اتصل بـ {company['username']}")
            else:
                st.warning("⚠️ لا توجد شركات تركيب مسجلة حالياً")
        else:
            st.error("❌ خطأ في الاتصال بقاعدة البيانات")

    elif st.session_state.current_page == "إدارة المستخدمين" and role == "Admin":
        st.title("👥 إدارة المستخدمين")
        # كود إدارة المستخدمين هنا...

    elif st.session_state.current_page == "تواصل":
        st.title("📞 تواصل معنا")
        with st.form("contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("👤 الاسم الكامل")
                email = st.text_input("📧 البريد الإلكتروني")
            with col2:
                phone = st.text_input("📱 رقم الهاتف")
                subject = st.text_input("📋 الموضوع")
            
            message = st.text_area("💬 رسالتك", height=150)
            submitted = st.form_submit_button("📤 إرسال الرسالة", use_container_width=True)
            
            if submitted and db:
                try:
                    db.collection("messages").add({
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "subject": subject,
                        "message": message,
                        "user_id": st.session_state.username,
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("✅ تم إرسال رسالتك بنجاح! سنرد عليك قريباً")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ خطأ في الإرسال: {e}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        VPC Solar © 2025 | تطوير المهندس محمد سعد الدين | 
        <a href='mailto:info@vpcsolar.com'>📧 اتصل بنا</a>
    </div>
    """, unsafe_allow_html=True)
