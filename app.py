import streamlit as st

st.set_page_config(
    page_title="VPC Solar",
    page_icon="☀️",
    layout="wide"
)

# ===== SIDEBAR =====

with st.sidebar:
    st.title("☀️ VPC Solar")

    page = st.radio(
        "Navigation",
        [
            "Home",
            "Solar Calculator",
            "Installation Companies",
            "Monitoring Plans",
            "Contact"
        ]
    )

# ===== HOME =====

if page == "Home":

    st.title("☀️ VPC Solar")
    st.subheader("Smart Solar Solutions")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("## 🏠 Residential Systems")
        st.button("Open Residential")

    with col2:
        st.markdown("## 🚜 Agricultural Systems")
        st.button("Open Agricultural")

# ===== SOLAR CALCULATOR =====

elif page == "Solar Calculator":

    st.title("⚡ Solar Calculator")

    power = st.number_input(
        "Device Power (W)",
        min_value=0,
        value=100
    )

    hours = st.number_input(
        "Usage Hours Per Day",
        min_value=0,
        value=5
    )

    energy = power * hours

    st.success(f"Daily Consumption = {energy} Wh")

    panels = energy / 500

    st.info(f"Estimated Solar Panels Needed: {round(panels,1)}")

# ===== COMPANIES =====

elif page == "Installation Companies":

    st.title("🏢 Installation Companies")

    st.markdown("### Featured Companies")

    st.card = """
    شركة تركيب طاقة شمسية
    ⭐ 4.8
    القاهرة
    """

    st.write(st.card)

# ===== MONITORING =====

elif page == "Monitoring Plans":

    st.title("📡 Monitoring Plans")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic")
        st.write("Monthly monitoring")
        st.write("Fault alerts")

    with col2:
        st.subheader("Premium")
        st.write("Maintenance visits")
        st.write("24/7 support")

# ===== CONTACT =====

elif page == "Contact":

    st.title("📞 Contact Us")

    name = st.text_input("Your Name")

    message = st.text_area("Message")

    if st.button("Send"):
        st.success("Message Sent Successfully")

# ===== FOOTER =====

st.markdown("---")
st.caption("VPC Solar © 2026")
