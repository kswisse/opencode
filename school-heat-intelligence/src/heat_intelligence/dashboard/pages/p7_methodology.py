"""Methodology page — formulas, assumptions, limitations."""
import streamlit as st
from heat_intelligence.config import HeatIntelligenceConfig

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Methodology & Limitations")
    st.markdown("""
## Composite Heat Risk Score

The Composite Heat Risk Score is an **illustrative heuristic index** for MVP/decision-support.
Default weights are NOT empirically calibrated.

### Formula
```
risk_score = (w_hi × HI_norm + w_rh × RH_norm + w_ws × WS_norm + w_sf × SF_norm) × 100
```

### Heat Index (Rothfusz 1979)
Standard regression for apparent temperature.

## Student Exposure Score
```
exposure = (w_risk × risk_norm + w_students × students_norm + w_hours × hours_norm)
```
Uses actual `exposure_hours` from input data. No arbitrary time weights.

## Intervention Simulation
**This is a heuristic scenario model, NOT a physical temperature model.**
Outputs: baseline risk, scenario config, simulated risk, relative change (%), assumptions list.

## Priority Score
```
priority = w_risk × risk_norm + w_exposure × exposure_norm + w_intervention × intervention_norm
```

## Limitations
1. All weights are illustrative heuristics, not empirically calibrated
2. Intervention effects are scenario projections, not measured outcomes
3. Synthetic demo data — not real sensor measurements
4. No causal claims — correlations only
5. Surface factors are categorical, not fixed temperature corrections
6. Forecast is a baseline — not validated against held-out data

## Data Provenance
- 🟡 Synthetic: Generated demo data
- 🟠 Predicted: Model forecasts
- 🔴 Simulated: Intervention scenario results
- 🟢 Measured: Real sensor data (not used in MVP)
- 🔵 Imported: External data sources (not used in MVP)
""")
    st.subheader("Current Configuration")
    st.json(config.model_dump())