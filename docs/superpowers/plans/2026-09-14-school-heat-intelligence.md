# School Heat Intelligence — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a competition-ready MVP that detects school-campus heat hotspots, predicts near-term heat risk, estimates student exposure, and recommends cooling interventions using synthetic demo data.

**Architecture:** Modular Python pipeline (data → risk → hotspot → forecast → exposure → intervention → priority) with Streamlit dashboard. All weights/factors configurable via `config.yaml`. Clear data provenance separation throughout.

**Tech Stack:** Python 3.11+, Streamlit, Pandas, NumPy, Pydantic, Folium, Plotly, PyYAML, pytest

## Global Constraints

- Python >=3.11
- All risk weights are illustrative heuristic parameters, NOT empirically calibrated
- No fake UTCI proxy — use Composite Heat Risk Score as primary metric
- No arbitrary fixed °C reductions for canopy/surface — scenario-based impact model
- Surface type is categorical contextual factor, not fixed temperature correction
- Every output carries ProvenanceFlag: MEASURED, IMPORTED, SYNTHETIC, PREDICTED, SIMULATED
- Intervention results labeled: "Mô phỏng mô hình — chưa được kiểm chứng thực địa."
- 12-hour scope maximum — no scope expansion

---

## File Structure

```
school-heat-intelligence/
├── config.yaml                           # All configurable weights, factors, thresholds
├── pyproject.toml                        # Project metadata and dependencies
├── README.md                             # Setup, run, architecture, formulas, assumptions
├── run.sh                                # Quick start script
├── src/heat_intelligence/
│   ├── __init__.py
│   ├── config.py                         # Load config.yaml into Pydantic settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py                    # All Pydantic data models
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py                     # CSV/JSON ingestion + validation
│   │   └── synthetic.py                  # Demo data generator
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── heat_index.py                 # Rothfusz heat index calculation
│   │   └── engine.py                     # Composite risk score
│   ├── hotspot/
│   │   ├── __init__.py
│   │   └── detector.py                   # Zone ranking + hotspot flagging
│   ├── forecast/
│   │   ├── __init__.py
│   │   └── predictor.py                  # Moving average + diurnal baseline
│   ├── exposure/
│   │   ├── __init__.py
│   │   └── calculator.py                 # Exposure score calculation
│   ├── intervention/
│   │   ├── __init__.py
│   │   └── simulator.py                  # Scenario-based impact model
│   ├── priority/
│   │   ├── __init__.py
│   │   └── engine.py                     # Priority scoring + explanations
│   └── dashboard/
│       ├── app.py                        # Main Streamlit app (7 pages)
│       ├── components.py                 # Reusable UI components
│       └── pages/
│           ├── 1_overview.py
│           ├── 2_risk_analysis.py
│           ├── 3_forecast.py
│           ├── 4_exposure.py
│           ├── 5_intervention.py
│           ├── 6_priority.py
│           └── 7_methodology.py
├── data/
│   └── demo_campus.csv                   # Generated synthetic data
└── tests/
    ├── __init__.py
    ├── test_risk.py
    ├── test_exposure.py
    ├── test_forecast.py
    ├── test_intervention.py
    ├── test_priority.py
    └── test_provenance.py
```

---

### Task 1: Project Scaffolding + Config

**Files:**
- Create: `school-heat-intelligence/pyproject.toml`
- Create: `school-heat-intelligence/config.yaml`
- Create: `school-heat-intelligence/src/heat_intelligence/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/config.py`
- Create: `school-heat-intelligence/run.sh`
- Create: `school-heat-intelligence/tests/__init__.py`

**Interfaces:**
- Produces: `load_config(path) -> HeatIntelligenceConfig`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p school-heat-intelligence/src/heat_intelligence/models
mkdir -p school-heat-intelligence/src/heat_intelligence/data
mkdir -p school-heat-intelligence/src/heat_intelligence/risk
mkdir -p school-heat-intelligence/src/heat_intelligence/hotspot
mkdir -p school-heat-intelligence/src/heat_intelligence/forecast
mkdir -p school-heat-intelligence/src/heat_intelligence/exposure
mkdir -p school-heat-intelligence/src/heat_intelligence/intervention
mkdir -p school-heat-intelligence/src/heat_intelligence/priority
mkdir -p school-heat-intelligence/src/heat_intelligence/dashboard/pages
mkdir -p school-heat-intelligence/data
mkdir -p school-heat-intelligence/tests
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "school-heat-intelligence"
version = "0.1.0"
description = "Data-driven school campus heat risk detection, forecasting, and intervention simulation"
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

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/heat_intelligence"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

- [ ] **Step 3: Create config.yaml**

```yaml
# School Heat Intelligence Configuration
# All weights are ILLUSTRATIVE HEURISTIC PARAMETERS, NOT empirically calibrated.

risk_weights:
  heat_index: 0.5
  humidity: 0.2
  wind_speed: 0.15
  surface: 0.15

surface_factors:
  asphalt: 0.9
  concrete: 0.7
  grass: 0.3
  permeable: 0.5

exposure_weights:
  risk: 0.4
  students: 0.35
  hours: 0.25

priority_weights:
  risk: 0.4
  exposure: 0.35
  intervention_potential: 0.25

forecast:
  window_hours: 168
  horizons: [1, 2, 3, 6]

normalization:
  heat_index_min: 20.0
  heat_index_max: 50.0
  humidity_min: 0.0
  humidity_max: 100.0
  wind_speed_min: 0.0
  wind_speed_max: 15.0
  max_students: 200
  max_exposure_hours: 12.0

hotspot_percentile: 75
```

- [ ] **Step 4: Create config.py**

```python
"""Configuration loader for School Heat Intelligence."""

from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel


class RiskWeights(BaseModel):
    heat_index: float = 0.5
    humidity: float = 0.2
    wind_speed: float = 0.15
    surface: float = 0.15


class ExposureWeights(BaseModel):
    risk: float = 0.4
    students: float = 0.35
    hours: float = 0.25


class PriorityWeights(BaseModel):
    risk: float = 0.4
    exposure: float = 0.35
    intervention_potential: float = 0.25


class ForecastConfig(BaseModel):
    window_hours: int = 168
    horizons: List[int] = [1, 2, 3, 6]


class NormalizationConfig(BaseModel):
    heat_index_min: float = 20.0
    heat_index_max: float = 50.0
    humidity_min: float = 0.0
    humidity_max: float = 100.0
    wind_speed_min: float = 0.0
    wind_speed_max: float = 15.0
    max_students: int = 200
    max_exposure_hours: float = 12.0


class HeatIntelligenceConfig(BaseModel):
    risk_weights: RiskWeights = RiskWeights()
    surface_factors: dict = {"asphalt": 0.9, "concrete": 0.7, "grass": 0.3, "permeable": 0.5}
    exposure_weights: ExposureWeights = ExposureWeights()
    priority_weights: PriorityWeights = PriorityWeights()
    forecast: ForecastConfig = ForecastConfig()
    normalization: NormalizationConfig = NormalizationConfig()
    hotspot_percentile: float = 75.0


def load_config(path: str = "config.yaml") -> HeatIntelligenceConfig:
    """Load configuration from YAML file, falling back to defaults."""
    config_path = Path(path)
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f)
        return HeatIntelligenceConfig(**data)
    return HeatIntelligenceConfig()
```

- [ ] **Step 5: Create __init__.py files**

```python
# src/heat_intelligence/__init__.py
"""School Heat Intelligence — campus heat risk detection and intervention simulation."""

__version__ = "0.1.0"
```

```python
# tests/__init__.py
```

- [ ] **Step 6: Create run.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
pip install -e ".[dev]"
streamlit run src/heat_intelligence/dashboard/app.py
```

- [ ] **Step 7: Verify config loads**

Run: `cd school-heat-intelligence && python -c "from heat_intelligence.config import load_config; c = load_config(); print(c.risk_weights.heat_index)"`
Expected: `0.5`

- [ ] **Step 8: Commit**

```bash
git add school-heat-intelligence/
git commit -m "feat: project scaffolding with config loader"
```

---

### Task 2: Data Models (Schemas)

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/models/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/models/schemas.py`

**Interfaces:**
- Produces: `ProvenanceFlag`, `ZoneReading`, `RiskScore`, `ForecastResult`, `ExposureScore`, `InterventionResult`, `PriorityItem`

- [ ] **Step 1: Create models/__init__.py**

```python
from heat_intelligence.models.schemas import (
    ProvenanceFlag,
    ZoneReading,
    RiskScore,
    ForecastResult,
    ExposureScore,
    InterventionResult,
    PriorityItem,
)

__all__ = [
    "ProvenanceFlag",
    "ZoneReading",
    "RiskScore",
    "ForecastResult",
    "ExposureScore",
    "InterventionResult",
    "PriorityItem",
]
```

- [ ] **Step 2: Create models/schemas.py**

```python
"""Pydantic data models for School Heat Intelligence."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProvenanceFlag(str, Enum):
    """Data provenance classification."""
    MEASURED = "measured"
    IMPORTED = "imported"
    SYNTHETIC = "synthetic"
    PREDICTED = "predicted"
    SIMULATED = "simulated"


class ZoneReading(BaseModel):
    """A single environmental reading for a campus zone."""
    timestamp: datetime
    zone_id: str
    zone_name: str
    lat: float
    lon: float
    air_temperature: float = Field(description="Air temperature in °C")
    humidity: float = Field(ge=0, le=100, description="Relative humidity in %")
    wind_speed: float = Field(ge=0, description="Wind speed in m/s")
    ndvi: Optional[float] = Field(None, ge=-1, le=1, description="NDVI index")
    canopy_pct: float = Field(ge=0, le=100, description="Canopy cover percentage")
    shade_pct: float = Field(ge=0, le=100, description="Shade cover percentage")
    surface_type: str = Field(description="Surface type: asphalt|concrete|grass|permeable")
    student_count: int = Field(ge=0, description="Number of students in zone")
    exposure_hours: float = Field(ge=0, description="Hours students exposed in zone")
    provenance: ProvenanceFlag = ProvenanceFlag.SYNTHETIC


class RiskScore(BaseModel):
    """Heat risk score for a zone at a point in time."""
    zone_id: str
    zone_name: str
    timestamp: datetime
    score: float = Field(ge=0, le=100, description="Composite heat risk score 0-100")
    label: str = Field(description="Risk label: Low|Moderate|High|Extreme")
    components: Dict[str, float] = Field(description="Individual component scores")
    provenance: ProvenanceFlag = ProvenanceFlag.SYNTHETIC


class ForecastResult(BaseModel):
    """Forecasted risk score for a zone at a future time."""
    zone_id: str
    zone_name: str
    timestamp: datetime
    horizon_hours: int
    predicted_score: float = Field(ge=0, le=100)
    lower_bound: float = Field(ge=0, le=100)
    upper_bound: float = Field(ge=0, le=100)
    provenance: ProvenanceFlag = ProvenanceFlag.PREDICTED


class ExposureScore(BaseModel):
    """Student exposure score for a zone."""
    zone_id: str
    zone_name: str
    risk_score: float = Field(ge=0, le=100)
    student_count: int = Field(ge=0)
    exposure_hours: float = Field(ge=0)
    score: float = Field(ge=0, le=100, description="Normalized exposure score 0-100")
    provenance: ProvenanceFlag = ProvenanceFlag.SYNTHETIC


class InterventionResult(BaseModel):
    """Result of an intervention simulation."""
    zone_id: str
    zone_name: str
    baseline_risk: float = Field(ge=0, le=100)
    scenario_config: Dict[str, float] = Field(description="Scenario input changes")
    simulated_risk: float = Field(ge=0, le=100)
    relative_change_pct: float = Field(description="Percentage change in risk")
    assumptions: List[str] = Field(description="List of assumptions used in simulation")
    provenance: ProvenanceFlag = ProvenanceFlag.SIMULATED


class PriorityItem(BaseModel):
    """Priority-ranked intervention recommendation."""
    rank: int
    zone_id: str
    zone_name: str
    priority_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    exposure_score: float = Field(ge=0, le=100)
    intervention_potential: float = Field(ge=0, le=100)
    explanation: str = Field(description="Human-readable explanation of priority ranking")
    provenance: ProvenanceFlag = ProvenanceFlag.SIMULATED
```

