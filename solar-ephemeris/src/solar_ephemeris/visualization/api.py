"""Multi-run figures V6-V9 + the Fig-01..Fig-13 registry (U5 + U6, R14-R26).

Eight ``plot_*`` entry points (R14), one record each for V1-V5, a frozen
run-set (``composition.py``) for V6-V9:

- ``plot_trajectory``        V1 (2D) / V2 (3D) straight from ``trajectory.npz``;
- ``plot_model_vs_reference`` V3 overlay vs the read-only lookup (KTD6 policy);
- ``plot_position_error``    V4 over the stored comparison (KTD10 normalize);
- ``plot_velocity_error``    V5, same source, velocity units;
- ``plot_conservation``      V6 energy/momentum/angular-momentum, derived (R21);
- ``plot_convergence``       V7 A1 orders / A2+B lattices, never ranked (R22);
- ``plot_body_count``        V8 tier vs control, role signal/control (R23);
- ``plot_horizon_error``     V9 error per horizon + growth annotation (R24).

Contracts honoured here:

- R13: ``truthful_limits`` axis bounds, labels from ``units.py`` (SI default,
  AU/km/s opt-in per R10), frame + projection tokens in the caption;
- R12: ONE reference identity per figure - record ``reference_kernel`` /
  ``kernel_sha256`` are stripped before extraction, the lookup identity wins;
- R26: a record without ``comparison`` is re-derived read-only (or refused
  with ``DataGapError``), never guessed;
- R29: matplotlib is imported lazily inside each function - importing this
  module never loads it (Gate A runs without matplotlib);
- R27/KTD3: read-only - no simulation ever runs (AST-enforced).

Pipeline per figure: load (any unusable input -> ``DataGapError``) ->
``build_sidecar`` (``ensure_finite`` before render) -> ``style_context`` ->
artists -> ``write_figure`` (sidecar final BEFORE the PNG appears, KTD9).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from solar_ephemeris.analysis import (
    angular_momentum_series,
    momentum_series,
    total_energy,
)
from solar_ephemeris.ephemeris.comparison import assert_compatible
from solar_ephemeris.ephemeris.time import jd_tdb_to_et
from solar_ephemeris.ephemeris.types import ReferenceState
from solar_ephemeris.frames.transforms import recenter_ssb_to_model
from solar_ephemeris.physics.constants import SECONDS_PER_DAY
from solar_ephemeris.simulation.engine import Trajectory

from .composition import (
    A1_INTEGRATORS,
    A1_RUNSET,
    A2_RUNSET,
    B_LATTICE_REL,
    V8_RUNSET,
    V9_RUNSET,
)
from .gaps import DataGapError, make_gap
from .loader import (
    RECORD_FILENAME,
    RESULTS_DIRNAME,
    LoadedRecord,
    load_record,
    load_trajectory,
)
from .normalize import NormalizedComparison, normalize_comparison
from .providers import resolve_reference_series, select_provider
from .provenance import build_sidecar, write_figure
from .style import role_style, style_context, truthful_limits
from .units import (
    AU_LABEL,
    KMS_LABEL,
    M_LABEL,
    MS_LABEL,
    m_to_au,
    ms_to_kms,
    position_label,
    velocity_label,
)


@dataclass(frozen=True, slots=True)
class FigureSpec:
    """One row of the HTD figure table (design doc, "Bộ figure cụ thể")."""

    id: str
    title: str
    feature: str
    function: str
    records: str
    source: str
    variant: str
    state: str


#: R25 - Fig-01..Fig-13, fields verbatim from the HTD table.
#: ``variant`` is the same full-§6d record for all.
FIGURE_REGISTRY: Final[dict[str, FigureSpec]] = {
    "fig-01": FigureSpec(
        id="fig-01",
        title="Quỹ đạo hệ trong SSB-ICRS (XY, AU)",
        feature="V1",
        function="plot_trajectory",
        records="results/experiment_C/tier_T*",
        source="npz trực tiếp",
        variant="full §6d",
        state="kernel-agnostic",
    ),
    "fig-02": FigureSpec(
        id="fig-02",
        title="Zoom quỹ đạo Đất–Trăng",
        feature="V1",
        function="plot_trajectory",
        records="results/experiment_C/tier_T2",
        source="npz trực tiếp",
        variant="full §6d",
        state="kernel-agnostic",
    ),
    "fig-03": FigureSpec(
        id="fig-03",
        title="Bố cục 3D tĩnh 10 body",
        feature="V2",
        function="plot_trajectory",
        records="results/experiment_C/tier_T4",
        source="npz trực tiếp",
        variant="full §6d",
        state="kernel-agnostic",
    ),
    "fig-04": FigureSpec(
        id="fig-04",
        title="Model vs DE440 (Đất)",
        feature="V3",
        function="plot_model_vs_reference",
        records="results/experiment_C/tier_T2",
        source="lookup read-only (KTD6)",
        variant="full §6d",
        state="cần kernel",
    ),
    "fig-05": FigureSpec(
        id="fig-05",
        title="Model vs fixture (V3 kernel-free)",
        feature="V3",
        function="plot_model_vs_reference",
        records="results/experiment_E/horizon_1d",
        source="lookup read-only (KTD6)",
        variant="full §6d",
        state="kernel-free",
    ),
    "fig-06": FigureSpec(
        id="fig-06",
        title="Lỗi vị trí theo thời gian (formal D 7d)",
        feature="V4",
        function="plot_position_error",
        records="results/experiment_D/T{1,2}_7d",
        source="payload stored (normalize)",
        variant="full §6d",
        state="stored",
    ),
    "fig-07": FigureSpec(
        id="fig-07",
        title="Lỗi vị trí per-body theo tier (+gap 8 body)",
        feature="V4",
        function="plot_position_error",
        records="results/experiment_C/tier_T*",
        source="payload stored (normalize)",
        variant="full §6d",
        state="stored",
    ),
    "fig-08": FigureSpec(
        id="fig-08",
        title="Lỗi vận tốc per-body",
        feature="V5",
        function="plot_velocity_error",
        records="results/experiment_C/tier_T*",
        source="payload stored (normalize)",
        variant="full §6d",
        state="stored",
    ),
    "fig-09": FigureSpec(
        id="fig-09",
        title="Conservation: năng lượng/động lượng/động lượng góc",
        feature="V6",
        function="plot_conservation",
        records="results/experiment_C/tier_T2",
        source="npz + analysis (derived)",
        variant="full §6d",
        state="derived",
    ),
    "fig-10": FigureSpec(
        id="fig-10",
        title="Convergence A1: lỗi cuối vs N + observed orders + floor",
        feature="V7",
        function="plot_convergence",
        records="results/experiment_A1/* + *_orders.json",
        source="*_orders.json, analysis.json",
        variant="full §6d",
        state="aggregate",
    ),
    "fig-11": FigureSpec(
        id="fig-11",
        title="A2 divisor ratios + B ref-lattice (cảnh báo floor-dominated)",
        feature="V7",
        function="plot_convergence",
        records="results/experiment_A2/analysis.json, results/experiment_B/ref_summary.json",
        source="*_orders.json, analysis.json",
        variant="full §6d",
        state="aggregate",
    ),
    "fig-12": FigureSpec(
        id="fig-12",
        title="Ảnh hưởng số body (signal vs control)",
        feature="V8",
        function="plot_body_count",
        records="results/experiment_C/* + analysis.json",
        source="payload stored + signals",
        variant="full §6d",
        state="stored",
    ),
    "fig-13": FigureSpec(
        id="fig-13",
        title="Lỗi theo horizon 1/30/90/365d + annotation phân biệt",
        feature="V9",
        function="plot_horizon_error",
        records="results/experiment_E/horizon_*",
        source="payload stored + growth_class",
        variant="full §6d",
        state="stored",
    ),
}


# ---------------------------------------------------------------------------
# Shared helpers (no matplotlib at module scope - R29)
# ---------------------------------------------------------------------------


def _record_payload(loaded: LoadedRecord) -> dict:
    """R6 record keys from the REQUESTED record; kernel identity excluded.

    Stripping ``reference_kernel``/``kernel_sha256`` is the R12 rule: the
    figure's ONE reference identity comes from ``extra`` (lookup identity),
    never from a record that may name a different kernel.
    """
    return {
        key: value
        for key, value in loaded.record.items()
        if key not in ("reference_kernel", "kernel_sha256")
    }


def _record_extra(loaded: LoadedRecord) -> dict:
    """Provenance the record keys do not carry: completeness + redirect (R9)."""
    extra: dict[str, object] = {
        "provenance_complete": not loaded.missing_provenance,
        "missing_provenance": list(loaded.missing_provenance),
    }
    if loaded.reused_from is not None:
        extra["reused_from"] = loaded.reused_from
        extra["reused_chain"] = list(loaded.reused_chain)
    return extra


def _role_kwargs(role: str, index: int) -> dict:
    """Frozen role style; further series of the same role fade toward white.

    linestyle/marker never change (R15 grayscale distinction is path/marker
    only); only lightness separates series 1..n of one role.
    """
    kwargs = role_style(role)
    if index:
        from matplotlib.colors import to_rgba

        r, g, b, a = to_rgba(kwargs["color"])
        fade = min(0.6, 0.15 * index)
        kwargs["color"] = (
            r + (1.0 - r) * fade,
            g + (1.0 - g) * fade,
            b + (1.0 - b) * fade,
            a,
        )
    return kwargs


def _position_in(values: np.ndarray, unit: str) -> np.ndarray:
    """Positions to the display unit (SI default; AU opt-in, R10)."""
    position_label(unit)  # validates the token against the frozen table
    return m_to_au(values) if unit == AU_LABEL else np.asarray(values, dtype=np.float64)


def _velocity_in(values: np.ndarray, unit: str) -> np.ndarray:
    """Velocities to the display unit (SI default; km/s opt-in, R10)."""
    velocity_label(unit)
    return ms_to_kms(values) if unit == KMS_LABEL else np.asarray(values, dtype=np.float64)


def _reference_in_model_frame(
    traj: Trajectory,
    *,
    kernel_path: Path | str | None,
    source_path: str,
) -> tuple[np.ndarray, np.ndarray, str, dict]:
    """Reference states of EVERY body, translated into the model frame.

    Same order as ``compare_trajectory``: read-only fetch per body (coverage
    gate first - a shortfall refuses the whole series, KTD5) -> per-sample
    translation via ``recenter_ssb_to_model`` (never a rotation) -> exact
    transform descriptor -> ``assert_compatible`` BEFORE any subtraction.
    Returns (pos_rel, vel_rel, transform, provider identity).
    """
    meta = traj.meta.state_meta
    epochs_jd = meta.epoch_jd + traj.times / SECONDS_PER_DAY
    provider = select_provider(kernel_path)

    ref_pos = np.empty_like(traj.positions)
    ref_vel = np.empty_like(traj.velocities)
    first: dict[str, ReferenceState] = {}
    identity: dict = {}
    for k, name in enumerate(traj.body_names):
        series = resolve_reference_series(
            provider, body=name, epochs_jd=epochs_jd, source_path=source_path
        )
        for i, state in enumerate(series.states):
            ref_pos[i, k] = state.position_m
            ref_vel[i, k] = state.velocity_ms
        first[name] = series.states[0]
        identity = series.identity

    pos_rel = np.empty_like(ref_pos)
    vel_rel = np.empty_like(ref_vel)
    origin_r = np.empty((traj.n_samples, 3), dtype=np.float64)
    for i in range(traj.n_samples):
        p, v, r_o, _v_o = recenter_ssb_to_model(
            ref_pos[i], ref_vel[i], traj.gm, traj.body_names
        )
        pos_rel[i] = p
        vel_rel[i] = v
        origin_r[i] = r_o

    et0 = jd_tdb_to_et(meta.epoch_jd)
    transform = (  # human-readable, exact (mirrors comparison.py)
        f"translation SSB(0) -> {meta.origin} by GM-weighted barycentre of "
        f"({', '.join(traj.body_names)}); no rotation; "
        f"origin offset at et0={et0:.0f}s: {np.array2string(origin_r[0], precision=3)} m"
    )
    for name, state in first.items():
        assert_compatible(meta, state, body=name, transform=transform)
    return pos_rel, vel_rel, transform, identity


def _stored_series(
    norm: NormalizedComparison, resolved: dict, kind: str, record_path: str
) -> tuple[list[tuple[str, np.ndarray, np.ndarray]], list[dict]]:
    """Plotted series + gaps from a stored comparison (KTD10).

    ``flat`` is single-series by design (no missing-body gaps); ``per_body``
    earns one gap per record body that carries no series. Nothing usable ->
    the caller raises ``DataGapError`` instead of drawing an empty figure.
    """
    attr = f"{kind}_error"
    series: list[tuple[str, np.ndarray, np.ndarray]] = []
    gaps: list[dict] = []
    for name, entry in norm.by_body.items():
        values = getattr(entry, attr)
        if entry.times_s is None or values is None:
            gaps.append(
                make_gap(
                    name,
                    reason="no stored error series",
                    detail=f"comparison for {name!r} carries no {attr} series",
                    source_path=record_path,
                )
            )
            continue
        series.append(
            (
                name,
                np.asarray(entry.times_s, dtype=np.float64),
                np.asarray(values, dtype=np.float64),
            )
        )
    if norm.shape == "per_body":
        for name in resolved.get("bodies") or ():
            if name not in norm.by_body:
                gaps.append(
                    make_gap(
                        name,
                        reason="no stored error series",
                        detail=f"record body {name!r} has no comparison entry",
                        source_path=record_path,
                    )
                )
    return series, gaps


# ---------------------------------------------------------------------------
# V1 / V2 - trajectory straight from trajectory.npz
# ---------------------------------------------------------------------------


def plot_trajectory(
    record_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    mode: str = "2d",
    bodies: Sequence[str] | None = None,
    origin: str | None = None,
    unit: str = M_LABEL,
) -> tuple[Path, Path]:
    """V1 (2D XY) / V2 (static 3D) - npz only, kernel-agnostic.

    ``origin="<body>"`` recentres every sample on that body (Fig-02 zoom);
    the caption/sidecar then say ``<body>-relative within <model origin>``.
    """
    if mode not in ("2d", "3d"):
        raise ValueError(f"mode {mode!r} must be '2d' or '3d'")
    loaded = load_record(record_dir)
    traj = load_trajectory(record_dir)
    meta = traj.meta.state_meta
    frame = str(meta.frame)

    names = list(traj.body_names)
    positions = traj.positions
    if bodies is not None:
        keep = [names.index(name) for name in bodies]
        positions = positions[:, keep, :]
        names = [names[i] for i in keep]
    origin_desc = meta.origin
    if origin is not None:
        j = names.index(origin)
        positions = positions - positions[:, j : j + 1, :]
        origin_desc = f"{origin}-relative within {meta.origin}"

    positions = _position_in(positions, unit)
    label = position_label(unit)
    arrays = {"positions": positions}
    projection = (
        "3D static (elev=20, azim=-60, camera-independent)"
        if mode == "3d"
        else f"XY projection of {frame} (axes-aligned, no rotation)"
    )
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="stored",
        frame=frame,
        origin=origin_desc,
        time_scale=str(meta.time_scale),
        units=unit,
        arrays=arrays,
        records=_record_payload(loaded),
        projection=projection,
    )

    import matplotlib.pyplot as plt

    with style_context():
        if mode == "3d":
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d")
            ax.view_init(elev=20, azim=-60)
        else:
            fig, ax = plt.subplots()
        try:
            for index, name in enumerate(names):
                x, y = positions[:, index, 0], positions[:, index, 1]
                kwargs = _role_kwargs("model", index)
                if mode == "3d":
                    ax.plot(x, y, positions[:, index, 2], label=name, **kwargs)
                else:
                    ax.plot(x, y, label=name, **kwargs)
            ax.set_xlim(*truthful_limits(positions[..., 0]))
            ax.set_ylim(*truthful_limits(positions[..., 1]))
            ax.set_xlabel(f"x {label}")
            ax.set_ylabel(f"y {label}")
            if mode == "3d":
                ax.set_zlim(*truthful_limits(positions[..., 2]))
                ax.set_zlabel(f"z {label}")
            if len(names) > 1:
                ax.legend()
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


# ---------------------------------------------------------------------------
# V3 - model vs reference via the read-only lookup (KTD6)
# ---------------------------------------------------------------------------


def plot_model_vs_reference(
    record_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    body: str = "Earth",
    kernel_path: Path | str | None = None,
    unit: str = M_LABEL,
) -> tuple[Path, Path]:
    """V3 - model overlay vs the reference chain at the recorded epochs.

    Refuses BEFORE any file exists when an epoch falls outside provider
    coverage (``DataGapError``, KTD5); the sidecar carries the ONE reference
    identity (fixture id + coverage, or kernel sha256) plus the exact
    translation descriptor (R12).
    """
    loaded = load_record(record_dir)
    traj = load_trajectory(record_dir)
    index = traj.body_names.index(body)
    pos_rel, _vel_rel, transform, identity = _reference_in_model_frame(
        traj,
        kernel_path=kernel_path,
        source_path=str(loaded.resolved_dir / RECORD_FILENAME),
    )
    meta = traj.meta.state_meta
    frame = str(meta.frame)

    model = _position_in(traj.positions[:, index, :2], unit)
    reference = _position_in(pos_rel[:, index, :2], unit)
    arrays = {"model": model, "reference": reference}
    label = position_label(unit)
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="derived",
        frame=frame,
        origin=meta.origin,
        time_scale=str(meta.time_scale),
        units=unit,
        arrays=arrays,
        records=_record_payload(loaded),
        projection=f"XY projection of {frame} (axes-aligned, no rotation)",
        extra={**_record_extra(loaded), **identity, "transform": transform},
    )

    import matplotlib.pyplot as plt

    with style_context():
        fig, ax = plt.subplots()
        try:
            ax.plot(
                model[:, 0],
                model[:, 1],
                label=f"model {body}",
                **_role_kwargs("model", 0),
            )
            ax.plot(
                reference[:, 0],
                reference[:, 1],
                label=f"reference {body}",
                **_role_kwargs("reference", 0),
            )
            ax.set_xlim(*truthful_limits(model[:, 0], reference[:, 0]))
            ax.set_ylim(*truthful_limits(model[:, 1], reference[:, 1]))
            ax.set_xlabel(f"x {label}")
            ax.set_ylabel(f"y {label}")
            ax.legend()
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


# ---------------------------------------------------------------------------
# V4 / V5 - error series, stored or re-derived (R26)
# ---------------------------------------------------------------------------


def _plot_error(
    record_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    unit: str,
    kernel_path: Path | str | None,
    kind: str,
) -> tuple[Path, Path]:
    """V4 (position) / V5 (velocity): stored payload, else re-derive read-only."""
    loaded = load_record(record_dir)
    record_path = str(loaded.resolved_dir / RECORD_FILENAME)
    norm = normalize_comparison(loaded.resolved_record, source_path=record_path)

    identity: dict = {}
    if norm.absent:
        traj = load_trajectory(record_dir)
        pos_rel, vel_rel, _transform, identity = _reference_in_model_frame(
            traj, kernel_path=kernel_path, source_path=record_path
        )
        meta = traj.meta.state_meta
        frame, origin_desc, time_scale = str(meta.frame), meta.origin, str(meta.time_scale)
        if kind == "position":
            error = np.linalg.norm(traj.positions - pos_rel, axis=2)
        else:
            error = np.linalg.norm(traj.velocities - vel_rel, axis=2)
        series = [
            (name, traj.times.copy(), error[:, k])
            for k, name in enumerate(traj.body_names)
        ]
        gaps: list[dict] = []
        source = "derived"
    else:
        resolved = loaded.resolved_record
        series, gaps = _stored_series(norm, resolved, kind, record_path)
        frame = str(resolved.get("reference_frame") or "unspecified")
        origin_desc = str(resolved.get("reference_origin") or "unspecified")
        time_scale = str(resolved.get("time_scale") or "unspecified")
        source = "stored"

    if not series:
        if not gaps:
            gaps = [
                make_gap(
                    f"{kind}_error",
                    reason="no stored error series",
                    detail=f"record carries no usable {kind}_error series",
                    source_path=record_path,
                )
            ]
        raise DataGapError(gaps)

    convert = _position_in if kind == "position" else _velocity_in
    series = [(name, times, convert(values, unit)) for name, times, values in series]
    arrays: dict[str, np.ndarray] = {}
    for name, times, values in series:
        arrays[f"{name}_times_s"] = times
        arrays[f"{name}_{kind}_error"] = values

    if kind == "position":
        ylabel = position_label(unit).replace("position", "position error", 1)
    else:
        ylabel = velocity_label(unit).replace("velocity", "velocity error", 1)

    sidecar = build_sidecar(
        figure_id=figure_id,
        source=source,
        frame=frame,
        origin=origin_desc,
        time_scale=time_scale,
        units=unit,
        arrays=arrays,
        gaps=gaps,
        records=_record_payload(loaded),
        extra={**_record_extra(loaded), **identity},
    )

    import matplotlib.pyplot as plt

    with style_context():
        fig, ax = plt.subplots()
        try:
            for index, (name, times, values) in enumerate(series):
                ax.plot(times, values, label=name, **_role_kwargs("error", index))
            ax.set_xlim(*truthful_limits(*(times for _, times, _ in series)))
            ax.set_ylim(
                *truthful_limits(*(values for _, _, values in series), include_zero=True)
            )
            ax.set_xlabel("time (s)")
            ax.set_ylabel(ylabel)
            if len(series) > 1:
                ax.legend()
            if gaps:
                shown = ", ".join(gap["name"] for gap in gaps[:8])
                ax.text(
                    0.01,
                    0.02,
                    f"gaps: {len(gaps)} (missing {kind} series) - {shown}",
                    transform=ax.transAxes,
                    va="bottom",
                    fontsize=8,
                )
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


def plot_position_error(
    record_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    unit: str = M_LABEL,
    kernel_path: Path | str | None = None,
) -> tuple[Path, Path]:
    """V4 - position-error series (stored comparison, R26 re-derive if absent)."""
    return _plot_error(
        record_dir,
        png_path,
        figure_id=figure_id,
        unit=unit,
        kernel_path=kernel_path,
        kind="position",
    )


def plot_velocity_error(
    record_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    unit: str = MS_LABEL,
    kernel_path: Path | str | None = None,
) -> tuple[Path, Path]:
    """V5 - velocity-error series (same source as V4, velocity units)."""
    return _plot_error(
        record_dir,
        png_path,
        figure_id=figure_id,
        unit=unit,
        kernel_path=kernel_path,
        kind="velocity",
    )


# ---------------------------------------------------------------------------
# Multi-run helpers (V6-V9): run-set gaps, aggregate JSON, log limits (KTD5)
# ---------------------------------------------------------------------------

#: AE4 - mandated growth annotation when a horizon is undecidable (R24).
GROWTH_UNDISCRIMINATED: Final[str] = "không phân biệt — chỉ report"


def _require_results(results_dir: Path) -> Path:
    """A multi-run figure reads only a completed ``results/`` tree (R5)."""
    root = Path(results_dir).resolve()
    if RESULTS_DIRNAME not in root.parts:
        raise DataGapError(
            make_gap(
                f"{RESULTS_DIRNAME}/ directory",
                reason="outside results root",
                detail=f"results_dir {root} is not inside a {RESULTS_DIRNAME}/ directory",
                source_path=str(root),
            )
        )
    return root


def _check_runset(exp_dir: Path, members: Sequence[str], gaps: list[dict]) -> list[Path]:
    """Present member dirs of a frozen run-set; absent members become gaps."""
    present: list[Path] = []
    for name in members:
        record_path = exp_dir / name / RECORD_FILENAME
        if record_path.is_file():
            present.append(record_path.parent)
        else:
            gaps.append(
                make_gap(
                    name,
                    reason="missing run-set member",
                    detail=f"{record_path} does not exist",
                    source_path=str(record_path),
                )
            )
    return present


def _aggregate(path: Path, gaps: list[dict] | None = None) -> dict | None:
    """Read one aggregate JSON object; a failure is a gap, never a guess.

    ``gaps=None`` marks optional enrichment: a missing or broken file then
    returns ``None`` silently. With a list, the finding is recorded so the
    caller can raise it when nothing at all is plottable.
    """

    def broken(reason: str, detail: str) -> None:
        if gaps is not None:
            gaps.append(
                make_gap(path.name, reason=reason, detail=detail, source_path=str(path))
            )

    if not path.is_file():
        broken("missing aggregate", f"{path} does not exist")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        broken("unreadable aggregate", f"{path} cannot be parsed: {exc}")
        return None
    if not isinstance(payload, dict):
        broken(
            "unrecognized aggregate shape",
            f"{path} holds {type(payload).__name__}, expected a JSON object",
        )
        return None
    return payload


def _record_payloads(members: Sequence[Path], gaps: list[dict]) -> list[dict]:
    """R6 ``sources[]`` - one entry per contributing record; failures -> gaps."""
    payloads: list[dict] = []
    for member_dir in members:
        try:
            loaded = load_record(member_dir)
        except DataGapError as exc:
            gaps.extend(exc.gaps)
            continue
        payloads.append(_record_payload(loaded))
    return payloads


def _log_limits(*groups: np.ndarray, extra: Sequence[float] = ()) -> tuple[float, float]:
    """Axis limits for a log scale: every value strictly positive, finite (KTD5)."""
    values = [
        float(v)
        for group in groups
        for v in np.asarray(group, dtype=np.float64).ravel()
    ]
    values.extend(float(v) for v in extra)
    bad = [v for v in values if not (np.isfinite(v) and v > 0.0)]
    if not values or bad:
        raise DataGapError(
            make_gap(
                "log-scaled series",
                reason="non-positive values",
                detail=(
                    f"{len(bad)} of {len(values)} values are not strictly "
                    "positive and finite"
                ),
                source_path="in-memory arrays",
            )
        )
    lo, hi = min(values), max(values)
    if lo == hi:
        lo, hi = lo / 10.0, hi * 10.0
    pad = (hi / lo) ** 0.05
    return lo / pad, hi * pad


def _annotate_gaps(ax, gaps: Sequence[dict], limit: int = 8) -> None:
    """Bottom-left gap banner (KTD5): the figure publishes WITH its gaps."""
    if not gaps:
        return
    shown = ", ".join(str(gap["name"]) for gap in gaps[:limit])
    ax.text(
        0.01,
        0.02,
        f"gaps: {len(gaps)} - {shown}",
        transform=ax.transAxes,
        va="bottom",
        fontsize=8,
    )


def _frame_tokens(payloads: Sequence[dict]) -> tuple[str, str, str]:
    """frame / origin / time_scale of a multi-record figure (first source)."""
    if not payloads:
        return "unspecified", "unspecified", "unspecified"
    first = payloads[0]
    return (
        str(first.get("reference_frame") or "unspecified"),
        str(first.get("reference_origin") or "unspecified"),
        str(first.get("time_scale") or "unspecified"),
    )


def _member_comparison(
    member_dir: Path, gaps: list[dict]
) -> tuple[dict, NormalizedComparison, str, dict] | None:
    """Load one run-set member: (payload, normalized comparison, path, record).

    A member that cannot be read contributes a gap and no series (KTD5).
    """
    try:
        loaded = load_record(member_dir)
    except DataGapError as exc:
        gaps.extend(exc.gaps)
        return None
    record_path = str(loaded.resolved_dir / RECORD_FILENAME)
    norm = normalize_comparison(loaded.resolved_record, source_path=record_path)
    return _record_payload(loaded), norm, record_path, loaded.resolved_record


def _comparison_series(
    member: str,
    norm: NormalizedComparison,
    resolved: dict,
    record_path: str,
    gaps: list[dict],
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Stored position-error series of one member; one gap per body without."""
    series: list[tuple[str, np.ndarray, np.ndarray]] = []
    for body, entry in norm.by_body.items():
        if entry.times_s is None or entry.position_error is None:
            gaps.append(
                make_gap(
                    f"{member}/{body}",
                    reason="no stored error series",
                    detail=f"comparison for {body!r} carries no position_error series",
                    source_path=record_path,
                )
            )
            continue
        series.append(
            (
                body,
                np.asarray(entry.times_s, dtype=np.float64),
                np.asarray(entry.position_error, dtype=np.float64),
            )
        )
    if norm.shape == "per_body":
        for body in resolved.get("bodies") or ():
            if body not in norm.by_body:
                gaps.append(
                    make_gap(
                        f"{member}/{body}",
                        reason="no stored error series",
                        detail=f"record body {body!r} has no comparison entry",
                        source_path=record_path,
                    )
                )
    return series


