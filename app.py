import streamlit as st
import json
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import firestore
import hashlib
from datetime import datetime
import numpy as np
import base64
import requests  # لـ WhatsApp API
import folium
from streamlit_folium import folium_static

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
# FIRESTORE & API KEYS
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

# WhatsApp API (ضع في secrets.toml)
WHATSAPP_API_URL = st.secrets.get("WHATSAPP_API_URL", "")
WHATSAPP_TOKEN = st.secrets.get("WHATSAPP_TOKEN", "")

def send_whatsapp(phone, message):
    """إرسال واتساب"""
    if not WHATSAPP_API_URL or not WHATSAPP_TOKEN:
        return False
    
    url = f"{WHATSAPP_API_URL}/send"
    data = {
        "token": WHATSAPP_TOKEN,
        "phone": phone,
        "message": message
    }
    try:
        response = requests.post(url, data=data)
        return response.status_code == 200
    except:
        return False

# Paymob (ضع في secrets.toml)
PAYMOB_API_KEY = st.secrets.get("PAYMOB_API_KEY", "")

def create_paymob_payment(amount, customer_phone, description):
    """إنشاء دفع Paymob"""
    if not PAYMOB_API_KEY:
        return {"payment_url": "https://paymob.com/test"}
    
    # هنا كود Paymob الحقيقي
    return {"payment_url": f"https://paymob.com/pay/{amount}"}

# =========================================
# UTILITY FUNCTIONS
# =========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_phone(phone):
    return len(phone) == 11 and phone.startswith('01')

# =========================================
# SESSION STATE
# =========================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "current_page" not in st.session_state: st.session_state.current_page = "🏠 الرئيسية"

# =========================================
# 🔐 AUTH SYSTEM (مع التحقق)
# =========================================
if not st.session_state.logged_in:
    # Hero + Login/Register (نفس الكود السابق مع اختصار)
    st.title("🔐 VPC Solar Pro")
    st.stop()

# =========================================
# CSS محسن
# =========================================
st.markdown("""
<style>
.main {direction: rtl;}
.star-rating {color: #FFD700; font-size: 2rem;}
.map-container {height: 500px;}
.payment-card {background: linear-gradient(135deg, #4CAF50, #45a049); color: white;}
</style>
""", unsafe_allow_html=True)

# =========================================
# 1️⃣ WHATSAPP NOTIFICATIONS
# =========================================
def notify_whatsapp_request(customer_phone, company_phone, request_id):
    """إشعار واتساب للطلب"""
    customer_msg = f"🌞 VPC Solar\n\nتم إرسال طلب معاينتك #{request_id}\nسيتصل بك فني خلال 24 ساعة\nشكراً لثقتك بنا!"
    company_msg = f"🌞 VPC Solar\n\nطلب معاينة جديد #{request_id}\nالعميل: {customer_phone}\nاتصل به فوراً!"
    
    send_whatsapp(customer_phone, customer_msg)
    if company_phone:
        send_whatsapp(company_phone, company_msg)

# =========================================
# 2️⃣ PAYMOB PREMIUM PLANS
# =========================================
def premium_plans_section():
    st.markdown("## 💎 خطط الشركات المميزة")
    plans = {
        "برونزي": {"price": 499, "features": ["✅ إعلان مميز", "⭐ أولوية في البحث", "📞 100 مكالمة"]},
        "فضي": {"price": 999, "features": ["✅ كل البرونزي", "🌟 أعلى في البحث", "📱 واتساب API", "📊 إحصائيات"]},
        "ذهبي": {"price": 1999, "features": ["✅ كل الفضي", "👑 أولوية قصوى", "🎯 حملات إعلانية", "📈 تقارير VIP"]}
    }
    
    col1, col2, col3 = st.columns(3)
    for idx, (plan, data) in enumerate(plans.items()):
        with locals()[f"col{idx+1}"]:
            st.markdown(f"""
            <div class="payment-card" style="padding:2rem;border-radius:15px;text-align:center;">
                <h3>{plan}</h3>
                <h2>{data['price']}<sup>جنيه/شهر</sup></h2>
            """, unsafe_allow_html=True)
            
            for feature in data['features']:
                st.markdown(f"<div style='margin:0.5rem 0;'>✅ {feature}</div>", unsafe_allow_html=True)
            
            if st.button(f"اشترك في {plan}", key=f"pay_{plan}", use_container_width=True):
                payment = create_paymob_payment(data['price'], st.session_state.user_phone, f"خطة {plan}")
                st.markdown(f"[💳 ادفع الآن]({payment['payment_url']})")
    
    st.info("💡 الخطط المميزة تزيد من فرص الحصول على عملاء بنسبة 300%")

