"""Single-run figures V1-V5 + the Fig-01..Fig-08 registry (U5, R14-R26).

Four ``plot_*`` entry points, one record each (R14):

- ``plot_trajectory``        V1 (2D) / V2 (3D) straight from ``trajectory.npz``;
- ``plot_model_vs_reference`` V3 overlay vs the read-only lookup (KTD6 policy);
- ``plot_position_error``    V4 over the stored comparison (KTD10 normalize);
- ``plot_velocity_error``    V5, same source, velocity units.

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

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

from solar_ephemeris.ephemeris.comparison import assert_compatible
from solar_ephemeris.ephemeris.time import jd_tdb_to_et
from solar_ephemeris.ephemeris.types import ReferenceState
from solar_ephemeris.frames.transforms import recenter_ssb_to_model
from solar_ephemeris.physics.constants import SECONDS_PER_DAY
from solar_ephemeris.simulation.engine import Trajectory

from .gaps import DataGapError, make_gap
from .loader import RECORD_FILENAME, LoadedRecord, load_record, load_trajectory
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


#: R25 - Fig-01..Fig-08, fields verbatim from the HTD table; U6 appends
#: Fig-09..Fig-13 later. ``variant`` is the same full-§6d record for all.
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