# ---------------------------------------------------------------------------
# V6 - conservation derived from trajectory.npz via analysis/* (R21)
# ---------------------------------------------------------------------------


def plot_conservation(
    record_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
) -> tuple[Path, Path]:
    """V6 - ΔE / |ΔP| / |ΔL| of ONE trajectory; sidecar ``source: derived``."""
    loaded = load_record(record_dir)
    traj = load_trajectory(record_dir)
    times = np.asarray(traj.times, dtype=np.float64)

    energy = np.asarray(total_energy(traj), dtype=np.float64)
    momentum = np.asarray(momentum_series(traj), dtype=np.float64)
    angmom = np.asarray(angular_momentum_series(traj), dtype=np.float64)
    deltas: list[tuple[str, str, np.ndarray]] = [
        ("ΔE = E(t) − E(0) (J)", "delta_energy_J", energy - energy[0]),
        (
            "|ΔP| = |P(t) − P(0)| (kg m/s)",
            "delta_momentum_norm",
            np.linalg.norm(momentum - momentum[0], axis=1),
        ),
        (
            "|ΔL| = |L(t) − L(0)| (kg m^2/s)",
            "delta_angular_momentum_norm",
            np.linalg.norm(angmom - angmom[0], axis=1),
        ),
    ]
    arrays: dict[str, np.ndarray] = {"times_s": times}
    for _label, key, values in deltas:
        arrays[key] = np.asarray(values, dtype=np.float64)

    sources = [_record_payload(loaded)]
    frame, origin_desc, time_scale = _frame_tokens(sources)
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="derived",
        frame=frame,
        origin=origin_desc,
        time_scale=time_scale,
        units="J, kg m/s, kg m^2/s",
        arrays=arrays,
        records=sources,
        extra={
            **_record_extra(loaded),
            "derived_from": [
                "analysis.energy.total_energy",
                "analysis.momentum.momentum_series",
                "analysis.momentum.angular_momentum_series",
            ],
        },
    )

    import matplotlib.pyplot as plt

    with style_context():
        fig, axes = plt.subplots(1, 3)
        try:
            for ax, (label, _key, values) in zip(axes, deltas):
                ax.plot(times, values, label=label, **_role_kwargs("error", 0))
                ax.set_xlim(*truthful_limits(times))
                ax.set_ylim(*truthful_limits(values, include_zero=True))
                ax.set_xlabel("time (s)")
                ax.set_ylabel(label)
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


