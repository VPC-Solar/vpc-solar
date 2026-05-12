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
from io import BytesIO

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

def validate_phone(phone):
    return len(phone) == 11 and phone.startswith('01')

def validate_pdf(file):
    """التحقق من ملف PDF"""
    if file.type != "application/pdf":
        return False, "يجب أن يكون الملف PDF فقط"
    if file.size > 5 * 1024 * 1024:  # 5MB max
        return False, "حجم الملف كبير جداً (الحد الأقصى 5 ميجا)"
    return True, "صالح"

def upload_pdf_to_firestore(file, doc_ref):
    """رفع PDF إلى Firestore Storage"""
    try:
        bucket = db.bucket()
        blob = bucket.blob(f"company_docs/{doc_ref.id}/{file.name}")
        blob.upload_from_string(file.getvalue(), content_type='application/pdf')
        blob.make_public()
        return blob.public_url
    except:
        return None

# =========================================
# SESSION STATE
# =========================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "current_page" not in st.session_state: st.session_state.current_page = "🏠 الرئيسية"

# =========================================
# 🔐 نظام التسجيل المحسن مع وثائق الشركات
# =========================================
if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .hero {background: linear-gradient(135deg, #00BFFF 0%, #1E90FF 100%); 
           padding: 4rem; border-radius: 25px; text-align: center; color: white; margin: 2rem 0;}
    .hero h1 {font-size: 3.5rem;}
    .doc-section {border: 2px dashed #00BFFF; padding: 2rem; border-radius: 15px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero">
        <h1>☀️ VPC Solar Pro</h1>
        <p>منصة الشركات المعتمدة للطاقة الشمسية</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab_login, tab_register = st.tabs(["🔐 تسجيل الدخول", "📝 إنشاء حساب"])
    
    # تسجيل الدخول
    with tab_login:
        col1, col2 = st.columns([1, 2])
        with col2:
            username = st.text_input("👤 الاسم")
            phone = st.text_input("📱 التليفون", placeholder="01xxxxxxxxx")
            password = st.text_input("🔒 كلمة السر", type="password")
            
            if st.button("🚀 دخول النظام", type="primary", use_container_width=True):
                if username == "admin" and hash_password(password) == hash_password("vpc2025"):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = "Admin"
                    st.rerun()
                elif db and validate_phone(phone):
                    users = db.collection("users").where("username", "==", username).stream()
                    for doc in users:
                        data = doc.to_dict()
                        if (data.get("phone") == phone and 
                            data.get("password_hash") == hash_password(password) and
                            data.get("is_verified", False)):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.user_role = data["role"]
                            st.session_state.user_data = data
                            st.session_state.user_id = doc.id
                            st.session_state.user_phone = phone
                            st.rerun()
                            break
                    st.error("❌ بيانات خاطئة أو الحساب غير مُفعّل")
    
    # إنشاء حساب جديد مع وثائق
    with tab_register:
        st.markdown("### إنشاء حساب جديد")
        account_type = st.radio("نوع الحساب:", ["عميل", "شركة تركيب"], key="reg_type")
        
        if account_type == "عميل":
            # تسجيل عميل عادي (بسيط)
            with st.form("client_form"):
                c_username = st.text_input("👤 الاسم")
                c_phone = st.text_input("📱 التليفون")
                c_email = st.text_input("📧 الإيميل")
                c_password = st.text_input("🔒 كلمة السر", type="password")
                
                c_submit = st.form_submit_button("إنشاء حساب عميل", use_container_width=True)
                if c_submit and db and validate_phone(c_phone):
                    try:
                        db.collection("users").add({
                            "username": c_username, "phone": c_phone, "email": c_email,
                            "password_hash": hash_password(c_password), "role": "عميل",
                            "is_active": True, "is_verified": True,
                            "created_at": firestore.SERVER_TIMESTAMP
                        })
                        st.success("✅ حساب العميل تم إنشاؤه!")
                    except:
                        st.error("❌ خطأ في الإنشاء")
        
        else:  # شركة تركيب
            st.markdown("""
            <div class="doc-section">
                <h3>📋 مطلوب وثائق الشركة للتوثيق</h3>
                <p>يجب رفع جميع الوثائق لتفعيل الحساب</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.form("company_form"):
                # بيانات أساسية
                col1, col2 = st.columns(2)
                with col1:
                    co_username = st.text_input("🏢 اسم الشركة")
                    co_phone = st.text_input("📱 تليفون الشركة", placeholder="01xxxxxxxxx")
                    co_email = st.text_input("📧 الإيميل الإلكتروني")
                    co_password = st.text_input("🔒 كلمة السر", type="password")
                    co_location = st.selectbox("📍 المقر الرئيسي", ["6 أكتوبر", "القاهرة", "الجيزة", "الإسكندرية"])
                
                with col2:
                    co_manager = st.text_input("👤 اسم المدير")
                    co_tax_card = st.file_uploader("🆔 البطاقة الضريبية (PDF)", type="pdf")
                    co_commercial_reg = st.file_uploader("🏛️ السجل التجاري (PDF)", type="pdf")
                    co_chamber_card = st.file_uploader("🏢 بطاقة الغرفة التجارية (PDF)", type="pdf")
                    co_contracts_license = st.file_uploader("📋 رخصة المقاولات (PDF)", type="pdf")
                
                # نبذة الشركة
                co_bio = st.text_area("📄 نبذة عن الشركة وخبراتها", height=100)
                
                co_submit = st.form_submit_button("📤 تقديم طلب التسجيل", use_container_width=True)
                
                if co_submit and db:
                    # التحقق من الوثائق
                    required_docs = [co_tax_card, co_commercial_reg, co_chamber_card]
                    if not all(required_docs):
                        st.error("❌ مطلوب رفع جميع الوثائق الأساسية (*)")
                        st.info("🆔 البطاقة الضريبية، 🏛️ السجل التجاري، 🏢 بطاقة الغرفة (* مطلوب)")
                    elif not validate_phone(co_phone):
                        st.error("❌ رقم التليفون غير صحيح")
                    else:
                        try:
                            # حفظ البيانات مع حالة "قيد المراجعة"
                            doc_ref = db.collection("pending_companies").add({
                                "company_name": co_username,
                                "phone": co_phone,
                                "email": co_email,
                                "password_hash": hash_password(co_password),
                                "manager": co_manager,
                                "location": co_location,
                                "bio": co_bio,
                                "role": "شركة تركيب",
                                "status": "قيد المراجعة",
                                "submitted_at": firestore.SERVER_TIMESTAMP,
                                "is_active": False
                            })
                            
                            # رفع الوثائق
                            docs = {}
                            for doc_file in [co_tax_card, co_commercial_reg, co_chamber_card, co_contracts_license]:
                                if doc_file:
                                    is_valid, msg = validate_pdf(doc_file)
                                    if is_valid:
                                        url = upload_pdf_to_firestore(doc_file, doc_ref[0])
                                        if 'tax' in doc_file.name.lower(): docs['tax_card'] = url
                                        elif 'commercial' in doc_file.name.lower() or 'سجل' in doc_file.name.lower(): docs['commercial_reg'] = url
                                        elif 'chamber' in doc_file.name.lower() or 'غرفة' in doc_file.name.lower(): docs['chamber_card'] = url
                                        else: docs['contracts_license'] = url
                            
                            db.collection("pending_companies").document(doc_ref[0].id).update({"documents": docs})
                            
                            st.success("""
                            ✅ تم تقديم طلب التسجيل بنجاح!
                            
                            📋 حالتك: **قيد المراجعة**
                            ⏳ سيتم مراجعة الوثائق خلال 48 ساعة
                            📧 سيتصل بك فريق VPC Solar لتأكيد الحساب
                            """)
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ خطأ: {e}")
    
    st.stop()

# =========================================
# MAIN APPLICATION
# =========================================
st.markdown("""
<style>
.main {direction: rtl;}
.stButton>button {background: linear-gradient(45deg,#00BFFF,#1E90FF);color:white;
                  border-radius:12px;border:none;font-weight:bold;box-shadow:0 4px 15px rgba(0,191,255,.3);}
.container {border:2px solid #00BFFF;border-radius:15px;padding:1.5rem;margin:1rem 0;}
.verified {color:#4CAF50;font-weight:bold;}
.pending {color:#FF9800;}
.rejected {color:#f44336;}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ☀️ VPC Solar Pro")
    if st.session_state.logged_in:
        st.markdown(f"""
        👤 **{st.session_state.username}**  
        📱 `{st.session_state.user_phone}`  
        🎭 **{st.session_state.user_role}**
        """)
        
        pages = {
            "Admin": ["🏠 لوحة التحكم", "👥 العملاء", "🏢 الشركات", "📋 طلبات الشركات", "📋 طلبات المعاينة"],
            "شركة تركيب": ["🏠 الرئيسية", "📋 طلبات المعاينة", "⚙️ حالة حسابي"],
            "عميل": ["🏠 الرئيسية", "⚡ الحاسبات", "🏢 الشركات المعتمدة"]
        }
        
        role_pages = pages.get(st.session_state.user_role, pages["عميل"])
        st.session_state.current_page = st.selectbox("القائمة", role_pages)
        st.button("🚪 خروج")

# =========================================
# لوحة تحكم الأدمن (مراجعة الشركات)
# =========================================
if st.session_state.user_role == "Admin" and "طلبات الشركات" in st.session_state.current_page:
    st.title("🏢 طلبات تسجيل الشركات")
    
    if db:
        pending = db.collection("pending_companies").where("status", "==", "قيد المراجعة").stream()
        approved = db.collection("users").where("role", "==", "شركة تركيب").where("is_verified", "==", True).stream()
        
        tab_pending, tab_approved = st.tabs(["📋 قيد المراجعة", "✅ المعتمدة"])
        
        with tab_pending:
            for doc in pending:
                company = doc.to_dict()
                with st.container(border=True, class_name="container"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.markdown(f"### **{company['company_name']}**")
                        st.caption(f"📱 {company['phone']} | 📍 {company['location']}")
                        st.write(company['bio'][:200] + "...")
                    
                    with col2:
                        st.caption(f"📄 {len(company.get('documents', {}))} وثيقة")
                    
                    with col3:
                        col_a, col_r = st.columns(2)
                        with col_a:
                            if st.button("✅ اعتماد", key=f"approve_{doc.id}"):
                                # نقل لجدول المستخدمين
                                user_data = {
                                    **company, "is_active": True, "is_verified": True,
                                    "verified_at": firestore.SERVER_TIMESTAMP
                                }
                                del user_data['status']
                                db.collection("users").add(user_data)
                                db.collection("pending_companies").document(doc.id).update({"status": "معتمد"})
                                st.success("✅ تم اعتماد الشركة!")
                        
                        with col_r:
                            if st.button("❌ رفض", key=f"reject_{doc.id}"):
                                db.collection("pending_companies").document(doc.id).update({"status": "مرفوض"})
                                st.error("❌ تم رفض الطلب")
        
        with tab_approved:
            st.subheader("الشركات المعتمدة")
            for doc in approved:
                data = doc.to_dict()
                st.markdown(f"✅ **{data['company_name']}** - {data['phone']}")

# باقي الصفحات (مختصرة)
elif st.session_state.current_page == "🏠 الرئيسية":
    st.title("🏠 VPC Solar Pro")
    st.success("التطبيق يعمل بنجاح!")

st.markdown("---")
st.caption("VPC Solar Pro © 2025 | نظام الشركات المعتمد")
