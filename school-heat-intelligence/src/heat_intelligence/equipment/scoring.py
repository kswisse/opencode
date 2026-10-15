"""Heuristic equipment failure probability from SHI heat risk + usage.

WARNING: illustrative heuristic, NOT empirically calibrated.
Links campus heat (0-100 from risk engine) with equipment load and age
so one sensor stack serves both students and machines.
"""

from __future__ import annotations


def equipment_failure_probability(
    heat_risk_0_100: float,
    load_0_1: float = 0.5,
    age_years: float = 3.0,
) -> tuple[float, dict[str, float]]:
    """Return (probability 0-1, contributions). Higher heat/load/age -> higher p."""
    heat = max(0.0, min(100.0, heat_risk_0_100)) / 100.0
    load = max(0.0, min(1.0, load_0_1))
    age = max(0.0, min(10.0, age_years)) / 10.0
    # ponytail: fixed weights, recalibrate from field data when available
    p = heat * 0.5 + load * 0.3 + age * 0.2
    p = max(0.0, min(1.0, p))
    return round(p, 4), {
        "campus_heat": round(heat * 0.5, 4),
        "equipment_load": round(load * 0.3, 4),
        "equipment_age": round(age * 0.2, 4),
    }
