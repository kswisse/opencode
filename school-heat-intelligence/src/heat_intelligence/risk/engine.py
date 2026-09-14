"""Composite heat risk score engine.
WARNING: This is an illustrative heuristic composite index for MVP/decision-support.
Default weights are NOT empirically calibrated.
"""
from typing import Dict
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import RiskScore, ZoneReading, ProvenanceFlag
from heat_intelligence.risk.heat_index import compute_heat_index


def normalize(value: float, min_val: float, max_val: float, invert: bool = False) -> float:
    if max_val == min_val:
        return 0.5
    normalized = (value - min_val) / (max_val - min_val)
    normalized = max(0.0, min(1.0, normalized))
    if invert:
        normalized = 1.0 - normalized
    return normalized


def surface_factor(surface_type: str, config: HeatIntelligenceConfig) -> float:
    return config.surface_factors.get(surface_type, 0.5)


def normalize_risk_label(score: float) -> str:
    if score <= 25:
        return "Low"
    elif score <= 50:
        return "Moderate"
    elif score <= 75:
        return "High"
    else:
        return "Extreme"


def compute_risk_score(reading: ZoneReading, config: HeatIntelligenceConfig) -> RiskScore:
    norm = config.normalization
    hi = compute_heat_index(reading.air_temperature, reading.humidity)
    hi_norm = normalize(hi, norm.heat_index_min, norm.heat_index_max)
    rh_norm = normalize(reading.humidity, norm.humidity_min, norm.humidity_max)
    ws_norm = normalize(reading.wind_speed, norm.wind_speed_min, norm.wind_speed_max, invert=True)
    sf_norm = surface_factor(reading.surface_type, config)
    w = config.risk_weights
    score = (w.heat_index * hi_norm + w.humidity * rh_norm +
             w.wind_speed * ws_norm + w.surface * sf_norm) * 100
    score = max(0.0, min(100.0, score))
    return RiskScore(
        zone_id=reading.zone_id, zone_name=reading.zone_name,
        timestamp=reading.timestamp, score=round(score, 1),
        label=normalize_risk_label(score),
        components={"heat_index": round(hi_norm * 100, 1), "humidity": round(rh_norm * 100, 1),
                     "wind_speed": round(ws_norm * 100, 1), "surface": round(sf_norm * 100, 1)},
        provenance=ProvenanceFlag.SYNTHETIC,
    )
