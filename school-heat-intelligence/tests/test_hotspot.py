"""Tests for hotspot detector."""
import pytest
from datetime import datetime
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.hotspot.detector import detect_hotspots
from heat_intelligence.models.schemas import RiskScore, ProvenanceFlag


class TestHotspotDetector:
    @pytest.fixture
    def config(self):
        return HeatIntelligenceConfig()

    @pytest.fixture
    def sample_scores(self):
        return [
            RiskScore(zone_id="z1", zone_name="Low", timestamp=datetime(2026, 7, 1),
                      score=20, label="Low", components={}, provenance=ProvenanceFlag.SYNTHETIC),
            RiskScore(zone_id="z2", zone_name="Medium", timestamp=datetime(2026, 7, 1),
                      score=50, label="Moderate", components={}, provenance=ProvenanceFlag.SYNTHETIC),
            RiskScore(zone_id="z3", zone_name="High", timestamp=datetime(2026, 7, 1),
                      score=80, label="High", components={}, provenance=ProvenanceFlag.SYNTHETIC),
            RiskScore(zone_id="z4", zone_name="Extreme", timestamp=datetime(2026, 7, 1),
                      score=95, label="Extreme", components={}, provenance=ProvenanceFlag.SYNTHETIC),
        ]

    def test_detect_hotspots_returns_results(self, sample_scores, config):
        results = detect_hotspots(sample_scores, config)
        assert len(results) == 4

    def test_detect_hotspots_sorted_descending(self, sample_scores, config):
        results = detect_hotspots(sample_scores, config)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_detect_hotspots_no_input_mutation(self, sample_scores, config):
        """Input RiskScore objects must NOT be mutated."""
        original_labels = [r.label for r in sample_scores]
        original_scores = [r.score for r in sample_scores]
        detect_hotspots(sample_scores, config)
        for i, rs in enumerate(sample_scores):
            assert rs.label == original_labels[i]
            assert rs.score == original_scores[i]

    def test_detect_hotspots_flags_top_quartile(self, sample_scores, config):
        results = detect_hotspots(sample_scores, config)
        hotspot_labels = [r.label for r in results if "HOTSPOT" in r.label]
        non_hotspot_labels = [r.label for r in results if "HOTSPOT" not in r.label]
        assert len(hotspot_labels) > 0
        assert len(non_hotspot_labels) > 0

    def test_detect_hotspots_empty(self, config):
        results = detect_hotspots([], config)
        assert results == []

    def test_detect_hotspots_single(self, config):
        scores = [RiskScore(zone_id="z1", zone_name="Solo", timestamp=datetime(2026, 7, 1),
                            score=50, label="Moderate", components={},
                            provenance=ProvenanceFlag.SYNTHETIC)]
        results = detect_hotspots(scores, config)
        assert len(results) == 1
