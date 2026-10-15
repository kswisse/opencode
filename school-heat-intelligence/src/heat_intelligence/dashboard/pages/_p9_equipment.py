"""Equipment page — school machines under heat stress (ported from FactoryGuard).

SHI stays the root: campus heat risk feeds equipment failure probability,
classified by the shared cost-aware policy.
"""
import streamlit as st
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.models.schemas import ZoneReading
from heat_intelligence.equipment.policy import (
    ACTIONS,
    DECISION_DISCLAIMER,
    POLICY_DISCLAIMER,
    RESEARCH_COSTS,
    THRESHOLD_COST_AWARE,
    THRESHOLD_DEFAULT,
    classify,
)
from heat_intelligence.equipment.scoring import equipment_failure_probability


def _avg_heat(data: list, config: HeatIntelligenceConfig) -> float:
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()
    scores = []
    for _, row in latest.iterrows():
        scores.append(compute_risk_score(ZoneReading(**row.to_dict()), config).score)
    return sum(scores) / len(scores) if scores else 0.0


def render(data: list, config: HeatIntelligenceConfig):
    st.header("🔧 Equipment under Heat")
    st.caption(
        "Same sensor stack, second decision: campus heat + load + age → "
        "failure probability → cost-aware maintenance action."
    )
    st.caption(POLICY_DISCLAIMER)

    avg_heat = _avg_heat(data, config)
    st.metric("Campus avg heat risk (input)", f"{avg_heat:.1f}")

    preset = st.radio("Preset", ["LOW", "WATCH", "HIGH"], horizontal=True,
                      help="Demo examples, not measurements.")
    defaults = {"LOW": (0.3, 1.0), "WATCH": (0.6, 4.0), "HIGH": (0.9, 8.0)}[preset]
    load = st.slider("Equipment load (0-1)", 0.0, 1.0, float(defaults[0]))
    age = st.slider("Equipment age (years)", 0.0, 10.0, float(defaults[1]))

    if st.button("Analyze equipment", type="primary"):
        p, contrib = equipment_failure_probability(avg_heat, load, age)
        level = classify(p)
        title, detail = ACTIONS[level]
        st.markdown(f"### {p:.1%} — :{level.color}[{level.card_label}]")
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.write(detail)
            st.caption(DECISION_DISCLAIMER)
        st.markdown("#### Main signals")
        top = sorted(contrib.items(), key=lambda kv: -kv[1])[:3]
        st.markdown("**" + " · ".join(f"{k} {v:.0%}" for k, v in top) + "**")
        st.caption("Heuristic contributions — not causal attribution.")

    with st.expander("Why not use 50%? Cost-aware threshold logic", expanded=False):
        st.metric("Default threshold", f"{THRESHOLD_DEFAULT:.2f}")
        st.metric("Cost-aware threshold (research)", f"{THRESHOLD_COST_AWARE}")
        st.markdown(
            f"Missed failure (FN={RESEARCH_COSTS['FN']}) is assumed far more "
            f"expensive than a false alarm (FP={RESEARCH_COSTS['FP']}), "
            "so the cheaper decision is to flag earlier."
        )
        st.warning("Research assumption — not real school economics.")
