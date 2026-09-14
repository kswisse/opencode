"""Simple moving average + diurnal baseline forecast. No ML."""
from datetime import timedelta
from typing import List
import numpy as np
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import ForecastResult, ProvenanceFlag, ZoneReading
from heat_intelligence.risk.engine import compute_risk_score

def forecast_risk(readings: List[ZoneReading], config: HeatIntelligenceConfig, zone_id: str) -> List[ForecastResult]:
    zone_readings = [r for r in readings if r.zone_id == zone_id]
    if not zone_readings:
        return []
    zone_readings.sort(key=lambda r: r.timestamp)
    risk_scores = []
    for r in zone_readings:
        rs = compute_risk_score(r, config)
        risk_scores.append((r.timestamp, rs.score))
    if len(risk_scores) < 24:
        return []
    scores_array = np.array([s for _, s in risk_scores])
    last_timestamp = zone_readings[-1].timestamp
    window = min(config.forecast.window_hours, len(scores_array))
    recent_scores = scores_array[-window:]
    results = []
    for horizon in config.forecast.horizons:
        predicted = float(np.mean(recent_scores[-24:]))
        std = float(np.std(recent_scores[-48:])) if len(recent_scores) >= 48 else float(np.std(recent_scores))
        uncertainty = std * np.sqrt(horizon / 6.0)
        lower = max(0.0, predicted - uncertainty)
        upper = min(100.0, predicted + uncertainty)
        results.append(ForecastResult(
            zone_id=zone_id, zone_name=zone_readings[-1].zone_name,
            timestamp=last_timestamp + timedelta(hours=horizon),
            horizon_hours=horizon, predicted_score=round(predicted, 1),
            lower_bound=round(lower, 1), upper_bound=round(upper, 1),
            provenance=ProvenanceFlag.PREDICTED,
        ))
    return results