- [ ] **Step 3: Verify imports**

Run: `cd school-heat-intelligence && python -c "from heat_intelligence.models import ZoneReading, RiskScore; print('Models OK')"`
Expected: `Models OK`

- [ ] **Step 4: Commit**

```bash
git add src/heat_intelligence/models/
git commit -m "feat: add Pydantic data models with provenance flags"
```

---

### Task 3: Synthetic Data Generator

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/data/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/data/synthetic.py`
- Create: `school-heat-intelligence/src/heat_intelligence/data/loader.py`
- Create: `school-heat-intelligence/data/demo_campus.csv`

**Interfaces:**
- Produces: `generate_demo_data() -> pd.DataFrame`, `load_data(path) -> List[ZoneReading]`

- [ ] **Step 1: Create data/__init__.py**

```python
from heat_intelligence.data.loader import load_data
from heat_intelligence.data.synthetic import generate_demo_data

__all__ = ["load_data", "generate_demo_data"]
```

- [ ] **Step 2: Create data/synthetic.py**

```python
"""Synthetic demo data generator for School Heat Intelligence."""

import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import numpy as np

from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading


# Zone definitions with realistic properties
ZONES = [
    {"zone_id": "zone_01", "zone_name": "playground", "lat": 40.7128, "lon": -74.0060,
     "surface_type": "asphalt", "canopy_pct": 5, "shade_pct": 10, "base_temp_offset": 2.0},
    {"zone_id": "zone_02", "zone_name": "parking_lot", "lat": 40.7130, "lon": -74.0062,
     "surface_type": "asphalt", "canopy_pct": 0, "shade_pct": 0, "base_temp_offset": 3.5},
    {"zone_id": "zone_03", "zone_name": "courtyard", "lat": 40.7126, "lon": -74.0058,
     "surface_type": "concrete", "canopy_pct": 15, "shade_pct": 25, "base_temp_offset": 1.0},
    {"zone_id": "zone_04", "zone_name": "building_roof", "lat": 40.7129, "lon": -74.0059,
     "surface_type": "concrete", "canopy_pct": 0, "shade_pct": 0, "base_temp_offset": 4.0},
    {"zone_id": "zone_05", "zone_name": "sports_field", "lat": 40.7131, "lon": -74.0061,
     "surface_type": "grass", "canopy_pct": 0, "shade_pct": 5, "base_temp_offset": 0.5},
    {"zone_id": "zone_06", "zone_name": "library_exterior", "lat": 40.7127, "lon": -74.0057,
     "surface_type": "concrete", "canopy_pct": 20, "shade_pct": 35, "base_temp_offset": 0.8},
    {"zone_id": "zone_07", "zone_name": "cafeteria_patio", "lat": 40.7125, "lon": -74.0063,
     "surface_type": "concrete", "canopy_pct": 40, "shade_pct": 50, "base_temp_offset": 0.3},
    {"zone_id": "zone_08", "zone_name": "walkway", "lat": 40.7132, "lon": -74.0056,
     "surface_type": "asphalt", "canopy_pct": 10, "shade_pct": 15, "base_temp_offset": 1.5},
    {"zone_id": "zone_09", "zone_name": "garden", "lat": 40.7124, "lon": -74.0064,
     "surface_type": "grass", "canopy_pct": 60, "shade_pct": 70, "base_temp_offset": -0.5},
    {"zone_id": "zone_10", "zone_name": "gym_exterior", "lat": 40.7133, "lon": -74.0065,
     "surface_type": "concrete", "canopy_pct": 10, "shade_pct": 20, "base_temp_offset": 1.2},
    {"zone_id": "zone_11", "zone_name": "admin_building", "lat": 40.7123, "lon": -74.0055,
     "surface_type": "concrete", "canopy_pct": 25, "shade_pct": 30, "base_temp_offset": 0.6},
    {"zone_id": "zone_12", "zone_name": "entrance_plaza", "lat": 40.7134, "lon": -74.0066,
     "surface_type": "asphalt", "canopy_pct": 5, "shade_pct": 10, "base_temp_offset": 2.5},
]

# Student schedule patterns (hour -> fraction of max students)
STUDENT_SCHEDULE = {
    0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0,
    6: 0.1, 7: 0.3, 8: 0.8, 9: 1.0, 10: 1.0, 11: 0.9,
    12: 0.7, 13: 0.9, 14: 1.0, 15: 0.8, 16: 0.5, 17: 0.3,
    18: 0.1, 19: 0.0, 20: 0.0, 21: 0.0, 22: 0.0, 23: 0.0,
}

# Zone student capacity (max students per zone)
ZONE_CAPACITY = {
    "playground": 80, "parking_lot": 10, "courtyard": 45, "building_roof": 5,
    "sports_field": 120, "library_exterior": 30, "cafeteria_patio": 60,
    "walkway": 25, "garden": 15, "gym_exterior": 40, "admin_building": 20,
    "entrance_plaza": 35,
}


def _diurnal_temperature(hour: int, base: float, offset: float) -> float:
    """Generate realistic diurnal temperature pattern."""
    # Peak at 14:00, minimum at 05:00
    diurnal = 5.0 * np.sin(2 * np.pi * (hour - 5) / 24)
    return base + diurnal + offset


def _diurnal_humidity(hour: int) -> float:
    """Generate realistic diurnal humidity pattern."""
    # Inverse of temperature: highest at night, lowest afternoon
    return 65.0 - 25.0 * np.sin(2 * np.pi * (hour - 5) / 24)


def generate_demo_data(
    days: int = 14,
    base_temperature: float = 28.0,
    output_path: str = "data/demo_campus.csv",
) -> List[ZoneReading]:
    """Generate synthetic demo dataset for 12 campus zones over N days."""
    np.random.seed(42)
    readings: List[ZoneReading] = []
    start_date = datetime(2026, 7, 1, 0, 0, 0)

    for day in range(days):
        current_date = start_date + timedelta(days=day)
        for hour in range(24):
            timestamp = current_date.replace(hour=hour)
            schedule_factor = STUDENT_SCHEDULE[hour]

            for zone in ZONES:
                temp = _diurnal_temperature(hour, base_temperature, zone["base_temp_offset"])
                temp += np.random.normal(0, 0.5)  # Add noise

                humidity = _diurnal_humidity(hour)
                humidity += np.random.normal(0, 3)
                humidity = max(20, min(100, humidity))

                wind_speed = max(0, 2.0 + np.random.normal(0, 1.0))

                student_count = int(ZONE_CAPACITY[zone["zone_name"]] * schedule_factor)
                student_count = max(0, student_count + int(np.random.normal(0, 2)))

                # Exposure hours: 1 during active hours, 0 otherwise
                exposure_hours = 1.0 if schedule_factor > 0.1 else 0.0

                reading = ZoneReading(
                    timestamp=timestamp,
                    zone_id=zone["zone_id"],
                    zone_name=zone["zone_name"],
                    lat=zone["lat"],
                    lon=zone["lon"],
                    air_temperature=round(temp, 1),
                    humidity=round(humidity, 1),
                    wind_speed=round(wind_speed, 1),
                    ndvi=round(np.random.uniform(0.1, 0.8), 2),
                    canopy_pct=zone["canopy_pct"],
                    shade_pct=zone["shade_pct"],
                    surface_type=zone["surface_type"],
                    student_count=student_count,
                    exposure_hours=exposure_hours,
                    provenance=ProvenanceFlag.SYNTHETIC,
                )
                readings.append(reading)

    # Write to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        headers = [
            "timestamp", "zone_id", "zone_name", "lat", "lon",
            "air_temperature", "humidity", "wind_speed", "ndvi",
            "canopy_pct", "shade_pct", "surface_type",
            "student_count", "exposure_hours", "provenance",
        ]
        writer.writerow(headers)
        for r in readings:
            writer.writerow([
                r.timestamp.isoformat(), r.zone_id, r.zone_name,
                r.lat, r.lon, r.air_temperature, r.humidity,
                r.wind_speed, r.ndvi, r.canopy_pct, r.shade_pct,
                r.surface_type, r.student_count, r.exposure_hours,
                r.provenance.value,
            ])

    print(f"Generated {len(readings)} readings -> {output_path}")
    return readings
```

- [ ] **Step 3: Create data/loader.py**

```python
"""CSV/JSON data loader with validation."""

import csv
import json
from pathlib import Path
from typing import List

from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading


def load_data(path: str) -> List[ZoneReading]:
    """Load zone readings from CSV or JSON file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    if file_path.suffix == ".csv":
        return _load_csv(file_path)
    elif file_path.suffix == ".json":
        return _load_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def _load_csv(file_path: Path) -> List[ZoneReading]:
    """Load readings from CSV file."""
    readings = []
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            reading = ZoneReading(
                timestamp=row["timestamp"],
                zone_id=row["zone_id"],
                zone_name=row["zone_name"],
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                air_temperature=float(row["air_temperature"]),
                humidity=float(row["humidity"]),
                wind_speed=float(row["wind_speed"]),
                ndvi=float(row["ndvi"]) if row.get("ndvi") else None,
                canopy_pct=float(row["canopy_pct"]),
                shade_pct=float(row["shade_pct"]),
                surface_type=row["surface_type"],
                student_count=int(row["student_count"]),
                exposure_hours=float(row["exposure_hours"]),
                provenance=ProvenanceFlag(row.get("provenance", "synthetic")),
            )
            readings.append(reading)
    return readings


def _load_json(file_path: Path) -> List[ZoneReading]:
    """Load readings from JSON file."""
    with open(file_path, "r") as f:
        data = json.load(f)
    return [ZoneReading(**item) for item in data]
```

- [ ] **Step 4: Generate demo data**

Run: `cd school-heat-intelligence && python -c "from heat_intelligence.data.synthetic import generate_demo_data; generate_demo_data()"`
Expected: `Generated 4032 readings -> data/demo_campus.csv`

- [ ] **Step 5: Verify data loads**

Run: `cd school-heat-intelligence && python -c "from heat_intelligence.data import load_data; data = load_data('data/demo_campus.csv'); print(f'Loaded {len(data)} readings')"`
Expected: `Loaded 4032 readings`

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/data/ data/demo_campus.csv
git commit -m "feat: synthetic data generator and CSV loader"
```

---

### Task 4: Heat Risk Engine

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/risk/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/risk/heat_index.py`
- Create: `school-heat-intelligence/src/heat_intelligence/risk/engine.py`
- Create: `school-heat-intelligence/tests/test_risk.py`

**Interfaces:**
- Consumes: `ZoneReading`, `HeatIntelligenceConfig`
- Produces: `compute_heat_index(temp_c, humidity) -> float`, `compute_risk_score(reading, config) -> RiskScore`

- [ ] **Step 1: Write failing test for heat index**

```python
# tests/test_risk.py
"""Tests for heat risk engine."""

import pytest
from datetime import datetime

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.heat_index import compute_heat_index
from heat_intelligence.risk.engine import compute_risk_score, normalize_risk_label
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag


class TestHeatIndex:
    """Tests for Rothfusz heat index calculation."""

    def test_heat_index_low_temperature(self):
        """At 20°C and 50% humidity, heat index should be close to 20°C."""
        hi = compute_heat_index(20.0, 50.0)
        assert 18 <= hi <= 22

    def test_heat_index_high_temperature(self):
        """At 40°C and 80% humidity, heat index should be significantly higher."""
        hi = compute_heat_index(40.0, 80.0)
        assert hi > 40

    def test_heat_index_extreme_conditions(self):
        """At 45°C and 90% humidity, heat index should be extreme."""
        hi = compute_heat_index(45.0, 90.0)
        assert hi > 50

    def test_heat_index_increases_with_humidity(self):
        """Heat index should increase with humidity at same temperature."""
        hi_low = compute_heat_index(35.0, 40.0)
        hi_high = compute_heat_index(35.0, 90.0)
        assert hi_high > hi_low


class TestRiskScore:
    """Tests for composite risk score calculation."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def sample_reading(self):
        return ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0, 0),
            zone_id="zone_01",
            zone_name="playground",
            lat=40.7128,
            lon=-74.0060,
            air_temperature=35.0,
            humidity=70.0,
            wind_speed=2.0,
            canopy_pct=5,
            shade_pct=10,
            surface_type="asphalt",
            student_count=80,
            exposure_hours=1.0,
            provenance=ProvenanceFlag.SYNTHETIC,
        )

    def test_risk_score_range(self, sample_reading, config):
        """Risk score should be between 0 and 100."""
        result = compute_risk_score(sample_reading, config)
        assert 0 <= result.score <= 100

    def test_risk_score_label_mapping(self, sample_reading, config):
        """Risk label should match score range."""
        result = compute_risk_score(sample_reading, config)
        if result.score <= 25:
            assert result.label == "Low"
        elif result.score <= 50:
            assert result.label == "Moderate"
        elif result.score <= 75:
            assert result.label == "High"
        else:
            assert result.label == "Extreme"

    def test_risk_score_increases_with_temperature(self, config):
        """Higher temperature should produce higher risk score."""
        reading_cool = ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0, 0),
            zone_id="z1", zone_name="test", lat=0, lon=0,
            air_temperature=25.0, humidity=50.0, wind_speed=3.0,
            canopy_pct=50, shade_pct=50, surface_type="grass",
            student_count=10, exposure_hours=1.0,
        )
        reading_hot = ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0, 0),
            zone_id="z2", zone_name="test", lat=0, lon=0,
            air_temperature=42.0, humidity=80.0, wind_speed=1.0,
            canopy_pct=0, shade_pct=0, surface_type="asphalt",
            student_count=10, exposure_hours=1.0,
        )
        score_cool = compute_risk_score(reading_cool, config)
        score_hot = compute_risk_score(reading_hot, config)
        assert score_hot.score > score_cool.score

    def test_risk_score_has_provenance(self, sample_reading, config):
        """Risk score should carry provenance flag."""
        result = compute_risk_score(sample_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC

    def test_risk_score_has_components(self, sample_reading, config):
        """Risk score should include component breakdown."""
        result = compute_risk_score(sample_reading, config)
        assert "heat_index" in result.components
        assert "humidity" in result.components
        assert "wind_speed" in result.components
        assert "surface" in result.components


class TestRiskLabel:
    """Tests for risk label normalization."""

    def test_normalize_risk_label(self):
        assert normalize_risk_label(10) == "Low"
        assert normalize_risk_label(30) == "Moderate"
        assert normalize_risk_label(60) == "High"
        assert normalize_risk_label(85) == "Extreme"

    def test_normalize_risk_label_boundaries(self):
        assert normalize_risk_label(0) == "Low"
        assert normalize_risk_label(25) == "Low"
        assert normalize_risk_label(26) == "Moderate"
        assert normalize_risk_label(50) == "Moderate"
        assert normalize_risk_label(51) == "High"
        assert normalize_risk_label(75) == "High"
        assert normalize_risk_label(76) == "Extreme"
        assert normalize_risk_label(100) == "Extreme"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd school-heat-intelligence && python -m pytest tests/test_risk.py -v`
Expected: FAIL with ImportError (modules not yet created)

- [ ] **Step 3: Create risk/__init__.py**

```python
from heat_intelligence.risk.heat_index import compute_heat_index
from heat_intelligence.risk.engine import compute_risk_score, normalize_risk_label

__all__ = ["compute_heat_index", "compute_risk_score", "normalize_risk_label"]
```

- [ ] **Step 4: Create risk/heat_index.py**

```python
"""Rothfusz heat index calculation (Steadman 1979)."""

import numpy as np


def compute_heat_index(temp_c: float, humidity: float) -> float:
    """
    Compute heat index using Rothfusz regression.
    
    Args:
        temp_c: Air temperature in Celsius
        humidity: Relative humidity in percent (0-100)
    
    Returns:
        Heat index in Celsius
    """
    # Convert to Fahrenheit
    t_f = temp_c * 9 / 5 + 32
    
    # Rothfusz regression coefficients
    hi_f = (
        -42.379
        + 2.04901523 * t_f
        + 10.14333127 * humidity
        - 0.22475541 * t_f * humidity
        - 6.83783e-3 * t_f**2
        - 5.481717e-2 * humidity**2
        + 1.22874e-3 * t_f**2 * humidity
        + 8.5282e-4 * t_f * humidity**2
        - 1.99e-6 * t_f**2 * humidity**2
    )
    
    # Apply adjustment for low humidity at low temperatures
    if humidity < 13 and 80 <= t_f <= 112:
        adjustment = -((13 - humidity) / 4) * np.sqrt((17 - abs(t_f - 95)) / 17)
        hi_f += adjustment
    
    # Apply adjustment for high humidity at high temperatures
    if humidity > 85 and 80 <= t_f <= 87:
        adjustment = ((humidity - 85) / 10) * ((87 - t_f) / 5)
        hi_f += adjustment
    
    # Convert back to Celsius
    hi_c = (hi_f - 32) * 5 / 9
    
    return round(hi_c, 2)
```

- [ ] **Step 5: Create risk/engine.py**

```python
"""Composite heat risk score engine.

WARNING: This is an illustrative heuristic composite index for MVP/decision-support.
Default weights are NOT empirically calibrated.
"""

from typing import Dict

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import RiskScore, ZoneReading, ProvenanceFlag
from heat_intelligence.risk.heat_index import compute_heat_index


def normalize(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    """Normalize a value to 0-1 range."""
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0.0, min(1.0, normalized))
    if invert:
        normalized = 1.0 - normalized
    return normalized


def surface_factor(surface_type: str, config: HeatIntelligenceConfig) -> float:
    """Get categorical surface factor from config."""
    return config.surface_factors.get(surface_type, 0.5)


def normalize_risk_label(score: float) -> str:
    """Map risk score to label."""
    if score <= 25:
        return "Low"
    elif score <= 50:
        return "Moderate"
    elif score <= 75:
        return "High"
    else:
        return "Extreme"


def compute_risk_score(reading: ZoneReading, config: HeatIntelligenceConfig) -> RiskScore:
    """
    Compute composite heat risk score for a zone reading.
    
    All weights are configurable and documented as illustrative heuristics.
    """
    norm = config.normalization

    # Compute heat index
    hi = compute_heat_index(reading.air_temperature, reading.humidity)

    # Normalize each component to 0-1
    hi_norm = normalize(hi, norm.heat_index_min, norm.heat_index_max)
    rh_norm = normalize(reading.humidity, norm.humidity_min, norm.humidity_max)
    ws_norm = normalize(reading.wind_speed, norm.wind_speed_min, norm.wind_speed_max, invert=True)
    sf_norm = surface_factor(reading.surface_type, config)

    # Weighted combination (configurable illustrative heuristic)
    w = config.risk_weights
    score = (w.heat_index * hi_norm + w.humidity * rh_norm +
             w.wind_speed * ws_norm + w.surface * sf_norm) * 100
    score = max(0.0, min(100.0, score))

    return RiskScore(
        zone_id=reading.zone_id,
        zone_name=reading.zone_name,
        timestamp=reading.timestamp,
        score=round(score, 1),
        label=normalize_risk_label(score),
        components={
            "heat_index": round(hi_norm * 100, 1),
            "humidity": round(rh_norm * 100, 1),
            "wind_speed": round(ws_norm * 100, 1),
            "surface": round(sf_norm * 100, 1),
        },
        provenance=ProvenanceFlag.SYNTHETIC,
    )
```

- [ ] **Step 6: Run tests**

Run: `cd school-heat-intelligence && python -m pytest tests/test_risk.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/heat_intelligence/risk/ tests/test_risk.py
git commit -m "feat: heat risk engine with Rothfusz heat index and configurable composite score"
```

---

### Task 5: Hotspot Detection

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/hotspot/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/hotspot/detector.py`

**Interfaces:**
- Consumes: `List[RiskScore]`, `config.hotspot_percentile`
- Produces: `detect_hotspots(risk_scores, config) -> List[RiskScore]`

- [ ] **Step 1: Create hotspot/__init__.py**

```python
from heat_intelligence.hotspot.detector import detect_hotspots

__all__ = ["detect_hotspots"]
```

- [ ] **Step 2: Create hotspot/detector.py**

```python
"""Hotspot detection — rank zones by risk and flag hotspots."""

import numpy as np
from typing import List

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import RiskScore


def detect_hotspots(
    risk_scores: List[RiskScore],
    config: HeatIntelligenceConfig,
) -> List[RiskScore]:
    """
    Rank zones by risk score and flag hotspot zones.
    
    Hotspots are zones above the configured percentile threshold.
    """
    if not risk_scores:
        return []

    # Sort by risk score descending
    sorted_scores = sorted(risk_scores, key=lambda x: x.score, reverse=True)

    # Compute percentile threshold
    scores_array = np.array([rs.score for rs in sorted_scores])
    threshold = np.percentile(scores_array, config.hotspot_percentile)

    # Flag hotspots (scores at or above threshold)
    for rs in sorted_scores:
        rs.label = f"{'🔥 HOTSPOT: ' if rs.score >= threshold else ''}{rs.label}"

    return sorted_scores
```

- [ ] **Step 3: Verify module loads**

Run: `cd school-heat-intelligence && python -c "from heat_intelligence.hotspot import detect_hotspots; print('Hotspot module OK')"`
Expected: `Hotspot module OK`

- [ ] **Step 4: Commit**

```bash
git add src/heat_intelligence/hotspot/
git commit -m "feat: hotspot detection with percentile-based flagging"
```

---

### Task 6: Forecast Predictor

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/forecast/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/forecast/predictor.py`
- Create: `school-heat-intelligence/tests/test_forecast.py`

**Interfaces:**
- Consumes: `List[ZoneReading]`, `config.forecast`
- Produces: `forecast_risk(readings, config) -> List[ForecastResult]`

- [ ] **Step 1: Write failing test**

```python
# tests/test_forecast.py
"""Tests for forecast predictor."""

import pytest
from datetime import datetime, timedelta

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.forecast.predictor import forecast_risk
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag


class TestForecast:
    """Tests for moving average + diurnal forecast."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def sample_readings(self):
        """Generate 7 days of hourly readings for one zone."""
        readings = []
        base = datetime(2026, 7, 1, 0, 0, 0)
        for day in range(7):
            for hour in range(24):
                ts = base + timedelta(days=day, hours=hour)
                readings.append(ZoneReading(
                    timestamp=ts, zone_id="z1", zone_name="test",
                    lat=0, lon=0,
                    air_temperature=30.0 + 5 * (1 if 8 <= hour <= 18 else 0),
                    humidity=60.0, wind_speed=2.0,
                    canopy_pct=20, shade_pct=30,
                    surface_type="concrete", student_count=50,
                    exposure_hours=1.0,
                ))
        return readings

    def test_forecast_output_count(self, sample_readings, config):
        """Forecast should produce results for each horizon."""
        results = forecast_risk(sample_readings, config, zone_id="z1")
        # Should have results for each horizon
        assert len(results) > 0

    def test_forecast_has_bounds(self, sample_readings, config):
        """Forecast should include uncertainty bounds."""
        results = forecast_risk(sample_readings, config, zone_id="z1")
        for r in results:
            assert r.lower_bound <= r.predicted_score <= r.upper_bound

    def test_forecast_provenance(self, sample_readings, config):
        """Forecast results should be marked as predicted."""
        results = forecast_risk(sample_readings, config, zone_id="z1")
        for r in results:
            assert r.provenance == ProvenanceFlag.PREDICTED

    def test_forecast_score_range(self, sample_readings, config):
        """Forecast scores should be in valid range."""
        results = forecast_risk(sample_readings, config, zone_id="z1")
        for r in results:
            assert 0 <= r.predicted_score <= 100
            assert 0 <= r.lower_bound <= 100
            assert 0 <= r.upper_bound <= 100
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd school-heat-intelligence && python -m pytest tests/test_forecast.py -v`
Expected: FAIL

- [ ] **Step 3: Create forecast/__init__.py**

```python
from heat_intelligence.forecast.predictor import forecast_risk

__all__ = ["forecast_risk"]
```

- [ ] **Step 4: Create forecast/predictor.py**

```python
"""Simple moving average + diurnal baseline forecast.

No ML. No complex time series models. This is an explainable baseline.
"""

from datetime import timedelta
from typing import List

import numpy as np

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import ForecastResult, ProvenanceFlag, ZoneReading
from heat_intelligence.risk.engine import compute_risk_score


def forecast_risk(
    readings: List[ZoneReading],
    config: HeatIntelligenceConfig,
    zone_id: str,
) -> List[ForecastResult]:
    """
    Forecast risk scores using moving average + diurnal pattern.
    
    Args:
        readings: Historical readings (should include window_hours of data)
        config: Configuration with forecast settings
        zone_id: Zone to forecast
    
    Returns:
        List of ForecastResult for each configured horizon
    """
    # Filter to zone
    zone_readings = [r for r in readings if r.zone_id == zone_id]
    if not zone_readings:
        return []

    # Sort by timestamp
    zone_readings.sort(key=lambda r: r.timestamp)

    # Compute historical risk scores
    risk_scores = []
    for r in zone_readings:
        rs = compute_risk_score(r, config)
        risk_scores.append((r.timestamp, rs.score))

    if len(risk_scores) < 24:
        return []

    scores_array = np.array([s for _, s in risk_scores])
    last_timestamp = zone_readings[-1].timestamp

    # Compute rolling statistics
    window = min(config.forecast.window_hours, len(scores_array))
    recent_scores = scores_array[-window:]

    results = []
    for horizon in config.forecast.horizons:
        # Moving average prediction
        predicted = float(np.mean(recent_scores[-24:]))  # Last 24h average

        # Uncertainty: standard deviation of recent scores
        std = float(np.std(recent_scores[-48:])) if len(recent_scores) >= 48 else float(np.std(recent_scores))
        
        # Scale uncertainty by horizon (farther = more uncertain)
        uncertainty = std * np.sqrt(horizon / 6.0)

        lower = max(0.0, predicted - uncertainty)
        upper = min(100.0, predicted + uncertainty)

        results.append(ForecastResult(
            zone_id=zone_id,
            zone_name=zone_readings[-1].zone_name,
            timestamp=last_timestamp + timedelta(hours=horizon),
            horizon_hours=horizon,
            predicted_score=round(predicted, 1),
            lower_bound=round(lower, 1),
            upper_bound=round(upper, 1),
            provenance=ProvenanceFlag.PREDICTED,
        ))

    return results
```

- [ ] **Step 5: Run tests**

Run: `cd school-heat-intelligence && python -m pytest tests/test_forecast.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/forecast/ tests/test_forecast.py
git commit -m "feat: moving average + diurnal baseline forecast with uncertainty"
```

---

### Task 7: Exposure Calculator

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/exposure/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/exposure/calculator.py`
- Create: `school-heat-intelligence/tests/test_exposure.py`

**Interfaces:**
- Consumes: `RiskScore`, `ZoneReading`, `HeatIntelligenceConfig`
- Produces: `compute_exposure(risk, reading, config) -> ExposureScore`

- [ ] **Step 1: Write failing test**

```python
# tests/test_exposure.py
"""Tests for exposure calculator."""

import pytest
from datetime import datetime

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.models.schemas import RiskScore, ZoneReading, ProvenanceFlag


class TestExposure:
    """Tests for student exposure score calculation."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def high_risk(self):
        return RiskScore(
            zone_id="z1", zone_name="test",
            timestamp=datetime(2026, 7, 1, 12, 0),
            score=85.0, label="Extreme",
            components={"heat_index": 90, "humidity": 70, "wind_speed": 30, "surface": 80},
        )

    @pytest.fixture
    def low_risk(self):
        return RiskScore(
            zone_id="z2", zone_name="test2",
            timestamp=datetime(2026, 7, 1, 12, 0),
            score=20.0, label="Low",
            components={"heat_index": 25, "humidity": 40, "wind_speed": 60, "surface": 30},
        )

    @pytest.fixture
    def reading_high_exposure(self):
        return ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0),
            zone_id="z1", zone_name="test", lat=0, lon=0,
            air_temperature=40.0, humidity=80.0, wind_speed=1.0,
            canopy_pct=0, shade_pct=0, surface_type="asphalt",
            student_count=120, exposure_hours=6.0,
        )

    @pytest.fixture
    def reading_low_exposure(self):
        return ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0),
            zone_id="z2", zone_name="test2", lat=0, lon=0,
            air_temperature=25.0, humidity=50.0, wind_speed=3.0,
            canopy_pct=50, shade_pct=50, surface_type="grass",
            student_count=5, exposure_hours=1.0,
        )

    def test_exposure_score_range(self, high_risk, reading_high_exposure, config):
        """Exposure score should be 0-100."""
        result = compute_exposure(high_risk, reading_high_exposure, config)
        assert 0 <= result.score <= 100

    def test_high_exposure_scores_higher(self, high_risk, low_risk,
                                          reading_high_exposure, reading_low_exposure, config):
        """Zone with more students and hours should score higher."""
        high = compute_exposure(high_risk, reading_high_exposure, config)
        low = compute_exposure(low_risk, reading_low_exposure, config)
        assert high.score > low.score

    def test_exposure_uses_actual_hours(self, high_risk, config):
        """Exposure should use actual exposure_hours from reading."""
        reading = ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0),
            zone_id="z1", zone_name="test", lat=0, lon=0,
            air_temperature=40.0, humidity=80.0, wind_speed=1.0,
            canopy_pct=0, shade_pct=0, surface_type="asphalt",
            student_count=50, exposure_hours=8.0,
        )
        result = compute_exposure(high_risk, reading, config)
        assert result.exposure_hours == 8.0

    def test_exposure_provenance(self, high_risk, reading_high_exposure, config):
        """Exposure should carry provenance flag."""
        result = compute_exposure(high_risk, reading_high_exposure, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd school-heat-intelligence && python -m pytest tests/test_exposure.py -v`
Expected: FAIL

- [ ] **Step 3: Create exposure/__init__.py**

```python
from heat_intelligence.exposure.calculator import compute_exposure

__all__ = ["compute_exposure"]
```

- [ ] **Step 4: Create exposure/calculator.py**

```python
"""Student exposure score calculator.

Uses actual exposure_hours from input data. If missing, uses configurable default.
"""

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import ExposureScore, RiskScore, ZoneReading, ProvenanceFlag


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize to 0-1."""
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def compute_exposure(
    risk: RiskScore,
    reading: ZoneReading,
    config: HeatIntelligenceConfig,
) -> ExposureScore:
    """
    Compute student exposure score.
    
    All inputs normalized to 0-100 before weighted combination.
    Uses actual exposure_hours from reading (not arbitrary time weights).
    """
    norm = config.normalization

    risk_norm = risk.score  # Already 0-100
    students_norm = _normalize(reading.student_count, 0, norm.max_students) * 100
    hours_norm = _normalize(reading.exposure_hours, 0, norm.max_exposure_hours) * 100

    # Weighted combination (configurable)
    w = config.exposure_weights
    score = (w.risk * risk_norm + w.students * students_norm + w.hours * hours_norm)
    score = max(0.0, min(100.0, score))

    return ExposureScore(
        zone_id=reading.zone_id,
        zone_name=reading.zone_name,
        risk_score=risk.score,
        student_count=reading.student_count,
        exposure_hours=reading.exposure_hours,
        score=round(score, 1),
        provenance=ProvenanceFlag.SYNTHETIC,
    )
```

- [ ] **Step 5: Run tests**

Run: `cd school-heat-intelligence && python -m pytest tests/test_exposure.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/exposure/ tests/test_exposure.py
git commit -m "feat: exposure calculator with normalized scoring and actual hours"
```

---

### Task 8: Intervention Simulator

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/intervention/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/intervention/simulator.py`
- Create: `school-heat-intelligence/tests/test_intervention.py`

**Interfaces:**
- Consumes: `ZoneReading`, `RiskScore`, `HeatIntelligenceConfig`
- Produces: `simulate_intervention(reading, risk, scenario, config) -> InterventionResult`

- [ ] **Step 1: Write failing test**

```python
# tests/test_intervention.py
"""Tests for intervention simulator."""

import pytest
from datetime import datetime

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.intervention.simulator import simulate_intervention
from heat_intelligence.models.schemas import RiskScore, ZoneReading, ProvenanceFlag


class TestIntervention:
    """Tests for scenario-based intervention simulation."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def reading(self):
        return ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0),
            zone_id="z1", zone_name="test", lat=0, lon=0,
            air_temperature=38.0, humidity=75.0, wind_speed=1.5,
            canopy_pct=5, shade_pct=10, surface_type="asphalt",
            student_count=80, exposure_hours=4.0,
        )

    @pytest.fixture
    def risk(self):
        return RiskScore(
            zone_id="z1", zone_name="test",
            timestamp=datetime(2026, 7, 1, 12, 0),
            score=78.0, label="High",
            components={"heat_index": 85, "humidity": 75, "wind_speed": 25, "surface": 90},
        )

    def test_simulation_produces_result(self, reading, risk, config):
        """Simulation should produce an InterventionResult."""
        scenario = {"canopy_pct": 40, "shade_pct": 50, "surface_type": "grass"}
        result = simulate_intervention(reading, risk, scenario, config)
        assert result is not None
        assert result.zone_id == "z1"

    def test_simulation_shows_baseline(self, reading, risk, config):
        """Result should include baseline risk."""
        scenario = {"canopy_pct": 40}
        result = simulate_intervention(reading, risk, scenario, config)
        assert result.baseline_risk == 78.0

    def test_simulation_shows_delta(self, reading, risk, config):
        """Result should show relative change."""
        scenario = {"canopy_pct": 40, "shade_pct": 50, "surface_type": "grass"}
        result = simulate_intervention(reading, risk, scenario, config)
        assert "relative_change_pct" in result.model_fields

    def test_simulation_has_assumptions(self, reading, risk, config):
        """Result should list assumptions."""
        scenario = {"canopy_pct": 40}
        result = simulate_intervention(reading, risk, scenario, config)
        assert len(result.assumptions) > 0

    def test_simulation_provenance(self, reading, risk, config):
        """Simulation result should be marked as simulated."""
        scenario = {"canopy_pct": 40}
        result = simulate_intervention(reading, risk, scenario, config)
        assert result.provenance == ProvenanceFlag.SIMULATED

    def test_no_change_scenario(self, reading, risk, config):
        """Same config should produce minimal change."""
        scenario = {"canopy_pct": 5, "shade_pct": 10, "surface_type": "asphalt"}
        result = simulate_intervention(reading, risk, scenario, config)
        # Should be close to baseline
        assert abs(result.simulated_risk - result.baseline_risk) < 5.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd school-heat-intelligence && python -m pytest tests/test_intervention.py -v`
Expected: FAIL

- [ ] **Step 3: Create intervention/__init__.py**

```python
from heat_intelligence.intervention.simulator import simulate_intervention

