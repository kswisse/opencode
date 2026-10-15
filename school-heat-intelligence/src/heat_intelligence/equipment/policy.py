"""Cost-aware equipment risk policy (ported from FactoryGuard AI).

Pure policy module: no sklearn, no streamlit, no file I/O.
SHI is the root system; this module only classifies an equipment
failure probability into LOW / WATCH / HIGH and maps it to a
school-maintenance action.

Thresholds live only here.
"""

from __future__ import annotations

from enum import Enum

import numpy as np

THRESHOLD_WATCH: float = 0.05
THRESHOLD_COST_AWARE: float = 0.0895
THRESHOLD_DEFAULT: float = 0.50

RESEARCH_COSTS: dict[str, int] = {"FN": 100, "FP": 5, "TP": 1, "TN": 0}

POLICY_DISCLAIMER: str = "Demo policy thresholds — not a safety standard."
DECISION_DISCLAIMER: str = "AI output is decision support, not an autonomous maintenance command."


class RiskLevel(str, Enum):
    LOW = "LOW"
    WATCH = "WATCH"
    HIGH = "HIGH"

    @property
    def card_label(self) -> str:
        return f"{self.value} RISK"

    @property
    def color(self) -> str:
        return _RISK_COLORS[self.value]


_RISK_COLORS: dict[str, str] = {
    "LOW": "#3B9EFF",
    "WATCH": "#F5A623",
    "HIGH": "#E5484D",
}


ACTIONS: dict[RiskLevel, tuple[str, str]] = {
    RiskLevel.LOW: (
        "Continue Monitoring",
        "Equipment conditions look normal. Continue routine checks.",
    ),
    RiskLevel.WATCH: (
        "Inspect & Increase Monitoring",
        "Risk is elevated (heat + load + age). Inspect fans/AC/pumps "
        "and check more often during hot hours.",
    ),
    RiskLevel.HIGH: (
        "Schedule Maintenance",
        "Failure risk is elevated. Inspect the equipment and consider "
        "maintenance before the next hot spell.",
    ),
}


def classify(probability: float) -> RiskLevel:
    """p < 0.05 -> LOW; 0.05 <= p < 0.0895 -> WATCH; p >= 0.0895 -> HIGH."""
    if probability < THRESHOLD_WATCH:
        return RiskLevel.LOW
    if probability < THRESHOLD_COST_AWARE:
        return RiskLevel.WATCH
    return RiskLevel.HIGH


def expected_cost(y_true, y_prob, threshold: float,
                  costs: dict[str, int] | None = None) -> float:
    """Mean per-sample misclassification cost; pred = (y_prob >= threshold)."""
    if costs is None:
        costs = RESEARCH_COSTS
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    predicted = (y_prob >= threshold).astype(int)
    actual = y_true.astype(int)
    fn = np.logical_and(actual == 1, predicted == 0).sum()
    fp = np.logical_and(actual == 0, predicted == 1).sum()
    tp = np.logical_and(actual == 1, predicted == 1).sum()
    tn = np.logical_and(actual == 0, predicted == 0).sum()
    total = costs["FN"] * fn + costs["FP"] * fp + costs["TP"] * tp + costs["TN"] * tn
    return float(total) / max(len(y_true), 1)
