"""Tests for forecast predictor."""
import pytest
from datetime import datetime, timedelta
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.forecast.predictor import forecast_risk
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag

class TestForecast:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def sample_readings(self):
        readings = []
        base = datetime(2026, 7, 1, 0, 0, 0)
        for day in range(7):
            for hour in range(24):
                ts = base + timedelta(days=day, hours=hour)
                readings.append(ZoneReading(
                    timestamp=ts, zone_id="z1", zone_name="test",
                    lat=0, lon=0, air_temperature=30.0 + 5 * (1 if 8 <= hour <= 18 else 0),
                    humidity=60.0, wind_speed=2.0, canopy_pct=20, shade_pct=30,
                    surface_type="concrete", student_count=50, exposure_hours=1.0,
                ))
        return readings

    def test_forecast_output_count(self, sample_readings, config):
        results = forecast_risk(sample_readings, config, zone_id="z1")
        assert len(results) > 0

    def test_forecast_has_bounds(self, sample_readings, config):
        results = forecast_risk(sample_readings, config, zone_id="z1")
        for r in results:
            assert r.lower_bound <= r.predicted_score <= r.upper_bound

    def test_forecast_provenance(self, sample_readings, config):
        results = forecast_risk(sample_readings, config, zone_id="z1")
        for r in results:
            assert r.provenance == ProvenanceFlag.PREDICTED

    def test_forecast_score_range(self, sample_readings, config):
        results = forecast_risk(sample_readings, config, zone_id="z1")
        for r in results:
            assert 0 <= r.predicted_score <= 100
            assert 0 <= r.lower_bound <= 100
            assert 0 <= r.upper_bound <= 100
