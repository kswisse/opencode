"""Research statistical analysis module.

Provides descriptive statistics, zone comparisons, correlation analysis,
regression analysis, effect sizes, forecast validation, and intervention
comparison for research data.

All functions return JSON-serializable dictionaries.
"""
from typing import Any, Dict, List, Optional
import numpy as np

from heat_intelligence.models.schemas import InterventionResult, ZoneReading


def descriptive_stats(data: List[ZoneReading]) -> Dict[str, Dict[str, float]]:
    """Compute descriptive statistics (mean, std, min, max) per zone."""
    zone_data: Dict[str, List[float]] = {}
    for r in data:
        zone_data.setdefault(r.zone_id, []).append(r.air_temperature)

    stats = {}
    for zone_id, temps in zone_data.items():
        arr = np.array(temps)
        stats[zone_id] = {
            "mean": round(float(np.mean(arr)), 2),
            "std": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0.0,
            "min": round(float(np.min(arr)), 2),
            "max": round(float(np.max(arr)), 2),
            "count": len(temps),
        }
    return stats


def zone_comparison(data: List[ZoneReading]) -> Dict[str, Any]:
    """Compare hot vs cool zone temperatures."""
    hot_temps = [r.air_temperature for r in data if r.zone_id in ("zone_01", "zone_04")]
    cool_temps = [r.air_temperature for r in data if r.zone_id in ("zone_02", "zone_05")]

    if not hot_temps or not cool_temps:
        return {"hot_mean": 0, "cool_mean": 0, "difference": 0, "cohens_d": 0}

    hot_arr = np.array(hot_temps)
    cool_arr = np.array(cool_temps)

    diff = float(np.mean(hot_arr) - np.mean(cool_arr))
    pooled_std = np.sqrt(
        (np.var(hot_arr, ddof=1) * (len(hot_arr) - 1) + np.var(cool_arr, ddof=1) * (len(cool_arr) - 1))
        / (len(hot_arr) + len(cool_arr) - 2)
    )
    d = diff / pooled_std if pooled_std > 0 else 0.0

    return {
        "hot_mean": round(float(np.mean(hot_arr)), 2),
        "cool_mean": round(float(np.mean(cool_arr)), 2),
        "difference": round(diff, 2),
        "cohens_d": round(float(d), 3),
        "hot_n": len(hot_arr),
        "cool_n": len(cool_arr),
    }


def correlation_analysis(data: List[ZoneReading]) -> Dict[str, Any]:
    """Compute Pearson and Spearman correlations between canopy, surface, and temperature."""
    canopy = np.array([r.canopy_pct for r in data])
    temp = np.array([r.air_temperature for r in data])

    # Surface as numeric (asphalt=0, concrete=1, grass=2)
    surface_map = {"asphalt": 0, "concrete": 1, "grass": 2, "permeable": 1.5}
    surface = np.array([surface_map.get(r.surface_type, 0.5) for r in data])

    # Pearson correlation
    pearson_canopy_temp = float(np.corrcoef(canopy, temp)[0, 1]) if len(canopy) > 1 else 0.0
    pearson_surface_temp = float(np.corrcoef(surface, temp)[0, 1]) if len(surface) > 1 else 0.0

    # Spearman (rank correlation) using numpy
    def _spearman(x: np.ndarray, y: np.ndarray) -> float:
        rank_x = np.argsort(np.argsort(x)).astype(float)
        rank_y = np.argsort(np.argsort(y)).astype(float)
        return float(np.corrcoef(rank_x, rank_y)[0, 1]) if len(x) > 1 else 0.0

    spearman_canopy_temp = _spearman(canopy, temp)
    spearman_surface_temp = _spearman(surface, temp)

    return {
        "pearson": {
            "canopy_temperature": round(pearson_canopy_temp, 4),
            "surface_temperature": round(pearson_surface_temp, 4),
        },
        "spearman": {
            "canopy_temperature": round(spearman_canopy_temp, 4),
            "surface_temperature": round(spearman_surface_temp, 4),
        },
        "n": len(data),
    }


