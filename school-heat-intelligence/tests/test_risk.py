"""Tests for heat risk engine."""
import pytest
from datetime import datetime
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.heat_index import compute_heat_index
from heat_intelligence.risk.engine import compute_risk_score, normalize, normalize_risk_label
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag


class TestHeatIndex:
    def test_heat_index_low_temperature(self):
        hi = compute_heat_index(20.0, 50.0)
        assert 24 <= hi <= 26

    def test_heat_index_high_temperature(self):
        hi = compute_heat_index(40.0, 80.0)
        assert hi > 40

    def test_heat_index_extreme_conditions(self):
        hi = compute_heat_index(45.0, 90.0)
        assert hi > 50

    def test_heat_index_increases_with_humidity(self):
        hi_low = compute_heat_index(35.0, 40.0)
        hi_high = compute_heat_index(35.0, 90.0)
        assert hi_high > hi_low


class TestRiskScore:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def sample_reading(self):
        return ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0, 0),
            zone_id="zone_01", zone_name="playground",
            lat=40.7128, lon=-74.0060,
            air_temperature=35.0, humidity=70.0, wind_speed=2.0,
            canopy_pct=5, shade_pct=10, surface_type="asphalt",
            student_count=80, exposure_hours=1.0,
            provenance=ProvenanceFlag.SYNTHETIC,
        )

    def test_risk_score_range(self, sample_reading, config):
        result = compute_risk_score(sample_reading, config)
        assert 0 <= result.score <= 100

    def test_risk_score_label_mapping(self, sample_reading, config):
        result = compute_risk_score(sample_reading, config)
        if result.score <= 25:
            assert result.label == "Low"
        elif result.score <= 50:
            assert result.label == "Moderate"
        elif result.score <= 75:
            assert result.label == "High"
        else:
            assert result.label == "Extreme"

    def test_risk_score_increases_with_temperature(self, config):
        reading_cool = ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0, 0),
            zone_id="z1", zone_name="test", lat=0, lon=0,
            air_temperature=25.0, humidity=50.0, wind_speed=3.0,
            canopy_pct=50, shade_pct=50, surface_type="grass",
            student_count=10, exposure_hours=1.0,
        )
        reading_hot = ZoneReading(
            timestamp=datetime(2026, 7, 1, 12, 0, 0),
            zone_id="z2", zone_name="test", lat=0, lon=0,
            air_temperature=42.0, humidity=80.0, wind_speed=1.0,
            canopy_pct=0, shade_pct=0, surface_type="asphalt",
            student_count=10, exposure_hours=1.0,
        )
        score_cool = compute_risk_score(reading_cool, config)
        score_hot = compute_risk_score(reading_hot, config)
        assert score_hot.score > score_cool.score

    def test_risk_score_has_provenance(self, sample_reading, config):
        result = compute_risk_score(sample_reading, config)
        assert result.provenance == ProvenanceFlag.SYNTHETIC

    def test_risk_score_has_components(self, sample_reading, config):
        result = compute_risk_score(sample_reading, config)
        assert "heat_index" in result.components
        assert "humidity" in result.components
        assert "wind_speed" in result.components
        assert "surface" in result.components


class TestRiskLabel:
    def test_normalize_risk_label(self):
        assert normalize_risk_label(10) == "Low"
        assert normalize_risk_label(30) == "Moderate"
        assert normalize_risk_label(60) == "High"
        assert normalize_risk_label(85) == "Extreme"

    def test_normalize_risk_label_boundaries(self):
        assert normalize_risk_label(0) == "Low"
        assert normalize_risk_label(25) == "Low"
        assert normalize_risk_label(26) == "Moderate"
        assert normalize_risk_label(50) == "Moderate"
        assert normalize_risk_label(51) == "High"
        assert normalize_risk_label(75) == "High"
        assert normalize_risk_label(76) == "Extreme"
        assert normalize_risk_label(100) == "Extreme"


class TestNormalize:
    def test_normalize_midpoint(self):
        assert normalize(5.0, 0.0, 10.0) == pytest.approx(0.5)

    def test_normalize_below_min(self):
        assert normalize(-5.0, 0.0, 10.0) == 0.0

    def test_normalize_above_max(self):
        assert normalize(15.0, 0.0, 10.0) == 1.0

    def test_normalize_at_bounds(self):
        assert normalize(0.0, 0.0, 10.0) == 0.0
        assert normalize(10.0, 0.0, 10.0) == 1.0

    def test_normalize_inverted(self):
        assert normalize(0.0, 0.0, 10.0, invert=True) == 1.0
        assert normalize(10.0, 0.0, 10.0, invert=True) == 0.0
        assert normalize(5.0, 0.0, 10.0, invert=True) == pytest.approx(0.5)

    def test_normalize_equal_min_max(self):
        assert normalize(5.0, 5.0, 5.0) == 0.5

    def test_normalize_negative_range(self):
        assert normalize(-3.0, -10.0, 0.0) == pytest.approx(0.7)
        assert normalize(-10.0, -10.0, 0.0) == 0.0
        assert normalize(0.0, -10.0, 0.0) == 1.0