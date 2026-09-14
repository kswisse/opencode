"""Student exposure score calculator. Uses actual exposure_hours from input data."""
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import ExposureScore, RiskScore, ZoneReading, ProvenanceFlag

def _normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

def compute_exposure(risk: RiskScore, reading: ZoneReading, config: HeatIntelligenceConfig) -> ExposureScore:
    norm = config.normalization
    risk_norm = risk.score
    students_norm = _normalize(reading.student_count, 0, norm.max_students) * 100
    hours_norm = _normalize(reading.exposure_hours, 0, norm.max_exposure_hours) * 100
    w = config.exposure_weights
    score = (w.risk * risk_norm + w.students * students_norm + w.hours * hours_norm)
    score = max(0.0, min(100.0, score))
    return ExposureScore(
        zone_id=reading.zone_id, zone_name=reading.zone_name,
        risk_score=risk.score, student_count=reading.student_count,
        exposure_hours=reading.exposure_hours, score=round(score, 1),
        provenance=ProvenanceFlag.SYNTHETIC,
    )
