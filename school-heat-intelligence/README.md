# School Heat Intelligence

Data-driven school campus heat risk detection, forecasting, and intervention simulation.

## Quick Start

```bash
pip install -e ".[dev]"
streamlit run src/heat_intelligence/dashboard/app.py
```

## Architecture

```
Pipeline: data → risk → hotspot → forecast → exposure → intervention → priority → dashboard
```

### Modules

| Module | Description |
|--------|-------------|
| `data/` | CSV/JSON ingestion, synthetic data generator |
| `risk/` | Heat index (Rothfusz), composite risk score |
| `hotspot/` | Zone ranking, percentile-based hotspot flagging |
| `forecast/` | Moving average + diurnal baseline prediction |
| `exposure/` | Student exposure scoring (normalized) |
| `intervention/` | Scenario-based impact simulation |
| `priority/` | Combined priority ranking with explanations |
| `dashboard/` | Streamlit 7-page interactive dashboard |

## Formulas

### Heat Index (Rothfusz 1979)
Standard regression for apparent temperature from air temperature and humidity.

### Composite Heat Risk Score
```
risk = (w_hi × HI_norm + w_rh × RH_norm + w_ws × WS_norm + w_sf × SF_norm) × 100
```
**All weights are illustrative heuristic parameters, NOT empirically calibrated.**

### Student Exposure Score
```
exposure = (w_risk × risk_norm + w_students × students_norm + w_hours × hours_norm)
```
Uses actual exposure_hours from input data.

### Priority Score
```
priority = w_risk × risk_norm + w_exposure × exposure_norm + w_intervention × intervention_norm
```

## Configuration

All weights, factors, and thresholds are configurable in `config.yaml`.

## Research Integrity

- All default weights are illustrative heuristics, not empirically calibrated
- Intervention results are scenario projections, not measured outcomes
- Synthetic demo data — not real sensor measurements
- No causal claims without validation data
- Methodology section in dashboard explains all formulas and assumptions

## Data Provenance

Every output carries a provenance flag: `measured`, `imported`, `synthetic`, `predicted`, or `simulated`.

## Testing

```bash
pytest tests/ -v
```

## Extension Points

- Replace synthetic data with real CSV/JSON sensor data
- Calibrate weights from field validation
- Add actual UTCI/PET when mean radiant temperature is available
- Integrate satellite NDVI data
- Add ML forecast models with proper validation

## License

MIT
