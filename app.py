import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import firestore
from PIL import Image
import hashlib
from datetime import datetime
import numpy as np

# =========================================
# PAGE CONFIG
# =========================================
st.set_page_config(
    page_title="VPC Solar Pro",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================
# FIRESTORE CONNECTION (آمن)
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
        st.error(f"❌ خطأ Firestore: {e}")
        return None

db = init_firestore()

# =========================================
# SECURITY FUNCTIONS
# =========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Admin credentials (آمن)
ADMIN_CREDS = {"admin": hash_password("vpc2025")}

# =========================================
# SESSION STATE INIT
# =========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "subscription_plan" not in st.session_state:
    st.session_state.subscription_plan = "مجاني"
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 الرئيسية"

# =========================================
# 🔐 LOGIN SYSTEM (مُصحح)
# =========================================
if not st.session_state.logged_in:
    # Hero Section
    st.markdown("""
    <style>
    .hero-section {
        background: linear-gradient(135deg, #00BFFF 0%, #1E90FF 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        text-align: center;
        color: white;
        margin: 1rem 0;
    }
    .hero-title { font-size: 3rem; margin-bottom: 1rem; }
    .hero-subtitle { font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">☀️ VPC Solar Pro</h1>
        <p class="hero-subtitle">منصة الوساطة الذكية للطاقة الشمسية</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Login Tabs
    tab_login, tab_register = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب"])
    
    with tab_login:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("### بيانات الدخول")
        with col2:
            username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسمك")
            password = st.text_input("🔒 كلمة المرور", type="password", placeholder="••••••")
            
            if st.button("🚀 دخول النظام", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("⚠️ أدخل بيانات الدخول")
                elif username == "admin" and ADMIN_CREDS["admin"] == hash_password(password):
                    # Admin login
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = "Admin"
                    st.session_state.user_data = {"role": "Admin"}
                    st.rerun()
                elif db:
                    # User login from Firestore
                    try:
                        users_ref = db.collection("users")
                        query = users_ref.where("username", "==", username).limit(1).stream()
                        for doc in query:
                            user_data = doc.to_dict()
                            if user_data.get("password_hash") == hash_password(password):
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_role = user_data.get("role", "عميل")
                                st.session_state.user_data = user_data
                                st.session_state.user_id = doc.id
                                st.success("✅ تم تسجيل الدخول بنجاح!")
                                st.rerun()
                                break
                        else:
                            st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
                    except Exception as e:
                        st.error(f"خطأ في قاعدة البيانات: {e}")
    
    with tab_register:
        st.markdown("### إنشاء حساب جديد")
        with st.form("register_form"):
            new_username = st.text_input("👤 اسم المستخدم")
            new_email = st.text_input("📧 البريد الإلكتروني")
            new_password = st.text_input("🔒 كلمة المرور", type="password")
            account_type = st.radio("نوع الحساب:", ["عميل", "شركة تركيب"])
            
            submitted = st.form_submit_button("💾 إنشاء الحساب", use_container_width=True)
            
            if submitted and db and new_username and new_password:
                try:
                    # Check if username exists
                    existing = db.collection("users").where("username", "==", new_username).limit(1).get()
                    if existing:
                        st.error("❌ اسم المستخدم موجود بالفعل")
                    else:
                        db.collection("users").add({
                            "username": new_username,
                            "email": new_email,
                            "password_hash": hash_password(new_password),
                            "role": account_type,
                            "subscription": "مجاني",
                            "commission_earned": 0,
                            "projects_completed": 0,
                            "is_active": True,
                            "created_at": firestore.SERVER_TIMESTAMP
                        })
                        st.success(f"✅ تم إنشاء حساب {account_type} بنجاح!")
                        st.info("🔄 يمكنك تسجيل الدخول الآن")
                except Exception as e:
                    st.error(f"❌ خطأ: {e}")
    
    st.stop()

# =========================================
# MAIN APPLICATION (بعد تسجيل الدخول)
# =========================================
st.markdown("""
<style>
.main { direction: rtl; text-align: right; }
.stButton > button {
    background: linear-gradient(45deg, #00BFFF, #1E90FF);
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(0,191,255,0.3);
}
.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(0,191,255,0.4);
    transform: translateY(-2px);
}
.metric-container { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important; }
</style>
""", unsafe_allow_html=True)

# =========================================
# SIDEBAR (مُصحح - بدون مشاكل الصور)
# =========================================
with st.sidebar:
    # Logo آمن
    try:
        if "logo_base64" in st.secrets:
            st.image(st.secrets["logo_base64"], width=180)
        else:
            st.markdown("### ☀️ **VPC Solar Pro**")
    except:
        st.markdown("### ☀️ **VPC Solar Pro**")
    
    st.markdown(f"""
    **👤 {st.session_state.username}**  
    🎭 {st.session_state.user_role}  
    💳 {st.session_state.subscription_plan}
    """)
    
    # Pages based on role
    if st.session_state.user_role == "Admin":
        pages = ["🏠 لوحة التحكم", "👥 المستخدمين", "💰 العمولات", "📊 التقارير"]
    elif st.session_state.user_role == "شركة تركيب":
        pages = ["🏠 الرئيسية", "📋 طلبات العملاء", "💰 عمولتي", "📊 إحصائياتي"]
    else:  # عميل
        pages = ["🏠 الرئيسية", "⚡ حاسبات الطاقة", "🏢 شركات التركيب", "💳 خطط المتابعة"]
    
    st.session_state.current_page = st.selectbox("📋 القائمة الرئيسية", pages)
    
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# =========================================
# MAIN PAGES
# =========================================

if st.session_state.current_page == "🏠 الرئيسية":
    st.title("🏠 VPC Solar Pro")
    st.markdown("### مرحباً بك في منصة الوساطة الذكية للطاقة الشمسية!")
    
    # Stats Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 عملاء", "1,247")
    with col2:
        st.metric("🏢 شركات", "23")
    with col3:
        st.metric("📋 طلبات", "156")
    with col4:
        st.metric("💰 عمولات", "458K جنيه")

    st.markdown("---")
    
    # Quick Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ حاسبة الطاقة", use_container_width=True):
            st.session_state.current_page = "⚡ حاسبات الطاقة"
            st.rerun()
    with col2:
        if st.button("🏢 شركات التركيب", use_container_width=True):
            st.session_state.current_page = "🏢 شركات التركيب"
            st.rerun()

elif st.session_state.current_page == "⚡ حاسبات الطاقة":
    st.title("⚡ حاسبات الطاقة الشمسية المتقدمة")
    
    tab1, tab2 = st.tabs(["🏠 سكني", "🚜 زراعي"])
    
    with tab1:
        st.subheader("🏠 نظام سكني")
        with st.form("solar_residential"):
            appliances = {
                "تكييف 1.5HP": 1800, "ثلاجة": 200, "إضاءة": 100,
                "تلفزيون": 150, "غسالة": 500, "مكنسة": 1200
            }
            
            selected = st.multiselect("اختر الأجهزة:", list(appliances.keys()), ["تكييف 1.5HP", "ثلاجة"])
            hours = st.slider("ساعات الاستخدام اليومي:", 1, 24, 8)
            backup_days = st.slider("احتياطي (أيام):", 1, 5, 2)
            
            if st.form_submit_button("🧮 احسب النظام", use_container_width=True):
                total_watts = sum(appliances[app] for app in selected)
                daily_kwh = total_watts * hours / 1000
                panels = max(1, round(daily_kwh / 5))  # 5 كيلووات ساعة لكل لوح
                inverter_w = max(1000, round(total_watts * 1.25 / 1000) * 1000)
                battery_ah = max(100, round(daily_kwh * backup_days / 0.8 * 1.2))
                
                cost = panels * 5000 + (inverter_w/1000)*3000 + (battery_ah/100)*8000 + 25000
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("☀️ الألواح", f"{panels}")
                col2.metric("🔌 الإنفرتر", f"{inverter_w} وات")
                col3.metric("🔋 البطارية", f"{battery_ah} أمبير")
                col4.metric("💰 التكلفة", f"{cost:,.0f} جنيه")
                
                if st.button("🚀 اطلب عرض أسعار", use_container_width=True):
                    if db:
                        db.collection("quotes").add({
                            "customer": st.session_state.username,
                            "type": "سكني",
                            "total_watts": total_watts,
                            "daily_kwh": daily_kwh,
                            "panels": panels,
                            "cost_estimate": cost,
                            "status": "جديد",
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("✅ تم إرسال طلبك لشركات التركيب!")
    
    with tab2:
        st.subheader("🚜 نظام ري زراعي")
        pumps = st.number_input("عدد المضخات:", 1, 20, 2)
        pump_hp = st.select_slider("حصان المضخة:", options=[1, 2, 3, 5, 7.5, 10])
        daily_hours = st.slider("ساعات التشغيل:", 2, 16, 6)
        
        if st.button("🧮 احسب النظام الزراعي", use_container_width=True):
            total_kw = pumps * pump_hp * 0.746 * 1.3
            daily_kwh = total_kw * daily_hours
            panels = max(1, round(daily_kwh / 5))
            
            st.success(f"""
            ✅ **الألواح المطلوبة**: {panels} لوح  
            💰 **التكلفة التقريبية**: {panels * 5000 + 75000:,.0f} جنيه
            """)

elif st.session_state.current_page == "🏢 شركات التركيب":
    st.title("🏢 شركات التركيب المعتمدة")
    
    if db:
        companies = db.collection("users").where("role", "==", "شركة تركيب").stream()
        for doc in companies:
            company = doc.to_dict()
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"### {company.get('username', 'غير معروف')}")
                    st.caption(f"📍 {company.get('location', 'غير محدد')}")
                    st.write(company.get('bio', 'شركة تركيبات معتمدة'))
                with col2:
                    if st.button("💬 طلب عرض أسعار", key=f"request_{doc.id}"):
                        st.success(f"✅ تم إرسال طلبك لـ {company['username']}")

elif st.session_state.current_page == "💳 خطط المتابعة":
    st.title("💳 خطط المتابعة والصيانة")
    
    plans_data = {
        "مجاني": {"price": 0, "features": ["📱 تنبيهات أساسية", "📊 تقارير شهرية"]},
        "برونزي": {"price": 299, "features": ["✅ كل المجاني", "🔧 زيارة صيانة سنوية", "⭐ دعم أولوية"]},
        "فضي": {"price": 599, "features": ["✅ كل البرونزي", "🔧 2 زيارة سنوياً", "📞 دعم 24/7"]},
        "ذهبي": {"price": 999, "features": ["✅ كل الفضي", "🔧 زيارات غير محدودة", "🛡️ ضمان شامل 5 سنوات"]}
    }
    
    cols = st.columns(4)
    for idx, (plan, data) in enumerate(plans_data.items()):
        with cols[idx]:
            st.markdown(f"### **{plan}**")
            st.markdown(f"**{data['price']} جنيه/شهر**")
            for feature in data['features']:
                st.write(feature)
            if st.button(f"اشترك في {plan}", key=f"plan_{plan}", use_container_width=True):
                st.session_state.subscription_plan = plan
                st.success(f"✅ تم الاشتراك في خطة **{plan}**!")

# =========================================
# FOOTER
# =========================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <strong>VPC Solar Pro © 2025</strong> | 
    منصة الوساطة الذكية للطاقة الشمسية | 
    تطوير المهندس محمد سعد الدين
</div>
""", unsafe_allow_html=True)
