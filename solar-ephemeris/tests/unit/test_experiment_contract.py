"""Hợp đồng thí nghiệm Phase 5 (design §7 row 4 — kernel-free).

Chống trôi grid/ngưỡng (R10): record schema đủ field §6d, output_hash tất
định trên BYTES mảng (không phải bytes npz), grid + ngưỡng đóng băng khớp
với ``docs/methodology/phase5-experiment-design.md``, và logic structural
gate của chuỗi E có chạy được thật (positive + negative check).

Import ``experiments.*`` cần repo root trên sys.path — Gate A chạy
``python -m pytest`` từ repo root; shim dưới đây cũng cho phép chạy ``pytest``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments import _common as C  # noqa: E402

DESIGN = REPO / "docs" / "methodology" / "phase5-experiment-design.md"


@pytest.fixture(scope="module")
def design_text() -> str:
    assert DESIGN.is_file(), f"design contract missing: {DESIGN}"
    return DESIGN.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Frozen grids == design document (code side AND doc side)
# ---------------------------------------------------------------------------


def test_frozen_grids_code_side():
    assert C.N_VALUES == (25, 50, 100, 200)
    assert C.A2_DIVISORS == (500, 1000, 2000, 4000)
    assert C.E_HORIZON_DAYS == (1, 30, 90, 365)
    assert C.TIER_T1 == ("Sun", "Earth")
    assert C.TIER_T2 == ("Sun", "Earth", "Moon")
    assert C.TIER_T3 == ("Sun", "Mercury", "Venus", "Earth", "Moon", "Mars")
    assert C.TIER_T4 == (
        "Sun", "Mercury", "Venus", "Earth", "Moon", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune",
    )  # correction #3: 10 standard bodies, Pluto excluded
    assert len(C.TIER_T4) == 10
    for tier in C.TIERS.values():
        assert "Pluto" not in tier
    assert C.C_SAMPLE_EVERY == 100
    assert C.C_CONTROL_SAMPLE_EVERY == 200
    assert C.E_SAMPLE_EVERY == 37


def test_frozen_thresholds_code_side():
    assert C.DT_EM == pytest.approx(2360.5915, abs=1e-3)
    assert C.DT_SE == pytest.approx(31558.1498, abs=1e-3)
    assert C.E_CONSERVATION_GATES == {
        "energy_rel_max": 1e-6,
        "momentum_rel_max": 1e-10,
        "angmom_rel_max": 1e-8,
    }
    assert C.VERLET_DRIFT_MAX == 1e-12
    assert C.C_SIGNAL_FACTOR == 10.0
    assert C.RK4_ORDER_WINDOW == (3.5, 4.5)
    assert C.VERLET_ORDER_WINDOW == (1.5, 2.5)
    assert C.A2_FLOOR_RATIO == 2.0
    assert C.IC_SOURCE_ANALYTIC == "analytic-circular"
    assert C.IC_SOURCE_REFERENCE == (
        "reference-ingested via ephemeris/ic.py (live de440s.bsp)"
    )
    assert C.REFERENCE_DATASET_STR == "JPL DE440 (de440s.bsp live)"


def test_roundoff_floor_is_the_phase_1_2_reuse(design_text: str):
    """Correction #5: floor REUSED verbatim, never re-derived to fit results."""
    assert C.ROUNDOFF_FLOOR_M == 1.5e11 * 2.0**-52
    assert 3.2e-5 < C.ROUNDOFF_FLOOR_M < 3.4e-5  # ≈ 3.3e-5 m @ 1 AU
    assert "3.3e-5" in design_text
    assert "1.5e11 × 2⁻⁵²" in design_text or "1.5e11 x 2^-52" in design_text


def test_design_doc_quotes_the_frozen_numbers(design_text: str):
    """Doc side of the contract: the same literals the code freezes."""
    for token in (
        "25, 50, 100, 200",
        "P_SE/4000",
        "P_SE/{500,1000,2000,4000}",
        "1 d → 30 d → 90 d → 365 d",
        "sample_every` chốt (100)",
        "sample_every = 200",
        "round(86400/dt) = 37",
        "1e-6",
        "1e-10",
        "1e-8",
        "1e-12",
        "10 × control",
        "[3.5, 4.5]",
        "[1.5, 2.5]",
        "APPROVED-WITH-CORRECTIONS",
    ):
        assert token in design_text, f"design doc missing frozen token: {token!r}"


