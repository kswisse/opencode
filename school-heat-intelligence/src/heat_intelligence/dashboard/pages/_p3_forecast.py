"""Forecast page — 6-hour risk prediction with uncertainty."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.forecast.predictor import forecast_risk
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.models.schemas import ProvenanceFlag
from heat_intelligence.dashboard.components import render_provenance_badge, render_methodology_warning

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Risk Forecast")
    zone_names = list(set(r.zone_name for r in data))
    zone_filter = st.selectbox("Select zone", zone_names)
    zone_id = next(r.zone_id for r in data if r.zone_name == zone_filter)
    forecasts = forecast_risk(data, config, zone_id)

    if not forecasts:
        st.warning("Insufficient data for forecast. Need at least 24 hours of historical data.")
        return

    st.info("Forecast uses moving average + diurnal baseline (explainable, no ML).")
    fig = go.Figure()
    zone_data = sorted([r for r in data if r.zone_id == zone_id], key=lambda r: r.timestamp)
    recent = zone_data[-48:]
    hist_times = [r.timestamp for r in recent]
    hist_scores = [compute_risk_score(r, config).score for r in recent]
    fig.add_trace(go.Scatter(x=hist_times, y=hist_scores, mode="lines", name="Historical", line=dict(color="blue")))
    fc_times = [f.timestamp for f in forecasts]
    fc_scores = [f.predicted_score for f in forecasts]
    fc_lower = [f.lower_bound for f in forecasts]
    fc_upper = [f.upper_bound for f in forecasts]
    fig.add_trace(go.Scatter(x=fc_times, y=fc_scores, mode="lines+markers", name="Forecast", line=dict(color="red", dash="dash")))
    fig.add_trace(go.Scatter(x=fc_times, y=fc_upper, mode="lines", name="Upper Bound", line=dict(color="gray", width=0.5)))
    fig.add_trace(go.Scatter(x=fc_times, y=fc_lower, mode="lines", name="Lower Bound",
                             line=dict(color="gray", width=0.5), fill="tonexty", fillcolor="rgba(128,128,128,0.2)"))
    fig.update_layout(title=f"6-Hour Forecast — {zone_filter}", xaxis_title="Time", yaxis_title="Risk Score")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Forecast Details")
    fc_df = pd.DataFrame([{"Horizon": f"{f.horizon_hours}h", "Predicted": f"{f.predicted_score:.1f}",
                           "Lower": f"{f.lower_bound:.1f}", "Upper": f"{f.upper_bound:.1f}",
                           "Provenance": f.provenance.value} for f in forecasts])
    st.dataframe(fc_df, use_container_width=True)
    render_provenance_badge(ProvenanceFlag.PREDICTED)
    render_methodology_warning()