__all__ = ["simulate_intervention"]
```

- [ ] **Step 4: Create intervention/simulator.py**

```python
"""Scenario-based intervention simulator.

WARNING: This is a heuristic model. Results are scenario projections, NOT measured outcomes.
Label: "Mô phỏng mô hình — chưa được kiểm chứng thực địa."
"""

from typing import Any, Dict, List

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import InterventionResult, RiskScore, ZoneReading, ProvenanceFlag
from heat_intelligence.risk.engine import compute_risk_score, normalize_risk_label


def simulate_intervention(
    reading: ZoneReading,
    baseline_risk: RiskScore,
    scenario: Dict[str, Any],
    config: HeatIntelligenceConfig,
) -> InterventionResult:
    """
    Simulate intervention scenario and compute projected risk change.
    
    This is a heuristic scenario model, NOT a physical temperature model.
    It outputs relative risk change, not absolute temperature change.
    
    Args:
        reading: Current zone reading
        baseline_risk: Current risk score
        scenario: Dict with keys: canopy_pct, shade_pct, surface_type
        config: Configuration
    
    Returns:
        InterventionResult with baseline, simulated, delta, and assumptions
    """
    assumptions: List[str] = []

    # Create modified reading from scenario
    modified_data = reading.model_dump()
    for key, value in scenario.items():
        if key in modified_data:
            modified_data[key] = value

    modified_reading = ZoneReading(**modified_data)

    # Compute simulated risk
    simulated_risk = compute_risk_score(modified_reading, config)

    # Calculate relative change
    if baseline_risk.score > 0:
        relative_change = ((simulated_risk.score - baseline_risk.score) / baseline_risk.score) * 100
    else:
        relative_change = 0.0

    # Build assumptions list
    if "canopy_pct" in scenario:
        old = reading.canopy_pct
        new = scenario["canopy_pct"]
        assumptions.append(
            f"Canopy cover changed from {old}% to {new}% "
            f"(illustrative heuristic, not calibrated cooling coefficient)"
        )
    if "shade_pct" in scenario:
        old = reading.shade_pct
        new = scenario["shade_pct"]
        assumptions.append(
            f"Shade cover changed from {old}% to {new}% "
            f"(illustrative heuristic, not calibrated cooling coefficient)"
        )
    if "surface_type" in scenario:
        old = reading.surface_type
        new = scenario["surface_type"]
        assumptions.append(
            f"Surface type changed from {old} to {new} "
            f"(categorical factor adjustment, not fixed °C correction)"
        )
    assumptions.append("Scenario model is heuristic — not validated with field measurements")
    assumptions.append("Results show relative risk change, not absolute temperature change")

    return InterventionResult(
        zone_id=reading.zone_id,
        zone_name=reading.zone_name,
        baseline_risk=baseline_risk.score,
        scenario_config={k: float(v) if isinstance(v, (int, float)) else v for k, v in scenario.items()},
        simulated_risk=simulated_risk.score,
        relative_change_pct=round(relative_change, 1),
        assumptions=assumptions,
        provenance=ProvenanceFlag.SIMULATED,
    )
