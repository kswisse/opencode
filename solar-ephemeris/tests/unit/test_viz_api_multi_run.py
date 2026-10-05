"""U6 - V6–V9 multi-run figures + bộ registry Fig-09…Fig-13.

Requirements: R21–R26 (V6–V9, Fig-09…Fig-13), R14 (bốn ``plot_*`` còn lại),
R27 (read-only), R29 (Gate A không cần matplotlib).

Mọi case dựng record + aggregate JSON **tổng hợp** dưới ``tmp_path`` - không
đụng cây ``results/`` thật, không kernel, không chạy physics. Ca render gọi
``pytest.importorskip("matplotlib")`` INSIDE chính test; ca registry / ma
trận / composition shim / subprocess import chạy không cần matplotlib.

Bảng HTD (Fig-09…Fig-13), ma trận nguồn V6–V9, hằng ``V9_UNDISCRIMINATED``
và bảng composition được viết cứng ở đây (test-side authority): bỏ một dòng
khỏi registry hoặc lệch một hằng ``experiments/_common.py`` là test đỏ ngay.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from solar_ephemeris.visualization import api, composition
from solar_ephemeris.visualization.gaps import GAP_KEYS, DataGapError

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
DAY = 86400.0
J2000 = 2451545.0

#: Record variant of every Fig-09…Fig-13 source row (contract table §6d).
VARIANT_FULL_6D = "full §6d"

#: Body set of the synthetic trajectories (all three are fixture-mapped).
BODIES = ("Sun", "Earth", "Moon")

#: The standard 10-body tier (Tier T4, correction #3 - Pluto never in a tier).
TIER_T4_BODIES = (
    "Sun",
    "Mercury",
    "Venus",
    "Earth",
    "Moon",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
)

#: AE4 - the mandated annotation for an undecidable growth classification.
V9_UNDISCRIMINATED = "không phân biệt — chỉ report"

#: HTD figure table (design doc, "Bộ figure cụ thể"), rows Fig-09…Fig-13.
HTD_FIGURES: dict[str, dict[str, str]] = {
    "fig-09": {
        "title": "Conservation: năng lượng/động lượng/động lượng góc",
        "feature": "V6",
        "function": "plot_conservation",
        "records": "results/experiment_C/tier_T2",
        "source": "npz + analysis (derived)",
        "state": "derived",
    },
    "fig-10": {
        "title": "Convergence A1: lỗi cuối vs N + observed orders + floor",
        "feature": "V7",
        "function": "plot_convergence",
        "records": "results/experiment_A1/* + *_orders.json",
        "source": "*_orders.json, analysis.json",
        "state": "aggregate",
    },
    "fig-11": {
        "title": "A2 divisor ratios + B ref-lattice (cảnh báo floor-dominated)",
        "feature": "V7",
        "function": "plot_convergence",
        "records": "results/experiment_A2/analysis.json, results/experiment_B/ref_summary.json",
        "source": "*_orders.json, analysis.json",
        "state": "aggregate",
    },
    "fig-12": {
        "title": "Ảnh hưởng số body (signal vs control)",
        "feature": "V8",
        "function": "plot_body_count",
        "records": "results/experiment_C/* + analysis.json",
        "source": "payload stored + signals",
        "state": "stored",
    },
    "fig-13": {
        "title": "Lỗi theo horizon 1/30/90/365d + annotation phân biệt",
        "feature": "V9",
        "function": "plot_horizon_error",
        "records": "results/experiment_E/horizon_*",
        "source": "payload stored + growth_class",
        "state": "stored",
    },
}

#: R26 source matrix, V6–V9 rows only (cột "Record full §6d"); V1–V5 rows
#: là phần của U5 và được kiểm trong test_viz_api_single_run.
SOURCE_MATRIX: dict[str, tuple[str, ...]] = {
    "V6": ("npz + analysis (derived)",),
    "V7": ("*_orders.json, analysis.json",),
    "V8": ("payload stored + signals",),
    "V9": ("payload stored + growth_class",),
}

#: R14/R21–R24: feature -> hàm tất định vẽ nó.
FEATURE_FUNCTION: dict[str, str] = {
    "V6": "plot_conservation",
    "V7": "plot_convergence",
    "V8": "plot_body_count",
    "V9": "plot_horizon_error",
}


# ---------------------------------------------------------------------------
# Synthetic record / npz builders (mirror test_viz_api_single_run)
# ---------------------------------------------------------------------------


def _traj_meta_json(bodies: tuple[str, ...]) -> str:
    payload = {
        "state_meta": {
            "frame": "active_bodies_barycentric",
            "origin": f"barycenter({', '.join(bodies)})",
            "epoch_jd": J2000,
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


def _positions(m: int, n: int) -> np.ndarray:
    """Deterministic, strictly distinct positions (M, N, 3), metres."""
    i = np.arange(1, m + 1, dtype=np.float64)[:, None]
    k = np.arange(1, n + 1, dtype=np.float64)[None, :]
    pos = np.empty((m, n, 3), dtype=np.float64)
    pos[:, :, 0] = i * 1.0e8 * k
    pos[:, :, 1] = i * 0.5e8 * k
    pos[:, :, 2] = (i + k) * 1.0e7
    return pos


def _write_npz(record_dir: Path, *, bodies: tuple[str, ...], times: np.ndarray) -> None:
    n, m = len(bodies), len(times)
    pos = _positions(m, n)
    np.savez(
        record_dir / "trajectory.npz",
        times=np.asarray(times, dtype=np.float64),
        positions=pos,
        velocities=pos / 1.0e5,
        gm=np.full(n, 1.32712440041939e20, dtype=np.float64),
        body_names=np.array(bodies),
        traj_meta_json=np.array(_traj_meta_json(bodies)),
    )


def _full_record(**over) -> dict:
    record = {
        "schema_version": 1,
        "experiment_id": "X/full",
        "epoch": J2000,
        "bodies": list(BODIES),
        "initial_condition_source": "synthetic fixture",
        "integrator": "rk4",
        "timestep": 1.0,
        "duration": 3.0 * DAY,
        "reference_dataset": "JPL DE440 (de440s.bsp live)",
        "reference_frame": "J2000",
        "reference_origin": "SSB(0)",
        "time_scale": "TDB",
        "units": "m, m/s, s",
        "software_version": "0.1.0",
        "configuration_hash": "hash-A",
        "output_hash": "0" * 64,
    }
    record.update(over)
    return record


def _per_body_comparison(bodies: tuple[str, ...] = ("Earth", "Moon")) -> dict:
    """Per-body map shape, mirroring results/experiment_C/tier_T2."""
    return {
        name: {
            "body": name,
            "schema_version": 1,
            "times_s": [0.0, 1.0],
            "position_error": [0.0, 10.0 + index],
            "velocity_error": [0.0, 0.1 + 0.01 * index],
        }
        for index, name in enumerate(bodies)
    }


def _growth(discriminated: bool, selected: str | None = None) -> dict:
    """Record-side growth_classification shape (experiment E, §6e)."""
    return {
        "discriminated": discriminated,
        "selected": selected,
        "note": "synthetic classification",
        "n_samples_fit": 3,
        "sse": {"linear": 1.0, "power": 2.0, "exponential": 3.0},
    }


def _orders(integrator: str) -> dict:
    """Synthetic ``<integrator>_orders.json`` (experiment A1 aggregate)."""
    if integrator == "rk4":
        errors, orders, window = [41589.0, 5198.6, 649.8, 81.2], [4.06, 4.0, 4.0], [3.5, 4.5]
    else:
        errors, orders, window = [1.0e6, 5.0e5, 2.5e5, 1.25e5], [1.0, 1.0, 1.0], [1.5, 2.5]
    return {
        "experiment_id": f"A1/{integrator}/orders",
        "n_values": list(composition.A1_N_VALUES),
        "errors_m": errors,
        "observed_orders": orders,
        "order_window": window,
        "roundoff_floor_m": 3.3306690738754696e-05,
        "all_passed": True,
        "gates": [],
    }


def _a2_analysis() -> dict:
    """Synthetic experiment_A2/analysis.json with a floor-dominated plateau."""
    return {
        "experiment_id": "A2/analysis",
        "D_by_divisor_m": {
            "500": 5587809.2,
            "1000": 5073209.5,
            "2000": 5073209.4,
            "4000": 5199954.1,
        },
        "ratios": [
            {
                "from_divisor": 500,
                "to_divisor": 1000,
                "ratio_Dk_over_Dk1": 1.101,
                "classification": "floor-dominated",
                "dt_from": 63116.3,
                "dt_to": 31558.1,
            },
            {
                "from_divisor": 1000,
                "to_divisor": 2000,
                "ratio_Dk_over_Dk1": 1.0,
                "classification": "floor-dominated",
                "dt_from": 31558.1,
                "dt_to": 15779.1,
            },
            {
                "from_divisor": 2000,
                "to_divisor": 4000,
                "ratio_Dk_over_Dk1": 0.976,
                "classification": "resolved",
                "dt_from": 15779.1,
                "dt_to": 7889.5,
            },
        ],
    }


def _b_summary() -> dict:
    """Synthetic experiment_B/ref_summary.json (both wings, no ranking)."""
    return {
        "experiment_id": "B/ref",
        "note": "no overall ranking claim",
        "per_divisor": [
            {
                "divisor": 500,
                "rk4_max_E_pos_m": 5587809.2,
                "verlet_max_E_pos_m": 5344879.5,
                "rk4_smaller": False,
            },
            {
                "divisor": 1000,
                "rk4_max_E_pos_m": 5073209.5,
                "verlet_max_E_pos_m": 4891234.5,
                "rk4_smaller": False,
            },
            {
                "divisor": 2000,
                "rk4_max_E_pos_m": 5073209.4,
                "verlet_max_E_pos_m": 4891123.4,
                "rk4_smaller": False,
            },
            {
                "divisor": 4000,
                "rk4_max_E_pos_m": 5199954.1,
                "verlet_max_E_pos_m": 5012345.6,
                "rk4_smaller": False,
            },
        ],
    }


@pytest.fixture
def results_root(tmp_path: Path) -> Path:
    root = tmp_path / "results"
    root.mkdir()
    return root


def _write_record(
    results_root: Path,
    rel: str,
    payload: dict,
    *,
    npz: bool = False,
    times: np.ndarray | None = None,
) -> Path:
    record_dir = results_root / rel
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "experiment_record.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    if npz:
        bodies = tuple(payload["bodies"])
        if times is None:
            times = np.arange(4, dtype=np.float64) * DAY
        _write_npz(record_dir, bodies=bodies, times=times)
    return record_dir


def _write_aggregate(results_root: Path, rel: str, payload: dict) -> Path:
    path = results_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _plt():
    mpl = pytest.importorskip("matplotlib")
    mpl.use("Agg", force=True)
    import matplotlib.pyplot as plt

    return plt


def _read(png_path: Path) -> dict:
    return json.loads(png_path.with_suffix(".json").read_text(encoding="utf-8"))


def _capture_axes(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Bắt trạng thái axes TRƯỚC khi figure được ghi (R13, không sửa output)."""
    shots: list[dict[str, Any]] = []
    real_write = api.write_figure

    def wrapper(fig, *, png_path, sidecar, arrays):
        for ax in fig.axes:
            shots.append(
                {
                    "xlim": ax.get_xlim(),
                    "ylim": ax.get_ylim(),
                    "xlabel": ax.get_xlabel(),
                    "ylabel": ax.get_ylabel(),
                    "lines": [
                        (line.get_label(), line.get_linestyle(), line.get_marker())
                        for line in ax.lines
                    ],
                    "texts": [text.get_text() for text in ax.texts],
                }
            )
        return real_write(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)

    monkeypatch.setattr(api, "write_figure", wrapper)
    return shots


