import streamlit as st

st.set_page_config(
    page_title="VPC Solar",
    page_icon="☀️",
    layout="wide"
)

# ===== HEADER =====

st.title("☀️ VPC Solar")
st.subheader("Smart Solar Solutions")

st.markdown("---")

# ===== MAIN BUTTONS =====

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🏠 Residential Systems")
    st.button("Open Residential")

with col2:
    st.markdown("### 🚜 Agricultural Systems")
    st.button("Open Agricultural")

st.markdown("---")

# ===== SOLAR CALCULATOR =====

st.header("⚡ Solar Calculator")

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

# ===== ESTIMATION =====

panels = energy / 500

st.info(f"Estimated Solar Panels Needed: {round(panels,1)}")

# ===== FOOTER =====

st.markdown("---")
st.caption("VPC Solar © 2026")