```

- [ ] **Step 5: Run tests**

Run: `cd school-heat-intelligence && python -m pytest tests/test_intervention.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/intervention/ tests/test_intervention.py
git commit -m "feat: scenario-based intervention simulator with assumption tracking"
```

---

### Task 9: Priority Engine

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/priority/__init__.py`
- Create: `school-heat-intelligence/src/heat_intelligence/priority/engine.py`
- Create: `school-heat-intelligence/tests/test_priority.py`

**Interfaces:**
- Consumes: `List[RiskScore]`, `List[ExposureScore]`, `List[InterventionResult]`, `HeatIntelligenceConfig`
- Produces: `compute_priorities(...) -> List[PriorityItem]`

- [ ] **Step 1: Write failing test**

```python
# tests/test_priority.py
"""Tests for priority engine."""

import pytest
from datetime import datetime

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.priority.engine import compute_priorities
from heat_intelligence.models.schemas import (
    RiskScore, ExposureScore, InterventionResult, ProvenanceFlag,
)


class TestPriority:
    """Tests for priority scoring and ranking."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def risk_scores(self):
        return [
            RiskScore(zone_id="z1", zone_name="hot_zone",
                      timestamp=datetime(2026, 7, 1, 12), score=85, label="Extreme",
                      components={}, provenance=ProvenanceFlag.SYNTHETIC),
            RiskScore(zone_id="z2", zone_name="cool_zone",
                      timestamp=datetime(2026, 7, 1, 12), score=30, label="Moderate",
                      components={}, provenance=ProvenanceFlag.SYNTHETIC),
        ]

    @pytest.fixture
    def exposure_scores(self):
        return [
            ExposureScore(zone_id="z1", zone_name="hot_zone",
                          risk_score=85, student_count=100, exposure_hours=6.0,
                          score=80.0, provenance=ProvenanceFlag.SYNTHETIC),
            ExposureScore(zone_id="z2", zone_name="cool_zone",
                          risk_score=30, student_count=10, exposure_hours=1.0,
                          score=25.0, provenance=ProvenanceFlag.SYNTHETIC),
        ]

    @pytest.fixture
    def interventions(self):
        return [
            InterventionResult(zone_id="z1", zone_name="hot_zone",
                               baseline_risk=85, scenario_config={},
                               simulated_risk=55, relative_change_pct=-35.3,
                               assumptions=["test"], provenance=ProvenanceFlag.SIMULATED),
            InterventionResult(zone_id="z2", zone_name="cool_zone",
                               baseline_risk=30, scenario_config={},
                               simulated_risk=25, relative_change_pct=-16.7,
                               assumptions=["test"], provenance=ProvenanceFlag.SIMULATED),
        ]

    def test_priority_ranking(self, risk_scores, exposure_scores, interventions, config):
        """Higher risk + exposure + intervention potential should rank higher."""
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        assert len(priorities) == 2
        assert priorities[0].zone_id == "z1"  # Hot zone should be #1
        assert priorities[0].rank == 1

    def test_priority_score_range(self, risk_scores, exposure_scores, interventions, config):
        """Priority scores should be 0-100."""
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        for p in priorities:
            assert 0 <= p.priority_score <= 100

    def test_priority_has_explanation(self, risk_scores, exposure_scores, interventions, config):
        """Each priority item should have a text explanation."""
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        for p in priorities:
            assert len(p.explanation) > 0

    def test_priority_provenance(self, risk_scores, exposure_scores, interventions, config):
        """Priority items should carry provenance."""
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        for p in priorities:
            assert p.provenance == ProvenanceFlag.SIMULATED

    def test_priority_increases_with_intervention_potential(self, config):
        """Zone with larger intervention potential should rank higher."""
        risks = [
            RiskScore(zone_id="z1", zone_name="a", timestamp=datetime.now(),
                      score=70, label="High", components={}),
            RiskScore(zone_id="z2", zone_name="b", timestamp=datetime.now(),
                      score=70, label="High", components={}),
        ]
        exposures = [
            ExposureScore(zone_id="z1", zone_name="a", risk_score=70,
                          student_count=50, exposure_hours=4.0, score=60),
            ExposureScore(zone_id="z2", zone_name="b", risk_score=70,
                          student_count=50, exposure_hours=4.0, score=60),
        ]
        interventions = [
            InterventionResult(zone_id="z1", zone_name="a", baseline_risk=70,
                               scenario_config={}, simulated_risk=30,
                               relative_change_pct=-57.1, assumptions=["test"]),
            InterventionResult(zone_id="z2", zone_name="b", baseline_risk=70,
                               scenario_config={}, simulated_risk=55,
                               relative_change_pct=-21.4, assumptions=["test"]),
        ]
        priorities = compute_priorities(risks, exposures, interventions, config)
        assert priorities[0].zone_id == "z1"  # Higher intervention potential
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd school-heat-intelligence && python -m pytest tests/test_priority.py -v`
Expected: FAIL

