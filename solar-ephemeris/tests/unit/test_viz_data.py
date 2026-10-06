"""U2 - data layer contract: loader / normalize / data-gap.

Requirements: R3, R5, R9, R14, R30; KTD4, KTD5, KTD10.

Gate A cases build tiny synthetic JSON + NPZ fixtures under
``tmp_path/results/`` - no ``results/`` dependency, no kernel. The four
REAL-record smoke cases (exactly one record per shape: flat / per-body /
absent / reused, per R30) are marked ``real_kernel`` so the default run
stays green without the results tree present (R29); they read files only
and need NO spice kernel.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from solar_ephemeris.simulation.runner import load_trajectory_npz
from solar_ephemeris.visualization.gaps import GAP_KEYS, DataGapError, make_gap
from solar_ephemeris.visualization.loader import load_record, load_trajectory
from solar_ephemeris.visualization.normalize import NormalizedComparison, normalize_comparison

REPO = Path(__file__).resolve().parents[2]
REAL_RESULTS = REPO / "results"

#: Provenance fields the reduced "reused" record variant is missing
#: (mirrors results/experiment_D/T2_30d: 15 - 4 = 11 absent fields, R9).
MISSING_IN_REUSED = frozenset(
    {
        "epoch",
        "bodies",
        "integrator",
        "timestep",
        "duration",
        "reference_dataset",
        "reference_frame",
        "reference_origin",
        "time_scale",
        "units",
        "software_version",
    }
)


# ---------------------------------------------------------------------------
# Synthetic fixture builders (JSON + NPZ, small on purpose)
# ---------------------------------------------------------------------------


def _traj_meta_json() -> str:
    payload = {
        "state_meta": {
            "frame": "active_bodies_barycentric",
            "origin": "barycenter(Sun, Earth)",
            "epoch_jd": 2451545.0,
            "time_scale": "TDB",
            "length_unit": "m",
            "time_unit": "s",
            "velocity_unit": "m/s",
            "gm_unit": "m^3/s^2",
            "axis_note": "synthetic fixture",
        },
        "integrator": "rk4",
        "integrator_order": 4,
        "dt": 1.0,
        "sample_every": 1,
        "n_steps": 3,
        "config_hash": "synthetic-hash",
        "software_version": "0.1.0",
        "schema_version": 1,
    }
    return json.dumps(payload, sort_keys=True)


def _write_npz(record_dir: Path, *, bodies=("Sun", "Earth"), samples: int = 4) -> Path:
    """trajectory.npz in the exact shape run_to_file persists (no run_record.json)."""
    record_dir.mkdir(parents=True, exist_ok=True)
    n, m = len(bodies), samples
    positions = np.arange(m * n * 3, dtype=np.float64).reshape(m, n, 3) + 1.0e6
    path = record_dir / "trajectory.npz"
    np.savez(
        path,
        times=np.arange(m, dtype=np.float64) * 10.0,
        positions=positions,
        velocities=positions / 1.0e5,
        gm=np.full(n, 1.32712440041939e20, dtype=np.float64),
        body_names=np.array(bodies),
        traj_meta_json=np.array(_traj_meta_json()),
    )
    return path


def _flat_comparison() -> dict:
    """Flat single-body shape, mirroring results/experiment_A2/d1000."""
    return {
        "body": "Earth",
        "schema_version": 1,
        "times_s": [0.0, 1.0, 2.0],
        "position_error": [0.0, 10.0, 20.0],
        "velocity_error": [0.0, 0.1, 0.2],
        "model_metadata": {"body_names": ["Sun", "Earth"], "config_hash": "hash-A"},
    }


def _per_body_comparison() -> dict:
    """Per-body map shape, mirroring results/experiment_C/tier_T2."""
    return {
        "Earth": {
            "body": "Earth",
            "times_s": [0.0, 1.0],
            "position_error": [0.0, 10.0],
            "velocity_error": [0.0, 0.1],
        },
        "Moon": {
            "body": "Moon",
            "times_s": [0.0, 1.0],
            "position_error": [0.0, 11.0],
            "velocity_error": [0.0, 0.2],
        },
    }


def _full_record(configuration_hash: str = "hash-A", **over) -> dict:
    """Full section-6d record variant - every provenance field present."""
    record = {
        "schema_version": 1,
        "experiment_id": "X/full",
        "epoch": 2451545.0,
        "bodies": ["Sun", "Earth"],
        "initial_condition_source": "synthetic fixture",
        "integrator": "rk4",
        "timestep": 1.0,
        "duration": 4.0,
        "reference_dataset": "JPL DE440 (de440s.bsp live)",
        "reference_frame": "J2000",
        "reference_origin": "SSB(0)",
        "time_scale": "TDB",
        "units": "m, m/s, s",
        "software_version": "0.1.0",
        "configuration_hash": configuration_hash,
        "output_hash": "0" * 64,
    }
    record.update(over)
    return record


def _reused_record(target_rel: str, configuration_hash: str) -> dict:
    """Reduced record variant, mirroring results/experiment_D/T2_30d."""
    return {
        "schema_version": 1,
        "experiment_id": "D/T2_30d",
        "configuration_hash": configuration_hash,
        "output_hash": "1" * 64,
        "initial_condition_source": "synthetic fixture",
        "reused_from": target_rel,
        "run_label": "report-only",
    }


@pytest.fixture
def results_root(tmp_path: Path) -> Path:
    root = tmp_path / "results"
    root.mkdir()
    return root


def _write_record(results_root: Path, rel: str, payload: dict) -> Path:
    record_dir = results_root / rel
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "experiment_record.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return record_dir


# ---------------------------------------------------------------------------
# KTD4 - load_trajectory_npz (runner-level, npz only)
# ---------------------------------------------------------------------------


def test_load_trajectory_npz_rebuilds_trajectory_without_run_record(tmp_path: Path) -> None:
    npz = _write_npz(tmp_path / "bare_run")
    assert not (npz.parent / "run_record.json").exists()  # KTD4 tolerance
    traj = load_trajectory_npz(npz)
    assert traj.positions.shape == (4, 2, 3)
    assert traj.times.shape == (4,)
    assert traj.velocities.shape == (4, 2, 3)
    assert traj.body_names == ("Sun", "Earth")
    assert traj.meta.integrator == "rk4"
    assert traj.meta.state_meta.time_scale == "TDB"


def test_load_trajectory_npz_missing_array_raises_value_error(tmp_path: Path) -> None:
    path = tmp_path / "partial.npz"
    np.savez(path, times=np.arange(3.0))
    with pytest.raises(ValueError, match="missing"):
        load_trajectory_npz(path)


# ---------------------------------------------------------------------------
# Loader - records + trajectory through the viz data layer
# ---------------------------------------------------------------------------


def test_load_trajectory_reads_npz_through_viz_loader(results_root: Path) -> None:
    record_dir = _write_record(results_root, "experiment_X/full", _full_record())
    _write_npz(record_dir, samples=5)
    traj = load_trajectory(record_dir)
    assert traj.positions.shape == (5, 2, 3)
    assert traj.body_names == ("Sun", "Earth")


def test_missing_trajectory_npz_without_redirect_is_data_gap(results_root: Path) -> None:
    record_dir = _write_record(results_root, "experiment_X/no_npz", _full_record())
    with pytest.raises(DataGapError) as exc:
        load_trajectory(record_dir)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["name"] == "trajectory.npz"
    assert "reused_from" in gap["detail"]
    assert gap["source_path"].endswith("trajectory.npz")


def test_corrupt_trajectory_npz_is_data_gap(results_root: Path) -> None:
    record_dir = _write_record(results_root, "experiment_X/truncated", _full_record())
    npz = _write_npz(record_dir)
    raw = npz.read_bytes()
    npz.write_bytes(raw[: len(raw) // 2])
    with pytest.raises(DataGapError) as exc:
        load_trajectory(record_dir)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["reason"] == "unreadable"
    assert gap["source_path"].endswith("trajectory.npz")


def test_loader_rejects_path_outside_results(tmp_path: Path) -> None:
    elsewhere = tmp_path / "elsewhere" / "experiment_X" / "rec"
    elsewhere.mkdir(parents=True)
    (elsewhere / "experiment_record.json").write_text(
        json.dumps(_full_record()), encoding="utf-8"
    )
    with pytest.raises(DataGapError) as exc:
        load_record(elsewhere)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert "results/" in gap["name"]
    assert "elsewhere" in gap["source_path"]


# ---------------------------------------------------------------------------
# Reused redirect + configuration_hash check (R9)
# ---------------------------------------------------------------------------


def test_reused_record_redirects_after_hash_check(results_root: Path) -> None:
    target = _write_record(
        results_root,
        "experiment_C/tier_T2",
        _full_record(configuration_hash="hash-A", experiment_id="C/T2"),
    )
    _write_npz(target, bodies=("Sun", "Earth", "Moon"))
    source = _write_record(
        results_root,
        "experiment_D/T2_30d",
        _reused_record("experiment_C/tier_T2", "hash-A"),
    )

    loaded = load_record(source)
    assert loaded.record_dir == source.resolve()
    assert loaded.reused_from == "experiment_C/tier_T2"
    assert loaded.reused_chain == ("experiment_C/tier_T2",)
    assert loaded.resolved_dir == target.resolve()
    assert loaded.record["experiment_id"] == "D/T2_30d"
    assert loaded.resolved_record["experiment_id"] == "C/T2"

    traj = load_trajectory(source)
    assert traj.body_names == ("Sun", "Earth", "Moon")


def test_reused_missing_target_record_is_data_gap(results_root: Path) -> None:
    source = _write_record(
        results_root,
        "experiment_D/ghost",
        _reused_record("experiment_C/missing", "hash-A"),
    )
    with pytest.raises(DataGapError) as exc:
        load_record(source)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    declared = gap["source_path"].replace("\\", "/")
    assert "experiment_C/missing" in declared
    assert declared.endswith("experiment_record.json")
    json.dumps(exc.value.report)  # machine-readable report, no raw exception


def test_reused_hash_mismatch_is_data_gap(results_root: Path) -> None:
    _write_record(results_root, "experiment_C/tier_T2", _full_record(configuration_hash="hash-B"))
    source = _write_record(
        results_root,
        "experiment_D/T2_30d",
        _reused_record("experiment_C/tier_T2", "hash-A"),
    )
    with pytest.raises(DataGapError) as exc:
        load_record(source)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["reason"] == "configuration_hash mismatch"
    assert "hash-A" in gap["detail"] and "hash-B" in gap["detail"]


def test_reused_redirect_cycle_is_data_gap(results_root: Path) -> None:
    source = _write_record(
        results_root,
        "experiment_A/rec",
        _reused_record("experiment_B/rec", "hash-A"),
    )
    _write_record(results_root, "experiment_B/rec", _reused_record("experiment_A/rec", "hash-A"))
    with pytest.raises(DataGapError) as exc:
        load_record(source)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["name"] == "reused_from"
    assert gap["reason"] == "redirect cycle"
    assert gap["source_path"].endswith("experiment_record.json")


def test_reused_redirect_escaping_results_root_is_data_gap(tmp_path: Path) -> None:
    root = tmp_path / "outer" / "results"
    source = _write_record(
        root,
        "experiment_D/escape",
        _reused_record("../../elsewhere/rec", "hash-A"),
    )
    elsewhere = _write_record(
        tmp_path / "elsewhere",
        "rec",
        _full_record(configuration_hash="hash-B", experiment_id="outside/rec"),
    )
    with pytest.raises(DataGapError) as exc:
        load_record(source)
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["name"] == "reused_from"
    assert gap["reason"] == "redirect escapes results root"
    declared = gap["source_path"].replace("\\", "/")
    assert declared.endswith("experiment_D/escape/experiment_record.json")
    assert (elsewhere / "experiment_record.json").is_file()  # never read: hash-B vs hash-A


def test_missing_provenance_fields_are_exposed(results_root: Path) -> None:
    full_dir = _write_record(results_root, "experiment_X/full", _full_record())
    assert load_record(full_dir).missing_provenance == ()

    _write_record(results_root, "experiment_C/tier_T2", _full_record(configuration_hash="hash-A"))
    source = _write_record(
        results_root,
        "experiment_D/T2_30d",
        _reused_record("experiment_C/tier_T2", "hash-A"),
    )
    loaded = load_record(source)
    assert set(loaded.missing_provenance) == MISSING_IN_REUSED
    assert "configuration_hash" not in loaded.missing_provenance
    assert "output_hash" not in loaded.missing_provenance


# ---------------------------------------------------------------------------
# normalize - R14: one adapter over the three comparison shapes
# ---------------------------------------------------------------------------


def test_normalize_flat_comparison() -> None:
    record = {"comparison": _flat_comparison()}
    norm = normalize_comparison(record, source_path="results/experiment_A2/d1000/experiment_record.json")
    assert isinstance(norm, NormalizedComparison)
    assert norm.absent is False
    assert norm.shape == "flat"
    assert norm.by_body["Earth"].position_error == [0.0, 10.0, 20.0]


def test_normalize_per_body_comparison() -> None:
    record = {"comparison": _per_body_comparison()}
    norm = normalize_comparison(record, source_path="results/experiment_C/tier_T2/experiment_record.json")
    assert norm.absent is False
    assert norm.shape == "per_body"
    assert set(norm.by_body) == {"Earth", "Moon"}
    assert norm.by_body["Moon"].velocity_error == [0.0, 0.2]


def test_normalize_absent_comparison() -> None:
    norm = normalize_comparison({}, source_path="results/experiment_B/one_period_rk4/experiment_record.json")
    assert norm.absent is True
    assert norm.shape == "absent"
    assert norm.by_body == {}


def test_normalize_malformed_comparison_is_data_gap(results_root: Path) -> None:
    source = results_root / "experiment_X" / "bad.json"
    source.parent.mkdir(parents=True)
    with pytest.raises(DataGapError) as exc:
        normalize_comparison({"comparison": "not a dict"}, source_path=str(source))
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert "comparison" in gap["name"]
    assert gap["reason"] == "unrecognized shape"
    assert gap["source_path"] == str(source)


def test_make_gap_follows_gate_style() -> None:
    gap = make_gap("body-list", reason="missing", detail="body list absent", source_path="p/r.json")
    assert tuple(gap) == GAP_KEYS
    assert gap["reason"] == "missing"
    err = DataGapError([gap])
    assert err.gaps == [gap]
    assert "body list absent" in err.report["gaps"][0]["detail"]


# ---------------------------------------------------------------------------
# R30 - exactly one REAL record per shape (marked, read-only, no kernels)
# ---------------------------------------------------------------------------

_REAL = [
    pytest.param(
        REAL_RESULTS / "experiment_A2" / "d1000", "flat", id="flat-d1000"
    ),
    pytest.param(
        REAL_RESULTS / "experiment_C" / "tier_T2", "per_body", id="per-body-tier_T2"
    ),
    pytest.param(
        REAL_RESULTS / "experiment_B" / "one_period_rk4", "absent", id="absent-one_period_rk4"
    ),
]


@pytest.mark.real_kernel
@pytest.mark.parametrize(("record_path", "expected_shape"), _REAL)
def test_real_record_shape_smoke(record_path: Path, expected_shape: str) -> None:
    loaded = load_record(record_path)
    norm = normalize_comparison(loaded.resolved_record, source_path=str(loaded.resolved_dir))
    assert norm.shape == expected_shape


@pytest.mark.real_kernel
def test_real_reused_record_smoke() -> None:
    """results/experiment_D/T2_30d - the reused redirect shape."""
    record_path = REAL_RESULTS / "experiment_D" / "T2_30d"
    loaded = load_record(record_path)
    assert loaded.reused_from == "experiment_C/tier_T2"
    assert loaded.resolved_dir.is_relative_to(REAL_RESULTS.resolve())
    assert set(loaded.missing_provenance) == MISSING_IN_REUSED
    traj = load_trajectory(record_path)
    assert traj.positions.ndim == 3
