"""Tests for data provenance flag integrity."""
import pytest
from datetime import datetime
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.intervention.simulator import simulate_intervention
from heat_intelligence.priority.engine import compute_priorities
from heat_intelligence.models.schemas import ZoneReading, RiskScore, ExposureScore, InterventionResult, ProvenanceFlag

class TestProvenance:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def synthetic_reading(self):
        return ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                           lat=0, lon=0, air_temperature=35.0, humidity=70.0, wind_speed=2.0,
                           canopy_pct=10, shade_pct=15, surface_type="asphalt",
                           student_count=50, exposure_hours=4.0,
                           provenance=ProvenanceFlag.SYNTHETIC)

    def test_risk_score_provenance(self, synthetic_reading, config):
        result = compute_risk_score(synthetic_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC

    def test_exposure_provenance(self, synthetic_reading, config):
        risk = compute_risk_score(synthetic_reading, config)
        result = compute_exposure(risk, synthetic_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC

    def test_intervention_provenance(self, synthetic_reading, config):
        risk = compute_risk_score(synthetic_reading, config)
        scenario = {"canopy_pct": 40, "surface_type": "grass"}
        result = simulate_intervention(synthetic_reading, risk, scenario, config)
        assert result.provenance == ProvenanceFlag.SIMULATED

    def test_priority_provenance(self, config):
        risk = RiskScore(zone_id="z1", zone_name="test", timestamp=datetime.now(),
                         score=70, label="High", components={}, provenance=ProvenanceFlag.SYNTHETIC)
        exposure = ExposureScore(zone_id="z1", zone_name="test", risk_score=70,
                                 student_count=50, exposure_hours=4.0, score=60,
                                 provenance=ProvenanceFlag.SYNTHETIC)
        intervention = InterventionResult(zone_id="z1", zone_name="test", baseline_risk=70,
                                          scenario_config={}, simulated_risk=40,
                                          relative_change_pct=-42.9, assumptions=["test"],
                                          provenance=ProvenanceFlag.SIMULATED)
        priorities = compute_priorities([risk], [exposure], [intervention], config)
        assert priorities[0].provenance == ProvenanceFlag.SIMULATED

    def test_all_flags_valid(self):
        for flag in ProvenanceFlag:
            assert flag.value in ["measured", "imported", "synthetic", "predicted", "simulated"]