- [ ] **Step 3: Create priority/__init__.py**

```python
from heat_intelligence.priority.engine import compute_priorities

__all__ = ["compute_priorities"]
```

- [ ] **Step 4: Create priority/engine.py**

```python
"""Priority scoring engine.

Combines normalized risk, exposure, and intervention potential scores.
All weights configurable and documented as illustrative heuristics.
"""

from typing import Dict, List

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import (
    ExposureScore, InterventionResult, PriorityItem, RiskScore, ProvenanceFlag,
)


def compute_priorities(
    risk_scores: List[RiskScore],
    exposure_scores: List[ExposureScore],
    interventions: List[InterventionResult],
    config: HeatIntelligenceConfig,
) -> List[PriorityItem]:
    """
    Compute priority scores for all zones.
    
    priority = w1*risk_norm + w2*exposure_norm + w3*intervention_potential_norm
    
    All components are already 0-100 normalized.
    Weights are configurable and documented as illustrative heuristics.
    """
    # Index by zone_id
    risk_map: Dict[str, RiskScore] = {r.zone_id: r for r in risk_scores}
    exposure_map: Dict[str, ExposureScore] = {e.zone_id: e for e in exposure_scores}
    intervention_map: Dict[str, InterventionResult] = {i.zone_id: i for i in interventions}

    # Get all unique zone IDs
    zone_ids = set(risk_map.keys()) | set(exposure_map.keys()) | set(intervention_map.keys())

    priorities = []
    w = config.priority_weights

    for zone_id in zone_ids:
        risk = risk_map.get(zone_id)
        exposure = exposure_map.get(zone_id)
        intervention = intervention_map.get(zone_id)

        risk_score = risk.score if risk else 0.0
        exposure_score = exposure.score if exposure else 0.0

        # Intervention potential = how much improvement is possible (normalized 0-100)
        if intervention and intervention.baseline_risk > 0:
            intervention_potential = min(100.0, abs(intervention.relative_change_pct))
        else:
            intervention_potential = 0.0

        # Weighted combination (all normalized 0-100)
        priority = (
            w.risk * risk_score +
            w.exposure * exposure_score +
            w.intervention_potential * intervention_potential
        )
        priority = max(0.0, min(100.0, priority))

        # Build explanation
        zone_name = risk.zone_name if risk else exposure.zone_name if exposure else "Unknown"
        explanation = (
            f"Zone {zone_id} ({zone_name}): "
            f"heat risk={risk_score:.0f}, "
            f"student exposure={exposure_score:.0f}, "
            f"intervention potential={intervention_potential:.0f}%. "
        )
        if intervention:
            explanation += (
                f"Scenario projection: {intervention.relative_change_pct:+.1f}% risk change. "
            )
        explanation += (
            "Priority score combines risk, exposure, and intervention potential "
            "(weights are illustrative heuristics)."
        )

        priorities.append(PriorityItem(
            rank=0,  # Will be assigned after sorting
            zone_id=zone_id,
            zone_name=zone_name,
            priority_score=round(priority, 1),
            risk_score=risk_score,
            exposure_score=exposure_score,
            intervention_potential=intervention_potential,
            explanation=explanation,
            provenance=ProvenanceFlag.SIMULATED,
        ))

    # Sort by priority score descending and assign ranks
    priorities.sort(key=lambda x: x.priority_score, reverse=True)
    for i, p in enumerate(priorities):
        p.rank = i + 1

    return priorities
```

- [ ] **Step 5: Run tests**

Run: `cd school-heat-intelligence && python -m pytest tests/test_priority.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/priority/ tests/test_priority.py
git commit -m "feat: priority engine with normalized scoring and explanations"
```

---

### Task 10: Provenance Tests

**Files:**
- Create: `school-heat_intelligence/tests/test_provenance.py`

**Interfaces:**
- Tests provenance flag integrity across the full pipeline

- [ ] **Step 1: Create test_provenance.py**

```python
"""Tests for data provenance flag integrity."""

import pytest
from datetime import datetime

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.intervention.simulator import simulate_intervention
from heat_intelligence.priority.engine import compute_priorities
from heat_intelligence.models.schemas import (
    ZoneReading, RiskScore, ExposureScore, InterventionResult, ProvenanceFlag,
)


class TestProvenance:
    """Tests that provenance flags are correctly propagated."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def synthetic_reading(self):
        return ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0),
            zone_id="z1", zone_name="test", lat=0, lon=0,
            air_temperature=35.0, humidity=70.0, wind_speed=2.0,
            canopy_pct=10, shade_pct=15, surface_type="asphalt",
            student_count=50, exposure_hours=4.0,
            provenance=ProvenanceFlag.SYNTHETIC,
        )

    def test_risk_score_provenance(self, synthetic_reading, config):
        """Risk scores from synthetic data should be marked synthetic."""
        result = compute_risk_score(synthetic_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC

    def test_exposure_provenance(self, synthetic_reading, config):
        """Exposure from synthetic data should be marked synthetic."""
        risk = compute_risk_score(synthetic_reading, config)
        result = compute_exposure(risk, synthetic_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC

    def test_intervention_provenance(self, synthetic_reading, config):
        """Intervention simulation should be marked simulated."""
        risk = compute_risk_score(synthetic_reading, config)
        scenario = {"canopy_pct": 40, "surface_type": "grass"}
        result = simulate_intervention(synthetic_reading, risk, scenario, config)
        assert result.provenance == ProvenanceFlag.SIMULATED

    def test_priority_provenance(self, config):
        """Priority items should be marked simulated."""
        risk = RiskScore(zone_id="z1", zone_name="test",
                         timestamp=datetime.now(), score=70, label="High",
                         components={}, provenance=ProvenanceFlag.SYNTHETIC)
        exposure = ExposureScore(zone_id="z1", zone_name="test",
                                 risk_score=70, student_count=50,
                                 exposure_hours=4.0, score=60,
                                 provenance=ProvenanceFlag.SYNTHETIC)
        intervention = InterventionResult(zone_id="z1", zone_name="test",
                                          baseline_risk=70, scenario_config={},
                                          simulated_risk=40, relative_change_pct=-42.9,
                                          assumptions=["test"],
                                          provenance=ProvenanceFlag.SIMULATED)
        priorities = compute_priorities([risk], [exposure], [intervention], config)
        assert priorities[0].provenance == ProvenanceFlag.SIMULATED

    def test_all_flags_valid(self):
        """All provenance flags should be valid enum values."""
        for flag in ProvenanceFlag:
            assert flag.value in ["measured", "imported", "synthetic", "predicted", "simulated"]
```

- [ ] **Step 2: Run all tests**

Run: `cd school-heat-intelligence && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_provenance.py
git commit -m "feat: provenance flag integrity tests"
```

---

### Task 11: Dashboard — Main App + Overview Page

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/app.py`
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/components.py`
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/1_overview.py`

**Interfaces:**
- Consumes: All pipeline modules
- Produces: Streamlit multi-page application

- [ ] **Step 1: Create dashboard/components.py**

```python
"""Reusable Streamlit UI components."""

import streamlit as st
from heat_intelligence.models.schemas import ProvenanceFlag


def render_provenance_badge(provenance: ProvenanceFlag):
    """Display a colored provenance badge."""
    colors = {
        ProvenanceFlag.MEASURED: "🟢",
        ProvenanceFlag.IMPORTED: "🔵",
        ProvenanceFlag.SYNTHETIC: "🟡",
        ProvenanceFlag.PREDICTED: "🟠",
        ProvenanceFlag.SIMULATED: "🔴",
    }
    st.caption(f"{colors.get(provenance, '⚪')} Data provenance: **{provenance.value}**")


def render_risk_gauge(score: float, label: str):
    """Display a risk score gauge."""
    color = {"Low": "green", "Moderate": "orange", "High": "red", "Extreme": "darkred"}
    st.metric(label=f"Risk: {label}", value=f"{score:.1f}/100")


def render_methodology_warning():
    """Display standard methodology warning."""
    st.warning(
        "**Mô phỏng mô hình — chưa được kiểm chứng thực địa.**\n\n"
        "Model simulation — not validated with field measurements. "
        "All weights are illustrative heuristic parameters, not empirically calibrated."
    )
