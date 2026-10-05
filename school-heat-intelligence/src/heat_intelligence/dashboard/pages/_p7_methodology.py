"""Methodology page — formulas, assumptions, limitations."""
import streamlit as st
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.forecast.predictor import evaluate_forecast

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Methodology & Limitations")

    st.warning(
        "**Composite Heat Risk Score là chỉ số tổng hợp phục vụ MVP/decision support; "
        "các trọng số mặc định là heuristic và chưa được hiệu chuẩn thực nghiệm.**"
    )

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

### Normalization
All components normalized to [0, 1] via min-max scaling:
- Heat index: [20°C, 50°C] — range chosen for MVP, not empirically derived
- Humidity: [0%, 100%]
- Wind speed: [0, 15 m/s] — inverted (higher wind = lower risk)
- Surface: categorical factor [0, 1] from config

**These ranges are illustrative heuristics, not empirically calibrated bounds.**

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
priority = w_risk × risk_norm + w_exposure × exposure_norm × w_intervention × intervention_norm
```

## Limitations
1. All weights are illustrative heuristics, not empirically calibrated
2. Intervention effects are scenario projections, not measured outcomes
3. Synthetic demo data — not real sensor measurements
4. No causal claims — correlations only
5. Surface factors are categorical, not fixed temperature corrections

## Data Provenance
- 🟡 Synthetic: Generated demo data
- 🟠 Predicted: Model forecasts
- 🔴 Simulated: Intervention scenario results
- 🟢 Measured: Real sensor data (not used in MVP)
- 🔵 Imported: External data sources (not used in MVP)
""")

    # Forecast Holdout Evaluation
    st.subheader("Forecast Holdout Evaluation")
    st.markdown(
        "The forecast baseline is evaluated using a **24-hour holdout test**. "
        "The model forecasts the last 24 hours from historical data, "
        "then compares predictions against actual computed risk scores."
    )

    zone_names = sorted(set(r.zone_name for r in data))
    zone_filter = st.selectbox("Select zone for evaluation", zone_names, key="eval_zone")
    zone_id = next(r.zone_id for r in data if r.zone_name == zone_filter)

    evaluations = evaluate_forecast(data, config, zone_id, holdout_hours=24)

    if evaluations:
        eval_df = pd.DataFrame([{
            "Horizon": f"{e.horizon_hours}h",
            "MAE": e.mae,
            "RMSE": e.rmse,
            "Samples": e.n_samples,
        } for e in evaluations])
        st.dataframe(eval_df, use_container_width=True, hide_index=True)

        st.markdown(
            "**MAE** = Mean Absolute Error (lower is better). "
            "**RMSE** = Root Mean Square Error (lower is better, penalizes large errors). "
            "**Samples** = number of forecast-actual pairs evaluated."
        )
    else:
        st.info("Insufficient data for holdout evaluation. Need >24 hours of history.")

    st.subheader("Current Configuration")
    st.json(config.model_dump())
