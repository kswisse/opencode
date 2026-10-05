"""Priority Actions page — ranked intervention recommendations."""
import streamlit as st
import plotly.express as px
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.intervention.simulator import simulate_intervention
from heat_intelligence.priority.engine import compute_priorities
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag
from heat_intelligence.dashboard.components import render_provenance_badge

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Priority Actions")
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()

    risk_scores, exposure_scores, interventions = [], [], []
    for _, row in latest.iterrows():
        reading = ZoneReading(**row.to_dict())
        risk = compute_risk_score(reading, config)
        exp = compute_exposure(risk, reading, config)
        scenario = {"canopy_pct": 60, "shade_pct": 70, "surface_type": "grass"}
        intervention = simulate_intervention(reading, risk, scenario, config)
        risk_scores.append(risk)
        exposure_scores.append(exp)
        interventions.append(intervention)

    priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)

    st.subheader("Intervention Priority Ranking")
    pri_df = pd.DataFrame([{"Rank": p.rank, "Zone": p.zone_name, "Priority Score": p.priority_score,
                            "Risk": p.risk_score, "Exposure": p.exposure_score,
                            "Intervention Potential": p.intervention_potential} for p in priorities])
    fig = px.bar(pri_df, x="Zone", y="Priority Score", color="Priority Score", color_continuous_scale="YlOrRd")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recommended Actions")
    for p in priorities:
        with st.expander(f"#{p.rank} {p.zone_name} — Priority Score: {p.priority_score:.1f}"):
            st.write(p.explanation)
            intervention = next(i for i in interventions if i.zone_id == p.zone_id)
            st.write(f"**Scenario:** {intervention.scenario_config}")
            st.write(f"**Projected change:** {intervention.relative_change_pct:+.1f}%")
    render_provenance_badge(ProvenanceFlag.SIMULATED)