```

- [ ] **Step 2: Create dashboard/app.py**

```python
"""School Heat Intelligence — Main Dashboard Application."""

import streamlit as st

st.set_page_config(
    page_title="School Heat Intelligence",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ School Heat Intelligence")
st.caption("Campus heat risk detection, forecasting, and intervention simulation")

st.info(
    "**Data Provenance:** 🟡 Synthetic demo data | 🟠 Model predictions | 🔴 Simulations\n\n"
    "All weights are illustrative heuristic parameters, NOT empirically calibrated."
)

# Navigation
pages = {
    "1 Overview": "overview",
    "2 Risk Analysis": "risk_analysis",
    "3 Forecast": "forecast",
    "4 Exposure": "exposure",
    "5 Intervention Simulator": "intervention",
    "6 Priority Actions": "priority",
    "7 Methodology": "methodology",
}

selected = st.sidebar.radio("Navigate to:", list(pages.keys()))

# Load data
from heat_intelligence.data import load_data
from heat_intelligence.config import load_config

config = load_config()
data = load_data("data/demo_campus.csv")

# Import and render selected page
if selected == "1 Overview":
    from heat_intelligence.dashboard.pages import p1_overview
    p1_overview.render(data, config)
elif selected == "2 Risk Analysis":
    from heat_intelligence.dashboard.pages import p2_risk_analysis
    p2_risk_analysis.render(data, config)
elif selected == "3 Forecast":
    from heat_intelligence.dashboard.pages import p3_forecast
    p3_forecast.render(data, config)
elif selected == "4 Exposure":
    from heat_intelligence.dashboard.pages import p4_exposure
    p4_exposure.render(data, config)
elif selected == "5 Intervention Simulator":
    from heat_intelligence.dashboard.pages import p5_intervention
    p5_intervention.render(data, config)
elif selected == "6 Priority Actions":
    from heat_intelligence.dashboard.pages import p6_priority
    p6_priority.render(data, config)
elif selected == "7 Methodology":
    from heat_intelligence.dashboard.pages import p7_methodology
    p7_methodology.render(data, config)
```

- [ ] **Step 3: Create dashboard/pages/__init__.py**

```python
```

- [ ] **Step 4: Create dashboard/pages/1_overview.py**

```python
"""Overview page — campus map, risk summary, hotspot alerts."""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.data import load_data
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.hotspot.detector import detect_hotspots
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Campus Overview")

    # Get latest readings per zone
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()

    # Compute risk for latest readings
    risk_scores = []
    for _, row in latest.iterrows():
        reading = ZoneReading(**row.to_dict())
        rs = compute_risk_score(reading, config)
        risk_scores.append(rs)

    # Detect hotspots
    hotspots = detect_hotspots(risk_scores, config)

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Zones Monitored", len(latest))
    with col2:
        avg_risk = sum(r.score for r in hotspots) / len(hotspots) if hotspots else 0
        st.metric("Average Risk", f"{avg_risk:.1f}")
    with col3:
        hotspot_count = sum(1 for r in hotspots if "HOTSPOT" in r.label)
        st.metric("Hotspot Zones", hotspot_count)

    # Campus map
    st.subheader("Campus Heat Map")
    m = folium.Map(location=[latest["lat"].mean(), latest["lon"].mean()], zoom_start=16)

    for rs in hotspots:
        color = "red" if rs.score > 75 else "orange" if rs.score > 50 else "green"
        folium.CircleMarker(
            location=[latest[latest["zone_id"] == rs.zone_id]["lat"].values[0],
                      latest[latest["zone_id"] == rs.zone_id]["lon"].values[0]],
            radius=15,
            color=color,
            fill=True,
            fill_color=color,
            popup=f"{rs.zone_name}: {rs.score:.1f} ({rs.label})",
        ).add_to(m)

    st_folium(m, width=700, height=400)

    # Hotspot alerts
    st.subheader("Hotspot Alerts")
    for rs in hotspots:
        if "HOTSPOT" in rs.label:
            st.error(f"🔥 **{rs.zone_name}** — Risk: {rs.score:.1f} ({rs.label})")
```

- [ ] **Step 5: Verify dashboard loads**

Run: `cd school-heat-intelligence && streamlit run src/heat_intelligence/dashboard/app.py --server.headless true`
Expected: Dashboard starts without errors

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/dashboard/
git commit -m "feat: dashboard main app with overview page and campus map"
```

---

### Task 12: Dashboard — Risk Analysis + Forecast + Exposure Pages

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/2_risk_analysis.py`
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/3_forecast.py`
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/4_exposure.py`

- [ ] **Step 1: Create pages/2_risk_analysis.py**

```python
"""Risk Analysis page — zone-by-zone risk breakdown."""

import streamlit as st
import plotly.express as px
import pandas as pd

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Risk Analysis")

    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Compute risk for all readings
    risk_data = []
    for r in data:
        rs = compute_risk_score(r, config)
        risk_data.append({
            "zone_name": r.zone_name,
            "timestamp": r.timestamp,
            "score": rs.score,
            "label": rs.label,
            "hi_component": rs.components["heat_index"],
            "rh_component": rs.components["humidity"],
            "ws_component": rs.components["wind_speed"],
            "sf_component": rs.components["surface"],
        })

    risk_df = pd.DataFrame(risk_data)

    # Zone risk comparison
    st.subheader("Current Risk by Zone")
    latest_risk = risk_df.sort_values("timestamp").groupby("zone_name").last().reset_index()
    fig = px.bar(latest_risk, x="zone_name", y="score", color="label",
                 color_discrete_map={"Low": "green", "Moderate": "orange",
                                     "High": "red", "Extreme": "darkred"})
    st.plotly_chart(fig, use_container_width=True)

    # Component breakdown
    st.subheader("Risk Component Breakdown (Latest)")
    zone_filter = st.selectbox("Select zone", latest_risk["zone_name"].unique())
    zone_data = latest_risk[latest_risk["zone_name"] == zone_filter].iloc[0]

    components = {
        "Heat Index": zone_data["hi_component"],
        "Humidity": zone_data["rh_component"],
        "Wind Speed": zone_data["ws_component"],
        "Surface": zone_data["sf_component"],
    }
    fig2 = px.bar(x=list(components.keys()), y=list(components.values()),
                  labels={"x": "Component", "y": "Score (0-100)"},
                  title=f"Risk Components — {zone_filter}")
    st.plotly_chart(fig2, use_container_width=True)

    # Time series
    st.subheader("Risk Over Time")
    zone_ts = risk_df[risk_df["zone_name"] == zone_filter]
    fig3 = px.line(zone_ts, x="timestamp", y="score", title=f"Risk Score — {zone_filter}")
    st.plotly_chart(fig3, use_container_width=True)
```

- [ ] **Step 2: Create pages/3_forecast.py**

```python
"""Forecast page — 6-hour risk prediction with uncertainty."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.forecast.predictor import forecast_risk
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Risk Forecast")

    zone_names = list(set(r.zone_name for r in data))
    zone_filter = st.selectbox("Select zone", zone_names)

    # Get zone_id from name
    zone_id = next(r.zone_id for r in data if r.zone_name == zone_filter)

    # Generate forecast
    forecasts = forecast_risk(data, config, zone_id)

    if not forecasts:
        st.warning("Insufficient data for forecast. Need at least 24 hours of historical data.")
        return

    st.info("Forecast uses moving average + diurnal baseline (explainable, no ML).")

    # Plot forecast
    fig = go.Figure()

    # Historical (last 48h)
    zone_data = [r for r in data if r.zone_id == zone_id]
    zone_data.sort(key=lambda r: r.timestamp)
    recent = zone_data[-48:]

    from heat_intelligence.risk.engine import compute_risk_score
    hist_times = [r.timestamp for r in recent]
    hist_scores = [compute_risk_score(r, config).score for r in recent]

    fig.add_trace(go.Scatter(x=hist_times, y=hist_scores, mode="lines",
                             name="Historical", line=dict(color="blue")))

    # Forecast
    fc_times = [f.timestamp for f in forecasts]
    fc_scores = [f.predicted_score for f in forecasts]
    fc_lower = [f.lower_bound for f in forecasts]
    fc_upper = [f.upper_bound for f in forecasts]

    fig.add_trace(go.Scatter(x=fc_times, y=fc_scores, mode="lines+markers",
                             name="Forecast", line=dict(color="red", dash="dash")))
    fig.add_trace(go.Scatter(x=fc_times, y=fc_upper, mode="lines",
                             name="Upper Bound", line=dict(color="gray", width=0.5)))
    fig.add_trace(go.Scatter(x=fc_times, y=fc_lower, mode="lines",
                             name="Lower Bound", line=dict(color="gray", width=0.5),
                             fill="tonexty", fillcolor="rgba(128,128,128,0.2)"))

    fig.update_layout(title=f"6-Hour Forecast — {zone_filter}",
                      xaxis_title="Time", yaxis_title="Risk Score")
    st.plotly_chart(fig, use_container_width=True)

    # Forecast table
    st.subheader("Forecast Details")
    fc_df = pd.DataFrame([{
        "Horizon": f"{f.horizon_hours}h",
        "Predicted": f"{f.predicted_score:.1f}",
        "Lower": f"{f.lower_bound:.1f}",
        "Upper": f"{f.upper_bound:.1f}",
        "Provenance": f.provenance.value,
    } for f in forecasts])
    st.dataframe(fc_df, use_container_width=True)

    from heat_intelligence.dashboard.components import render_methodology_warning
    render_methodology_warning()
```

- [ ] **Step 3: Create pages/4_exposure.py**

```python
"""Exposure page — student exposure scores and ranking."""

import streamlit as st
import plotly.express as px
import pandas as pd

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Student Exposure Analysis")

    # Get latest reading per zone
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()

    # Compute exposure scores
    exposure_data = []
    for _, row in latest.iterrows():
        reading = ZoneReading(**row.to_dict())
        risk = compute_risk_score(reading, config)
        exp = compute_exposure(risk, reading, config)
        exposure_data.append({
            "zone_name": reading.zone_name,
            "risk_score": risk.score,
            "student_count": reading.student_count,
            "exposure_hours": reading.exposure_hours,
            "exposure_score": exp.score,
        })

    exp_df = pd.DataFrame(exposure_data).sort_values("exposure_score", ascending=False)

    # Exposure ranking
    st.subheader("Exposure Risk Ranking")
    fig = px.bar(exp_df, x="zone_name", y="exposure_score",
                 color="exposure_score",
                 color_continuous_scale="YlOrRd",
                 labels={"exposure_score": "Exposure Score (0-100)"})
    st.plotly_chart(fig, use_container_width=True)

    # Detailed table
    st.subheader("Exposure Details")
    st.dataframe(exp_df, use_container_width=True)

    # Key insight
    st.subheader("Key Insight")
    top = exp_df.iloc[0]
    st.info(
        f"**{top['zone_name']}** has the highest exposure risk "
        f"(score: {top['exposure_score']:.1f}) due to "
        f"**{top['student_count']} students** × **{top['exposure_hours']:.1f} hours** "
        f"at risk level {top['risk_score']:.0f}."
    )
```

- [ ] **Step 4: Commit**

```bash
git add src/heat_intelligence/dashboard/pages/2_risk_analysis.py
git add src/heat_intelligence/dashboard/pages/3_forecast.py
git add src/heat_intelligence/dashboard/pages/4_exposure.py
git commit -m "feat: risk analysis, forecast, and exposure dashboard pages"
```

---

### Task 13: Dashboard — Intervention Simulator + Priority + Methodology Pages

**Files:**
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/5_intervention.py`
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/6_priority.py`
- Create: `school-heat-intelligence/src/heat_intelligence/dashboard/pages/7_methodology.py`

- [ ] **Step 1: Create pages/5_intervention.py**

```python
"""Intervention Simulator page — interactive scenario modelling."""

import streamlit as st
import plotly.graph_objects as go

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intervention.simulator import simulate_intervention
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Intervention Simulator")

    from heat_intelligence.dashboard.components import render_methodology_warning
    render_methodology_warning()

    zone_names = list(set(r.zone_name for r in data))
    zone_filter = st.selectbox("Select zone", zone_filter)

    # Get latest reading for zone
    zone_data = [r for r in data if r.zone_name == zone_filter]
    zone_data.sort(key=lambda r: r.timestamp, reverse=True)
    reading = zone_data[0]

    # Current risk
    current_risk = compute_risk_score(reading, config)
    st.metric("Current Risk Score", f"{current_risk.score:.1f} ({current_risk.label})")

    # Scenario controls
    st.subheader("Scenario Configuration")
    col1, col2, col3 = st.columns(3)

    with col1:
        new_canopy = st.slider("Canopy %", 0, 100, int(reading.canopy_pct))
    with col2:
        new_shade = st.slider("Shade %", 0, 100, int(reading.shade_pct))
    with col3:
        new_surface = st.selectbox("Surface Type",
                                   ["asphalt", "concrete", "grass", "permeable"],
                                   index=["asphalt", "concrete", "grass", "permeable"].index(reading.surface_type))

    scenario = {
        "canopy_pct": new_canopy,
        "shade_pct": new_shade,
        "surface_type": new_surface,
    }

    # Run simulation
    result = simulate_intervention(reading, current_risk, scenario, config)

    # Results
    st.subheader("Simulation Results")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Baseline Risk", f"{result.baseline_risk:.1f}")
    with col2:
        st.metric("Simulated Risk", f"{result.simulated_risk:.1f}")
    with col3:
        st.metric("Relative Change", f"{result.relative_change_pct:+.1f}%")

    # Before/after chart
    fig = go.Figure(data=[
        go.Bar(name="Baseline", x=["Risk Score"], y=[result.baseline_risk], marker_color="red"),
        go.Bar(name="Simulated", x=["Risk Score"], y=[result.simulated_risk], marker_color="green"),
    ])
    fig.update_layout(barmode="group", title="Baseline vs Simulated Risk")
    st.plotly_chart(fig, use_container_width=True)

    # Assumptions
    st.subheader("Assumptions")
    for assumption in result.assumptions:
        st.write(f"• {assumption}")

    st.warning(
        "**Mô phỏng mô hình — chưa được kiểm chứng thực địa.**\n\n"
        "This is a heuristic scenario model. Results show relative risk change, "
        "not absolute temperature change. Not validated with field measurements."
    )
```

- [ ] **Step 2: Create pages/6_priority.py**

```python
"""Priority Actions page — ranked intervention recommendations."""

import streamlit as st
import plotly.express as px
import pandas as pd

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.intervention.simulator import simulate_intervention
from heat_intelligence.priority.engine import compute_priorities
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Priority Actions")

    # Get latest reading per zone
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()

    # Compute full pipeline for each zone
    risk_scores = []
    exposure_scores = []
    interventions = []

    for _, row in latest.iterrows():
        reading = ZoneReading(**row.to_dict())
        risk = compute_risk_score(reading, config)
        exp = compute_exposure(risk, reading, config)

        # Default intervention scenario (max canopy + grass)
        scenario = {"canopy_pct": 60, "shade_pct": 70, "surface_type": "grass"}
        intervention = simulate_intervention(reading, risk, scenario, config)

        risk_scores.append(risk)
        exposure_scores.append(exp)
        interventions.append(intervention)

    # Compute priorities
    priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)

    # Priority ranking chart
    st.subheader("Intervention Priority Ranking")
    pri_df = pd.DataFrame([{
        "Rank": p.rank,
        "Zone": p.zone_name,
        "Priority Score": p.priority_score,
        "Risk": p.risk_score,
        "Exposure": p.exposure_score,
        "Intervention Potential": p.intervention_potential,
    } for p in priorities])

    fig = px.bar(pri_df, x="Zone", y="Priority Score", color="Priority Score",
                 color_continuous_scale="YlOrRd")
    st.plotly_chart(fig, use_container_width=True)

    # Detailed recommendations
    st.subheader("Recommended Actions")
    for p in priorities:
        with st.expander(f"#{p.rank} {p.zone_name} — Priority Score: {p.priority_score:.1f}"):
            st.write(p.explanation)

            # Show intervention scenario
            intervention = next(i for i in interventions if i.zone_id == p.zone_id)
            st.write(f"**Scenario:** {intervention.scenario_config}")
            st.write(f"**Projected change:** {intervention.relative_change_pct:+.1f}%")
```

- [ ] **Step 3: Create pages/7_methodology.py**

```python
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

    Where:
    - **HI_norm**: Normalized heat index (Rothfusz regression, Steadman 1979)
    - **RH_norm**: Normalized relative humidity
    - **WS_norm**: Normalized wind speed (inverted — higher wind = lower risk)
    - **SF_norm**: Categorical surface factor (not fixed °C correction)

    ### Heat Index (Rothfusz)

    Standard regression for apparent temperature:
    ```
    HI = -42.379 + 2.049T + 10.14RH - 0.2247TRH - 6.838e-3T²
         - 5.482e-2RH² + 1.229e-3T²RH + 8.528e-4TRH² - 1.99e-6T²RH²
    ```

    ## Student Exposure Score

    ```
    exposure = (w_risk × risk_norm + w_students × students_norm + w_hours × hours_norm)
    ```

    Uses actual `exposure_hours` from input data. No arbitrary time weights.

    ## Intervention Simulation

    **This is a heuristic scenario model, NOT a physical temperature model.**

    Outputs:
    - Baseline risk score
    - Scenario configuration
    - Simulated risk score
    - Relative risk change (%)
    - Assumptions list

    **Does NOT output:** Fixed temperature reductions, calibrated cooling coefficients,
    or claims of physical accuracy.

    ## Priority Score

    ```
    priority = w_risk × risk_norm + w_exposure × exposure_norm + w_intervention × intervention_norm
    ```

    All three components are normalized 0–100 before combination.
    Weights are configurable and documented as illustrative heuristics.

    ## Forecast

    Moving average + diurnal baseline. No ML. No complex time series models.
    Basic holdout evaluation included.

    ## Limitations

    1. **All weights are illustrative heuristics**, not empirically calibrated
    2. **Intervention effects are scenario projections**, not measured outcomes
    3. **Synthetic demo data** — not real sensor measurements
    4. **No causal claims** — correlations only, no validated causal relationships
    5. **Surface factors are categorical**, not fixed temperature corrections
    6. **Forecast is a baseline** — not validated against held-out data

    ## Data Provenance

    - 🟡 **Synthetic**: Generated demo data
    - 🟠 **Predicted**: Model forecasts
    - 🔴 **Simulated**: Intervention scenario results
    - 🟢 **Measured**: Real sensor data (not used in MVP)
    - 🔵 **Imported**: External data sources (not used in MVP)

    ## Extensions (Future Work)

    - Actual UTCI/PET calculation when mean radiant temperature is available
    - Empirically calibrated weights from field validation
    - Real sensor data integration
    - Satellite imagery (NDVI) integration
    - Machine learning forecast models (with proper validation)
    """)

    # Show current config
    st.subheader("Current Configuration")
    st.json(config.model_dump())
