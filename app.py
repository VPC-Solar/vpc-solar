import streamlit as st
import json
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import firestore
import firebase_admin
from firebase_admin import auth, credentials
from PIL import Image

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="VPC Solar SaaS", layout="wide")

# =========================
# FIREBASE INIT
# =========================
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project=key_dict["project_id"])

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_profile = None

# =========================
# HELPERS
# =========================
def get_company_id():
    return st.session_state.user_profile["company_id"]

def get_role():
    return st.session_state.user_profile["role"]

# =========================
# LOGIN
# =========================
def login():
    st.title("🔐 VPC Solar Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            user = auth.get_user_by_email(email)

            user_doc = db.collection("users").document(user.uid).get()

            if user_doc.exists:
                st.session_state.logged_in = True
                st.session_state.user_id = user.uid
                st.session_state.user_profile = user_doc.to_dict()
                st.rerun()
            else:
                st.error("User profile not found")

        except Exception:
            st.error("Invalid login")

# =========================
# SOLAR ENGINE (PRO VERSION)
# =========================
def solar_engine(power, hours, backup_hours, voltage):

    daily_energy = power * hours

    system_efficiency = 0.75
    ps_hours = 5.5

    required_energy = daily_energy / system_efficiency

    pv_size_kw = required_energy / (ps_hours * 1000)

    inverter_size = power * 1.3

    battery_capacity = (daily_energy * backup_hours) / (voltage * 0.8)

    return {
        "daily_energy_wh": daily_energy,
        "pv_size_kw": round(pv_size_kw, 2),
        "inverter_w": int(inverter_size),
        "battery_ah": int(battery_capacity)
    }

# =========================
# SAVE TO FIRESTORE
# =========================
def save_calc(data):
    db.collection("solar_calculations").add({
        "company_id": get_company_id(),
        "user_id": st.session_state.user_id,
        **data
    })

# =========================
# MAIN APP
# =========================
def main_app():

    user = st.session_state.user_profile
    company_id = user["company_id"]
    role = user["role"]

    st.sidebar.title("☀️ VPC Solar SaaS")
    st.sidebar.write(f"Role: {role}")

    page = st.sidebar.radio("Menu", [
        "Dashboard",
        "Solar Calculator",
        "Company Data"
    ])

    # ================= DASHBOARD =================
    if page == "Dashboard":
        st.title("📊 Dashboard")

        docs = db.collection("solar_calculations") \
            .where("company_id", "==", company_id).stream()

        data = [d.to_dict() for d in docs]

        st.metric("Total Calculations", len(data))

        if data:
            df = pd.DataFrame(data)
            st.dataframe(df)

    # ================= CALCULATOR =================
    elif page == "Solar Calculator":
        st.title("⚡ Solar Sizing Engine")

        power = st.number_input("Load (W)", 100, 10000, 1000)
        hours = st.number_input("Usage Hours", 1, 24, 5)
        backup = st.slider("Backup Hours", 1, 24, 5)
        voltage = st.selectbox("System Voltage", [12, 24, 48])

        if st.button("Calculate System"):

            result = solar_engine(power, hours, backup, voltage)

            st.success("System Calculated Successfully")

            st.write(result)

            df = pd.DataFrame({
                "Component": ["PV Size (kW)", "Inverter (W)", "Battery (Ah)"],
                "Value": [result["pv_size_kw"], result["inverter_w"], result["battery_ah"]]
            })

            fig = px.bar(df, x="Component", y="Value", title="System Design")
            st.plotly_chart(fig, use_container_width=True)

            save_calc(result)

    # ================= COMPANY DATA =================
    elif page == "Company Data":

        st.title("🏢 Company Management")

        if role != "owner":
            st.error("Access denied")
            return

        users = db.collection("users") \
            .where("company_id", "==", company_id).stream()

        users_data = [u.to_dict() for u in users]

        st.write("Team Members")
        st.dataframe(pd.DataFrame(users_data))

# =========================
# ROUTER
# =========================
if not st.session_state.logged_in:
    login()
else:
    main_app()
