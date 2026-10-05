"""Exposure page — student exposure scores and ranking."""
import streamlit as st
import plotly.express as px
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag
from heat_intelligence.dashboard.components import render_provenance_badge

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Student Exposure Analysis")
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()

    exposure_data = []
    for _, row in latest.iterrows():
        reading = ZoneReading(**row.to_dict())
        risk = compute_risk_score(reading, config)
        exp = compute_exposure(risk, reading, config)
        exposure_data.append({"zone_name": reading.zone_name, "risk_score": risk.score,
                              "student_count": reading.student_count,
                              "exposure_hours": reading.exposure_hours,
                              "exposure_score": exp.score})
    exp_df = pd.DataFrame(exposure_data).sort_values("exposure_score", ascending=False)

    st.subheader("Exposure Risk Ranking")
    fig = px.bar(exp_df, x="zone_name", y="exposure_score", color="exposure_score",
                 color_continuous_scale="YlOrRd", labels={"exposure_score": "Exposure Score (0-100)"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Exposure Details")
    st.dataframe(exp_df, use_container_width=True)

    st.subheader("Key Insight")
    top = exp_df.iloc[0]
    st.info(f"**{top['zone_name']}** has the highest exposure risk (score: {top['exposure_score']:.1f}) "
            f"due to **{top['student_count']} students** × **{top['exposure_hours']:.1f} hours** "
            f"at risk level {top['risk_score']:.0f}.")
    render_provenance_badge(ProvenanceFlag.SYNTHETIC)