# ---------------------------------------------------------------------------
# V7 - convergence aggregates (A1 orders, A2 + B lattices), never ranked (R22)
# ---------------------------------------------------------------------------


def plot_convergence(
    results_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    variant: str = "a1",
) -> tuple[Path, Path]:
    """V7 - ``variant="a1"`` draws Fig-10 (final error, observed orders,
    roundoff floor); ``variant="a2b"`` draws Fig-11 (A2 divisor lattice + B
    ref-lattice with the floor-dominated warning). Both refuse to rank
    integrators (R22); missing run-set members and aggregates are gaps.
    """
    if variant not in ("a1", "a2b"):
        raise ValueError(f"variant {variant!r} must be 'a1' or 'a2b'")
    root = _require_results(results_dir)
    if variant == "a1":
        return _convergence_a1(root, png_path, figure_id)
    return _convergence_a2b(root, png_path, figure_id)


def _convergence_a1(root: Path, png_path: Path, figure_id: str) -> tuple[Path, Path]:
    exp_dir = root / "experiment_A1"
    gaps: list[dict] = []
    members = _check_runset(exp_dir, A1_RUNSET, gaps)
    sources = _record_payloads(members, gaps)

    arrays: dict[str, np.ndarray] = {}
    error_series: list[tuple[str, np.ndarray, np.ndarray]] = []
    order_series: list[tuple[str, np.ndarray, np.ndarray]] = []
    order_window = None
    floor: float | None = None
    for integrator in A1_INTEGRATORS:
        path = exp_dir / f"{integrator}_orders.json"
        payload = _aggregate(path, gaps)
        if payload is None:
            continue
        if order_window is None and isinstance(payload.get("order_window"), list):
            order_window = payload["order_window"]
        if floor is None and isinstance(payload.get("roundoff_floor_m"), (int, float)):
            floor = float(payload["roundoff_floor_m"])
        n_values = np.asarray(payload.get("n_values") or (), dtype=np.float64)
        errors = np.asarray(payload.get("errors_m") or (), dtype=np.float64)
        if n_values.size and errors.size:
            arrays[f"{integrator}_n_values"] = n_values
            arrays[f"{integrator}_errors_m"] = errors
            error_series.append((integrator, n_values, errors))
        else:
            gaps.append(
                make_gap(
                    f"{integrator}_orders",
                    reason="unrecognized aggregate shape",
                    detail=f"{path} carries no errors_m series",
                    source_path=str(path),
                )
            )
        observed = np.asarray(payload.get("observed_orders") or (), dtype=np.float64)
        observed = observed[: max(n_values.size - 1, 0)]
        if observed.size:
            arrays[f"{integrator}_observed_orders"] = observed
            order_series.append((integrator, n_values[1 : 1 + observed.size], observed))
    if not error_series:
        raise DataGapError(gaps)
    if floor is not None:
        arrays["roundoff_floor_m"] = np.atleast_1d(np.float64(floor))

    frame, origin_desc, time_scale = _frame_tokens(sources)
    extra: dict[str, object] = {
        "ranking": "none (R22)",
        "runset_members": [member.name for member in members],
    }
    if order_window is not None:
        extra["order_window"] = order_window
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="aggregate",
        frame=frame,
        origin=origin_desc,
        time_scale=time_scale,
        units="m, dimensionless order",
        arrays=arrays,
        gaps=gaps,
        records=sources,
        extra=extra,
    )

    import matplotlib.pyplot as plt

    with style_context():
        fig, (ax_error, ax_order) = plt.subplots(1, 2)
        try:
            for index, (name, n_values, errors) in enumerate(error_series):
                ax_error.plot(n_values, errors, label=name, **_role_kwargs("error", index))
            if floor is not None:
                ax_error.axhline(
                    floor, label="roundoff floor", **_role_kwargs("reference", 0)
                )
            x_groups = [n_values for _, n_values, _ in error_series]
            y_groups = [errors for _, _, errors in error_series]
            if floor is not None:
                y_groups.append(np.asarray([floor], dtype=np.float64))
            ax_error.set_xscale("log")
            ax_error.set_yscale("log")
            ax_error.set_xlim(*_log_limits(*x_groups))
            ax_error.set_ylim(*_log_limits(*y_groups))
            ax_error.set_xlabel("N")
            ax_error.set_ylabel("final position error (m)")
            for index, (name, x, observed) in enumerate(order_series):
                ax_order.plot(
                    x,
                    observed,
                    label=f"{name} observed orders",
                    **_role_kwargs("model", index),
                )
            if order_series:
                ax_order.set_xscale("log")
                ax_order.set_xlim(*_log_limits(*(x for _, x, _ in order_series)))
                ax_order.set_ylim(
                    *truthful_limits(
                        *(observed for _, _, observed in order_series),
                        include_zero=True,
                    )
                )
            ax_order.set_xlabel("N")
            ax_order.set_ylabel("observed order")
            _annotate_gaps(ax_error, gaps)
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