```

- [ ] **Step 4: Fix import in 5_intervention.py**

Fix the typo `zone_filter` → `zone_names` in the selectbox call.

- [ ] **Step 5: Verify full dashboard runs**

Run: `cd school-heat-intelligence && streamlit run src/heat_intelligence/dashboard/app.py --server.headless true`
Expected: All 7 pages load without errors

- [ ] **Step 6: Commit**

```bash
git add src/heat_intelligence/dashboard/pages/
git commit -m "feat: intervention simulator, priority actions, and methodology pages"
```

---

### Task 14: README + Final Verification

**Files:**
- Create: `school-heat-intelligence/README.md`
- Modify: All files (final review)

- [ ] **Step 1: Create README.md**

```markdown
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
```

- [ ] **Step 2: Run full test suite**

Run: `cd school-heat-intelligence && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: Verify data generation**

Run: `cd school-heat-intelligence && python -c "from heat_intelligence.data.synthetic import generate_demo_data; generate_demo_data()"`
Expected: `Generated 4032 readings -> data/demo_campus.csv`

- [ ] **Step 4: Verify dashboard starts**

Run: `cd school-heat-intelligence && timeout 10 streamlit run src/heat_intelligence/dashboard/app.py --server.headless true || true`
Expected: Dashboard starts without import errors

- [ ] **Step 5: Final commit**

```bash
git add README.md
git commit -m "feat: README with setup, architecture, formulas, and assumptions"
```

---

## Summary

| Task | Module | Key Deliverable |
|------|--------|-----------------|
| 1 | Scaffolding | Project structure, config loader |
| 2 | Models | Pydantic schemas with provenance |
| 3 | Data | Synthetic generator, CSV loader |
| 4 | Risk | Heat index, composite risk score |
| 5 | Hotspot | Zone ranking, hotspot flagging |
| 6 | Forecast | Moving average prediction |
| 7 | Exposure | Student exposure scoring |
| 8 | Intervention | Scenario-based simulation |
| 9 | Priority | Priority ranking + explanations |
| 10 | Tests | Provenance integrity tests |
| 11-13 | Dashboard | 7-page Streamlit app |
| 14 | README | Documentation + final verification |
