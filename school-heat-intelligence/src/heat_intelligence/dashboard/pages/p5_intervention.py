"""Intervention Simulator page — interactive scenario modelling."""
import streamlit as st
import plotly.graph_objects as go
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.intervention.simulator import simulate_intervention

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Intervention Simulator")
    from heat_intelligence.dashboard.components import render_methodology_warning
    render_methodology_warning()

    zone_names = list(set(r.zone_name for r in data))
    zone_filter = st.selectbox("Select zone", zone_names)
    zone_data = sorted([r for r in data if r.zone_name == zone_filter], key=lambda r: r.timestamp, reverse=True)
    reading = zone_data[0]
    current_risk = compute_risk_score(reading, config)
    st.metric("Current Risk Score", f"{current_risk.score:.1f} ({current_risk.label})")

    st.subheader("Scenario Configuration")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_canopy = st.slider("Canopy %", 0, 100, int(reading.canopy_pct))
    with col2:
        new_shade = st.slider("Shade %", 0, 100, int(reading.shade_pct))
    with col3:
        new_surface = st.selectbox("Surface Type", ["asphalt", "concrete", "grass", "permeable"],
                                   index=["asphalt", "concrete", "grass", "permeable"].index(reading.surface_type))

    scenario = {"canopy_pct": new_canopy, "shade_pct": new_shade, "surface_type": new_surface}
    result = simulate_intervention(reading, current_risk, scenario, config)

    st.subheader("Simulation Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Baseline Risk", f"{result.baseline_risk:.1f}")
    with col2:
        st.metric("Simulated Risk", f"{result.simulated_risk:.1f}")
    with col3:
        st.metric("Relative Change", f"{result.relative_change_pct:+.1f}%")

    fig = go.Figure(data=[
        go.Bar(name="Baseline", x=["Risk Score"], y=[result.baseline_risk], marker_color="red"),
        go.Bar(name="Simulated", x=["Risk Score"], y=[result.simulated_risk], marker_color="green"),
    ])
    fig.update_layout(barmode="group", title="Baseline vs Simulated Risk")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Assumptions")
    for assumption in result.assumptions:
        st.write(f"• {assumption}")

    st.warning("**Mô phỏng mô hình — chưa được kiểm chứng thực địa.**\n\n"
               "This is a heuristic scenario model. Results show relative risk change, "
               "not absolute temperature change. Not validated with field measurements.")