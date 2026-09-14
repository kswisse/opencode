"""Priority scoring engine. Combines normalized risk, exposure, and intervention potential."""
from typing import Dict, List
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import ExposureScore, InterventionResult, PriorityItem, RiskScore, ProvenanceFlag

def compute_priorities(
    risk_scores: List[RiskScore], exposure_scores: List[ExposureScore],
    interventions: List[InterventionResult], config: HeatIntelligenceConfig,
) -> List[PriorityItem]:
    risk_map: Dict[str, RiskScore] = {r.zone_id: r for r in risk_scores}
    exposure_map: Dict[str, ExposureScore] = {e.zone_id: e for e in exposure_scores}
    intervention_map: Dict[str, InterventionResult] = {i.zone_id: i for i in interventions}
    zone_ids = set(risk_map.keys()) | set(exposure_map.keys()) | set(intervention_map.keys())
    priorities = []
    w = config.priority_weights
    for zone_id in zone_ids:
        risk = risk_map.get(zone_id)
        exposure = exposure_map.get(zone_id)
        intervention = intervention_map.get(zone_id)
        risk_score = risk.score if risk else 0.0
        exposure_score = exposure.score if exposure else 0.0
        if intervention and intervention.baseline_risk > 0:
            intervention_potential = min(100.0, abs(intervention.relative_change_pct))
        else:
            intervention_potential = 0.0
        priority = (w.risk * risk_score + w.exposure * exposure_score + w.intervention_potential * intervention_potential)
        priority = max(0.0, min(100.0, priority))
        zone_name = risk.zone_name if risk else exposure.zone_name if exposure else "Unknown"
        explanation = (f"Zone {zone_id} ({zone_name}): heat risk={risk_score:.0f}, student exposure={exposure_score:.0f}, intervention potential={intervention_potential:.0f}%. ")
        if intervention:
            explanation += f"Scenario projection: {intervention.relative_change_pct:+.1f}% risk change. "
        explanation += "Priority score combines risk, exposure, and intervention potential (weights are illustrative heuristics)."
        priorities.append(PriorityItem(rank=0, zone_id=zone_id, zone_name=zone_name,
            priority_score=round(priority, 1), risk_score=risk_score, exposure_score=exposure_score,
            intervention_potential=intervention_potential, explanation=explanation,
            provenance=ProvenanceFlag.SIMULATED))
    priorities.sort(key=lambda x: x.priority_score, reverse=True)
    for i, p in enumerate(priorities):
        p.rank = i + 1
    return priorities
