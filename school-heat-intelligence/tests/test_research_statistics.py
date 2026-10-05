"""Tests for research statistical analysis module."""
import pytest
from heat_intelligence.research.statistics import (
    descriptive_stats, zone_comparison, correlation_analysis,
    regression_analysis, effect_sizes, forecast_validation,
    intervention_comparison,
)
from heat_intelligence.research.synthetic_generator import generate_synthetic_environmental
from heat_intelligence.models.schemas import InterventionResult, ProvenanceFlag
from datetime import datetime


@pytest.fixture(scope="module")
def env_data():
    return generate_synthetic_environmental(seed=42, output_csv="data/test_stats_env.csv")


class TestDescriptiveStats:
    def test_returns_all_zones(self, env_data):
        stats = descriptive_stats(env_data)
        assert len(stats) == 5
        for zone_id in ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05"]:
            assert zone_id in stats

    def test_stats_have_required_fields(self, env_data):
        stats = descriptive_stats(env_data)
        for zone_id, s in stats.items():
            assert "mean" in s
            assert "std" in s
            assert "min" in s
            assert "max" in s
            assert "count" in s
            assert s["min"] <= s["mean"] <= s["max"]
            assert s["count"] > 0

    def test_temperature_range(self, env_data):
        stats = descriptive_stats(env_data)
        for zone_id, s in stats.items():
            assert 15.0 <= s["min"] <= 50.0
            assert 15.0 <= s["max"] <= 50.0


class TestZoneComparison:
    def test_returns_expected_keys(self, env_data):
        zc = zone_comparison(env_data)
        assert "hot_mean" in zc
        assert "cool_mean" in zc
        assert "difference" in zc
        assert "cohens_d" in zc

    def test_hot_warmer_than_cool(self, env_data):
        zc = zone_comparison(env_data)
        assert zc["hot_mean"] > zc["cool_mean"]
        assert zc["difference"] > 0


class TestCorrelationAnalysis:
    def test_returns_expected_structure(self, env_data):
        corr = correlation_analysis(env_data)
        assert "pearson" in corr
        assert "spearman" in corr
        assert "canopy_temperature" in corr["pearson"]
        assert "surface_temperature" in corr["pearson"]

    def test_canopy_negatively_correlated(self, env_data):
        corr = correlation_analysis(env_data)
        assert corr["pearson"]["canopy_temperature"] < 0

    def test_correlation_range(self, env_data):
        corr = correlation_analysis(env_data)
        for key in ["pearson", "spearman"]:
            for var in ["canopy_temperature", "surface_temperature"]:
                assert -1.0 <= corr[key][var] <= 1.0


class TestRegressionAnalysis:
    def test_returns_expected_keys(self, env_data):
        reg = regression_analysis(env_data)
        assert "slope" in reg
        assert "intercept" in reg
        assert "r_squared" in reg
        assert "n" in reg

    def test_slope_negative(self, env_data):
        reg = regression_analysis(env_data)
        assert reg["slope"] < 0  # more canopy = less temp

    def test_r_squared_non_negative(self, env_data):
        reg = regression_analysis(env_data)
        assert 0.0 <= reg["r_squared"] <= 1.0


class TestEffectSizes:
    def test_returns_expected_keys(self, env_data):
        es = effect_sizes(env_data)
        assert "hot_vs_cool" in es
        assert "asphalt_vs_grass" in es

    def test_hot_vs_cool_positive(self, env_data):
        es = effect_sizes(env_data)
        assert es["hot_vs_cool"]["cohens_d"] > 0

    def test_asphalt_warmer_than_grass(self, env_data):
        es = effect_sizes(env_data)
        assert es["asphalt_vs_grass"]["asphalt_mean"] > es["asphalt_vs_grass"]["grass_mean"]


class TestForecastValidation:
    def test_empty_results(self):
        result = forecast_validation([])
        assert "horizons" in result
        assert len(result["horizons"]) == 0

    def test_with_mock_results(self):
        from heat_intelligence.forecast.predictor import ForecastEvaluation
        mock_evals = [
            ForecastEvaluation(horizon_hours=1, mae=2.5, rmse=3.0, n_samples=10),
            ForecastEvaluation(horizon_hours=3, mae=4.0, rmse=5.0, n_samples=8),
        ]
        result = forecast_validation(mock_evals)
        assert len(result["horizons"]) == 2
        assert result["avg_mae"] == 3.25
        assert result["avg_rmse"] == 4.0


class TestInterventionComparison:
    def test_empty_results(self):
        result = intervention_comparison([])
        assert "interventions" in result
        assert len(result["interventions"]) == 0

    def test_with_mock_results(self):
        mock_iv = [
            InterventionResult(
                zone_id="zone_01", zone_name="Playground",
                baseline_risk=60.0, scenario_config={"canopy_pct": 30.0},
                simulated_risk=50.0, relative_change_pct=-16.7,
                assumptions=["test"], provenance=ProvenanceFlag.SIMULATED,
            ),
        ]
        result = intervention_comparison(mock_iv)
        assert len(result["interventions"]) == 1
        assert result["avg_relative_change_pct"] == -16.7
