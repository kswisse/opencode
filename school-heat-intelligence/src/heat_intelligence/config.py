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
        if data is not None:
            return HeatIntelligenceConfig(**data)
    return HeatIntelligenceConfig()
