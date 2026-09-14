"""Hotspot detection — rank zones by risk and flag hotspots."""
import numpy as np
from typing import List
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import RiskScore

def detect_hotspots(risk_scores: List[RiskScore], config: HeatIntelligenceConfig) -> List[RiskScore]:
    if not risk_scores:
        return []
    sorted_scores = sorted(risk_scores, key=lambda x: x.score, reverse=True)
    scores_array = np.array([rs.score for rs in sorted_scores])
    threshold = np.percentile(scores_array, config.hotspot_percentile)
    for rs in sorted_scores:
        rs.label = f"{'HOTSPOT: ' if rs.score >= threshold else ''}{rs.label}"
    return sorted_scores