def regression_analysis(data: List[ZoneReading]) -> Dict[str, Any]:
    """Simple linear regression: temperature ~ canopy_pct."""
    x = np.array([r.canopy_pct for r in data])
    y = np.array([r.air_temperature for r in data])

    if len(x) < 2:
        return {"slope": 0, "intercept": 0, "r_squared": 0, "n": len(x)}

    # OLS: y = slope * x + intercept
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    slope = float(np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2))
    intercept = float(y_mean - slope * x_mean)

    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)
    r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "r_squared": round(r_squared, 4),
        "n": len(data),
        "interpretation": f"Each 10% increase in canopy is associated with {abs(slope * 10):.2f}°C {'decrease' if slope < 0 else 'increase'} in temperature (illustrative, not causal).",
    }


def effect_sizes(data: List[ZoneReading]) -> Dict[str, Any]:
    """Compute Cohen's d for hot vs cool zones and asphalt vs grass."""
    hot_temps = np.array([r.air_temperature for r in data if r.zone_id in ("zone_01", "zone_04")])
    cool_temps = np.array([r.air_temperature for r in data if r.zone_id in ("zone_02", "zone_05")])
    asphalt_temps = np.array([r.air_temperature for r in data if r.surface_type == "asphalt"])
    grass_temps = np.array([r.air_temperature for r in data if r.surface_type == "grass"])

    def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
        if len(a) < 2 or len(b) < 2:
            return 0.0
        pooled = np.sqrt(
            (np.var(a, ddof=1) * (len(a) - 1) + np.var(b, ddof=1) * (len(b) - 1))
            / (len(a) + len(b) - 2)
        )
        return float((np.mean(a) - np.mean(b)) / pooled) if pooled > 0 else 0.0

    return {
        "hot_vs_cool": {
            "cohens_d": round(_cohens_d(hot_temps, cool_temps), 3),
            "hot_mean": round(float(np.mean(hot_temps)), 2) if len(hot_temps) > 0 else 0,
            "cool_mean": round(float(np.mean(cool_temps)), 2) if len(cool_temps) > 0 else 0,
            "hot_n": len(hot_temps),
            "cool_n": len(cool_temps),
        },
        "asphalt_vs_grass": {
            "cohens_d": round(_cohens_d(asphalt_temps, grass_temps), 3),
            "asphalt_mean": round(float(np.mean(asphalt_temps)), 2) if len(asphalt_temps) > 0 else 0,
            "grass_mean": round(float(np.mean(grass_temps)), 2) if len(grass_temps) > 0 else 0,
            "asphalt_n": len(asphalt_temps),
            "grass_n": len(grass_temps),
        },
    }


def forecast_validation(eval_results: List) -> Dict[str, Any]:
    """Summarize MAE/RMSE from holdout forecast evaluation."""
    if not eval_results:
        return {"horizons": [], "message": "No evaluation results available."}

    summaries = []
    for e in eval_results:
        summaries.append({
            "horizon_hours": e.horizon_hours,
            "mae": e.mae,
            "rmse": e.rmse,
            "n_samples": e.n_samples,
        })

    avg_mae = np.mean([s["mae"] for s in summaries])
    avg_rmse = np.mean([s["rmse"] for s in summaries])

    return {
        "horizons": summaries,
        "avg_mae": round(float(avg_mae), 2),
        "avg_rmse": round(float(avg_rmse), 2),
    }


def intervention_comparison(interventions: List[InterventionResult]) -> Dict[str, Any]:
    """Summarize intervention simulation results."""
    if not interventions:
        return {"interventions": [], "message": "No intervention results available."}

    results = []
    for iv in interventions:
        results.append({
            "zone_id": iv.zone_id,
            "zone_name": iv.zone_name,
            "baseline_risk": iv.baseline_risk,
            "simulated_risk": iv.simulated_risk,
            "relative_change_pct": iv.relative_change_pct,
        })

    avg_change = np.mean([r["relative_change_pct"] for r in results])

    return {
        "interventions": results,
        "avg_relative_change_pct": round(float(avg_change), 2),
    }
