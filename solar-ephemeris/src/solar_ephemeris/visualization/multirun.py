"""Multi-run figures V6-V9 and their run-set helpers (U6, R21-R24).

- ``plot_conservation``      V6 energy/momentum/angular-momentum, derived (R21);
- ``plot_convergence``       V7 A1 orders / A2+B lattices, never ranked (R22);
- ``plot_body_count``        V8 tier vs control, role signal/control (R23);
- ``plot_horizon_error``     V9 error per horizon + growth annotation (R24).

Re-exported by ``visualization.api``; matplotlib is imported lazily inside
each function (R29).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import numpy as np

from solar_ephemeris.analysis import (
    angular_momentum_series,
    momentum_series,
    total_energy,
)

from .composition import (
    A1_INTEGRATORS,
    A1_RUNSET,
    A2_RUNSET,
    B_LATTICE_REL,
    V8_RUNSET,
    V9_RUNSET,
)
from .gaps import DataGapError, make_gap
from .helpers import (
    _annotate_gaps,
    _attach_member_provenance,
    _error_ylabel,
    _frame_tokens,
    _position_in,
    _record_extra,
    _record_payload,
    _role_kwargs,
    _stored_series,
)
from .loader import (
    RECORD_FILENAME,
    RESULTS_DIRNAME,
    load_record,
    load_trajectory_from,
)
from .normalize import NormalizedComparison, normalize_comparison
from .provenance import build_sidecar
from .style import style_context, truthful_limits
from .units import M_LABEL


def _write_figure(fig, *, png_path, sidecar, arrays):
    """Render via ``api.write_figure`` (callers patch the api-module binding)."""
    from . import api

    return api.write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)


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


def _collect_runset_series(
    members: Sequence[Path],
    *,
    role_for,
    gaps: list[dict],
    unit: str,
) -> tuple[
    list[dict],
    list[tuple[str, str, str, int, np.ndarray, np.ndarray]],
    dict[str, dict],
]:
    """Stored position-error series of every present member (V8/V9 shared).

    Returns ``(sources, series, resolved_by_member)``; each member unable to
    contribute a series leaves a ``gaps[]`` entry instead of raising (KTD5).
    """
    sources: list[dict] = []
    series: list[tuple[str, str, str, int, np.ndarray, np.ndarray]] = []
    fade: dict[str, int] = {}
    resolved_by_member: dict[str, dict] = {}
    for member_dir in members:
        member = member_dir.name
        found = _member_comparison(member_dir, gaps)
        if found is None:
            continue
        payload, norm, record_path, resolved = found
        sources.append(payload)
        resolved_by_member[member] = resolved
        role = role_for(member)
        before = len(gaps)
        body_series, _ = _stored_series(
            norm,
            resolved,
            "position",
            record_path,
            prefix=f"{member}/",
            gaps=gaps,
        )
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
    return sources, series, resolved_by_member


def _series_arrays(
    series: Sequence[tuple[str, str, str, int, np.ndarray, np.ndarray]],
) -> dict[str, np.ndarray]:
    """Sidecar arrays of run-set series: ``<member>__<body>_*`` keys."""
    arrays: dict[str, np.ndarray] = {}
    for _role, member, body, _index, times, values in series:
        arrays[f"{member}__{body}_times_s"] = times
        arrays[f"{member}__{body}_position_error"] = values
    return arrays


def _require_any_series(
    series: Sequence, gaps: list[dict], empty_name: str, empty_detail: str, exp_dir: Path
) -> None:
    """No member carried anything plottable -> refuse the whole figure (KTD4)."""
    if series:
        return
    if not gaps:
        gaps.append(
            make_gap(
                empty_name,
                reason="no stored error series",
                detail=empty_detail,
                source_path=str(exp_dir),
            )
        )
    raise DataGapError(gaps)


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
    traj = load_trajectory_from(loaded)
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
            return _write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
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
    _attach_member_provenance(sidecar, sources)

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
            return _write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
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
    _attach_member_provenance(sidecar, sources)

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
            return _write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
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

    sources, series, _resolved_by_member = _collect_runset_series(
        members,
        role_for=lambda member: "control" if member.startswith("control_") else "signal",
        gaps=gaps,
        unit=unit,
    )
    _require_any_series(
        series,
        gaps,
        "experiment C",
        f"no run-set member under {exp_dir} carries a series",
        exp_dir,
    )
    arrays = _series_arrays(series)

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
    _attach_member_provenance(sidecar, sources)

    ylabel = _error_ylabel("position", unit)

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
            return _write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
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

    sources, series, resolved_by_member = _collect_runset_series(
        members,
        role_for=lambda _member: "error",
        gaps=gaps,
        unit=unit,
    )
    _require_any_series(
        series,
        gaps,
        "experiment E",
        f"no horizon under {exp_dir} carries a series",
        exp_dir,
    )

    classifications: dict[str, str | None] = {}
    undecidable: list[str] = []
    for member, resolved in resolved_by_member.items():
        growth = resolved.get("growth_classification")
        if isinstance(growth, dict) and growth.get("discriminated") is True:
            selected = growth.get("selected")
            classifications[member] = str(selected) if selected is not None else None
        else:
            classifications[member] = None
            undecidable.append(member)

    arrays = _series_arrays(series)

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
    _attach_member_provenance(sidecar, sources)

    ylabel = _error_ylabel("position", unit)

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
            return _write_figure(fig, png_path=png_path, sidecar=sidecar, arrays=arrays)
        finally:
            plt.close(fig)
