"""Scenario-based intervention simulator.
WARNING: This is a heuristic model. Results are scenario projections, NOT measured outcomes.
Label: "Mô phỏng mô hình — chưa được kiểm chứng thực địa."
"""
from typing import Any, Dict, List
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import InterventionResult, RiskScore, ZoneReading, ProvenanceFlag
from heat_intelligence.risk.engine import compute_risk_score


def simulate_intervention(
    reading: ZoneReading, baseline_risk: RiskScore,
    scenario: Dict[str, Any], config: HeatIntelligenceConfig,
) -> InterventionResult:
    assumptions: List[str] = []
    modified_data = reading.model_dump()
    for key, value in scenario.items():
        if key in modified_data:
            modified_data[key] = value
    modified_reading = ZoneReading(**modified_data)
    simulated_risk = compute_risk_score(modified_reading, config)
    if baseline_risk.score > 0:
        relative_change = ((simulated_risk.score - baseline_risk.score) / baseline_risk.score) * 100
    else:
        relative_change = 0.0
    if "canopy_pct" in scenario:
        assumptions.append(f"Canopy cover changed from {reading.canopy_pct}% to {scenario['canopy_pct']}% (illustrative heuristic, not calibrated cooling coefficient)")
    if "shade_pct" in scenario:
        assumptions.append(f"Shade cover changed from {reading.shade_pct}% to {scenario['shade_pct']}% (illustrative heuristic)")
    if "surface_type" in scenario:
        assumptions.append(f"Surface type changed from {reading.surface_type} to {scenario['surface_type']} (categorical factor, not fixed °C correction)")
    assumptions.append("Scenario model is heuristic — not validated with field measurements")
    assumptions.append("Results show relative risk change, not absolute temperature change")
    return InterventionResult(
        zone_id=reading.zone_id, zone_name=reading.zone_name,
        baseline_risk=baseline_risk.score,
        scenario_config={k: float(v) if isinstance(v, (int, float)) else v for k, v in scenario.items()},
        simulated_risk=simulated_risk.score,
        relative_change_pct=round(relative_change, 1),
        assumptions=assumptions, provenance=ProvenanceFlag.SIMULATED,
    )
