"""School Heat Intelligence — Main Dashboard Application."""
import streamlit as st

st.set_page_config(page_title="School Heat Intelligence", page_icon="🌡️", layout="wide")
st.title("🌡️ School Heat Intelligence")
st.caption("Campus heat risk detection, forecasting, and intervention simulation")
st.info("**Data Provenance:** 🟡 Synthetic demo data | 🟠 Model predictions | 🔴 Simulations\n\nAll weights are illustrative heuristic parameters, NOT empirically calibrated.")

from heat_intelligence.data import load_data
from heat_intelligence.config import load_config

config = load_config()
data = load_data("data/demo_campus.csv")

page = st.sidebar.radio("Navigate to:", [
    "1 Overview", "2 Risk Analysis", "3 Forecast", "4 Exposure",
    "5 Intervention Simulator", "6 Priority Actions", "7 Methodology"
])

if page == "1 Overview":
    from heat_intelligence.dashboard.pages import p1_overview
    p1_overview.render(data, config)
elif page == "2 Risk Analysis":
    from heat_intelligence.dashboard.pages import p2_risk_analysis
    p2_risk_analysis.render(data, config)
elif page == "3 Forecast":
    from heat_intelligence.dashboard.pages import p3_forecast
    p3_forecast.render(data, config)
elif page == "4 Exposure":
    from heat_intelligence.dashboard.pages import p4_exposure
    p4_exposure.render(data, config)
elif page == "5 Intervention Simulator":
    from heat_intelligence.dashboard.pages import p5_intervention
    p5_intervention.render(data, config)
elif page == "6 Priority Actions":
    from heat_intelligence.dashboard.pages import p6_priority
    p6_priority.render(data, config)
elif page == "7 Methodology":
    from heat_intelligence.dashboard.pages import p7_methodology
    p7_methodology.render(data, config)