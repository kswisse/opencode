"""Risk Analysis page — zone-by-zone risk breakdown."""
import streamlit as st
import plotly.express as px
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag
from heat_intelligence.dashboard.components import render_provenance_badge

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Risk Analysis")
    risk_data = []
    for r in data:
        rs = compute_risk_score(r, config)
        risk_data.append({"zone_name": r.zone_name, "timestamp": r.timestamp,
                          "score": rs.score, "label": rs.label,
                          "hi_component": rs.components["heat_index"],
                          "rh_component": rs.components["humidity"],
                          "ws_component": rs.components["wind_speed"],
                          "sf_component": rs.components["surface"]})
    risk_df = pd.DataFrame(risk_data)
    risk_df["timestamp"] = pd.to_datetime(risk_df["timestamp"])

    st.subheader("Current Risk by Zone")
    latest_risk = risk_df.sort_values("timestamp").groupby("zone_name").last().reset_index()
    fig = px.bar(latest_risk, x="zone_name", y="score", color="label",
                 color_discrete_map={"Low": "green", "Moderate": "orange",
                                     "High": "red", "Extreme": "darkred"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Risk Component Breakdown")
    zone_filter = st.selectbox("Select zone", latest_risk["zone_name"].unique())
    zone_data = latest_risk[latest_risk["zone_name"] == zone_filter].iloc[0]
    components = {"Heat Index": zone_data["hi_component"], "Humidity": zone_data["rh_component"],
                  "Wind Speed": zone_data["ws_component"], "Surface": zone_data["sf_component"]}
    fig2 = px.bar(x=list(components.keys()), y=list(components.values()),
                  labels={"x": "Component", "y": "Score (0-100)"},
                  title=f"Risk Components — {zone_filter}")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Risk Over Time")
    zone_ts = risk_df[risk_df["zone_name"] == zone_filter]
    fig3 = px.line(zone_ts, x="timestamp", y="score", title=f"Risk Score — {zone_filter}")
    st.plotly_chart(fig3, use_container_width=True)

    render_provenance_badge(ProvenanceFlag.SYNTHETIC)