# ---------------------------------------------------------------------------
# output_hash: deterministic over array bytes, insensitive to file bytes
# ---------------------------------------------------------------------------


def _sample_arrays():
    rng = np.random.default_rng(20261003)
    times = np.arange(7, dtype=np.float64) * 123.5
    positions = rng.normal(size=(7, 3, 3))
    velocities = rng.normal(size=(7, 3, 3))
    return times, positions, velocities


def test_output_hash_deterministic_and_content_sensitive(tmp_path: Path):
    times, positions, velocities = _sample_arrays()
    h1 = C.output_hash(times=times, positions=positions, velocities=velocities)
    h2 = C.output_hash(times=times, positions=positions, velocities=velocities)
    assert h1 == h2 and len(h1) == 64

    # npz round-trip: file bytes change, array bytes (and hash) must not.
    f = tmp_path / "a.npz"
    np.savez(f, times=times, positions=positions, velocities=velocities)
    with np.load(f, allow_pickle=False) as data:
        h3 = C.output_hash(
            times=data["times"],
            positions=data["positions"],
            velocities=data["velocities"],
        )
    assert h3 == h1

    # content sensitivity: one ulp in positions changes the hash
    mutated = positions.copy()
    mutated[0, 0, 0] = np.nextafter(mutated[0, 0, 0], np.inf)
    h4 = C.output_hash(times=times, positions=mutated, velocities=velocities)
    assert h4 != h1

    # channel order fixed: swapping channel contents changes the hash
    h5 = C.output_hash(times=times, positions=velocities, velocities=positions)
    assert h5 != h1


def test_gate_triple_shape():
    g = C.gate("x", threshold=1.0, measured=0.5, reason="r", passed=True)
    assert set(g) == {"name", "threshold", "measured", "reason", "passed"}
    assert g["passed"] is True


# ---------------------------------------------------------------------------
# Experiment record: §6d schema + gate triples + JSON round-trip
# ---------------------------------------------------------------------------


def _mini_record() -> dict:
    cfg = C.SimulationConfig(
        bodies=("Sun", "Earth"),
        integrator="rk4",
        dt=100.0,
        duration=1000.0,
        epoch_jd=C.EPOCH_JD,
    )
    return C.experiment_record(
        "T/test",
        cfg,
        initial_condition_source=C.IC_SOURCE_ANALYTIC,
        output_hash_value="ab" * 32,
        reproducible=True,
        runtime_s=(0.01, 0.01),
        reference_frame="analytic two-body exact (rigid rotation)",
        reference_origin="barycenter(Sun, Earth)",
        gates=[C.gate("g", threshold=1, measured=1, reason="r", passed=True)],
    )


def test_experiment_record_has_every_required_6d_field():
    record = _mini_record()
    for field in C.REQUIRED_RECORD_FIELDS:
        assert field in record, f"missing §6d field: {field}"
        if field.startswith("reference_") and record[field] is None:
            continue  # synthetic run: no reference dataset by design (§4)
        assert record[field] not in ("", None), f"empty §6d field: {field}"
    assert C.provenance_fields_present(record)
    assert record["units"] == "m, m/s, s"
    assert record["time_scale"] == "TDB"
    assert record["initial_condition_source"] == "analytic-circular"


def test_record_is_json_serializable_no_nan(tmp_path: Path):
    path = C.write_record(tmp_path / "r.json", _mini_record())
    back = json.loads(path.read_text(encoding="utf-8"))
    assert back["experiment_id"] == "T/test"
    assert back["gates"][0]["passed"] is True


def test_provenance_detects_missing_field():
    record = _mini_record()
    del record["output_hash"]
    assert not C.provenance_fields_present(record)


# ---------------------------------------------------------------------------
# Structural gates (§6b): runnable positive + negative check
# ---------------------------------------------------------------------------


def _tiny_sem_run(tmp_path: Path):
    from solar_ephemeris.simulation.initial_conditions import make_sun_earth_moon_ic

    ic = make_sun_earth_moon_ic()
    cfg = C.SimulationConfig(
        bodies=("Sun", "Earth", "Moon"),
        integrator="rk4",
        dt=1000.0,
        duration=10000.0,
        epoch_jd=C.EPOCH_JD,
    )
    rr = C.run_reproducible(cfg, ic.state(), tmp_path, sample_every=3)
    return cfg, rr


def test_structural_gates_pass_on_a_healthy_run(tmp_path: Path):
    cfg, rr = _tiny_sem_run(tmp_path / "healthy")
    gates = C.evaluate_structural_gates(
        traj=rr["traj"],
        second_traj=rr["traj_second"],
        config=cfg,
        sample_every=3,
        provenance_ok=True,
        provenance_measured="test",
    )
    assert len(gates) == 8  # 6 categories, conservation split into 4a/4b/4c
    assert C.gates_passed(gates), [g for g in gates if not g["passed"]]
    # conservation thresholds are the FROZEN §6b bounds (correction #1:
    # never derived from any observed E error)
    assert gates[3]["threshold"] == 1e-6
    assert gates[4]["threshold"] == 1e-10
    assert gates[5]["threshold"] == 1e-8
    # no E_pos/E_vel acceptance threshold anywhere in the gate set
    for g in gates:
        assert "E_pos" not in g["name"] and "E_vel" not in g["name"]


def test_structural_gate_catches_wrong_sample_grid(tmp_path: Path):
    cfg, rr = _tiny_sem_run(tmp_path / "grid")
    gates = C.evaluate_structural_gates(
        traj=rr["traj"],
        second_traj=rr["traj_second"],
        config=cfg,
        sample_every=5,  # wrong grid on purpose
        provenance_ok=True,
        provenance_measured="test",
    )
    completion = [g for g in gates if g["name"].startswith("3 ")]
    assert completion and not completion[0]["passed"]
    assert not C.gates_passed(gates)


def test_structural_gate_catches_nonfinite(tmp_path: Path):
    cfg, rr = _tiny_sem_run(tmp_path / "nonfinite")
    broken = rr["traj_second"]
    broken.positions[0, 0, 0] = np.nan
    gates = C.evaluate_structural_gates(
        traj=rr["traj"],
        second_traj=broken,
        config=cfg,
        sample_every=3,
        provenance_ok=True,
        provenance_measured="test",
    )
    assert gates[0]["passed"]  # first run itself is finite
    assert not gates[1]["passed"]  # item 2: reproducibility broken
    assert not C.gates_passed(gates)


# ---------------------------------------------------------------------------
# Gap 1: momentum diagnostics promoted, old test imports them
# ---------------------------------------------------------------------------


def test_momentum_promoted_and_test_conservation_imports_it():
    from solar_ephemeris.analysis import angular_momentum_series, momentum_series

    assert callable(angular_momentum_series) and callable(momentum_series)
    text = (REPO / "tests" / "numerical" / "test_conservation.py").read_text(
        encoding="utf-8"
    )
    assert "from solar_ephemeris.analysis.momentum import" in text


# ---------------------------------------------------------------------------
# Growth classification (§6e): discrimination rule
# ---------------------------------------------------------------------------


def test_growth_classification_discriminates_clean_linear():
    t = np.arange(0, 11, dtype=np.float64)
    y = 2.0 * t
    result = C.growth_classification(t, y)
    assert result["discriminated"] and result["selected"] == "linear"


def test_growth_classification_no_discrimination_on_noise():
    t = np.arange(1, 8, dtype=np.float64)
    y = np.array([1.0, 1.4, 1.1, 1.6, 1.2, 1.7, 1.3])  # flat-ish, no winner
    result = C.growth_classification(t, y)
    assert not result["discriminated"]
    assert result["selected"] is None


def test_growth_classification_too_few_samples():
    result = C.growth_classification(np.array([0.0, 1.0]), np.array([0.0, 1.0]))
    assert not result["discriminated"]
    assert result["selected"] is None
