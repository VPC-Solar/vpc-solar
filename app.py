import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from google.cloud import firestore
from PIL import Image
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
# FIRESTORE & CACHE
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
# SECURITY & STATE
# =========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

ADMIN_CREDENTIALS = {"admin": hashlib.sha256("vpc2025".encode()).hexdigest()}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "subscription_plan" not in st.session_state:
    st.session_state.subscription_plan = "مجاني"

# =========================================
# LOGIN SYSTEM (محسن)
# =========================================
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .hero { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown('<div class="hero"><h1>☀️ VPC Solar Pro</h1><p>منصة ذكية للطاقة الشمسية</p></div>', unsafe_allow_html=True)
    
    with col2:
        tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "📝 حساب جديد"])
        
        with tab1:
            user_in = st.text_input("👤 اسم المستخدم")
            pass_in = st.text_input("🔒 كلمة المرور", type="password")
            
            if st.button("🚀 دخول النظام", use_container_width=True, type="primary"):
                # Admin login
                if user_in == "admin" and ADMIN_CREDENTIALS["admin"] == hash_password(pass_in):
                    st.session_state.logged_in = True
                    st.session_state.username = user_in
                    st.session_state.user_role = "Admin"
                    st.rerun()
                # User login
                elif db:
                    users = db.collection("users").where("username", "==", user_in).stream()
                    for doc in users:
                        data = doc.to_dict()
                        if data.get("password_hash") == hash_password(pass_in):
                            st.session_state.logged_in = True
                            st.session_state.username = user_in
                            st.session_state.user_role = data.get("role", "عميل")
                            st.session_state.user_data = data
                            st.session_state.user_id = doc.id
                            st.rerun()
                    st.error("❌ بيانات غير صحيحة")
        
        with tab2:
            with st.form("signup"):
                new_user = st.text_input("👤 اسم المستخدم")
                new_email = st.text_input("📧 البريد الإلكتروني")
                new_pass = st.text_input("🔒 كلمة المرور", type="password")
                role = st.radio("نوع الحساب", ["عميل", "شركة تركيب"])
                
                if st.form_submit_button("💾 إنشاء حساب", use_container_width=True):
                    if db and new_user and new_pass:
                        db.collection("users").add({
                            "username": new_user,
                            "email": new_email,
                            "password_hash": hash_password(new_pass),
                            "role": role,
                            "subscription": "مجاني",
                            "commission_earned": 0,
                            "projects_completed": 0,
                            "created_at": firestore.SERVER_TIMESTAMP
                        })
                        st.success("✅ الحساب تم إنشاؤه!")
    
    st.stop()