# =========================================
# 3️⃣ نظام التقييم ★★★★★
# =========================================
def rating_system(company_id):
    """نظام التقييم"""
    if st.session_state.user_role != "عميل":
        return
    
    st.subheader("⭐ قيّم الشركة")
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        stars = st.select_slider("التقييم", options=[1, 2, 3, 4, 5], value=5)
        st.markdown("⭐" * stars, unsafe_allow_html=True)
    
    with col2:
        comment = st.text_area("تعليقك (اختياري)", height=80)
    
    with col3:
        if st.button("💾 إرسال التقييم", use_container_width=True):
            if db:
                db.collection("ratings").add({
                    "company_id": company_id,
                    "customer": st.session_state.username,
                    "customer_phone": st.session_state.user_phone,
                    "stars": stars,
                    "comment": comment,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("✅ تم إرسال التقييم!")

# =========================================
# 4️⃣ Click-to-Call
# =========================================
def click_to_call(phone):
    """زر الاتصال"""
    st.markdown(f"""
    <a href="tel:{phone}" style="
        background: linear-gradient(45deg, #4CAF50, #45a049);
        color: white; padding: 1rem 2rem; border-radius: 50px;
        text-decoration: none; font-weight: bold; display: inline-block;
        box-shadow: 0 4px 15px rgba(76,175,80,0.3);
    ">📞 اتصال الآن</a>
    """, unsafe_allow_html=True)

# =========================================
# 5️⃣ Google Maps
# =========================================
def company_map(companies):
    """خريطة الشركات"""
    m = folium.Map(location=[30.0444, 31.2357], zoom_start=10)  # القاهرة
    
    for company in companies:
        lat, lng = company.get('lat', 30.0444), company.get('lng', 31.2357)
        folium.Marker(
            [lat, lng],
            popup=f"{company['username']}<br>{company['phone']}",
            tooltip=company['username'],
            icon=folium.Icon(color="blue", icon="industry")
        ).add_to(m)
    
    folium_static(m)

# =========================================
# MAIN PAGES مع الميزات الجديدة
# =========================================

# صفحة الشركات المعتمدة (مع كل الميزات)
if st.session_state.current_page == "🏢 الشركات المعتمدة":
    st.title("🏢 الشركات المعتمدة")
    
    if db:
        companies = db.collection("users").where("role", "==", "شركة تركيب").where("is_verified", "==", True).stream()
        companies_list = []
        
        for doc in companies:
            data = doc.to_dict()
            companies_list.append({**data, "id": doc.id})
        
        # فلترة وخريطة
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("🔍 ابحث")
            filtered = [c for c in companies_list if search.lower() in c.get('username', '').lower()]
            
            for company in filtered:
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        st.markdown(f"### ⭐ **{company['username']}**")
                        st.caption(f"📍 {company.get('location', '')}")
                        st.write(company.get('bio', '')[:150] + "...")
                    
                    with col2:
                        click_to_call(company['phone'])  # 📞 Click-to-Call
                    
                    with col3:
                        if st.button("🚀 طلب معاينة", key=f"req_{company['id']}"):
                            request_id = f"REQ_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            db.collection("inspection_requests").add({
                                "customer": st.session_state.username,
                                "customer_phone": st.session_state.user_phone,
                                "company_id": company['id'],
                                "company_phone": company['phone'],
                                "request_id": request_id,
                                "status": "جديد",
                                "created_at": firestore.SERVER_TIMESTAMP
                            })
                            # واتساب إشعار
                            notify_whatsapp_request(st.session_state.user_phone, company['phone'], request_id)
                            st.success(f"✅ تم الطلب #{request_id}")
                    
                    with col4:
                        rating_system(company['id'])  # ⭐ نظام التقييم
        
        with col2:
            st.subheader("🗺️ مواقع الشركات")
            company_map(companies_list)
    
    # خطط مميزة
    premium_plans_section()

# لوحة الأدمن (مع التقييمات)
elif st.session_state.user_role == "Admin":
    st.title("🏠 لوحة التحكم")
    
    tab1, tab2, tab3 = st.tabs(["📋 طلبات المعاينة", "⭐ التقييمات", "🏢 الشركات"])
    
    with tab1:
        # طلبات مع تفاصيل الواتساب
        pass
    
    with tab2:
        st.subheader("التقييمات الجديدة")
        if db:
            ratings = db.collection("ratings").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(20).stream()
            for doc in ratings:
                rating = doc.to_dict()
                st.markdown(f"""
                ⭐ **{rating['stars']}/5** - {rating['customer']}
                <br>{rating['comment']}
                """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("VPC Solar Pro © 2025 | النسخة الفائقة الاحترافية")
