import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import firestore
import hashlib
from datetime import datetime, timedelta
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
# FIRESTORE & UTILS
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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_CREDS = {"admin": hash_password("vpc2025")}

# Phone validation
def validate_phone(phone):
    return len(phone) == 11 and phone.startswith('01')

# =========================================
# SESSION STATE
# =========================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "current_page" not in st.session_state: st.session_state.current_page = "🏠 الرئيسية"
if "user_phone" not in st.session_state: st.session_state.user_phone = ""

# =========================================
# 🔐 AUTH SYSTEM (محسن)
# =========================================
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .hero {background: linear-gradient(135deg, #00BFFF 0%, #1E90FF 100%); 
           padding: 4rem; border-radius: 25px; text-align: center; color: white; margin: 2rem 0;}
    .hero h1 {font-size: 3.5rem; margin: 0;}
    .hero p {font-size: 1.3rem;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero">
        <h1>☀️ VPC Solar Pro</h1>
        <p>أذكى منصة للطاقة الشمسية في مصر</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 الدخول", "📝 التسجيل"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col2:
            username = st.text_input("👤 الاسم", placeholder="اسم المستخدم")
            phone = st.text_input("📱 التليفون", placeholder="01xxxxxxxxx")
            password = st.text_input("🔒 كلمة السر", type="password")
            
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                if st.button("🚀 دخول", type="primary"):
                    if username == "admin" and ADMIN_CREDS["admin"] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = "Admin"
                        st.rerun()
                    elif db and validate_phone(phone):
                        try:
                            users = db.collection("users").where("username", "==", username).stream()
                            for doc in users:
                                data = doc.to_dict()
                                if data.get("phone") == phone and data.get("password_hash") == hash_password(password):
                                    st.session_state.logged_in = True
                                    st.session_state.username = username
                                    st.session_state.user_role = data["role"]
                                    st.session_state.user_data = data
                                    st.session_state.user_id = doc.id
                                    st.session_state.user_phone = phone
                                    st.rerun()
                                    break
                            st.error("❌ بيانات خاطئة")
                        except:
                            st.error("خطأ في الاتصال")
    
    with tab2:
        with st.form("signup_form"):
            username = st.text_input("👤 الاسم الكامل")
            phone = st.text_input("📱 رقم التليفون", help="01xxxxxxxxx")
            email = st.text_input("📧 الإيميل")
            password = st.text_input("🔒 كلمة السر", type="password")
            role = st.radio("نوع الحساب", ["عميل", "شركة تركيب"])
            
            if role == "شركة تركيب":
                location = st.selectbox("📍 الموقع", ["6 أكتوبر", "القاهرة", "الجيزة", "الإسكندرية"])
                bio = st.text_area("نبذة عن الشركة", height=80)
            
            submit = st.form_submit_button("💾 إنشاء حساب", use_container_width=True)
            
            if submit and db:
                if not validate_phone(phone):
                    st.error("❌ رقم التليفون غير صحيح")
                else:
                    try:
                        # Check duplicates
                        dup_user = db.collection("users").where("username", "==", username).limit(1).get()
                        dup_phone = db.collection("users").where("phone", "==", phone).limit(1).get()
                        
                        if dup_user or dup_phone:
                            st.error("❌ الاسم أو التليفون موجود")
                        else:
                            data = {
                                "username": username, "phone": phone, "email": email,
                                "password_hash": hash_password(password), "role": role,
                                "is_active": True, "created_at": firestore.SERVER_TIMESTAMP,
                                "projects": 0, "rating": 0
                            }
                            if role == "شركة تركيب":
                                data.update({"location": location, "bio": bio})
                            
                            db.collection("users").add(data)
                            st.success("✅ الحساب تم إنشاؤه!")
                    except Exception as e:
                        st.error(f"❌ خطأ: {e}")
    
    st.stop()

# =========================================
# MAIN DASHBOARD
# =========================================
st.markdown("""
<style>
.main {direction: rtl;}
.stButton>button {background: linear-gradient(45deg,#00BFFF,#1E90FF); 
                  color:white;border:none;border-radius:12px;font-weight:bold;
                  box-shadow:0 4px 15px rgba(0,191,255,.3);}
.stButton>button:hover {box-shadow:0 6px 20px rgba(0,191,255,.4);}
</style>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### ☀️ **VPC Solar Pro**")
    st.markdown(f"""
    👤 **{st.session_state.username}**  
    📱 `{st.session_state.user_phone}`  
    🎭 **{st.session_state.user_role}**
    """)
    
    role_pages = {
        "Admin": ["🏠 لوحة التحكم", "👥 العملاء", "🏢 الشركات", "📋 طلبات المعاينة", "📊 التقارير"],
        "شركة تركيب": ["🏠 الرئيسية", "📋 طلباتي", "⭐ تقييماتي", "⚙️ ملفي"],
        "عميل": ["🏠 الرئيسية", "⚡ الحاسبات", "🏢 الشركات", "📋 طلباتي"]
    }
    
    pages = role_pages.get(st.session_state.user_role, role_pages["عميل"])
    st.session_state.current_page = st.selectbox("📋 القائمة", pages)
    st.button("🚪 خروج", use_container_width=True)

# =========================================
# PAGES SYSTEM
# =========================================

def display_stats():
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("👥 المستخدمين", "1,247")
    with col2: st.metric("🏢 الشركات", "23")
    with col3: st.metric("📋 الطلبات", "156")
    with col4: st.metric("⭐ التقييم", "4.8/5")

if st.session_state.current_page == "🏠 الرئيسية" or st.session_state.current_page == "🏠 لوحة التحكم":
    st.title("🏠 VPC Solar Pro")
    display_stats()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚡ حاسبات متقدمة")
        st.info("احسب نظامك بدقة 99%")
        st.button("الحاسبات", use_container_width=True)
    with col2:
        st.markdown("### 🏢 شركات معتمدة")
        st.info("اطلب معاينة فورية")
        st.button("الشركات", use_container_width=True)

elif "الحاسبات" in st.session_state.current_page or "⚡ الحاسبات" in st.session_state.current_page:
    st.title("⚡ حاسبات الطاقة الشمسية")
    
    tab1, tab2, tab3 = st.tabs(["🏠 سكني", "🚜 زراعي", "🏭 تجاري"])
    
    with tab1:
        with st.form("residential_calc"):
            appliances = {
                "تكييف 1.5 حصان": 1800, "تكييف 2 حصان": 2500,
                "ثلاجة كبيرة": 250, "ثلاجة صغيرة": 150,
                "إضاءة LED (10 لمبات)": 100, "تلفزيون 55 بوصة": 200,
                "غسالة أوتوماتيك": 500, "ميكروويف": 1200
            }
            
            selected = st.multiselect("اختر أجهزتك:", list(appliances.keys()), 
                                    ["تكييف 1.5 حصان", "ثلاجة كبيرة", "إضاءة LED (10 لمبات)"])
            hours = st.slider("ساعات التشغيل اليومي:", 2, 24, 8)
            backup_days = st.slider("أيام الاحتياطي:", 1, 7, 2)
            submit = st.form_submit_button("🧮 احسب النظام", use_container_width=True)
            
            if submit:
                total_w = sum(appliances[a] for a in selected)
                daily_kwh = total_w * hours / 1000
                panels = max(2, np.ceil(daily_kwh / 5.5))
                inverter_kw = np.ceil(total_w * 1.25 / 1000)
                battery_ah = np.ceil(daily_kwh * backup_days * 1.2 / 48)
                
                cost_breakdown = {
                    "الألواح": panels * 4800,
                    "الإنفرتر": inverter_kw * 1000 * 2.8,
                    "البطاريات": battery_ah * 85,
                    "التركيب": 28000
                }
                total_cost = sum(cost_breakdown.values())
                
                # Results
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("☀️ الألواح", f"{panels} لوح")
                r2.metric("🔌 الإنفرتر", f"{inverter_kw} كيلو وات")
                r3.metric("🔋 البطاريات", f"{battery_ah} أمبير")
                r4.metric("💰 الإجمالي", f"{total_cost:,.0f} جنيه")
                
                # Pie chart
                fig = px.pie(values=list(cost_breakdown.values()), 
                           names=list(cost_breakdown.keys()),
                           title="توزيع التكلفة")
                st.plotly_chart(fig, use_container_width=True)
                
                st.session_state.last_calc = {
                    "type": "سكني", "total_w": total_w, "daily_kwh": daily_kwh,
                    "panels": panels, "inverter": inverter_kw, "battery": battery_ah,
                    "cost": total_cost
                }
    
    with tab2:
        st.subheader("🚜 الري الزراعي")
        col1, col2 = st.columns(2)
        with col1:
            pumps = st.number_input("عدد المضخات", 1, 50, 3)
            hp = st.select_slider("حصان المضخة", [1, 1.5, 2, 3, 5, 7.5, 10])
        with col2:
            depth = st.slider("عمق السحب (متر)", 5, 100, 20)
            hours = st.slider("ساعات العمل", 2, 20, 8)
        
        if st.button("🧮 احسب النظام الزراعي", use_container_width=True):
            total_hp = pumps * hp
            total_kw = total_hp * 0.746 * 1.5  # معامل الرفع
            daily_kwh = total_kw * hours
            panels = max(4, np.ceil(daily_kwh / 6))
            
            st.balloons()
            st.success(f"""
            ✅ **المضخات**: {pumps} × {hp} حصان  
            ☀️ **الألواح**: {panels} لوح  
            💰 **التكلفة**: {panels * 4800 + 85000:,.0f} جنيه
            """)
    
    with tab3:
        st.info("🏭 الحاسبة التجارية قيد التطوير")

    # Request Inspection Button
    if hasattr(st.session_state, 'last_calc'):
        if st.button("🚀 اطلب معاينة مجانية", type="primary", use_container_width=True):
            if db:
                db.collection("inspection_requests").add({
                    "customer": st.session_state.username,
                    "customer_phone": st.session_state.user_phone,
                    "calc_data": st.session_state.last_calc,
                    "status": "جديد",
                    "priority": "عالي",
                    "created_at": firestore.SERVER_TIMESTAMP
                })
                st.success("✅ تم إرسال طلب المعاينة! اتصل بك فني خلال 24 ساعة")
                st.balloons()

elif "الشركات" in st.session_state.current_page or "🏢 الشركات" in st.session_state.current_page:
    st.title("🏢 شركات التركيبات المعتمدة")
    
    if db:
        companies_query = db.collection("users").where("role", "==", "شركة تركيب").where("is_active", "==", True).stream()
        companies = []
        for doc in companies_query:
            companies.append({**doc.to_dict(), "id": doc.id})
        
        # Filter & Search
        search = st.text_input("🔍 ابحث عن شركة")
        location_filter = st.selectbox("📍 المحافظة", ["الكل"] + ["6 أكتوبر", "القاهرة", "الجيزة"])
        
        filtered = [c for c in companies 
                   if (not search or search.lower() in c.get('username', '').lower())
                   and (location_filter == "الكل" or c.get('location') == location_filter)]
        
        for company in filtered:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"### ⭐ **{company['username']}**")
                    st.caption(f"📱 {company.get('phone', 'غير محدد')} | 📍 {company.get('location', '')}")
                    st.markdown(company.get('bio', ''))
                
                with col2:
                    if st.button("📞 معاينة فورية", key=f"req_{company['id']}"):
                        db.collection("inspection_requests").add({
                            "customer": st.session_state.username,
                            "customer_phone": st.session_state.user_phone,
                            "company_id": company['id'],
                            "company_name": company['username'],
                            "status": "جديد",
                            "source": "شركة محددة",
                            "created_at": firestore.SERVER_TIMESTAMP
                        })
                        st.success(f"✅ تم طلب معاينة من {company['username']}")
                
                with col3:
                    st.button("💬 واتساب", key=f"wa_{company['id']}")

# Admin Dashboard
elif st.session_state.user_role == "Admin":
    if "طلبات المعاينة" in st.session_state.current_page:
        st.title("📋 طلبات المعاينة")
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("📋 الطلبات الجديدة", "15")
        with col2: st.metric("✅ المكتملة", "42")
        with col3: st.metric("⏳ قيد التنفيذ", "8")
        
        if db:
            # Recent requests
            recent = db.collection("inspection_requests").order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
            
            for doc in recent:
                req = doc.to_dict()
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{req.get('customer', 'غير معروف')}**")
                        st.caption(f"📱 {req.get('customer_phone', '')}")
                        if 'calc_data' in req:
                            st.caption(f"الألواح: {req['calc_data'].get('panels', '?')}")
                    
                    with col2:
                        st.caption(req.get('company_name', 'طلب عام'))
                    
                    with col3:
                        st.caption(str(req.get('created_at', '').to_datetime())[:16])
                    
                    with col4:
                        status = req.get('status', 'غير محدد')
                        st.caption(f"**{status}**")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#666;padding:2rem;'>
    VPC Solar Pro © 2025 | منصة الوساطة الرائدة للطاقة الشمسية
</div>
""", unsafe_allow_html=True)