# =========================================
# MAIN APP - DASHBOARD PRO
# =========================================
if st.session_state.logged_in:
    # Enhanced CSS
    st.markdown("""
    <style>
    .main {direction: rtl;}
    .stMetric > label {font-size: 1.2rem !important;}
    .card {background: linear-gradient(145deg, #f0f8ff, #e6f3ff); border-radius: 15px; padding: 1.5rem;}
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar Pro
    with st.sidebar:
        st.image(Image.open("logo.png") if 'logo.png' in st.secrets else None, width=200)
        st.markdown(f"**👤 {st.session_state.username}**")
        st.caption(f"🎭 {st.session_state.user_role} | {st.session_state.subscription_plan}")
        
        pages = {
            "عميل": ["🏠 الرئيسية", "⚡ حاسبات الطاقة", "🏢 شركات التركيب", "📊 مشاريعي", "💳 خطط المتابعة", "📞 دعم"],
            "شركة تركيب": ["🏠 الرئيسية", "📋 طلبات العملاء", "💰 عمولتي", "📊 إحصائياتي", "⚙️ ملفي", "📞 دعم"],
            "Admin": ["🏠 لوحة التحكم", "👥 المستخدمين", "💰 العمولات", "📊 التقارير", "⚙️ الإعدادات"]
        }
        
        role_pages = pages.get(st.session_state.user_role, pages["عميل"])
        st.session_state.current_page = st.selectbox("📋 القائمة", role_pages, key="page_selector")
        
        st.markdown("---")
        if st.button("🚪 خروج"):
            for key in st.session_state.keys():
                delattr(st.session_state, key)
            st.rerun()

    # =========================================
    # صفحات العميل
    # =========================================
    if st.session_state.user_role == "عميل":
        
        if st.session_state.current_page == "⚡ حاسبات الطاقة":
            st.title("⚡ حاسبات الطاقة الشمسية المتقدمة")
            
            tab1, tab2, tab3 = st.tabs(["🏠 سكني", "🚜 زراعي", "🏭 صناعي"])
            
            with tab1:  # سكني
                with st.form("residential"):
                    col1, col2 = st.columns(2)
                    with col1:
                        loads = st.multiselect("الأجهزة", 
                                             ["تكييف (1.5HP)", "ثلاجة", "إضاءة", "تلفزيون", "غسالة"],
                                             ["تكييف (1.5HP)", "ثلاجة"])
                        people = st.slider("عدد الأفراد", 1, 10, 4)
                    
                    with col2:
                        hours = st.slider("ساعات الاستخدام", 1, 24, 8)
                        backup = st.slider("احتياطي (أيام)", 1, 5, 2)
                    
                    if st.form_submit_button("🧮 احسب النظام السكني"):
                        total_power = len(loads) * 1200 + people * 100
                        daily_kwh = total_power * hours / 1000
                        
                        panels = np.ceil(daily_kwh / 6)  # 6 كيلو وات ساعة لكل لوح
                        inverter = np.ceil(total_power * 1.3 / 1000) * 1000
                        batteries = np.ceil((daily_kwh * backup) / 48 * 1.2)
                        
                        cost = panels * 5000 + inverter * 3 + batteries * 8000 + 30000
                        
                        st.subheader("📊 النتيجة السكنية")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("☀️ الألواح", f"{panels} لوح")
                        c2.metric("🔌 الإنفرتر", f"{inverter} وات")
                        c3.metric("🔋 البطاريات", f"{batteries} بطارية")
                        c4.metric("💰 التكلفة", f"{cost:,.0f} جنيه")
                        
                        # حفظ الطلب
                        if st.button("🚀 اطلب عرض أسعار", use_container_width=True):
                            db.collection("quotes").add({
                                "customer_id": st.session_state.user_id,
                                "type": "سكني",
                                "power": total_power,
                                "cost": cost,
                                "status": "جديد",
                                "timestamp": firestore.SERVER_TIMESTAMP
                            })
                            st.success("✅ تم إرسال طلبك لشركات التركيب!")
            
            with tab2:  # زراعي
                st.subheader("🚜 حاسبة الري الزراعي")
                pumps = st.number_input("عدد المضخات", 1, 10, 2)
                pump_power = st.selectbox("قدرة المضخة", [2, 3, 5, 7.5, 10])  # حصان
                daily_hours = st.slider("ساعات التشغيل", 2, 12, 6)
                
                if st.button("🧮 احسب النظام الزراعي", use_container_width=True):
                    total_hp = pumps * pump_power
                    total_kw = total_hp * 0.746 * 1.25  # معامل الأمان
                    daily_kwh = total_kw * daily_hours
                    
                    panels = np.ceil(daily_kwh / 6)
                    inverter = np.ceil(total_kw * 1000)
                    
                    st.metric("☀️ الألواح المطلوبة", f"{panels} لوح")
                    st.metric("💰 التكلفة التقريبية", f"{panels * 5000 + 50000:,.0f} جنيه")
            
            with tab3:  # صناعي
                st.info("🏭 قيد التطوير...")
        
        elif st.session_state.current_page == "🏢 شركات التركيب":
            st.title("🏢 شركات التركيب المعتمدة")
            companies = []
            if db:
                for doc in db.collection("users").where("role", "==", "شركة تركيب").stream():
                    companies.append(doc.to_dict())
            
            for company in companies:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"### {company['username']}")
                        st.caption(f"⭐ تقييم: 4.8 | 📍 {company.get('location', '')}")
                    
                    with col2:
                        if st.button("💬 عرض أسعار", key=f"comp_{company['username']}"):
                            st.success(f"✅ تم طلب عرض من {company['username']}")
                    
                    with col3:
                        st.button("⭐ تقييم", key=f"rate_{company['username']}")
        
        elif st.session_state.current_page == "💳 خطط المتابعة":
            st.title("💳 خطط المتابعة والصيانة")
            
            plans = {
                "مجاني": {"price": 0, "features": ["تنبيهات أساسية", "تقارير شهرية"], "color": "#ccc"},
                "برونزي": {"price": 299, "features": ["كل المجاني", "زيارة صيانة سنوية", "دعم أولوية"], "color": "#cd7f32"},
                "فضي": {"price": 599, "features": ["كل البرونزي", "2 زيارة سنوياً", "دعم 24/7"], "color": "#c0c0c0"},
                "ذهبي": {"price": 999, "features": ["كل الفضي", "زيارات غير محدودة", "ضمان شامل"], "color": "#ffd700"}
            }
            
            col1, col2, col3, col4 = st.columns(4)
            
            for i, (plan, data) in enumerate(plans.items()):
                with locals()[f"col{i+1}"]:
                    st.markdown(f"""
                    <div style='border: 3px solid {data['color']}; border-radius: 15px; padding: 1.5rem; text-align: center;'>
                        <h3>{plan}</h3>
                        <h2 style='color: {data['color']}'>{data['price']}<sup>جنيه/شهر</sup></h2>
                    """, unsafe_allow_html=True)
                    
                    for feature in data['features']:
                        st.write(f"✅ {feature}")
                    
                    if st.button(f"اشترك في {plan}", key=f"sub_{plan}", use_container_width=True):
                        st.session_state.subscription_plan = plan
                        if db:
                            db.collection("users").document(st.session_state.user_id).update({
                                "subscription": plan,
                                "subscription_date": firestore.SERVER_TIMESTAMP
                            })
                        st.success(f"✅ تم الاشتراك في خطة {plan}!")
            
            st.info("💡 خطط المتابعة تتيح لك متابعة نظامك 24/7 مع صيانة دورية")

    # =========================================
    # صفحات شركات التركيب
    # =========================================
    elif st.session_state.user_role == "شركة تركيب":
        
        if st.session_state.current_page == "📋 طلبات العملاء":
            st.title("📋 طلبات العملاء الواردة")
            
            quotes = []
            if db:
                for doc in db.collection("quotes").where("status", "==", "جديد").stream():
                    data = doc.to_dict()
                    quotes.append({"id": doc.id, **data})
            
            for quote in quotes:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"**طلب #{quote['id'][:8]}**")
                        st.write(f"العميل: {quote.get('customer_id', 'غير معروف')}")
                        st.write(f"الطاقة: {quote.get('power', 0)} وات")
                    
                    with col2:
                        if st.button("💰 عرض سعر", key=f"quote_{quote['id']}"):
                            price = st.number_input("سعر العرض", value=0, key=f"price_{quote['id']}")
                            if st.button("إرسال العرض", key=f"send_{quote['id']}"):
                                db.collection("quotes").document(quote['id']).update({
                                    "company_offer": price,
                                    "status": "عرض سعر مرسل"
                                })
                    
                    with col3:
                        if st.button("✅ قبول", key=f"accept_{quote['id']}"):
                            db.collection("quotes").document(quote['id']).update({
                                "status": "مقبول",
                                "completed_by": st.session_state.username
                            })
        
        elif st.session_state.current_page == "💰 عمولتي":
            st.title("💰 عمولتي وعوائدي")
            st.metric("💵 العمولة المستحقة", "25,500 جنيه")
            st.metric("📊 المشاريع المكتملة", "17 مشروع")
            st.metric("⭐ تقييم العملاء", "4.8/5")
    
    # =========================================
    # لوحة تحكم الأدمن
    # =========================================
    elif st.session_state.user_role == "Admin":
        if st.session_state.current_page == "🏠 لوحة التحكم":
            st.title("🏠 لوحة تحكم VPC Solar")
            
            # إحصائيات رئيسية
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("👥 إجمالي المستخدمين", "1,247")
            col2.metric("🏢 شركات التركيب", "23")
            col3.metric("📋 طلبات جديدة", "17")
            col4.metric("💰 إجمالي العمولات", "458,200 جنيه")
            
            # رسم بياني
            fig = go.Figure()
            fig.add_trace(go.Bar(x=['يناير', 'فبراير', 'مارس'], y=[120, 180, 250]))
            st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("*VPC Solar Pro © 2025 | تطوير المهندس محمد سعد الدين*")
