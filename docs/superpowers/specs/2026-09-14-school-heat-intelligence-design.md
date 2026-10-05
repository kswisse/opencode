# School Heat Intelligence — MVP Design Spec

**Date:** 2026-09-14
**Scope:** Competition-ready MVP, 12-hour max
**Architecture:** Approach A — Modular Pipeline + Streamlit Dashboard

---

## 1. Overview

A data-driven system that detects school-campus heat hotspots, predicts near-term heat risk, estimates student exposure, and recommends the best cooling intervention. Uses synthetic demonstration data with clear provenance separation.

**Pipeline:** `environmental data → heat risk → hotspot detection → short-term forecast → student exposure → intervention simulation → priority ranking → dashboard`

---

## 2. Data Layer

### 2.1 Input Format

CSV/JSON with fields:
- `timestamp` (ISO 8601)
- `zone_id`, `zone_name`, `lat`, `lon`
- `air_temperature` (°C)
- `humidity` (%, relative)
- `wind_speed` (m/s)
- `ndvi` (0–1, optional)
- `canopy_pct` (0–100)
- `shade_pct` (0–100)
- `surface_type` (asphalt | concrete | grass | permeable)
- `student_count` (integer)
- `exposure_hours` (float, actual hours students use zone)

### 2.2 Synthetic Demo Dataset

- 14-day hourly data, 12 campus zones
- Zones: playground, parking_lot, courtyard, building_roof, sports_field, library_exterior, cafeteria_patio, walkway, garden, gym_exterior, admin_building, entrance_plaza
- Realistic diurnal patterns, surface effects, student schedules
- All records flagged `provenance: SYNTHETIC`

### 2.3 Data Models

```python
class ProvenanceFlag(str, Enum):
    MEASURED = "measured"
    IMPORTED = "imported"
    SYNTHETIC = "synthetic"
    PREDICTED = "predicted"
    SIMULATED = "simulated"

class ZoneReading(BaseModel):
    timestamp: datetime
    zone_id: str
    zone_name: str
    lat: float
    lon: float
    air_temperature: float
    humidity: float
    wind_speed: float
    ndvi: Optional[float]
    canopy_pct: float
    shade_pct: float
    surface_type: str
    student_count: int
    exposure_hours: float
    provenance: ProvenanceFlag
```

---

## 3. Heat Risk Engine

### 3.1 Heat Index

Standard Rothfusz regression (Steadman 1979):
```
HI = -42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH
     - 6.83783e-3*T² - 5.481717e-2*RH² + 1.22874e-3*T²*RH
     + 8.5282e-4*T*RH² - 1.99e-6*T²*RH²
```
where T = air_temperature (°F), RH = relative humidity (%)

### 3.2 Composite Heat Risk Score

**This is an illustrative heuristic index for MVP/decision-support purposes. The default weights are heuristic and have not been empirically calibrated.**

```python
def compute_risk_score(heat_index, humidity, wind_speed, surface_type, config):
    """
    Composite Heat Risk Score (0-100).
    
    WARNING: This is an illustrative heuristic composite index.
    Default weights are NOT empirically calibrated.
    """

    # Normalize each component to 0-1
    hi_norm = normalize(heat_index, min_val=20, max_val=50)   # °C range
    rh_norm = normalize(humidity, min_val=0, max_val=100)     # %
    ws_norm = normalize(wind_speed, min_val=0, max_val=15, invert=True)  # higher wind = lower risk
    sf_norm = surface_factor(surface_type)                     # categorical, 0-1

    # Weighted combination (configurable, illustrative heuristic)
    score = (
        config.risk_weights.heat_index * hi_norm +
        config.risk_weights.humidity * rh_norm +
        config.risk_weights.wind_speed * ws_norm +
        config.risk_weights.surface * sf_norm
    ) * 100

    return clamp(score, 0, 100)
```

### 3.3 Surface Factor