# ---------------------------------------------------------------------------
# R29 - importing api + composition must not load matplotlib
# ---------------------------------------------------------------------------


def test_importing_api_and_composition_does_not_load_matplotlib() -> None:
    code = (
        "import sys; import solar_ephemeris.visualization.api; "
        "import solar_ephemeris.visualization.composition; "
        "print('MATPLOTLIB_LOADED' if 'matplotlib' in sys.modules else 'CLEAN')"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SRC), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120
    )
    assert proc.returncode == 0, proc.stderr
    assert "CLEAN" in proc.stdout, f"matplotlib loaded on import: {proc.stdout}"


# ---------------------------------------------------------------------------
# KTD8 - composition table == hằng đóng băng experiments/_common.py
# ---------------------------------------------------------------------------


def test_composition_runsets_match_frozen_experiment_constants() -> None:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from experiments import _common as C

    assert composition.A1_N_VALUES == C.N_VALUES
    assert composition.A2_DIVISORS == C.A2_DIVISORS
    assert composition.E_HORIZON_DAYS == C.E_HORIZON_DAYS
    assert composition.V8_TIER_DIRS == tuple(f"tier_{k}" for k in C.TIERS)
    assert len(C.TIER_T4) == 10
    assert composition.V8_CONTROL_DIRS == ("control_T2_dt2", "control_T3_dt2")
    assert composition.V8_RUNSET == composition.V8_TIER_DIRS + composition.V8_CONTROL_DIRS
    assert composition.A1_INTEGRATORS == ("rk4", "verlet")
    assert composition.A1_RUNSET == tuple(
        f"{integrator}_n{n}" for integrator in ("rk4", "verlet") for n in C.N_VALUES
    )
    assert composition.A2_RUNSET == tuple(f"d{d}" for d in C.A2_DIVISORS)
    assert composition.B_LATTICE_REL == "ref_lattice"
    assert composition.V9_RUNSET == tuple(f"horizon_{d}d" for d in C.E_HORIZON_DAYS)
    assert composition.V9_RUNSET == (
        "horizon_1d",
        "horizon_30d",
        "horizon_90d",
        "horizon_365d",
    )


