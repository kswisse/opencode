"""Tests for config loader."""
import pytest
import yaml
from heat_intelligence.config import load_config, HeatIntelligenceConfig


class TestConfigLoader:
    def test_load_default(self):
        config = load_config("/nonexistent/path.yaml")
        assert isinstance(config, HeatIntelligenceConfig)
        assert config.risk_weights.heat_index == 0.5

    def test_load_valid_yaml(self, tmp_path):
        cfg = {
            "risk_weights": {"heat_index": 0.6, "humidity": 0.2},
            "hotspot_percentile": 80.0,
        }
        path = tmp_path / "config.yaml"
        path.write_text(yaml.dump(cfg))
        config = load_config(str(path))
        assert config.risk_weights.heat_index == 0.6
        assert config.risk_weights.humidity == 0.2
        assert config.hotspot_percentile == 80.0

    def test_load_partial_yaml_uses_defaults(self, tmp_path):
        cfg = {"risk_weights": {"heat_index": 0.7}}
        path = tmp_path / "config.yaml"
        path.write_text(yaml.dump(cfg))
        config = load_config(str(path))
        assert config.risk_weights.heat_index == 0.7
        assert config.risk_weights.humidity == 0.2  # default
        assert config.hotspot_percentile == 75.0  # default

    def test_load_empty_yaml_uses_defaults(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("")
        config = load_config(str(path))
        assert config.risk_weights.heat_index == 0.5

    def test_config_model_dump(self):
        config = HeatIntelligenceConfig()
        dumped = config.model_dump()
        assert "risk_weights" in dumped
        assert "forecast" in dumped
        assert "normalization" in dumped
