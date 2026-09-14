"""Pydantic data models for School Heat Intelligence."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
    zone_id: str
    zone_name: str
    timestamp: datetime
    score: float = Field(ge=0, le=100, description="Composite heat risk score 0-100")
    label: str = Field(description="Risk label: Low|Moderate|High|Extreme")
    components: Dict[str, float] = Field(description="Individual component scores")
    provenance: ProvenanceFlag = ProvenanceFlag.SYNTHETIC


class ForecastResult(BaseModel):
    zone_id: str
    zone_name: str
    timestamp: datetime
    horizon_hours: int
    predicted_score: float = Field(ge=0, le=100)
    lower_bound: float = Field(ge=0, le=100)
    upper_bound: float = Field(ge=0, le=100)
    provenance: ProvenanceFlag = ProvenanceFlag.PREDICTED


class ExposureScore(BaseModel):
    zone_id: str
    zone_name: str
    risk_score: float = Field(ge=0, le=100)
    student_count: int = Field(ge=0)
    exposure_hours: float = Field(ge=0)
    score: float = Field(ge=0, le=100, description="Normalized exposure score 0-100")
    provenance: ProvenanceFlag = ProvenanceFlag.SYNTHETIC


class InterventionResult(BaseModel):
    zone_id: str
    zone_name: str
    baseline_risk: float = Field(ge=0, le=100)
    scenario_config: Dict[str, Any] = Field(description="Scenario input changes")
    simulated_risk: float = Field(ge=0, le=100)
    relative_change_pct: float = Field(description="Percentage change in risk")
    assumptions: List[str] = Field(description="List of assumptions used in simulation")
    provenance: ProvenanceFlag = ProvenanceFlag.SIMULATED


class PriorityItem(BaseModel):
    rank: int
    zone_id: str
    zone_name: str
    priority_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    exposure_score: float = Field(ge=0, le=100)
    intervention_potential: float = Field(ge=0, le=100)
    explanation: str = Field(description="Human-readable explanation")
    provenance: ProvenanceFlag = ProvenanceFlag.SIMULATED