# ---------------------------------------------------------------------------
# R25 - registry khớp bảng HTD Fig-09…Fig-13; R14 - trỏ tới plot_* có thật
# ---------------------------------------------------------------------------


def test_registry_matches_htd_table_for_fig09_to_fig13() -> None:
    for fig_id, expected in HTD_FIGURES.items():
        spec = api.FIGURE_REGISTRY.get(fig_id)
        assert spec is not None, f"{fig_id} missing from FIGURE_REGISTRY (R25)"
        assert spec.id == fig_id, f"{fig_id}: id field {spec.id!r}"
        for field, want in expected.items():
            assert getattr(spec, field) == want, (
                f"{fig_id}.{field}: {getattr(spec, field)!r} != {want!r} (HTD table)"
            )
        assert spec.variant == VARIANT_FULL_6D, f"{fig_id}.variant must be {VARIANT_FULL_6D!r}"
        assert callable(getattr(api, spec.function, None)), (
            f"{fig_id} points at {spec.function!r}, which is not implemented (R14)"
        )
    assert set(HTD_FIGURES) <= set(api.FIGURE_REGISTRY)


# ---------------------------------------------------------------------------
# R26 - mọi nguồn V6–V9 khai báo nằm trong ma trận nguồn
# ---------------------------------------------------------------------------


def test_registry_sources_stay_inside_the_v6_v9_source_matrix() -> None:
    checked = 0
    for spec in api.FIGURE_REGISTRY.values():
        if spec.feature not in SOURCE_MATRIX:
            continue  # V1–V5 rows belong to U5
        assert spec.source in SOURCE_MATRIX[spec.feature], (
            f"{spec.id}: source {spec.source!r} outside the matrix for {spec.feature}"
        )
        assert spec.function == FEATURE_FUNCTION[spec.feature], (
            f"{spec.id}: {spec.feature} must be drawn by {FEATURE_FUNCTION[spec.feature]}"
        )
        checked += 1
    assert checked == len(HTD_FIGURES), f"checked {checked} figures against the matrix"


# ---------------------------------------------------------------------------
# V6 (R21) - sidecar source=derived, trỏ output_hash record nguồn, nhãn đơn vị
# ---------------------------------------------------------------------------


def test_v6_conservation_is_derived_and_keeps_the_source_output_hash(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record = _full_record()
    record_dir = _write_record(results_root, "experiment_C/tier_T2", record, npz=True)

    png, sc_path = api.plot_conservation(
        record_dir, tmp_path / "figures" / "fig-09.png", figure_id="fig-09"
    )

    sidecar = _read(png)
    assert png.is_file() and sc_path.is_file()
    assert sidecar["source"] == "derived"
    assert sidecar["output_hash"] == record["output_hash"], "V6 traces back to its record"
    assert sidecar["gaps"] == []
    assert sidecar["units"] == "J, kg m/s, kg m^2/s"
    assert any("total_energy" in str(name) for name in sidecar["derived_from"])
    labels = [shot["ylabel"] for shot in shots]
    assert labels == [
        "ΔE = E(t) − E(0) (J)",
        "|ΔP| = |P(t) − P(0)| (kg m/s)",
        "|ΔL| = |L(t) − L(0)| (kg m^2/s)",
    ], labels
    assert all(shot["xlabel"] == "time (s)" for shot in shots)
    styles = {(linestyle, marker) for _, linestyle, marker in shots[0]["lines"]}
    assert styles == {("-", "s")}, f"conservation series must use the error role: {styles}"


# ---------------------------------------------------------------------------
# V9 (R24, AE4) - record discriminated: false -> annotation bắt buộc
# ---------------------------------------------------------------------------


def _write_horizons(results_root: Path, discriminated: dict[str, bool]) -> None:
    for member, is_discriminated in discriminated.items():
        record = _full_record(
            experiment_id=f"E/{member}",
            bodies=["Earth", "Moon"],
            horizon_days=int(member.removeprefix("horizon_").removesuffix("d")),
        )
        record["comparison"] = _per_body_comparison()
        record["growth_classification"] = _growth(
            is_discriminated, selected="power" if is_discriminated else None
        )
        _write_record(results_root, f"experiment_E/{member}", record)


def test_v9_undecidable_member_forces_the_annotation(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    _write_horizons(
        results_root,
        {
            "horizon_1d": False,
            "horizon_30d": True,
            "horizon_90d": True,
            "horizon_365d": False,
        },
    )

    png, sc_path = api.plot_horizon_error(
        results_root, tmp_path / "figures" / "fig-13.png", figure_id="fig-13"
    )

    sidecar = _read(png)
    assert png.is_file() and sc_path.is_file()
    assert sidecar["gaps"] == []
    assert sidecar["growth_discriminated"] is False
    assert sidecar["growth_annotation"] == V9_UNDISCRIMINATED
    assert set(sidecar["growth_undecidable_members"]) == {"horizon_1d", "horizon_365d"}
    assert sidecar["growth_classification"]["horizon_30d"] == "power"
    texts = [text for shot in shots for text in shot["texts"]]
    assert V9_UNDISCRIMINATED in texts, texts
    labels = [label for shot in shots for label, _, _ in shot["lines"]]
    assert "horizon_365d Earth" in labels, labels
    assert len(labels) == 8, labels  # 4 horizons x 2 bodies


def test_v9_all_discriminated_makes_no_undecidability_claim(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    _write_horizons(
        results_root,
        {
            "horizon_1d": True,
            "horizon_30d": True,
            "horizon_90d": True,
            "horizon_365d": True,
        },
    )

    png, _ = api.plot_horizon_error(
        results_root, tmp_path / "figures" / "fig-13.png", figure_id="fig-13"
    )

    sidecar = _read(png)
    texts = [text for shot in shots for text in shot["texts"]]
    assert V9_UNDISCRIMINATED not in texts, texts
    assert sidecar["growth_discriminated"] is True
    assert sidecar["growth_classification"] == {
        member: "power"
        for member in ("horizon_1d", "horizon_30d", "horizon_90d", "horizon_365d")
    }
    assert "growth_annotation" not in sidecar
    assert sidecar["growth_undecidable_members"] == []


# ---------------------------------------------------------------------------
# V7 (R22, error) - thiếu một n-value -> gaps[] có entry, figure vẫn phát hành
# ---------------------------------------------------------------------------


def test_v7_missing_a1_member_is_one_gap_and_seven_sources(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    for integrator in ("rk4", "verlet"):
        _write_aggregate(
            results_root, f"experiment_A1/{integrator}_orders.json", _orders(integrator)
        )
    for name in composition.A1_RUNSET:
        if name == "rk4_n50":
            continue
        _write_record(
            results_root,
            f"experiment_A1/{name}",
            _full_record(experiment_id=f"A1/{name}", integrator=name.split("_")[0]),
        )

    png, _ = api.plot_convergence(
        results_root, tmp_path / "figures" / "fig-10.png", figure_id="fig-10"
    )

    sidecar = _read(png)
    assert png.is_file(), "a figure with a gap is still published (KTD5)"
    assert sidecar["source"] == "aggregate"
    assert sidecar["ranking"] == "none (R22)"
    assert sidecar["order_window"] == [3.5, 4.5]
    assert len(sidecar["sources"]) == 7, len(sidecar["sources"])
    assert len(sidecar["gaps"]) == 1, sidecar["gaps"]
    gap = sidecar["gaps"][0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["name"] == "rk4_n50"
    assert gap["reason"] == "missing run-set member"
    assert gap["source_path"].endswith("experiment_record.json")
    labels0 = [label for label, _, _ in shots[0]["lines"]]
    assert labels0 == ["rk4", "verlet", "roundoff floor"], labels0
    assert shots[0]["ylabel"] == "final position error (m)"
    assert shots[0]["xlabel"] == "N"
    labels1 = [label for label, _, _ in shots[1]["lines"]]
    assert labels1 == ["rk4 observed orders", "verlet observed orders"], labels1
    assert shots[1]["ylabel"] == "observed order"


# ---------------------------------------------------------------------------
# V7 (R22) - A2 + B: cảnh báo floor-dominated, không xếp hạng
# ---------------------------------------------------------------------------


def test_v7_a2b_two_panels_with_floor_dominated_annotation(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    for divisor in composition.A2_DIVISORS:
        _write_record(
            results_root,
            f"experiment_A2/d{divisor}",
            _full_record(experiment_id=f"A2/d{divisor}"),
        )
        _write_record(
            results_root,
            f"experiment_B/ref_lattice/d{divisor}",
            _full_record(experiment_id=f"B/ref_lattice/d{divisor}"),
        )
    _write_aggregate(results_root, "experiment_A2/analysis.json", _a2_analysis())
    _write_aggregate(results_root, "experiment_B/ref_summary.json", _b_summary())

    png, _ = api.plot_convergence(
        results_root,
        tmp_path / "figures" / "fig-11.png",
        figure_id="fig-11",
        variant="a2b",
    )

    sidecar = _read(png)
    assert png.is_file()
    assert sidecar["source"] == "aggregate"
    assert sidecar["gaps"] == []
    assert len(sidecar["sources"]) == 8, len(sidecar["sources"])
    assert sidecar["ranking"] == "none (R22)"
    intervals = sidecar["floor_dominated_intervals"]
    assert [entry["from_divisor"] for entry in intervals] == [500, 1000], intervals
    assert all(entry["classification"] == "floor-dominated" for entry in intervals)
    assert any("floor-dominated" in text for text in shots[0]["texts"]), shots[0]["texts"]
    styles0 = {(linestyle, marker) for _, linestyle, marker in shots[0]["lines"]}
    assert styles0 == {("-", "s")}, styles0
    assert shots[0]["xlabel"] == "divisor"
    labels1 = [label for label, _, _ in shots[1]["lines"]]
    assert labels1 == ["rk4", "verlet"], labels1
    styles1 = {(linestyle, marker) for _, linestyle, marker in shots[1]["lines"]}
    assert styles1 == {("-", "o")}, styles1


def test_v7_a2b_without_any_aggregate_refuses_before_writing(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    out_dir = tmp_path / "figures"

    with pytest.raises(DataGapError) as exc:
        api.plot_convergence(
            results_root, out_dir / "fig-11.png", figure_id="fig-11", variant="a2b"
        )

    assert {gap["reason"] for gap in exc.value.gaps} == {"missing aggregate"}
    json.dumps(exc.value.report)
    assert not out_dir.exists(), "the refused figure must leave no PNG behind"


# ---------------------------------------------------------------------------
# V8 (R23) - tier 10 body: gap cho 8 body + 5 thành viên run-set thiếu
# ---------------------------------------------------------------------------


def test_v8_tier_t4_only_publishes_with_member_and_body_gaps(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record = _full_record(bodies=list(TIER_T4_BODIES))
    record["comparison"] = _per_body_comparison()
    _write_record(results_root, "experiment_C/tier_T4", record)

    png, _ = api.plot_body_count(
        results_root, tmp_path / "figures" / "fig-12.png", figure_id="fig-12"
    )

    sidecar = _read(png)
    assert png.is_file(), "a figure with gaps is still published (KTD5)"
    assert sidecar["source"] == "stored"
    assert sidecar["runset_members"] == ["tier_T4"]
    names = {gap["name"] for gap in sidecar["gaps"]}
    missing_members = set(composition.V8_RUNSET) - {"tier_T4"}
    assert len(missing_members) == 5
    assert missing_members <= names, names
    body_gaps = names - missing_members
    assert body_gaps == {
        f"tier_T4/{name}"
        for name in TIER_T4_BODIES
        if name not in ("Earth", "Moon")
    }, body_gaps
    assert len(sidecar["gaps"]) == 13, len(sidecar["gaps"])
    for gap in sidecar["gaps"]:
        assert set(gap) == set(GAP_KEYS)
        assert gap["source_path"].endswith("experiment_record.json")
    assert any(
        gap["reason"] == "missing run-set member"
        for gap in sidecar["gaps"]
        if gap["name"] in missing_members
    )
    assert any(
        gap["reason"] == "no stored error series"
        for gap in sidecar["gaps"]
        if gap["name"].startswith("tier_T4/")
    )
    labels = [label for label, _, _ in shots[0]["lines"]]
    assert labels == ["tier_T4: Earth", "tier_T4: Moon"], labels
    styles = {(linestyle, marker) for _, linestyle, marker in shots[0]["lines"]}
    assert styles == {(":", "x")}, f"tier runs are the signal role: {styles}"
    assert shots[0]["xlabel"] == "time (s)"
    assert "position error" in shots[0]["ylabel"] and "m" in shots[0]["ylabel"]
    assert any(text.startswith("gaps: 13") for text in shots[0]["texts"]), shots[0]["texts"]


# ---------------------------------------------------------------------------
# Integration - record E thật: 4 horizon, annotation cho các record undecidable
# ---------------------------------------------------------------------------


@pytest.mark.real_kernel
def test_v9_real_experiment_e_renders_and_reports_growth(tmp_path: Path) -> None:
    _plt()
    results = REPO / "results"

    png, _ = api.plot_horizon_error(
        results, tmp_path / "figures" / "fig-13.png", figure_id="fig-13"
    )

    sidecar = _read(png)
    assert png.is_file()
    assert len(sidecar["sources"]) == 4, len(sidecar["sources"])
    assert sidecar["runset_members"] == list(composition.V9_RUNSET)
    assert sidecar["growth_discriminated"] is False
    assert sidecar["growth_annotation"] == V9_UNDISCRIMINATED
    assert "horizon_365d" in sidecar["growth_undecidable_members"]
    assert "horizon_30d" not in sidecar["growth_undecidable_members"]
    sun_gaps = {gap["name"] for gap in sidecar["gaps"]}
    assert sun_gaps == {f"{member}/Sun" for member in composition.V9_RUNSET}, sun_gaps
