"""Validation comparison layer (requirements 6, 12, 13).

The only place reference and model states are ever allowed near each other:
``assert_compatible`` runs the 7-class mismatch matrix FIRST (body → frame →
center/origin → epoch_jd → time_scale → length_unit → velocity_unit), then
and only then are vectors subtracted (requirement 6). Statistics are what
the samples say — no fitting, no smoothing, no alignment search (Phase-3
rule inherited).

Frame rule is two-sided, not equality: the model must be
``ACTIVE_BODIES_BARYCENTRIC``, the reference must be ``SSB_ICRS`` — they
differ by the documented translation ``transform`` descriptor, never by an
undetected rotation (R8: transform layer is translation-only).

Backend-agnostic: talks to the ``ReferenceProvider`` protocol only, never
SPICE. Requires ``ic_source`` (R4): a comparison cannot exist without saying
where its initial conditions came from.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.ephemeris.mapping import naif_id
from solar_ephemeris.ephemeris.reference import ReferenceProvider
from solar_ephemeris.ephemeris.time import jd_tdb_to_et
from solar_ephemeris.ephemeris.types import (
    MetadataMismatchError,
    ReferenceMetadata,
    ReferenceState,
)
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.frames.transforms import recenter_ssb_to_model
from solar_ephemeris.physics.state import StateMeta
from solar_ephemeris.simulation.engine import Trajectory


@dataclass(frozen=True, slots=True)
class ErrorStatistics:
    mean: float
    median: float
    max: float
    percentiles: Mapping[str, float]  # {"p95": ...} — caller-configurable
    n_samples: int


def error_statistics(
    err: NDArray[np.float64], percentiles: Sequence[float] = (95,)
) -> ErrorStatistics:
    """mean/median/max + percentile dict (np.percentile, method='linear')."""
    arr = np.asarray(err, dtype=np.float64)
    if arr.ndim != 1 or arr.size == 0:
        raise ValueError(f"error array must be 1-D and non-empty, got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError("error array contains NaN or inf")
    if len(percentiles) == 0:
        raise ValueError("at least one percentile is required")
    pct: dict[str, float] = {}
    for p in percentiles:
        if not 0.0 <= float(p) <= 100.0:
            raise ValueError(f"percentile {p!r} outside [0, 100]")
        key = f"p{float(p):g}"
        if key in pct:
            raise ValueError(f"duplicate percentile {p!r}")
        pct[key] = float(np.percentile(arr, float(p), method="linear"))
    return ErrorStatistics(
        mean=float(np.mean(arr)),
        median=float(np.median(arr)),
        max=float(np.max(arr)),
        percentiles=pct,
        n_samples=int(arr.size),
    )


def relative_error(
    err: NDArray[np.float64], norms: NDArray[np.float64]
) -> NDArray[np.float64]:
    """E_rel = err / |ref| with an explicit zero-denominator guard."""
    err = np.asarray(err, dtype=np.float64)
    norms = np.asarray(norms, dtype=np.float64)
    if err.shape != norms.shape:
        raise ValueError(f"shapes differ: {err.shape} vs {norms.shape}")
    if np.any(norms == 0.0):
        raise ValueError(
            "relative-error denominator is zero (|r_ref| == 0); "
            "relative error undefined"
        )
    return err / norms


def assert_compatible(
    model_meta: StateMeta,
    ref: ReferenceState,
    *,
    body: str,
    transform: str | None = None,
) -> None:
    """7-class mismatch matrix, run BEFORE any subtraction (requirement 6).

    Order (mandate 18, one exception class each):

    1. ``body`` — queried body must be the reference state's body.
    2. ``frame`` — model must be ``ACTIVE_BODIES_BARYCENTRIC`` AND reference
       must be ``SSB_ICRS`` (two-sided; they are *documented* to differ by
       the translation in ``transform``, never by equality).
    3. ``center`` — a non-empty transform descriptor must be present (the
       documented bridge SSB → model origin) and the reference center must
       be its native ``ssb(0)``.
    4. ``epoch_jd`` — exact ``==``, the same rule as ``engine._align``.
    5. ``time_scale`` — model must be TDB (reference states are TDB by
       construction; non-TDB is refused, never converted).
    6. ``length_unit`` — must be ``m``.
    7. ``velocity_unit`` — must be ``m/s``.

    Structural check (no isinstance gate): ``StateMeta`` itself already
    refuses non-m/m/s units at construction, so classes 6-7 are
    belt-and-suspenders here and are exercised with stand-in metadata.
    Raises MetadataMismatchError(field, model_value, reference_value).
    """
    if ref.body != body:
        raise MetadataMismatchError("body", body, ref.body)
    if model_meta.frame is not ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC:
        raise MetadataMismatchError(
            "frame",
            model_meta.frame,
            ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        )
    if ref.frame is not ReferenceFrame.SSB_ICRS:
        raise MetadataMismatchError("frame", ref.frame, ReferenceFrame.SSB_ICRS)
    if not transform or not transform.strip():
        raise MetadataMismatchError(
            "center", model_meta.origin, "<missing transform descriptor>"
        )
    if ref.center != "ssb(0)":
        raise MetadataMismatchError("center", ref.center, "ssb(0)")
    if model_meta.epoch_jd != ref.epoch_jd:
        raise MetadataMismatchError("epoch_jd", model_meta.epoch_jd, ref.epoch_jd)
    if model_meta.time_scale is not TimeScale.TDB:
        raise MetadataMismatchError("time_scale", model_meta.time_scale, TimeScale.TDB)
    if model_meta.length_unit != "m":
        raise MetadataMismatchError("length_unit", model_meta.length_unit, "m")
    if model_meta.velocity_unit != "m/s":
        raise MetadataMismatchError(
            "velocity_unit", model_meta.velocity_unit, "m/s"
        )


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    body: str
    epoch_jd: float
    times_s: NDArray[np.float64]  # (M,), s since epoch (model grid)
    model_metadata: Mapping[str, object]  # frame/origin/units/integrator/…
    reference_metadata: ReferenceMetadata
    transform: str  # exact transform applied (translation, R8)
    position_error: NDArray[np.float64]  # (M,), m
    velocity_error: NDArray[np.float64]  # (M,), m/s
    position_stats: ErrorStatistics
    velocity_stats: ErrorStatistics
    relative_position_error: NDArray[np.float64]  # (M,), dimensionless

    def to_dict(self) -> dict[str, object]:
        """Machine-readable audit record (comparison_record.json payload).

        Answers "which DE440 data generated this result?": kernel filename +
        sha256 + coverage + retrieval date + body IDs + frame/center + time
        standard + native units + spiceypy version, plus the model side
        (integrator, dt, config_hash, ic_source) and the exact transform.
        """
        return {
            "schema_version": 1,
            "body": self.body,
            "epoch_jd": self.epoch_jd,
            "times_s": self.times_s.tolist(),
            "model_metadata": dict(self.model_metadata),
            "reference_metadata": self.reference_metadata.to_dict(),
            "transform": self.transform,
            "position_error": self.position_error.tolist(),
            "velocity_error": self.velocity_error.tolist(),
            "position_stats": _stats_to_dict(self.position_stats),
            "velocity_stats": _stats_to_dict(self.velocity_stats),
            "relative_position_error": self.relative_position_error.tolist(),
        }


def _stats_to_dict(stats: ErrorStatistics) -> dict[str, object]:
    return {
        "mean": stats.mean,
        "median": stats.median,
        "max": stats.max,
        "percentiles": dict(stats.percentiles),
        "n_samples": stats.n_samples,
    }


def compare_trajectory(
    traj: Trajectory,
    provider: ReferenceProvider,
    *,
    body: str,
    ic_source: str,
    percentiles: Sequence[float] = (95,),
) -> ComparisonResult:
    """Compare a model trajectory against reference states, sample by sample.

    Computation order (plan §9 — reference query first, gate, then math):

    1. map ``body`` → NAIF ID (raises if unmapped);
    2. ``et0 = jd_tdb_to_et(epoch_jd)``; per-sample epochs are
       ``et0 + t_s`` only — no per-sample JD round-trip anywhere (R9);
    3. query the provider for every model body × every epoch (coverage
       checked per epoch by the provider);
    4. translate reference states from SSB to the model origin with the
       translation-only transform layer (frames/transforms, never metrics);
    5. ``assert_compatible`` — BEFORE any subtraction;
    6. E_pos, E_vel, E_rel per sample;
    7. statistics on both arrays; ``ic_source`` recorded verbatim.

    No fitting, no smoothing, no alignment search.
    """
    if not ic_source or not ic_source.strip():
        raise ValueError(
            "ic_source is required: record where the initial conditions came "
            "from (e.g. 'reference-ingested via ephemeris/ic.py')"
        )
    naif_id(body)  # step 1: unmapped body raises UnknownBodyMappingError
    if body not in traj.body_names:
        raise MetadataMismatchError("body", body, tuple(traj.body_names))

    meta = traj.meta.state_meta
    et0 = jd_tdb_to_et(meta.epoch_jd)  # step 2
    epochs_et = et0 + traj.times

    n_m, n_n = traj.n_samples, traj.n_bodies  # step 3
    ref_pos = np.empty((n_m, n_n, 3), dtype=np.float64)
    ref_vel = np.empty((n_m, n_n, 3), dtype=np.float64)
    first_states: dict[str, ReferenceState] = {}
    for i, et in enumerate(epochs_et):
        for k, name in enumerate(traj.body_names):
            state = provider.state_at(body=name, et=float(et))
            ref_pos[i, k] = state.position_m
            ref_vel[i, k] = state.velocity_ms
            if i == 0:
                first_states[name] = state

    k_body = traj.body_names.index(body)
    pos_rel = np.empty_like(ref_pos)  # step 4: transform layer, not metrics
    vel_rel = np.empty_like(ref_vel)
    origin_r = np.empty((n_m, 3), dtype=np.float64)
    for i in range(n_m):
        p, v, r_o, _v_o = recenter_ssb_to_model(
            ref_pos[i], ref_vel[i], traj.gm, traj.body_names
        )
        pos_rel[i] = p
        vel_rel[i] = v
        origin_r[i] = r_o

    transform = (  # human-readable, exact
        f"translation SSB(0) -> {meta.origin} by GM-weighted barycentre of "
        f"({', '.join(traj.body_names)}); no rotation; "
        f"origin offset at et0={et0:.0f}s: {np.array2string(origin_r[0], precision=3)} m"
    )
    assert_compatible(  # step 5 — gate before subtraction
        meta, first_states[body], body=body, transform=transform
    )

    model_pos = traj.positions[:, k_body, :]
    model_vel = traj.velocities[:, k_body, :]
    ref_norms = np.linalg.norm(pos_rel[:, k_body, :], axis=1)
    position_error = np.linalg.norm(model_pos - pos_rel[:, k_body, :], axis=1)
    velocity_error = np.linalg.norm(model_vel - vel_rel[:, k_body, :], axis=1)
    relative = relative_error(position_error, ref_norms)  # step 6 guard

    model_metadata: dict[str, object] = {  # auditable model side (R13/R16)
        "frame": str(meta.frame.value),
        "origin": meta.origin,
        "epoch_jd": meta.epoch_jd,
        "time_scale": str(meta.time_scale.value),
        "length_unit": meta.length_unit,
        "velocity_unit": meta.velocity_unit,
        "axis_note": meta.axis_note,
        "integrator": traj.meta.integrator,
        "integrator_order": traj.meta.integrator_order,
        "dt": traj.meta.dt,
        "sample_every": traj.meta.sample_every,
        "n_steps": traj.meta.n_steps,
        "config_hash": traj.meta.config_hash,
        "software_version": traj.meta.software_version,
        "ic_source": ic_source,
        "n_bodies": n_n,
        "body_names": list(traj.body_names),
    }

    return ComparisonResult(  # step 7
        body=body,
        epoch_jd=meta.epoch_jd,
        times_s=traj.times.copy(),
        model_metadata=model_metadata,
        reference_metadata=first_states[body].provenance,
        transform=transform,
        position_error=position_error,
        velocity_error=velocity_error,
        position_stats=error_statistics(position_error, percentiles),
        velocity_stats=error_statistics(velocity_error, percentiles),
        relative_position_error=relative,
    )


def write_comparison_record(result: ComparisonResult, path: Path) -> None:
    """Serialize a ComparisonResult to comparison_record.json (R13)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_dict(), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
