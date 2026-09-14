"""Tests for intervention simulator."""
import pytest
from datetime import datetime
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.intervention.simulator import simulate_intervention
from heat_intelligence.models.schemas import RiskScore, ZoneReading, ProvenanceFlag
from heat_intelligence.risk.engine import compute_risk_score

class TestIntervention:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def reading(self):
        return ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                           lat=0, lon=0, air_temperature=38.0, humidity=75.0, wind_speed=1.5,
                           canopy_pct=5, shade_pct=10, surface_type="asphalt",
                           student_count=80, exposure_hours=4.0)

    @pytest.fixture
    def risk(self):
        return RiskScore(zone_id="z1", zone_name="test", timestamp=datetime(2026, 7, 1, 12, 0),
                         score=78.0, label="High", components={}, provenance=ProvenanceFlag.SYNTHETIC)

    def test_simulation_produces_result(self, reading, risk, config):
        scenario = {"canopy_pct": 40, "shade_pct": 50, "surface_type": "grass"}
        result = simulate_intervention(reading, risk, scenario, config)
        assert result is not None
        assert result.zone_id == "z1"

    def test_simulation_shows_baseline(self, reading, risk, config):
        scenario = {"canopy_pct": 40}
        result = simulate_intervention(reading, risk, scenario, config)
        assert result.baseline_risk == 78.0

    def test_simulation_has_assumptions(self, reading, risk, config):
        scenario = {"canopy_pct": 40}
        result = simulate_intervention(reading, risk, scenario, config)
        assert len(result.assumptions) > 0

    def test_simulation_provenance(self, reading, risk, config):
        scenario = {"canopy_pct": 40}
        result = simulate_intervention(reading, risk, scenario, config)
        assert result.provenance == ProvenanceFlag.SIMULATED

    def test_no_change_scenario(self, reading, config):
        baseline = compute_risk_score(reading, config)
        scenario = {"canopy_pct": 5, "shade_pct": 10, "surface_type": "asphalt"}
        result = simulate_intervention(reading, baseline, scenario, config)
        assert abs(result.simulated_risk - result.baseline_risk) < 5.0