def _convergence_a2b(root: Path, png_path: Path, figure_id: str) -> tuple[Path, Path]:
    gaps: list[dict] = []
    a2_path = root / "experiment_A2" / "analysis.json"
    b_path = root / "experiment_B" / "ref_summary.json"
    analysis = _aggregate(a2_path, gaps)
    summary = _aggregate(b_path, gaps)
    if analysis is None and summary is None:
        raise DataGapError(gaps)

    members = [
        *_check_runset(root / "experiment_A2", A2_RUNSET, gaps),
        *_check_runset(root / "experiment_B" / B_LATTICE_REL, A2_RUNSET, gaps),
    ]
    sources = _record_payloads(members, gaps)

    arrays: dict[str, np.ndarray] = {}
    intervals: list[dict] = []
    a2_series: tuple[np.ndarray, np.ndarray] | None = None
    b_series: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None

    if analysis is not None:
        raw = analysis.get("D_by_divisor_m")
        pairs: list[tuple[int, float]] = []
        if isinstance(raw, dict):
            try:
                pairs = sorted((int(k), float(v)) for k, v in raw.items())
            except (TypeError, ValueError):
                pairs = []
        if pairs:
            a2_series = (
                np.asarray([p[0] for p in pairs], dtype=np.float64),
                np.asarray([p[1] for p in pairs], dtype=np.float64),
            )
            arrays["a2_divisors"] = a2_series[0]
            arrays["a2_D_by_divisor_m"] = a2_series[1]
        else:
            gaps.append(
                make_gap(
                    a2_path.name,
                    reason="unrecognized aggregate shape",
                    detail=f"{a2_path} carries no divisor -> error map",
                    source_path=str(a2_path),
                )
            )
        ratios = analysis.get("ratios")
        if isinstance(ratios, list):
            intervals = [
                entry
                for entry in ratios
                if isinstance(entry, dict) and entry.get("classification") == "floor-dominated"
            ]

    if summary is not None:
        rows = summary.get("per_divisor")
        parsed: list[tuple[int, float, float]] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                try:
                    parsed.append(
                        (
                            int(row["divisor"]),
                            float(row["rk4_max_E_pos_m"]),
                            float(row["verlet_max_E_pos_m"]),
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
        if parsed:
            b_series = (
                np.asarray([r[0] for r in parsed], dtype=np.float64),
                np.asarray([r[1] for r in parsed], dtype=np.float64),
                np.asarray([r[2] for r in parsed], dtype=np.float64),
            )
            arrays["b_divisors"] = b_series[0]
            arrays["b_rk4_max_E_pos_m"] = b_series[1]
            arrays["b_verlet_max_E_pos_m"] = b_series[2]
        else:
            gaps.append(
                make_gap(
                    b_path.name,
                    reason="unrecognized aggregate shape",
                    detail=f"{b_path} carries no per_divisor rows",
                    source_path=str(b_path),
                )
            )

    if a2_series is None and b_series is None:
        raise DataGapError(gaps)

    frame, origin_desc, time_scale = _frame_tokens(sources)
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="aggregate",
        frame=frame,
        origin=origin_desc,
        time_scale=time_scale,
        units="m",
        arrays=arrays,
        gaps=gaps,
        records=sources,
        extra={
            "ranking": "none (R22)",
            "runset_members": [member.name for member in members],
            "floor_dominated_intervals": intervals,
        },
    )

    import matplotlib.pyplot as plt

    with style_context():
        n_panels = int(a2_series is not None) + int(b_series is not None)
        fig, axes = plt.subplots(1, n_panels)
        axes = np.atleast_1d(axes)
        try:
            shown = 0
            if a2_series is not None:
                ax = axes[shown]
                shown += 1
                x, y = a2_series
                ax.plot(x, y, label="A2 max E_pos", **_role_kwargs("error", 0))
                ax.set_xlabel("divisor")
                ax.set_ylabel("max E_pos (m)")
                ax.set_xlim(*truthful_limits(x))
                ax.set_ylim(*truthful_limits(y, include_zero=True))
                if intervals:
                    described = ", ".join(
                        f"{entry.get('from_divisor')}->{entry.get('to_divisor')}"
                        for entry in intervals
                    )
                    ax.text(
                        0.01,
                        0.98,
                        f"floor-dominated: {described}",
                        transform=ax.transAxes,
                        va="top",
                        fontsize=8,
                    )
            if b_series is not None:
                ax = axes[shown]
                x, rk4_y, verlet_y = b_series
                ax.plot(x, rk4_y, label="rk4", **_role_kwargs("model", 0))
                ax.plot(x, verlet_y, label="verlet", **_role_kwargs("model", 1))
                ax.set_xlabel("divisor")
                ax.set_ylabel("max E_pos (m)")
                ax.set_xlim(*truthful_limits(x))
                ax.set_ylim(*truthful_limits(rk4_y, verlet_y, include_zero=True))
                ax.text(
                    0.01,
                    0.98,
                    "no integrator ranking (R22)",
                    transform=ax.transAxes,
                    va="top",
                    fontsize=8,
                )
            _annotate_gaps(axes[0], gaps)
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


# ---------------------------------------------------------------------------
# V8 - tier vs control error series (signal / control roles, R23)
# ---------------------------------------------------------------------------


def plot_body_count(
    results_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    unit: str = M_LABEL,
) -> tuple[Path, Path]:
    """V8 - stored position-error series of every experiment C run-set member.

    Roles follow the frozen style table (tier -> ``signal``, control ->
    ``control``); a body without a stored series and a member that was never
    produced are ``gaps[]`` entries (KTD5), never silently dropped.
    """
    root = _require_results(results_dir)
    exp_dir = root / "experiment_C"
    gaps: list[dict] = []
    members = _check_runset(exp_dir, V8_RUNSET, gaps)

    sources: list[dict] = []
    series: list[tuple[str, str, str, int, np.ndarray, np.ndarray]] = []
    fade: dict[str, int] = {}
    for member_dir in members:
        member = member_dir.name
        found = _member_comparison(member_dir, gaps)
        if found is None:
            continue
        payload, norm, record_path, resolved = found
        sources.append(payload)
        role = "control" if member.startswith("control_") else "signal"
        before = len(gaps)
        body_series = _comparison_series(member, norm, resolved, record_path, gaps)
        if not body_series and len(gaps) == before:
            gaps.append(
                make_gap(
                    member,
                    reason="no stored error series",
                    detail=f"{member} carries no comparison payload",
                    source_path=record_path,
                )
            )
        for body, times, values in body_series:
            index = fade.get(role, 0)
            fade[role] = index + 1
            series.append(
                (role, member, body, index, times, _position_in(values, unit))
            )

    if not series:
        if not gaps:
            gaps.append(
                make_gap(
                    "experiment C",
                    reason="no stored error series",
                    detail=f"no run-set member under {exp_dir} carries a series",
                    source_path=str(exp_dir),
                )
            )
        raise DataGapError(gaps)

    arrays: dict[str, np.ndarray] = {}
    for _role, member, body, _index, times, values in series:
        arrays[f"{member}__{body}_times_s"] = times
        arrays[f"{member}__{body}_position_error"] = values

    frame, origin_desc, time_scale = _frame_tokens(sources)
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="stored",
        frame=frame,
        origin=origin_desc,
        time_scale=time_scale,
        units=unit,
        arrays=arrays,
        gaps=gaps,
        records=sources,
        extra={"runset_members": [member.name for member in members]},
    )

    ylabel = position_label(unit).replace("position", "position error", 1)

    import matplotlib.pyplot as plt

    with style_context():
        fig, ax = plt.subplots()
        try:
            plotted: list[tuple[np.ndarray, np.ndarray]] = []
            for role, member, body, index, times, values in series:
                ax.plot(
                    times,
                    values,
                    label=f"{member}: {body}",
                    **_role_kwargs(role, index),
                )
                plotted.append((times, values))
            ax.set_xlim(*truthful_limits(*(t for t, _ in plotted)))
            ax.set_ylim(*truthful_limits(*(v for _, v in plotted), include_zero=True))
            ax.set_xlabel("time (s)")
            ax.set_ylabel(ylabel)
            if len(plotted) > 1:
                ax.legend()
            _annotate_gaps(ax, gaps)
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)


# ---------------------------------------------------------------------------
# V9 - horizon error series + AE4 growth annotation (R24)
# ---------------------------------------------------------------------------


def plot_horizon_error(
    results_dir: Path,
    png_path: Path,
    *,
    figure_id: str,
    unit: str = M_LABEL,
) -> tuple[Path, Path]:
    """V9 - stored position-error series per horizon; growth READ, never fit.

    ``growth_classification`` comes from each record: if any run-set member
    is not discriminated, the figure carries the AE4 annotation and the
    sidecar says so in machine-readable form.
    """
    root = _require_results(results_dir)
    exp_dir = root / "experiment_E"
    gaps: list[dict] = []
    members = _check_runset(exp_dir, V9_RUNSET, gaps)

    sources: list[dict] = []
    series: list[tuple[str, str, str, int, np.ndarray, np.ndarray]] = []
    fade: dict[str, int] = {}
    classifications: dict[str, str | None] = {}
    undecidable: list[str] = []
    for member_dir in members:
        member = member_dir.name
        found = _member_comparison(member_dir, gaps)
        if found is None:
            continue
        payload, norm, record_path, resolved = found
        sources.append(payload)
        growth = resolved.get("growth_classification")
        if isinstance(growth, dict) and growth.get("discriminated") is True:
            selected = growth.get("selected")
            classifications[member] = str(selected) if selected is not None else None
        else:
            classifications[member] = None
            undecidable.append(member)
        before = len(gaps)
        body_series = _comparison_series(member, norm, resolved, record_path, gaps)
        if not body_series and len(gaps) == before:
            gaps.append(
                make_gap(
                    member,
                    reason="no stored error series",
                    detail=f"{member} carries no comparison payload",
                    source_path=record_path,
                )
            )
        for body, times, values in body_series:
            index = fade.get("error", 0)
            fade["error"] = index + 1
            series.append(
                ("error", member, body, index, times, _position_in(values, unit))
            )

    if not series:
        if not gaps:
            gaps.append(
                make_gap(
                    "experiment E",
                    reason="no stored error series",
                    detail=f"no horizon under {exp_dir} carries a series",
                    source_path=str(exp_dir),
                )
            )
        raise DataGapError(gaps)

    arrays: dict[str, np.ndarray] = {}
    for _role, member, body, _index, times, values in series:
        arrays[f"{member}__{body}_times_s"] = times
        arrays[f"{member}__{body}_position_error"] = values

    extra: dict[str, object] = {
        "runset_members": [member.name for member in members],
        "growth_discriminated": not undecidable,
        "growth_classification": classifications,
        "growth_undecidable_members": undecidable,
    }
    if undecidable:
        extra["growth_annotation"] = GROWTH_UNDISCRIMINATED
    frame, origin_desc, time_scale = _frame_tokens(sources)
    sidecar = build_sidecar(
        figure_id=figure_id,
        source="stored",
        frame=frame,
        origin=origin_desc,
        time_scale=time_scale,
        units=unit,
        arrays=arrays,
        gaps=gaps,
        records=sources,
        extra=extra,
    )

    ylabel = position_label(unit).replace("position", "position error", 1)

    import matplotlib.pyplot as plt

    with style_context():
        fig, ax = plt.subplots()
        try:
            for role, member, body, index, times, values in series:
                ax.plot(
                    times,
                    values,
                    label=f"{member} {body}",
                    **_role_kwargs(role, index),
                )
            ax.set_xlim(
                *truthful_limits(*(t for _r, _m, _b, _i, t, _v in series))
            )
            ax.set_ylim(
                *truthful_limits(
                    *(v for _r, _m, _b, _i, _t, v in series), include_zero=True
                )
            )
            ax.set_xlabel("time (s)")
            ax.set_ylabel(ylabel)
            if len(series) > 1:
                ax.legend()
            if undecidable:
                ax.text(
                    0.01,
                    0.98,
                    GROWTH_UNDISCRIMINATED,
                    transform=ax.transAxes,
                    va="top",
                    fontsize=9,
                )
            _annotate_gaps(ax, gaps)
            return write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)
