"""Hợp đồng tài liệu Phase 6: docs <-> design contract (R28, kernel-free).

Theo mẫu ``tests/unit/test_phase4_doc_contract.py``: heading bắt buộc,
token V1–V9, 8 tên ``plot_*``, hằng đóng băng ``149597870700`` — tất cả phải
hiện diện trong ``docs/methodology/phase6-visualization-design.md``.
Không import matplotlib, không đụng kernel.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "methodology" / "phase6-visualization-design.md"

REQUIRED_HEADINGS = [
    "Goal Capsule",
    "Product Contract",
    "Planning Contract",
    "Implementation Units",
    "Verification Contract",
    "Definition of Done",
]

REQUIRED_TOKENS = [f"V{i}" for i in range(1, 10)]  # V1..V9

REQUIRED_PLOTS = [
    "plot_trajectory",
    "plot_model_vs_reference",
    "plot_position_error",
    "plot_velocity_error",
    "plot_conservation",
    "plot_convergence",
    "plot_body_count",
    "plot_horizon_error",
]

FROZEN_CONSTANT = "149597870700"


def _missing(text: str) -> list[str]:
    missing: list[str] = []
    missing += [f"heading '## {h}'" for h in REQUIRED_HEADINGS if f"## {h}" not in text]
    missing += [f"token {t}" for t in REQUIRED_TOKENS if t not in text]
    missing += [f"plot name {p}" for p in REQUIRED_PLOTS if p not in text]
    if FROZEN_CONSTANT not in text:
        missing.append(f"frozen constant {FROZEN_CONSTANT}")
    return missing


def test_doc_satisfies_full_phase6_contract():
    text = DOC.read_text(encoding="utf-8")
    missing = _missing(text)
    assert not missing, f"phase6 doc missing contract items: {missing}"


def test_contract_catches_v9_removed_from_a_copy(tmp_path: Path):
    text = DOC.read_text(encoding="utf-8")
    assert _missing(text) == [], "baseline doc must be complete before mutation"
    copy = tmp_path / DOC.name
    copy.write_text(text.replace("V9", "VX"), encoding="utf-8")
    mutated = copy.read_text(encoding="utf-8")
    assert mutated != text, "doc unexpectedly lacks a V9 occurrence to strip"
    assert "token V9" in _missing(mutated), "contract failed to flag a dropped V9 token"