Surface type is treated as a **categorical/contextual factor** in the heuristic risk model. It maps to a normalized 0–1 value based on known surface properties (albedo, thermal mass). No fixed °C corrections are applied.

```yaml
# config.yaml
surface_factors:
  asphalt: 0.9     # High thermal absorption
  concrete: 0.7
  grass: 0.3       # Evapotranspiration cooling
  permeable: 0.5
```

### 3.4 Risk Labels

| Score Range | Label |
|-------------|-------|
| 0–25 | Low |
| 26–50 | Moderate |
| 51–75 | High |
| 76–100 | Extreme |

---

## 4. Hotspot Detection

- Rank zones by risk_score descending
- Flag zones above 75th percentile as "hotspots"
- Return sorted list with zone metadata and provenance

---

## 5. Forecast

### 5.1 Method

Simple moving average + diurnal pattern extraction (no ML):
- Compute hourly averages over a rolling historical window (default: 168 hours / 7 days)
- Project forward 1, 2, 3, and 6 hours
- Uncertainty: ±1 standard deviation bands

### 5.2 Evaluation

Basic train/test holdout evaluation:
- Hold out last 24 hours
- Compute MAE, RMSE for each forecast horizon
- Display evaluation metrics in methodology section

### 5.3 Claims

No ML capability claims. No forecast accuracy claims without held-out evaluation.

---

## 6. Student Exposure

### 6.1 Exposure Score

Uses actual `exposure_hours` from input data. If missing, defaults to a configurable parameter (documented as modelling assumption).

```python
def compute_exposure_score(risk_score, student_count, exposure_hours, config):
    """
    Student exposure score. All inputs normalized to 0-100 before combination.
    """
    risk_norm = risk_score  # Already 0-100
    students_norm = normalize(student_count, min_val=0, max_val=config.max_students)
    hours_norm = normalize(exposure_hours, min_val=0, max_val=config.max_exposure_hours)

    # Weighted combination (configurable)
    score = (
        config.exposure_weights.risk * risk_norm +
        config.exposure_weights.students * students_norm +
        config.exposure_weights.hours * hours_norm
    )

    return clamp(score, 0, 100)
```

### 6.2 Ranking

Rank zones by exposure_score, not temperature alone. Identify "high exposure + high risk" zones as priority.

---

## 7. Intervention Simulator

### 7.1 Approach

**Scenario-based impact model.** NOT a physical temperature reduction model.

User adjusts:
- `canopy_pct` (0–100)
- `shade_pct` (0–100)
- `surface_type` (asphalt | concrete | grass | permeable)

### 7.2 Output

For each scenario:
```
baseline_risk       | scenario_config    | simulated_risk | relative_change | assumptions
82 (High)           | canopy: 5→40%      | 61 (Moderate)  | -25.6%          | [list]
```

### 7.3 Label

Visible on every simulation result:

> **"Mô phỏng mô hình — chưa được kiểm chứng thực địa."**
> **"Model simulation — not validated with field measurements."**

### 7.4 Assumptions

Every simulation displays its assumption list:
- "Canopy increase modelled as illustrative heuristic reduction"
- "Surface change modelled as categorical risk factor adjustment"
- "Results are scenario projections, not measured outcomes"

---

## 8. Priority Engine

### 8.1 Formula

All three components normalized to 0–100 before combination:

```python
def compute_priority_score(risk_score, exposure_score, intervention_potential, config):
    """
    Priority = w1*risk_norm + w2*exposure_norm + w3*intervention_norm
    
    All weights configurable and documented as heuristic.
    """
    priority = (
        config.priority_weights.risk * risk_score +
        config.priority_weights.exposure * exposure_score +
        config.priority_weights.intervention_potential * intervention_potential
    )
    return clamp(priority, 0, 100)
```

### 8.2 Explanations

Each zone gets a text explanation:
> "Zone X is priority #1 because: high heat risk (82), high student exposure (45 students × 3 hrs), large intervention potential (scenario projection: -25.6% risk change)"

