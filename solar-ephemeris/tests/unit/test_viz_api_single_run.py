"""U5 - V1–V5 single-run figures + bộ registry Fig-01…Fig-08.

Requirements: R16–R20, R13 (nhãn đơn vị / giới hạn trục / projection trong
caption), R25 (registry khớp bảng HTD), R26 (mọi nguồn nằm trong ma trận
nguồn), R14 (bốn ``plot_*`` tất định, side-effect chỉ ghi vào đường dẫn khai
báo).

Mọi case dựng record + ``trajectory.npz`` tổng hợp dưới ``tmp_path`` - không
đụng cây ``results/`` thật, không kernel, không chạy physics (R27/R29), nên
Gate A luôn xanh trên máy chưa cài matplotlib. Ca render gọi
``pytest.importorskip("matplotlib")`` INSIDE chính test; ca registry / ma
trận / subprocess import chạy không cần matplotlib.

Ảnh chụp trục (R13): các ca giới hạn trục bắt ``write_figure`` qua monkeypatch
để đọc xlim / ylim / nhãn / annotation TRƯỚC khi figure được ghi - assert
trên đường vẽ thật chứ không trên ghi chú.

Hằng số bảng HTD và ma trận nguồn được viết cứng ở đây (test-side authority)
thay vì import từ implementation: bỏ một dòng khỏi registry là test đỏ ngay.
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

from solar_ephemeris.visualization import api
from solar_ephemeris.visualization.gaps import GAP_KEYS, DataGapError

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
DAY = 86400.0
J2000 = 2451545.0

#: Recorded fixture window: tests/fixtures/reference/de440s_recorded.json.
FIXTURE_INTERVAL = (-DAY, 10.0 * DAY)

#: Record variant of every Fig-01…Fig-08 source row (contract table §6d).
VARIANT_FULL_6D = "full §6d"

#: Body set of the synthetic trajectories (all three are fixture-mapped).
BODIES = ("Sun", "Earth", "Moon")

#: R6 record-level keys a DIRECT full record carries (the two kernel keys are
#: deliberately absent here - see test_viz_provenance for the full list).
R6_RECORD_KEYS = (
    "experiment_id",
    "configuration_hash",
    "output_hash",
    "bodies",
    "epoch",
    "duration",
    "integrator",
    "timestep",
    "reference_dataset",
)

#: HTD figure table (design doc, "Bộ figure cụ thể"), rows Fig-01…Fig-08.
HTD_FIGURES: dict[str, dict[str, str]] = {
    "fig-01": {
        "title": "Quỹ đạo hệ trong SSB-ICRS (XY, AU)",
        "feature": "V1",
        "function": "plot_trajectory",
        "records": "results/experiment_C/tier_T*",
        "source": "npz trực tiếp",
        "state": "kernel-agnostic",
    },
    "fig-02": {
        "title": "Zoom quỹ đạo Đất–Trăng",
        "feature": "V1",
        "function": "plot_trajectory",
        "records": "results/experiment_C/tier_T2",
        "source": "npz trực tiếp",
        "state": "kernel-agnostic",
    },
    "fig-03": {
        "title": "Bố cục 3D tĩnh 10 body",
        "feature": "V2",
        "function": "plot_trajectory",
        "records": "results/experiment_C/tier_T4",
        "source": "npz trực tiếp",
        "state": "kernel-agnostic",
    },
    "fig-04": {
        "title": "Model vs DE440 (Đất)",
        "feature": "V3",
        "function": "plot_model_vs_reference",
        "records": "results/experiment_C/tier_T2",
        "source": "lookup read-only (KTD6)",
        "state": "cần kernel",
    },
    "fig-05": {
        "title": "Model vs fixture (V3 kernel-free)",
        "feature": "V3",
        "function": "plot_model_vs_reference",
        "records": "results/experiment_E/horizon_1d",
        "source": "lookup read-only (KTD6)",
        "state": "kernel-free",
    },
    "fig-06": {
        "title": "Lỗi vị trí theo thời gian (formal D 7d)",
        "feature": "V4",
        "function": "plot_position_error",
        "records": "results/experiment_D/T{1,2}_7d",
        "source": "payload stored (normalize)",
        "state": "stored",
    },
    "fig-07": {
        "title": "Lỗi vị trí per-body theo tier (+gap 8 body)",
        "feature": "V4",
        "function": "plot_position_error",
        "records": "results/experiment_C/tier_T*",
        "source": "payload stored (normalize)",
        "state": "stored",
    },
    "fig-08": {
        "title": "Lỗi vận tốc per-body",
        "feature": "V5",
        "function": "plot_velocity_error",
        "records": "results/experiment_C/tier_T*",
        "source": "payload stored (normalize)",
        "state": "stored",
    },
}

#: R26 source matrix, V1–V5 row only (cột "Record full §6d"); V6–V9 rows là
#: phần của U6 và không thuộc phạm vi test này.
SOURCE_MATRIX: dict[str, tuple[str, ...]] = {
    "V1": ("npz trực tiếp",),
    "V2": ("npz trực tiếp",),
    "V3": ("lookup read-only (KTD6)",),
    "V4": ("payload stored (normalize)",),
    "V5": ("payload stored (normalize)",),
}

#: R14/R16–R20: feature -> hàm tất định vẽ nó.
FEATURE_FUNCTION: dict[str, str] = {
    "V1": "plot_trajectory",
    "V2": "plot_trajectory",
    "V3": "plot_model_vs_reference",
    "V4": "plot_position_error",
    "V5": "plot_velocity_error",
}


# ---------------------------------------------------------------------------
# Synthetic record / npz builders (mirror test_viz_data, kernel-free)
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
    """Deterministic, strictly distinct positions (M, N, 3), metres.

    x = (i+1)·1e8·(k+1), y = (i+1)·0.5e8·(k+1) - distinct per body AND per
    sample, so a body-relative origin shift is visible in the axis limits.
    """
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


def _reused_record(target_rel: str, configuration_hash: str) -> dict:
    """Reduced record variant, mirroring results/experiment_D/T2_30d."""
    return {
        "schema_version": 1,
        "experiment_id": "D/T2_30d",
        "configuration_hash": configuration_hash,
        "output_hash": "1" * 64,
        "initial_condition_source": "synthetic fixture",
        "reused_from": target_rel,
    }


def _flat_comparison() -> dict:
    """Flat single-body shape, mirroring results/experiment_A2/d1000."""
    return {
        "body": "Earth",
        "schema_version": 1,
        "times_s": [0.0, 1.0, 2.0],
        "position_error": [0.0, 10.0, 20.0],
        "velocity_error": [0.0, 0.1, 0.2],
    }


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
            shot = {
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
            if hasattr(ax, "elev"):  # Axes3D only - R17 static camera
                shot["elev"] = ax.elev
                shot["azim"] = ax.azim
            shots.append(shot)
        return real_write(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)

    monkeypatch.setattr(api, "write_figure", wrapper)
    return shots


# ---------------------------------------------------------------------------
# R29 - importing api must not load matplotlib; Gate A runs without it
# ---------------------------------------------------------------------------


def test_importing_api_does_not_load_matplotlib() -> None:
    code = (
        "import sys; import solar_ephemeris.visualization.api; "
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
    assert "CLEAN" in proc.stdout, f"matplotlib loaded on api import: {proc.stdout}"


# ---------------------------------------------------------------------------
# R25 - registry khớp bảng HTD; R14 - mỗi entry trỏ tới một plot_* có thật
# ---------------------------------------------------------------------------


def test_registry_matches_htd_table_for_fig01_to_fig08() -> None:
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
# R26 - mọi nguồn V1–V5 khai báo nằm trong ma trận nguồn; feature -> plot_*
# ---------------------------------------------------------------------------


def test_registry_sources_stay_inside_the_v1_v5_source_matrix() -> None:
    checked = 0
    for spec in api.FIGURE_REGISTRY.values():
        if spec.feature not in SOURCE_MATRIX:
            continue  # V6–V9 rows belong to U6
        assert spec.source in SOURCE_MATRIX[spec.feature], (
            f"{spec.id}: source {spec.source!r} outside the matrix for {spec.feature}"
        )
        assert spec.function == FEATURE_FUNCTION[spec.feature], (
            f"{spec.id}: {spec.feature} must be drawn by {FEATURE_FUNCTION[spec.feature]}"
        )
        checked += 1
    assert checked >= len(HTD_FIGURES), f"only {checked} figures checked against the matrix"


# ---------------------------------------------------------------------------
# V1 (R16) - 2D: caption nêu frame + projection, trục bao trùm dữ liệu
# ---------------------------------------------------------------------------


def test_v1_2d_caption_states_frame_and_projection(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    record = _full_record()
    record_dir = _write_record(results_root, "experiment_C/tier_T2", record, npz=True)

    png, sc_path = api.plot_trajectory(
        record_dir,
        tmp_path / "figures" / "fig-01.png",
        figure_id="fig-01",
        mode="2d",
        unit="au",
    )

    sidecar = _read(png)
    caption = sidecar["caption"]
    assert png.is_file() and sc_path.is_file()
    assert f"frame={sidecar['frame']}" in caption, caption
    assert "projection=" in caption, caption
    assert "XY" in sidecar["projection"]
    assert sidecar["frame"] == "active_bodies_barycentric"
    assert sidecar["origin"] == "barycenter(Sun, Earth, Moon)"
    assert sidecar["time_scale"] == "TDB"
    assert sidecar["source"] == "stored"
    assert sidecar["gaps"] == []
    assert sidecar["units"] == "au"


# ---------------------------------------------------------------------------
# V2 (R17) - 3D tĩnh, camera độc lập: elev/azim ghim, không trang trí
# ---------------------------------------------------------------------------


def test_v1_3d_mode_renders_with_static_camera(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record_dir = _write_record(
        results_root, "experiment_C/tier_T4", _full_record(), npz=True
    )

    png, sc_path = api.plot_trajectory(
        record_dir, tmp_path / "figures" / "fig-03.png", figure_id="fig-03", mode="3d"
    )

    sidecar = _read(png)
    assert png.is_file() and sc_path.is_file()
    assert "3D static" in sidecar["projection"]
    assert "camera-independent" in sidecar["projection"]
    assert shots[0]["elev"] == 20, shots[0].get("elev")
    assert shots[0]["azim"] == -60, shots[0].get("azim")


# ---------------------------------------------------------------------------
# Fig-02 - origin="Earth" dịch toạ độ vào khung body-relative (R13/R16)
# ---------------------------------------------------------------------------


def test_fig02_origin_earth_shifts_axes_into_body_relative_frame(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record_dir = _write_record(
        results_root, "experiment_C/tier_T2", _full_record(), npz=True
    )
    positions = np.load(record_dir / "trajectory.npz")["positions"]
    earth = BODIES.index("Earth")
    expected = positions - positions[:, earth : earth + 1, :]

    png, _ = api.plot_trajectory(
        record_dir,
        tmp_path / "figures" / "fig-02.png",
        figure_id="fig-02",
        mode="2d",
        origin="Earth",
    )

    sidecar = _read(png)
    assert sidecar["origin"].startswith("Earth-relative within ")
    xlim, ylim = shots[0]["xlim"], shots[0]["ylim"]
    for axis, values in ((xlim, expected[:, :, 0]), (ylim, expected[:, :, 1])):
        assert axis[0] <= values.min() <= values.max() <= axis[1], (
            f"axis {axis} does not cover the plotted extent {values.min()}..{values.max()}"
        )
    # The origin shift is what puts Earth itself on x=y=0; the unshifted
    # x range starts at 1e8 > 0, so 0 inside the limits proves the shift.
    assert xlim[0] <= 0.0 <= xlim[1]
    assert ylim[0] <= 0.0 <= ylim[1]


# ---------------------------------------------------------------------------
# V4 (R19) - record flat: PNG + sidecar source=stored + đủ khóa R6
# ---------------------------------------------------------------------------


def test_v4_flat_record_renders_stored_sidecar_with_r6_keys(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    record = _full_record()
    record["comparison"] = _flat_comparison()
    record_dir = _write_record(results_root, "experiment_A2/d1000", record)

    png, sc_path = api.plot_position_error(
        record_dir, tmp_path / "figures" / "fig-06.png", figure_id="fig-06"
    )

    sidecar = _read(png)
    assert png.is_file() and sc_path.is_file()
    assert sidecar["figure_id"] == "fig-06"
    assert sidecar["source"] == "stored"
    assert sidecar["gaps"] == [], "flat comparison is single-series by design"
    for key in R6_RECORD_KEYS:
        assert sidecar[key] == record[key], f"missing/incorrect R6 record key: {key}"
    assert "reference_kernel" not in sidecar, "no reference identity is looked up for V4"
    assert "kernel_sha256" not in sidecar


# ---------------------------------------------------------------------------
# V4 - record per_body: một đường cho mỗi series, đúng role
# ---------------------------------------------------------------------------


def test_v4_per_body_record_plots_one_line_per_series(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record = _full_record(bodies=["Earth", "Moon"])
    record["comparison"] = _per_body_comparison()
    record_dir = _write_record(results_root, "experiment_C/tier_T2", record)

    png, _ = api.plot_position_error(
        record_dir, tmp_path / "figures" / "fig-07.png", figure_id="fig-07"
    )

    sidecar = _read(png)
    assert sidecar["source"] == "stored"
    assert sidecar["gaps"] == []
    labels = [label for label, _, _ in shots[0]["lines"]]
    assert labels == ["Earth", "Moon"], labels
    styles = {(linestyle, marker) for _, linestyle, marker in shots[0]["lines"]}
    assert styles == {("-", "s")}, f"error role style must be solid+square: {styles}"


# ---------------------------------------------------------------------------
# V4 (R13) - trục bao trùm toàn bộ series, baseline y=0 không bị cắt
# ---------------------------------------------------------------------------


def test_v4_axes_cover_full_series_extent_and_zero_baseline(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record = _full_record()
    record["comparison"] = _flat_comparison()
    record_dir = _write_record(results_root, "experiment_A2/d1000", record)

    api.plot_position_error(
        record_dir, tmp_path / "figures" / "fig-06.png", figure_id="fig-06"
    )

    times = np.asarray(record["comparison"]["times_s"], dtype=np.float64)
    errors = np.asarray(record["comparison"]["position_error"], dtype=np.float64)
    xlim, ylim = shots[0]["xlim"], shots[0]["ylim"]
    assert xlim[0] <= times.min() and times.max() <= xlim[1], xlim
    assert ylim[0] <= 0.0, f"zero-error baseline cut off: {ylim}"
    assert errors.max() <= ylim[1], f"signal cut off: {ylim}"
    assert ylim[1] > errors.max(), "no headroom above the signal (R13 padding)"


# ---------------------------------------------------------------------------
# V5 (R20) - cùng nguồn KTD10, nhãn đơn vị vận tốc
# ---------------------------------------------------------------------------


def test_v5_velocity_error_uses_velocity_units(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record = _full_record(bodies=["Earth", "Moon"])
    record["comparison"] = _per_body_comparison()
    record_dir = _write_record(results_root, "experiment_C/tier_T2", record)

    png, _ = api.plot_velocity_error(
        record_dir, tmp_path / "figures" / "fig-08.png", figure_id="fig-08"
    )

    sidecar = _read(png)
    assert sidecar["source"] == "stored"
    assert sidecar["gaps"] == []
    assert "velocity error" in shots[0]["ylabel"], shots[0]["ylabel"]
    assert "m/s" in shots[0]["ylabel"], shots[0]["ylabel"]
    assert shots[0]["xlabel"] == "time (s)"
    labels = [label for label, _, _ in shots[0]["lines"]]
    assert labels == ["Earth", "Moon"], labels


# ---------------------------------------------------------------------------
# Fig-07 (integration) - 8 body thiếu error series -> gaps[] + annotation,
# figure VẪN được phát hành
# ---------------------------------------------------------------------------


def test_fig07_gap_annotation_for_bodies_without_error_series(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    bodies = (
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
    record = _full_record(bodies=list(bodies))
    record["comparison"] = _per_body_comparison(("Earth", "Moon"))
    record_dir = _write_record(results_root, "experiment_C/tier_T4", record)
    missing = [name for name in bodies if name not in ("Earth", "Moon")]
    assert len(missing) == 8, missing

    png, _ = api.plot_position_error(
        record_dir, tmp_path / "figures" / "fig-07.png", figure_id="fig-07"
    )

    sidecar = _read(png)
    assert png.is_file(), "a figure with gaps is still published"
    assert len(sidecar["gaps"]) == 8, sidecar["gaps"]
    assert {gap["name"] for gap in sidecar["gaps"]} == set(missing)
    for gap in sidecar["gaps"]:
        assert set(gap) == set(GAP_KEYS)
        assert gap["reason"] == "no stored error series"
        assert gap["source_path"].endswith("experiment_record.json")
    assert "gaps=8" in sidecar["caption"], sidecar["caption"]
    assert any("gap" in text for text in shots[0]["texts"]), shots[0]["texts"]
    labels = [label for label, _, _ in shots[0]["lines"]]
    assert labels == ["Earth", "Moon"], labels


# ---------------------------------------------------------------------------
# V3 (R18, AE1) - kernel-free: provider fixture + coverage, không sha256 (R12)
# ---------------------------------------------------------------------------


def test_v3_kernel_free_render_reports_fixture_identity(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    record = _full_record()
    record["reference_kernel"] = "kernels/de440s.bsp"
    record["kernel_sha256"] = "ab" * 32
    record_dir = _write_record(results_root, "experiment_E/horizon_1d", record, npz=True)

    png, sc_path = api.plot_model_vs_reference(
        record_dir,
        tmp_path / "figures" / "fig-05.png",
        body="Earth",
        figure_id="fig-05",
        kernel_path=tmp_path / "absent.bsp",
    )

    sidecar = _read(png)
    assert png.is_file() and sc_path.is_file()
    assert sidecar["source"] == "derived"
    assert sidecar["gaps"] == []
    assert sidecar["reference_provider"] == "fixture"
    assert sidecar["reference_kernel"] == "fixture"
    assert sidecar["coverage"]["intervals"] == [list(FIXTURE_INTERVAL)]
    assert "kernel_sha256" not in sidecar, (
        "one figure carries ONE reference identity: fixture, never a kernel hash"
    )
    assert sidecar["transform"].startswith("translation SSB(0) -> "), sidecar["transform"]
    assert "epoch" in sidecar, "record identity keys still extracted (R6)"


# ---------------------------------------------------------------------------
# V3 (AE2) - epoch vượt coverage fixture -> DataGapError, KHÔNG ghi file
# ---------------------------------------------------------------------------


def test_v3_epochs_outside_fixture_coverage_refuse_before_any_write(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    record_dir = _write_record(
        results_root,
        "experiment_E/horizon_365d",
        _full_record(),
        npz=True,
        times=np.array([0.0, 40.0 * DAY]),
    )
    out_dir = tmp_path / "figures"

    with pytest.raises(DataGapError) as exc:
        api.plot_model_vs_reference(
            record_dir,
            out_dir / "fig-05.png",
            body="Earth",
            figure_id="fig-05",
            kernel_path=tmp_path / "absent.bsp",
        )

    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["reason"] == "epochs outside coverage"
    assert "first outside et=" in gap["detail"], gap["detail"]
    json.dumps(exc.value.report)  # machine-readable, never a raw traceback
    assert not out_dir.exists(), "the refused series must leave no PNG behind"


# ---------------------------------------------------------------------------
# R9 - record reused: identity khai báo redirect + provenance không đầy đủ
# ---------------------------------------------------------------------------


def test_reused_record_reports_incomplete_provenance(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    target_record = _full_record(
        configuration_hash="hash-A", experiment_id="C/T2", bodies=["Earth", "Moon"]
    )
    target_record["comparison"] = _per_body_comparison()
    _write_record(results_root, "experiment_C/tier_T2", target_record)
    source = _write_record(
        results_root, "experiment_D/T2_30d", _reused_record("experiment_C/tier_T2", "hash-A")
    )

    png, _ = api.plot_position_error(
        source, tmp_path / "figures" / "fig-06.png", figure_id="fig-06"
    )

    sidecar = _read(png)
    assert png.is_file()
    assert sidecar["experiment_id"] == "D/T2_30d", "identity comes from the requested record"
    assert sidecar["reused_from"] == "experiment_C/tier_T2"
    assert sidecar["reused_chain"] == ["experiment_C/tier_T2"]
    assert sidecar["provenance_complete"] is False
    assert "epoch" in sidecar["missing_provenance"], sidecar["missing_provenance"]
    assert sidecar["gaps"] == [], "payload came from the resolved record"
    assert sidecar["source"] == "stored"


def test_reused_record_discloses_provenance_in_trajectory_sidecar(
    results_root: Path, tmp_path: Path
) -> None:
    _plt()
    target = _full_record(
        configuration_hash="hash-A", experiment_id="C/T2", bodies=["Earth", "Moon"]
    )
    _write_record(results_root, "experiment_C/tier_T2", target, npz=True)
    source = _write_record(
        results_root,
        "experiment_D/T2_30d",
        _reused_record("experiment_C/tier_T2", "hash-A"),
    )

    png, _ = api.plot_trajectory(
        source, tmp_path / "figures" / "fig-01.png", figure_id="fig-01"
    )

    sidecar = _read(png)
    assert png.is_file()
    assert sidecar["experiment_id"] == "D/T2_30d", "identity comes from the requested record"
    assert sidecar["reused_from"] == "experiment_C/tier_T2"
    assert sidecar["reused_chain"] == ["experiment_C/tier_T2"]
    assert sidecar["provenance_complete"] is False
    assert "epoch" in sidecar["missing_provenance"], sidecar["missing_provenance"]


def test_sources_entries_carry_per_member_r9_disclosure(results_root: Path) -> None:
    target = _full_record(
        configuration_hash="hash-A", experiment_id="C/T2", bodies=["Earth", "Moon"]
    )
    target["comparison"] = _per_body_comparison()
    _write_record(results_root, "experiment_C/tier_T2", target)
    reused = _write_record(
        results_root,
        "experiment_D/T2_30d",
        _reused_record("experiment_C/tier_T2", "hash-A"),
    )
    direct = _write_record(results_root, "experiment_A/rk4_n25", _full_record())
    payloads = [
        api._record_payload(api.load_record(path)) for path in (direct, reused)
    ]

    sidecar = api.build_sidecar(
        figure_id="fig-90",
        source="stored",
        frame="active_bodies_barycentric",
        origin="barycenter(Sun, Earth, Moon)",
        time_scale="TDB",
        units="m",
        arrays={"times_s": np.array([0.0, 1.0])},
        records=payloads,
    )
    entries = sidecar["sources"]
    assert len(entries) == 2
    assert "reused_from" not in entries[1], "RECORD_KEYS strips R9 keys outright"
    api._attach_member_provenance(sidecar, payloads)

    direct_entry, reused_entry = sidecar["sources"]
    assert direct_entry["provenance_complete"] is True
    assert direct_entry["missing_provenance"] == []
    assert "reused_from" not in direct_entry
    assert reused_entry["reused_from"] == "experiment_C/tier_T2"
    assert reused_entry["reused_chain"] == ["experiment_C/tier_T2"]
    assert reused_entry["provenance_complete"] is False
    assert "epoch" in reused_entry["missing_provenance"]
    json.dumps(sidecar)  # machine-readable, per-member disclosure


# ---------------------------------------------------------------------------
# R26 - record KHÔNG có comparison: re-derive read-only nếu coverage đủ
# ---------------------------------------------------------------------------


def test_v4_absent_comparison_rederives_from_readonly_lookup(
    results_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _plt()
    shots = _capture_axes(monkeypatch)
    record_dir = _write_record(
        results_root, "experiment_A1/rk4_n25", _full_record(), npz=True
    )

    png, _ = api.plot_position_error(
        record_dir,
        tmp_path / "figures" / "fig-06.png",
        figure_id="fig-06",
        kernel_path=tmp_path / "absent.bsp",
    )

    sidecar = _read(png)
    assert png.is_file()
    assert sidecar["source"] == "derived", "re-derived read-only, declared (R26)"
    assert sidecar["gaps"] == []
    assert sidecar["reference_kernel"] == "fixture"
    assert "kernel_sha256" not in sidecar
    labels = [label for label, _, _ in shots[0]["lines"]]
    assert labels == list(BODIES), labels
