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
    def base_risk(self):
        return RiskScore(zone_id="z1", zone_name="test", timestamp=datetime(2026, 7, 1, 12, 0),
                         score=50.0, label="Moderate", components={}, provenance=ProvenanceFlag.SYNTHETIC)

    @pytest.fixture
    def high_risk(self):
        return RiskScore(zone_id="z1", zone_name="test", timestamp=datetime(2026, 7, 1, 12, 0),
                         score=85.0, label="Extreme", components={}, provenance=ProvenanceFlag.SYNTHETIC)

    @pytest.fixture
    def low_risk(self):
        return RiskScore(zone_id="z2", zone_name="test2", timestamp=datetime(2026, 7, 1, 12, 0),
                         score=20.0, label="Low", components={}, provenance=ProvenanceFlag.SYNTHETIC)

    @pytest.fixture
    def base_reading(self):
        return ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                           lat=0, lon=0, air_temperature=35.0, humidity=70.0, wind_speed=2.0,
                           canopy_pct=10, shade_pct=15, surface_type="concrete",
                           student_count=50, exposure_hours=4.0)

    def test_exposure_score_range(self, base_risk, base_reading, config):
        result = compute_exposure(base_risk, base_reading, config)
        assert 0 <= result.score <= 100

    def test_high_risk_increases_exposure(self, base_risk, high_risk, base_reading, config):
        low_exp = compute_exposure(base_risk, base_reading, config)
        high_exp = compute_exposure(high_risk, base_reading, config)
        assert high_exp.score > low_exp.score

    def test_more_students_increases_exposure(self, base_risk, config):
        few = ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                          lat=0, lon=0, air_temperature=35.0, humidity=70.0, wind_speed=2.0,
                          canopy_pct=10, shade_pct=15, surface_type="concrete",
                          student_count=10, exposure_hours=4.0)
        many = ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                           lat=0, lon=0, air_temperature=35.0, humidity=70.0, wind_speed=2.0,
                           canopy_pct=10, shade_pct=15, surface_type="concrete",
                           student_count=150, exposure_hours=4.0)
        exp_few = compute_exposure(base_risk, few, config)
        exp_many = compute_exposure(base_risk, many, config)
        assert exp_many.score > exp_few.score

    def test_more_hours_increases_exposure(self, base_risk, config):
        short = ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                            lat=0, lon=0, air_temperature=35.0, humidity=70.0, wind_speed=2.0,
                            canopy_pct=10, shade_pct=15, surface_type="concrete",
                            student_count=50, exposure_hours=1.0)
        long = ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                           lat=0, lon=0, air_temperature=35.0, humidity=70.0, wind_speed=2.0,
                           canopy_pct=10, shade_pct=15, surface_type="concrete",
                           student_count=50, exposure_hours=8.0)
        exp_short = compute_exposure(base_risk, short, config)
        exp_long = compute_exposure(base_risk, long, config)
        assert exp_long.score > exp_short.score

    def test_exposure_uses_actual_hours(self, base_risk, config):
        reading = ZoneReading(timestamp=datetime(2026, 7, 1, 12, 0), zone_id="z1", zone_name="test",
                              lat=0, lon=0, air_temperature=40.0, humidity=80.0, wind_speed=1.0,
                              canopy_pct=0, shade_pct=0, surface_type="asphalt",
                              student_count=50, exposure_hours=8.0)
        result = compute_exposure(base_risk, reading, config)
        assert result.exposure_hours == 8.0

    def test_exposure_provenance(self, base_risk, base_reading, config):
        result = compute_exposure(base_risk, base_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC
