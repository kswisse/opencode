"""Tests for exposure calculator."""
import pytest
from datetime import datetime
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.exposure.calculator import compute_exposure
from heat_intelligence.models.schemas import RiskScore, ZoneReading, ProvenanceFlag

class TestExposure:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def high_risk(self):
        return RiskScore(zone_id="z1", zone_name="test", timestamp=datetime(2026, 7, 1, 12, 0),
                         score=85.0, label="Extreme", components={}, provenance=ProvenanceFlag.SYNTHETIC)

    @pytest.fixture
    def low_risk(self):
        return RiskScore(zone_id="z2", zone_name="test2", timestamp=datetime(2026, 7, 1, 12, 0),
                         score=20.0, label="Low", components={}, provenance=ProvenanceFlag.SYNTHETIC)

    @pytest.fixture
    def reading_high_exposure(self):
        return ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                           lat=0, lon=0, air_temperature=40.0, humidity=80.0, wind_speed=1.0,
                           canopy_pct=0, shade_pct=0, surface_type="asphalt",
                           student_count=120, exposure_hours=6.0)

    @pytest.fixture
    def reading_low_exposure(self):
        return ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z2", zone_name="test2",
                           lat=0, lon=0, air_temperature=25.0, humidity=50.0, wind_speed=3.0,
                           canopy_pct=50, shade_pct=50, surface_type="grass",
                           student_count=5, exposure_hours=1.0)

    def test_exposure_score_range(self, high_risk, reading_high_exposure, config):
        result = compute_exposure(high_risk, reading_high_exposure, config)
        assert 0 <= result.score <= 100

    def test_high_exposure_scores_higher(self, high_risk, low_risk, reading_high_exposure, reading_low_exposure, config):
        high = compute_exposure(high_risk, reading_high_exposure, config)
        low = compute_exposure(low_risk, reading_low_exposure, config)
        assert high.score > low.score

    def test_exposure_uses_actual_hours(self, high_risk, config):
        reading = ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                              lat=0, lon=0, air_temperature=40.0, humidity=80.0, wind_speed=1.0,
                              canopy_pct=0, shade_pct=0, surface_type="asphalt",
                              student_count=50, exposure_hours=8.0)
        result = compute_exposure(high_risk, reading, config)
        assert result.exposure_hours == 8.0

    def test_exposure_provenance(self, high_risk, reading_high_exposure, config):
        result = compute_exposure(high_risk, reading_high_exposure, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC
