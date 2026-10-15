"""Tests for equipment module (SHI root, FactoryGuard policy port)."""
import pytest
from heat_intelligence.equipment.policy import RiskLevel, classify, expected_cost
from heat_intelligence.equipment.scoring import equipment_failure_probability


class TestClassify:
    def test_boundaries(self):
        assert classify(0.0) == RiskLevel.LOW
        assert classify(0.0499) == RiskLevel.LOW
        assert classify(0.05) == RiskLevel.WATCH
        assert classify(0.0894) == RiskLevel.WATCH
        assert classify(0.0895) == RiskLevel.HIGH
        assert classify(1.0) == RiskLevel.HIGH


class TestScoring:
    def test_range(self):
        p, _ = equipment_failure_probability(50.0, 0.5, 3.0)
        assert 0.0 <= p <= 1.0

    def test_heat_increases_p(self):
        p_cool, _ = equipment_failure_probability(10.0, 0.5, 3.0)
        p_hot, _ = equipment_failure_probability(90.0, 0.5, 3.0)
        assert p_hot > p_cool

    def test_contributions_sum(self):
        p, contrib = equipment_failure_probability(80.0, 0.8, 5.0)
        assert sum(contrib.values()) == pytest.approx(p, abs=1e-3)


class TestExpectedCost:
    def test_cheap_threshold_wins_when_fn_costly(self):
        y_true = [0, 0, 0, 1]
        y_prob = [0.1, 0.2, 0.06, 0.3]
        assert expected_cost(y_true, y_prob, 0.0895) <= expected_cost(y_true, y_prob, 0.50)
