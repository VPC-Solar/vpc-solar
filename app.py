import streamlit as st
import json
import pandas as pd
import plotly.express as px
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
# FIRESTORE (آمن)
# =========================================
@st.cache_resource
def init_firestore():
    try:
        if "textkey" in st.secrets:
            key_dict = json.loads(st.secrets["textkey"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            return firestore.Client(credentials=creds, project=key_dict["project_id"])
        return None
    except:
        return None

db = init_firestore()

# =========================================
# SECURITY
# =========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_CREDS = {"admin": hash_password("vpc2025")}

# =========================================
# SESSION STATE
# =========================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "subscription_plan" not in st.session_state: st.session_state.subscription_plan = "مجاني"
if "current_page" not in st.session_state: st.session_state.current_page = "🏠 الرئيسية"

# =========================================
# 🔐 LOGIN & REGISTER (مع رقم التلفون)
# =========================================
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .hero-section {
        background: linear-gradient(135deg, #00BFFF 0%, #1E90FF 100%);
        padding: 3rem 2rem; border-radius: 20px; text-align: center;
        color: white; margin: 1rem 0;
    }
    .hero-title { font-size: 3rem; margin-bottom: 1rem; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">☀️ VPC Solar Pro</h1>
        <p>منصة الوساطة الذكية للطاقة الشمسية</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_login, tab_register = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب"])
    
    with tab_login:
        col1, col2 = st.columns([1, 2])
        with col2:
            username = st.text_input("👤 اسم المستخدم")
            phone = st.text_input("📱 رقم التلفون", placeholder="01xxxxxxxxx")
            password = st.text_input("🔒 كلمة المرور", type="password")
            
            if st.button("🚀 دخول النظام", type="primary", use_container_width=True):
                if username == "admin" and ADMIN_CREDS["admin"] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = "Admin"
                    st.rerun()
                elif db and username and phone and password:
                    try:
                        users_ref = db.collection("users")
                        query = users_ref.where("username", "==", username).limit(1).stream()
                        for doc in query:
                            user_data = doc.to_dict()
                            if (user_data.get("password_hash") == hash_password(password) and 
                                user_data.get("phone") == phone):
                                st.session_state.logged_in = True
                                st.session_state.username = username
                                st.session_state.user_role = user_data.get("role", "عميل")
                                st.session_state.user_data = user_data
                                st.session_state.user_id = doc.id
                                st.session_state.user_phone = phone
                                st.success("✅ تم تسجيل الدخول!")
                                st.rerun()
                                break
                        st.error("❌ بيانات غير صحيحة")
                    except:
                        st.error("خطأ في الاتصال")
    
    with tab_register:
        st.markdown("### إنشاء حساب جديد")
        with st.form("register"):
            new_username = st.text_input("👤 اسم المستخدم")
            new_phone = st.text_input("📱 رقم التلفون", placeholder="01xxxxxxxxx")
            new_email = st.text_input("📧 البريد الإلكتروني")
            new_password = st.text_input("🔒 كلمة المرور", type="password")
            account_type = st.radio("نوع الحساب:", ["عميل", "شركة تركيب"])
            
            if account_type == "شركة تركيب":
                st.markdown("### بيانات الشركة")
                company_location = st.selectbox("📍 المحافظة", ["القاهرة", "الجيزة", "6 أكتوبر", "الإسكندرية"])
                company_bio = st.text_area("نبذة عن الشركة")
            
            submitted = st.form_submit_button("💾 إنشاء الحساب", use_container_width=True)
            
            if submitted and db and new_username and new_phone and new_password:
                if len(new_phone) != 11 or not new_phone.startswith('01'):
                    st.error("❌ رقم التلفون غير صحيح (يجب أن يكون 01xxxxxxxxx)")
                else:
                    try:
                        # Check username/phone
                        existing_user = db.collection("users").where("username", "==", new_username).limit(1).get()
                        existing_phone = db.collection("users").where("phone", "==", new_phone).limit(1).get()
                        
                        if existing_user or existing_phone:
                            st.error("❌ اسم المستخدم أو رقم التلفون موجود")
                        else:
                            user_data = {
                                "username": new_username,
                                "phone": new_phone,
                                "email": new_email,
                                "password_hash": hash_password(new_password),
                                "role": account_type,
                                "subscription": "مجاني",
                                "is_active": True,
                                "created_at": firestore.SERVER_TIMESTAMP
                            }
                            
                            if account_type == "شركة تركيب":
                                user_data.update({
                                    "location": company_location,
                                    "bio": company_bio
                                })
                            
                            db.collection("users").add(user_data)
                            st.success(f"✅ تم إنشاء حساب {account_type}!")
                            st.info("🔄 سجل دخولك الآن")
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")
    
    st.stop()

# =========================================
# MAIN APP (التصميم النهائي)
# =========================================
st.markdown("""
<style>
.main { direction: rtl; }
.stButton > button {
    background: linear-gradient(45deg, #00BFFF, #1E90FF);
    color: white; border-radius: 12px; border: none;
    font-weight: bold; box-shadow: 0 4px 15px rgba(0,191,255,0.3);
}
.stButton > button:hover { box-shadow: 0 6px 20px rgba(0,191,255,0.4); }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ☀️ **VPC Solar Pro**")
    st.markdown(f"""
    **👤 {st.session_state.username}**  
    📱 {st.session_state.get('user_phone', 'غير محدد')}  
    🎭 {st.session_state.user_role}
    """)
    
    # Pages حسب الدور
    if st.session_state.user_role == "Admin":
        pages = ["🏠 لوحة التحكم", "👥 العملاء", "🏢 الشركات", "📋 طلبات المعاينة"]
    elif st.session_state.user_role == "شركة تركيب":
        pages = ["🏠 الرئيسية", "📋 طلبات المعاينة", "👤 ملفي"]
    else:  # عميل
        pages = ["🏠 الرئيسية", "⚡ حاسبات الطاقة", "🏢 شركات التركيب"]
    
    st.session_state.current_page = st.selectbox("📋 القائمة", pages)
    
    st.button("🚪 تسجيل الخروج", use_container_width=True)

# =========================================
# الصفحات الرئيسية
# =========================================

if st.session_state.current_page == "🏠 الرئيسية":
    st.title("🏠 VPC Solar Pro")
    st.markdown("### منصة الوساطة بين العملاء وشركات التركيبات الشمسية")
    
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("👥 عملاء مسجلين", "247")
    with col2: st.metric("🏢 شركات تركيب", "12")
    with col3: st.metric("📋 طلبات اليوم", "5")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚡ حاسبات الطاقة")
        st.info("احسب نظامك الشمسي بدقة عالية")
        if st.button("ابدأ الحساب", use_container_width=True):
            st.session_state.current_page = "⚡ حاسبات الطاقة"
            st.rerun()
    with col2:
        st.markdown("### 🏢 شركات التركيب")
        st.info("اطلب معاينة من الشركات المعتمدة")
        if st.button("عرض الشركات", use_container_width=True):
            st.session_state.current_page = "🏢 شركات التركيب"
            st.rerun()

elif st.session_state.current_page == "⚡ حاسبات الطاقة":
    st.title("⚡ حاسبة الطاقة الشمسية المتقدمة")
    
    tab1, tab2 = st.tabs(["🏠 سكني", "🚜 زراعي"])
    
    with tab1:  # سكني
        with st.form("calc_residential"):
            appliances = {
                "تكييف 1.5HP": 1800, "تكييف 2HP": 2500,
                "ثلاجة": 200, "تلفزيون": 150,
                "إضاءة (5 لمبات)": 100, "غسالة": 500
            }
            
            selected = st.multiselect("الأجهزة:", list(appliances.keys()), ["تكييف 1.5HP", "ثلاجة", "إضاءة (5 لمبات)"])
            hours = st.slider("ساعات الاستخدام:", 4, 24, 8)
            backup = st.slider("احتياطي (أيام):", 1, 5, 2)
            
            if st.form_submit_button("🧮 احسب النظام", use_container_width=True):
                total_watts = sum(appliances[app] for app in selected)
                daily_kwh = total_watts * hours / 1000
                panels = max(1, round(daily_kwh / 5))
                inverter = max(1000, round(total_watts * 1.25 / 1000) * 1000)
                battery = max(100, round(daily_kwh * backup / 0.8))
                cost = panels * 5000 + (inverter/1000)*3000 + (battery/100)*8000 + 25000
                
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("☀️ الألواح", f"{panels}")
                r2.metric("🔌 الإنفرتر", f"{inverter} وات")
                r3.metric("🔋 البطارية", f"{battery} أمبير")
                r4.metric("💰 التقدير", f"{cost:,.0f} جنيه")
                
                st.session_state.last_calc = {
                    "total_watts": total_watts, "daily_kwh": daily_kwh,
                    "panels": panels, "inverter": inverter,
                    "battery": battery, "cost": cost
                }
    
    with tab2:  # زراعي
        st.subheader("🚜 نظام الري الزراعي")
        pumps = st.number_input("عدد المضخات:", 1, 20, 2)
        hp = st.select_slider("حصان المضخة:", [1, 2, 3, 5, 7.5, 10])
        hours = st.slider("ساعات التشغيل:", 2, 16, 6)
        
        if st.button("🧮 احسب", use_container_width=True):
            total_kw = pumps * hp * 0.746 * 1.3
            daily_kwh = total_kw * hours
            panels = max(1, round(daily_kwh / 5))
            st.success(f"""
            ✅ **الألواح**: {panels} لوح  
            💰 **التكلفة**: {panels * 5000 + 75000:,.0f} جنيه
            """)
    
    # زر طلب المعاينة
    if hasattr(st.session_state, 'last_calc'):
        if st.button("🚀 اطلب معاينة ميدانية", use_container_width=True):
            if db:
                db.collection("inspection_requests").add({
                    "customer": st.session_state.username,
                    "customer_phone": st.session_state.get('user_phone', ''),
                    "system_data": st.session_state.last_calc,
                    "status": "جديد",
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "customer_type": st.session_state.user_role
                })
                st.success("✅ تم إرسال طلب المعاينة! سيتصل بك ممثل قريباً")
                st.balloons()

elif st.session_state.current_page == "🏢 شركات التركيب":
    st.title("🏢 شركات التركيبات المعتمدة")
    
    if db:
        companies = db.collection("users").where("role", "==", "شركة تركيب").where("is_active", "==", True).stream()
        
        for doc in companies:
            company = doc.to_dict()
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### **{company.get('username', 'غير معروف')}**")
                    st.caption(f"📱 {company.get('phone', 'غير محدد')} | 📍 {company.get('location', '')}")
                    st.write(company.get('bio', 'شركة تركيبات معتمدة'))
                
                with col2:
                    if st.button("📞 طلب معاينة", key=f"inspect_{doc.id}"):
                        if db:
                            db.collection("inspection_requests").add({
                                "customer": st.session_state.username,
                                "customer_phone": st.session_state.get('user_phone', ''),
                                "company_id": doc.id,
                                "company_name": company.get('username'),
                                "status": "جديد",
                                "type": "طلب مباشر",
                                "timestamp": firestore.SERVER_TIMESTAMP
                            })
                            st.success(f"✅ تم إرسال طلب المعاينة لـ {company['username']}")
                
                with col3:
                    st.button("⭐ تقييم", key=f"rate_{doc.id}")

# =========================================
# لوحة التحكم (ليك إنت بس كصاحب التطبيق)
# =========================================
elif st.session_state.user_role == "Admin" and "لوحة التحكم" in st.session_state.current_page:
    st.title("🏠 لوحة تحكم VPC Solar")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👥 العملاء", "247")
    with col2: st.metric("🏢 الشركات", "12")
    with col3: st.metric("📋 طلبات جديدة", "15")
    with col4: st.metric("📞 طلبات معاينة", "28")
    
    # جدول طلبات المعاينة (هنا بتشوف كل حاجة)
    if db:
        requests = db.collection("inspection_requests").where("status", "==", "جديد").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20).stream()
        
        st.subheader("📋 طلبات المعاينة الجديدة")
        for doc in requests:
            req = doc.to_dict()
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{req.get('customer', 'غير معروف')}**")
                    st.caption(f"📱 {req.get('customer_phone', '')}")
                    if 'system_data' in req:
                        st.caption(f"الألواح: {req['system_data'].get('panels', 0)}")
                with col2:
                    st.caption(req.get('company_name', 'طلب عام'))
                with col3:
                    st.caption(str(req['timestamp'].to_datetime())[:16])

# Footer
st.markdown("---")
st.markdown("*VPC Solar Pro © 2025 | منصة الوساطة الذكية للطاقة الشمسية*")
