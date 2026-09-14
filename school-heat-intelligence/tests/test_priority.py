"""Tests for priority engine."""
import pytest
from datetime import datetime
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.priority.engine import compute_priorities
from heat_intelligence.models.schemas import RiskScore, ExposureScore, InterventionResult, ProvenanceFlag

class TestPriority:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def risk_scores(self):
        return [
            RiskScore(zone_id="z1", zone_name="hot_zone", timestamp=datetime(2026, 7, 1, 12),
                      score=85, label="Extreme", components={}, provenance=ProvenanceFlag.SYNTHETIC),
            RiskScore(zone_id="z2", zone_name="cool_zone", timestamp=datetime(2026, 7, 1, 12),
                      score=30, label="Moderate", components={}, provenance=ProvenanceFlag.SYNTHETIC),
        ]

    @pytest.fixture
    def exposure_scores(self):
        return [
            ExposureScore(zone_id="z1", zone_name="hot_zone", risk_score=85, student_count=100,
                          exposure_hours=6.0, score=80.0, provenance=ProvenanceFlag.SYNTHETIC),
            ExposureScore(zone_id="z2", zone_name="cool_zone", risk_score=30, student_count=10,
                          exposure_hours=1.0, score=25.0, provenance=ProvenanceFlag.SYNTHETIC),
        ]

    @pytest.fixture
    def interventions(self):
        return [
            InterventionResult(zone_id="z1", zone_name="hot_zone", baseline_risk=85,
                               scenario_config={}, simulated_risk=55, relative_change_pct=-35.3,
                               assumptions=["test"], provenance=ProvenanceFlag.SIMULATED),
            InterventionResult(zone_id="z2", zone_name="cool_zone", baseline_risk=30,
                               scenario_config={}, simulated_risk=25, relative_change_pct=-16.7,
                               assumptions=["test"], provenance=ProvenanceFlag.SIMULATED),
        ]

    def test_priority_ranking(self, risk_scores, exposure_scores, interventions, config):
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        assert len(priorities) == 2
        assert priorities[0].zone_id == "z1"
        assert priorities[0].rank == 1

    def test_priority_score_range(self, risk_scores, exposure_scores, interventions, config):
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        for p in priorities:
            assert 0 <= p.priority_score <= 100

    def test_priority_has_explanation(self, risk_scores, exposure_scores, interventions, config):
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        for p in priorities:
            assert len(p.explanation) > 0

    def test_priority_provenance(self, risk_scores, exposure_scores, interventions, config):
        priorities = compute_priorities(risk_scores, exposure_scores, interventions, config)
        for p in priorities:
            assert p.provenance == ProvenanceFlag.SIMULATED
