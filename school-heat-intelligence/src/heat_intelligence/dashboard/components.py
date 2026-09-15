"""Reusable Streamlit UI components."""
import streamlit as st
from heat_intelligence.models.schemas import ProvenanceFlag

def render_provenance_badge(provenance: ProvenanceFlag):
    colors = {ProvenanceFlag.MEASURED: "🟢", ProvenanceFlag.IMPORTED: "🔵",
              ProvenanceFlag.SYNTHETIC: "🟡", ProvenanceFlag.PREDICTED: "🟠",
              ProvenanceFlag.SIMULATED: "🔴"}
    st.caption(f"{colors.get(provenance, '⚪')} Data provenance: **{provenance.value}**")

def render_risk_gauge(score: float, label: str):
    color = {"Low": "green", "Moderate": "orange", "High": "red", "Extreme": "darkred"}
    st.metric(label=f"Risk: {label}", value=f"{score:.1f}/100")

def render_methodology_warning():
    st.warning(
        "**Mô phỏng mô hình — chưa được kiểm chứng thực địa.**\n\n"
        "Model simulation — not validated with field measurements. "
        "All weights are illustrative heuristic parameters, not empirically calibrated."
    )