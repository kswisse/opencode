"""Tests for forecast predictor and evaluation."""
import pytest
from datetime import datetime, timedelta
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.forecast.predictor import forecast_risk, evaluate_forecast
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


class TestForecastEvaluation:
    """Tests for holdout-based forecast evaluation."""

    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def long_readings(self):
        """Generate 10 days of hourly data (enough for holdout)."""
        readings = []
        base = datetime(2026, 7, 1, 0, 0, 0)
        for day in range(10):
            for hour in range(24):
                ts = base + timedelta(days=day, hours=hour)
                readings.append(ZoneReading(
                    timestamp=ts, zone_id="z1", zone_name="test",
                    lat=0, lon=0,
                    air_temperature=30.0 + 5 * (1 if 8 <= hour <= 18 else 0),
                    humidity=60.0, wind_speed=2.0, canopy_pct=20, shade_pct=30,
                    surface_type="concrete", student_count=50, exposure_hours=1.0,
                ))
        return readings

    def test_evaluate_returns_results(self, long_readings, config):
        results = evaluate_forecast(long_readings, config, zone_id="z1", holdout_hours=24)
        assert len(results) > 0

    def test_evaluate_has_all_horizons(self, long_readings, config):
        results = evaluate_forecast(long_readings, config, zone_id="z1", holdout_hours=24)
        horizons = [e.horizon_hours for e in results]
        assert 1 in horizons
        assert 6 in horizons

    def test_evaluate_mae_non_negative(self, long_readings, config):
        results = evaluate_forecast(long_readings, config, zone_id="z1", holdout_hours=24)
        for e in results:
            assert e.mae >= 0

    def test_evaluate_rmse_non_negative(self, long_readings, config):
        results = evaluate_forecast(long_readings, config, zone_id="z1", holdout_hours=24)
        for e in results:
            assert e.rmse >= 0

    def test_evaluate_rmse_ge_mae(self, long_readings, config):
        """RMSE should always be >= MAE (property of the metrics)."""
        results = evaluate_forecast(long_readings, config, zone_id="z1", holdout_hours=24)
        for e in results:
            assert e.rmse >= e.mae - 0.01  # small tolerance for rounding

    def test_evaluate_n_samples_positive(self, long_readings, config):
        results = evaluate_forecast(long_readings, config, zone_id="z1", holdout_hours=24)
        for e in results:
            assert e.n_samples > 0

    def test_evaluate_insufficient_data(self, config):
        """With only 7 days, holdout of 24h should still work but less data."""
        readings = []
        base = datetime(2026, 7, 1, 0, 0, 0)
        for day in range(7):
            for hour in range(24):
                ts = base + timedelta(days=day, hours=hour)
                readings.append(ZoneReading(
                    timestamp=ts, zone_id="z1", zone_name="test",
                    lat=0, lon=0, air_temperature=30.0, humidity=60.0,
                    wind_speed=2.0, canopy_pct=20, shade_pct=30,
                    surface_type="concrete", student_count=50, exposure_hours=1.0,
                ))
        results = evaluate_forecast(readings, config, zone_id="z1", holdout_hours=24)
        assert isinstance(results, list)

    def test_evaluate_empty_for_short_data(self, config):
        """With only 10 readings, holdout should return empty."""
        readings = []
        base = datetime(2026, 7, 1, 0, 0, 0)
        for hour in range(10):
            ts = base + timedelta(hours=hour)
            readings.append(ZoneReading(
                timestamp=ts, zone_id="z1", zone_name="test",
                lat=0, lon=0, air_temperature=30.0, humidity=60.0,
                wind_speed=2.0, canopy_pct=20, shade_pct=30,
                surface_type="concrete", student_count=50, exposure_hours=1.0,
            ))
        results = evaluate_forecast(readings, config, zone_id="z1", holdout_hours=24)
        assert results == []
