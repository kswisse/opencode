"""Simple moving average + diurnal baseline forecast. No ML."""
from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Optional
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


@dataclass
class ForecastEvaluation:
    """Evaluation metrics for forecast holdout test."""
    horizon_hours: int
    mae: float
    rmse: float
    n_samples: int


def evaluate_forecast(
    readings: List[ZoneReading],
    config: HeatIntelligenceConfig,
    zone_id: str,
    holdout_hours: int = 24,
) -> List[ForecastEvaluation]:
    """
    Evaluate forecast accuracy using a holdout test.

    Holds out the last `holdout_hours` of data, forecasts into that window,
    and computes MAE/RMSE per horizon where actual values exist.

    Args:
        readings: Full historical readings for the zone
        config: Configuration
        zone_id: Zone to evaluate
        holdout_hours: Number of hours to hold out (default 24)

    Returns:
        List of ForecastEvaluation, one per horizon
    """
    zone_readings = [r for r in readings if r.zone_id == zone_id]
    zone_readings.sort(key=lambda r: r.timestamp)

    if len(zone_readings) < holdout_hours + 24:
        return []

    # Split: train = all but last holdout_hours, test = last holdout_hours
    train_readings = zone_readings[:-holdout_hours]
    test_readings = zone_readings[-holdout_hours:]

    # Compute actual risk scores for test period
    actual_scores = {}
    for r in test_readings:
        rs = compute_risk_score(r, config)
        actual_scores[r.timestamp] = rs.score

    # Forecast from the end of training data
    forecasts = forecast_risk(train_readings, config, zone_id)
    if not forecasts:
        return []

    # For each horizon, find actual values and compute error
    evaluations = []
    for fc in forecasts:
        horizon = fc.horizon_hours
        # The forecast timestamp = last_train_timestamp + horizon
        # We need actual values at that timestamp
        forecast_time = fc.timestamp

        if forecast_time not in actual_scores:
            continue

        actual = actual_scores[forecast_time]
        error = fc.predicted_score - actual

        # Collect all forecasts at this horizon across the holdout window
        # by re-forecasting from different points
        errors_at_horizon = []

        # Re-forecast from each point in the holdout period that has enough history
        for i in range(len(train_readings), len(zone_readings)):
            sub_train = zone_readings[:i]
            if len(sub_train) < 24:
                continue
            sub_forecasts = forecast_risk(sub_train, config, zone_id)
            for sf in sub_forecasts:
                if sf.horizon_hours == horizon and sf.timestamp in actual_scores:
                    err = sf.predicted_score - actual_scores[sf.timestamp]
                    errors_at_horizon.append(err)

        if not errors_at_horizon:
            # Fallback: use single forecast error
            errors_at_horizon = [error]

        errors_arr = np.array(errors_at_horizon)
        mae = float(np.mean(np.abs(errors_arr)))
        rmse = float(np.sqrt(np.mean(errors_arr ** 2)))

        evaluations.append(ForecastEvaluation(
            horizon_hours=horizon,
            mae=round(mae, 2),
            rmse=round(rmse, 2),
            n_samples=len(errors_at_horizon),
        ))

    return evaluations