---

## 9. Dashboard (7 Sections)

1. **Overview** — Campus zone map (folium), current risk summary, hotspot alerts
2. **Risk Analysis** — Zone-by-zone risk breakdown with component charts
3. **Forecast** — 6-hour risk prediction with uncertainty bands + evaluation metrics
4. **Exposure** — Exposure scores sorted, student impact summary
5. **Intervention Simulator** — Interactive sliders, baseline/scenario/delta comparison
6. **Priority Actions** — Ranked intervention recommendations with explanations
7. **Methodology** — Formulas, assumptions, normalization, limitations, data provenance

---

## 10. Research Integrity

### 10.1 Data Provenance

Every record and output carries `ProvenanceFlag`: MEASURED, IMPORTED, SYNTHETIC, PREDICTED, SIMULATED. Dashboard shows provenance badges.

### 10.2 Methodology Panel

Visible methodology section explaining:
- All formulas used
- All assumptions and their justifications
- Normalization approach
- Limitations and caveats
- Data provenance (what is measured vs modelled vs simulated)
- "Composite Heat Risk Score là chỉ số tổng hợp phục vụ MVP/decision support; các trọng số mặc định là heuristic và chưa được hiệu chuẩn thực nghiệm."

### 10.3 No Causal Claims

No causal relationships claimed without validation data. No real-world accuracy claims without field measurements.

---

## 11. Engineering

### 11.1 File Structure

```
school-heat-intelligence/
├── config.yaml
├── src/heat_intelligence/
│   ├── __init__.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── synthetic.py
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── heat_index.py
│   │   └── engine.py
│   ├── hotspot/
│   │   ├── __init__.py
│   │   └── detector.py
│   ├── forecast/
│   │   ├── __init__.py
│   │   └── predictor.py
│   ├── exposure/
│   │   ├── __init__.py
│   │   └── calculator.py
│   ├── intervention/
│   │   ├── __init__.py
│   │   └── simulator.py
│   ├── priority/
│   │   ├── __init__.py
│   │   └── engine.py
│   └── dashboard/
│       ├── app.py
│       ├── pages/
│       │   ├── 1_overview.py
│       │   ├── 2_risk_analysis.py
│       │   ├── 3_forecast.py
│       │   ├── 4_exposure.py
│       │   ├── 5_intervention.py
│       │   ├── 6_priority.py
│       │   └── 7_methodology.py
│       └── components.py
├── data/
│   └── demo_campus.csv
├── tests/
│   ├── __init__.py
│   ├── test_risk.py
│   ├── test_exposure.py
│   ├── test_forecast.py
│   ├── test_intervention.py
│   ├── test_priority.py
│   └── test_provenance.py
├── pyproject.toml
├── README.md
└── run.sh
```

### 11.2 Dependencies

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.30.0",
    "pandas>=2.1.0",
    "numpy>=1.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "folium>=0.15.0",
    "plotly>=5.18.0",
    "pyyaml>=6.0",
]
```

### 11.3 Tests

- `test_risk.py` — Heat index calculation, risk score normalization, surface factors
- `test_exposure.py` — Exposure normalization, weighting
- `test_forecast.py` — Predictor output shape, evaluation metrics
- `test_intervention.py` — Simulator delta calculation, assumption tracking
- `test_priority.py` — Priority ranking, normalized combination
- `test_provenance.py` — Provenance flag integrity across pipeline

### 11.4 Run

```bash
pip install -e .
streamlit run src/heat_intelligence/dashboard/app.py
```

---

## 12. Scope Control

**DO NOT add:**
- Authentication
- Payments
- Mobile app
- Chatbot
- Unnecessary AI agents
- Complex cloud infrastructure
- 3D visualization
- Real-time IoT

**This is a 12-hour MVP. Functionality and research credibility over visual polish.**
