"""Hotspot detection — rank zones by risk and flag hotspots."""
import copy
import numpy as np
from typing import List
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import RiskScore

def detect_hotspots(risk_scores: List[RiskScore], config: HeatIntelligenceConfig) -> List[RiskScore]:
    """Rank zones by risk score and flag hotspots above the percentile threshold.

    Returns a new list with copied RiskScore objects — input objects are NOT mutated.
    """
    if not risk_scores:
        return []

    sorted_scores = sorted(risk_scores, key=lambda x: x.score, reverse=True)
    scores_array = np.array([rs.score for rs in sorted_scores])
    threshold = np.percentile(scores_array, config.hotspot_percentile)

    result = []
    for rs in sorted_scores:
        rs_copy = rs.model_copy(deep=True)
        if rs_copy.score >= threshold:
            rs_copy.label = f"HOTSPOT: {rs_copy.label}"
        result.append(rs_copy)
    return result
