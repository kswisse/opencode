"""Frozen constants + shared helpers for Phase 5 experiments.

Contract: every constant here is COPIED from
``docs/methodology/phase5-experiment-design.md`` (cited per item) and is
asserted against that document by ``tests/unit/test_experiment_contract.py``.
Nothing in this module may be tuned after a run observes a number (design
R-S3 / correction #1): thresholds come from (i) accepted Phase 1-4 results,
(ii) convergence-order theory, (iii) the frozen design document itself.

Kernel-free by design: no ``spiceypy`` / ``spice_backend`` import at module
scope, so the contract test can import this file on any machine.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris import __version__
from solar_ephemeris.analysis.momentum import (
    angular_momentum_series,
    momentum_series,
)
from solar_ephemeris.physics.constants import AU_M, GM_EARTH, GM_SUN
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine, Trajectory
from solar_ephemeris.simulation.initial_conditions import (
    CircularTwoBodyIC,
    make_circular_two_body_ic,
)
from solar_ephemeris.physics.state import State

# ---------------------------------------------------------------------------
# Frozen experiment variables (design §3.0)
# ---------------------------------------------------------------------------

EPOCH_JD: float = 2451545.0  # J2000, TDB (§3.0)
DESIGN_DOC = Path("docs/methodology/phase5-experiment-design.md")

#: A1 grid (§3.1 row A1): dt = (P/4)/n
N_VALUES: tuple[int, ...] = (25, 50, 100, 200)

#: A2 dt lattice + B ref-lattice (§3.1 rows A2/B): dt = P_SE/divisor
A2_DIVISORS: tuple[int, ...] = (500, 1000, 2000, 4000)

#: E horizons, days (§3.1 row E), gated 1 -> 30 -> 90 -> 365
E_HORIZON_DAYS: tuple[int, ...] = (1, 30, 90, 365)

#: Experiment C tiers (§3.1 row C; correction #3: T4 = the standard 10
#: MASTERPLAN bodies; Pluto is a selected-body extension, NEVER in a tier).
TIER_T1: tuple[str, ...] = ("Sun", "Earth")
TIER_T2: tuple[str, ...] = ("Sun", "Earth", "Moon")
TIER_T3: tuple[str, ...] = (
    "Sun", "Mercury", "Venus", "Earth", "Moon", "Mars",
)
TIER_T4: tuple[str, ...] = (
    "Sun", "Mercury", "Venus", "Earth", "Moon", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune",
)
TIERS: dict[str, tuple[str, ...]] = {
    "T1": TIER_T1, "T2": TIER_T2, "T3": TIER_T3, "T4": TIER_T4,
}

#: Period conventions — SAME expressions as tests/real_kernel/
#: test_staged_validation.py so D's dt bit-matches the accepted Phase-4
#: runs whose thresholds are being re-checked (§5).
P_SE_S: float = 365.256363004 * 86400.0  # s, Earth mean orbital period
P_EM_S: float = 27.321661 * 86400.0  # s, Moon mean orbital period

DT_SE: float = P_SE_S / 1000.0  # ≈ 31558.1498 s (stage9)
DT_EM: float = P_EM_S / 1000.0  # ≈ 2360.5915 s (stage10 / C / E)

#: C sampling (§3.1 row C): one dt for every tier, control doubles dt and
#: halves sample frequency so control sample TIMES match the main grid.
C_SAMPLE_EVERY: int = 100
C_CONTROL_SAMPLE_EVERY: int = 200
#: E sampling (§3.1 row E): ~1 sample/day on the step*dt grid.
E_SAMPLE_EVERY: int = 37

#: Frozen signal criterion (§3.1 row C): signal >= 10 x control.
C_SIGNAL_FACTOR: float = 10.0

#: E structural conservation gates (§6b item 4) — frozen in the design doc
#: BEFORE any E run; stability gates only, never accuracy thresholds.
E_CONSERVATION_GATES: dict[str, float] = {
    "energy_rel_max": 1.0e-6,   # max|dE/E0|
    "momentum_rel_max": 1.0e-10,  # max|P_rel|
    "angmom_rel_max": 1.0e-8,   # max|dL|/|L0|
}

#: Definition pinned before the first E run (see module of record):
#: P_rel(t) = |P(t) - P(0)| / sum_i m_i |v_i(t)|, masses = GM/G.
#: The system barycentric frame makes P(0) ~ 0, so the denominator is the
#: cancellation-free internal momentum scale (sum of magnitudes).
MOMENTUM_SCALE_DEFINITION: str = "|P(t) - P(0)| / sum_i m_i |v_i(t)| (masses = GM/G)"

#: Verlet energy drift bound on one period (§6b; Phase-3 accepted slope
#: test: measured |slope|*P/|E0| = 2.8e-16, bound 1e-12).
VERLET_DRIFT_MAX: float = 1.0e-12

#: Roundoff floor — REUSED verbatim from the Phase 1-2 numerical policy
#: (correction #5): tests/numerical/test_convergence.py uses
#: 1.5e11 x 2^-52 ≈ 3.3e-5 m @ 1 AU. Never adjusted to fit results.
ROUNDOFF_FLOOR_M: float = 1.5e11 * 2.0 ** -52
#: A1 acceptance 6a.3: final error must exceed 1000x the floor.
FLOOR_SAFETY_FACTOR: float = 1000.0

#: A1 observed-order windows (§6a item 2, order theory).
RK4_ORDER_WINDOW: tuple[float, float] = (3.5, 4.5)
VERLET_ORDER_WINDOW: tuple[float, float] = (1.5, 2.5)

#: A2 floor-dominance descriptive rule (§6a item 4): an interval is
#: floor-dominated when D_k / D_{k+1} < 2.
A2_FLOOR_RATIO: float = 2.0

#: E growth-classification discrimination (§6e): best SSE <= 0.1 x second.
GROWTH_SSE_RATIO: float = 0.1

#: IC provenance labels (§4).
IC_SOURCE_ANALYTIC: str = "analytic-circular"
IC_SOURCE_REFERENCE: str = "reference-ingested via ephemeris/ic.py (live de440s.bsp)"

#: D formal thresholds — Phase-4 stage9/stage10 acceptance bands, copied
#: UNCHANGED from tests/real_kernel/test_staged_validation.py (§6/§3.1 row D:
#: thresholds already accepted, never re-derived).
STAGE9_BANDS: dict[str, tuple[float, float]] = {
    "E_pos": (5.0e4, 5.1e8),
    "E_vel": (0.16, 1650.0),
    "E_rel_max": (0.0, 3.45e-3),
}
STAGE10_BANDS: dict[str, tuple[float, float]] = {
    "E_pos": (150.0, 1.51e6),
    "E_vel": (4.8e-4, 4.88),
}

#: Strings the driver uses for configs that ran against the live kernel.
REFERENCE_DATASET_STR: str = "JPL DE440 (de440s.bsp live)"

#: §6d reproducibility fields every experiment record must carry.
REQUIRED_RECORD_FIELDS: tuple[str, ...] = (
    "experiment_id",
    "epoch",
    "bodies",
    "initial_condition_source",
    "integrator",
    "timestep",
    "duration",
    "reference_dataset",
    "reference_frame",
    "reference_origin",
    "time_scale",
    "units",
    "software_version",
    "configuration_hash",
    "output_hash",
)


# ---------------------------------------------------------------------------
# Synthetic (analytic) two-body IC in the endpoint_error helper shape
# ---------------------------------------------------------------------------


def _rotz(theta: float) -> NDArray[np.float64]:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


class SyntheticCircularIC:
    """Source ``CircularTwoBodyIC`` exposed in the shape the tests'
    ``endpoint_error`` expects (``positions0`` / ``velocities0`` /
    ``exact_at``). Exact solution = rigid rotation (conftest math, mirrored
    by ``make_circular_two_body_ic`` — same numbers)."""

    __slots__ = ("_ic",)

    def __init__(self, ic: CircularTwoBodyIC) -> None:
        self._ic = ic

    @property
    def source(self) -> CircularTwoBodyIC:
        return self._ic

    @property
    def positions0(self) -> NDArray[np.float64]:
        return self._ic.positions

    @property
    def velocities0(self) -> NDArray[np.float64]:
        return self._ic.velocities

    @property
    def gm(self) -> NDArray[np.float64]:
        return self._ic.gm

    @property
    def period(self) -> float:
        return self._ic.period

    @property
    def omega(self) -> float:
        return self._ic.omega

    def exact_at(self, t: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        rot = _rotz(self._ic.omega * t)
        return (rot @ self._ic.positions.T).T, (rot @ self._ic.velocities.T).T

    def state(self) -> State:
        return self._ic.state(epoch_jd=EPOCH_JD)


def synthetic_sun_earth_ic() -> SyntheticCircularIC:
    """Sun-Earth circular two-body analytic IC at 1 AU (design §4 group A)."""
    return SyntheticCircularIC(
        make_circular_two_body_ic(GM_SUN, GM_EARTH, AU_M, names=("Sun", "Earth"))
    )


# ---------------------------------------------------------------------------
# Convergence helpers — formulas copied verbatim from
# tests/numerical/test_convergence.py (design §7 row 3: "không đổi công thức")
# ---------------------------------------------------------------------------


def endpoint_error(integ, ic, n: int, horizon: float) -> float:
    """Integrate to `horizon` with n steps; return max body position error (m)."""
    from solar_ephemeris.physics.gravity import newtonian_acceleration

    dt = horizon / n
    accel = newtonian_acceleration(ic.gm)
    q = ic.positions0.copy()
    v = ic.velocities0.copy()
    t = 0.0
    for _ in range(n):
        q, v = integ.step(q, v, dt, accel, t)
        t += dt
    q_exact, _ = ic.exact_at(horizon)
    return float(np.max(np.linalg.norm(q - q_exact, axis=1)))


def observed_orders(errors: Sequence[float]) -> list[float]:
    return [float(np.log2(errors[k] / errors[k + 1])) for k in range(len(errors) - 1)]


# ---------------------------------------------------------------------------
# output_hash + records (design §6d, §7 row 2)
# ---------------------------------------------------------------------------


def output_hash(
    *,
    times: NDArray[np.float64],
    positions: NDArray[np.float64],
    velocities: NDArray[np.float64],
) -> str:
    """SHA-256 over the array BYTES of times/positions/velocities (float64,
    fixed order + shape + channel name) — never over npz file bytes (zip
    timestamps differ by design)."""
    h = hashlib.sha256()
    for name, arr in (("times", times), ("positions", positions), ("velocities", velocities)):
        a = np.ascontiguousarray(arr, dtype=np.float64)
        h.update(name.encode("ascii"))
        h.update(str(a.shape).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def traj_output_hash(traj: Trajectory) -> str:
    return output_hash(times=traj.times, positions=traj.positions, velocities=traj.velocities)


def gate(
    name: str, *, threshold: Any, measured: Any, reason: str, passed: bool
) -> dict[str, Any]:
    """One threshold/measured/reason triple (design R-S3 record rule)."""
    return {
        "name": name,
        "threshold": threshold,
        "measured": measured,
        "reason": reason,
        "passed": bool(passed),
    }


def jsonable(obj: Any) -> Any:
    """Recursive converter: numpy scalars/arrays, tuples, Paths -> JSON-safe."""
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj


def write_record(path: Path, payload: dict[str, Any]) -> Path:
    """Machine-readable record, NaN/Infinity forbidden (allow_nan=False)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )
    return path


def experiment_record(
    experiment_id: str,
    config: SimulationConfig,
    *,
    initial_condition_source: str,
    output_hash_value: str,
    reproducible: bool,
    runtime_s: Sequence[float],
    second_output_hash: str | None = None,
    run_record: dict[str, Any] | None = None,
    reference_frame: str | None = None,
    reference_origin: str | None = None,
    comparison: dict[str, Any] | None = None,
    gates: Sequence[dict[str, Any]] | None = None,
    interpretation: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Experiment record wrapping RunRecord + §6d fields (design §7 row 2)."""
    record: dict[str, Any] = {
        "schema_version": 1,
        "experiment_id": experiment_id,
        "epoch": config.epoch_jd,
        "bodies": list(config.bodies),
        "initial_condition_source": initial_condition_source,
        "integrator": config.integrator,
        "timestep": config.dt,
        "duration": config.duration,
        "reference_dataset": config.reference_dataset,
        "reference_frame": reference_frame,
        "reference_origin": reference_origin,
        "time_scale": str(config.time_scale),
        "units": "m, m/s, s",
        "software_version": __version__,
        "configuration_hash": config.config_hash(),
        "output_hash": output_hash_value,
        "second_output_hash": second_output_hash,
        "reproducible": bool(reproducible),
        "runtime_s": [float(x) for x in runtime_s],
        "frame_model": str(config.frame),
        "sample_grid": "times = step * dt (no accumulation)",
        "gates": [gate_json for gate_json in (gates or [])],
        "interpretation": interpretation,
        "design_contract": "docs/methodology/phase5-experiment-design.md",
    }
    if run_record is not None:
        record["run_record"] = run_record
    if comparison is not None:
        record["comparison"] = jsonable(comparison)
    if extra:
        record.update(jsonable(extra))
    return record


def provenance_fields_present(record: dict[str, Any]) -> bool:
    """§6d: every required field exists and is non-empty (None allowed only
    for reference_* on synthetic runs)."""
    for field in REQUIRED_RECORD_FIELDS:
        if field not in record:
            return False
        value = record[field]
        if field.startswith("reference_") and value is None:
            continue
        if value in ("", None):
            return False
    return True


# ---------------------------------------------------------------------------
# Reproducible run (§3.0 replication row, §6d)
# ---------------------------------------------------------------------------


def run_reproducible(
    config: SimulationConfig,
    initial: State,
    out_dir: Path,
    *,
    sample_every: int = 1,
) -> dict[str, Any]:
    """Run the SAME config twice; require bitwise identity + equal hashes.

    Run 1 persists via runner.run_to_file (trajectory.npz + run_record.json);
    run 2 is in-memory. Returns traj (run 1), hashes, runtimes.
    Raises AssertionError when reproducibility fails (a gate failure — the
    caller must stop the experiment chain, design §6b item 2).
    """
    from solar_ephemeris.simulation.runner import load_run, run_to_file

    out_dir = Path(out_dir)
    t0 = time.perf_counter()
    run_record = run_to_file(config, initial, out_dir, sample_every=sample_every)
    t1 = time.perf_counter()
    traj2 = SimulationEngine(config).run(initial, sample_every=sample_every)
    t2 = time.perf_counter()

    traj1, loaded = load_run(out_dir)
    for label, a, b in (
        ("times", traj1.times, traj2.times),
        ("positions", traj1.positions, traj2.positions),
        ("velocities", traj1.velocities, traj2.velocities),
    ):
        assert np.array_equal(a, b), (
            f"non-reproducible run ({label}): {config.config_hash()}"
        )
    assert loaded.config_hash == run_record.config_hash == config.config_hash()

    h1 = traj_output_hash(traj1)
    h2 = traj_output_hash(traj2)
    assert h1 == h2, f"output_hash mismatch: {h1} != {h2}"
    return {
        "traj": traj1,
        "traj_second": traj2,
        "run_record": run_record.to_dict(),
        "output_hash": h1,
        "second_output_hash": h2,
        "reproducible": True,
        "runtime_s": (t1 - t0, t2 - t1),
    }


# ---------------------------------------------------------------------------
# Conservation diagnostics for the E structural gates (§6b item 4)
# ---------------------------------------------------------------------------


def max_relative_energy_error(traj: Trajectory) -> float:
    from solar_ephemeris.analysis.energy import relative_energy_error

    return float(np.max(relative_energy_error(traj)))


def max_momentum_rel_error(traj: Trajectory) -> float:
    """max_t |P(t) - P(0)| / sum_i m_i |v_i(t)| — MOMENTUM_SCALE_DEFINITION."""
    from solar_ephemeris.physics.constants import G_SI

    p = momentum_series(traj)  # (M, 3)
    masses = traj.gm / G_SI  # (N,)
    speeds = np.linalg.norm(traj.velocities, axis=2)  # (M, N)
    scale = speeds @ masses  # (M,) = sum_i m_i |v_i|
    if np.any(scale == 0.0):
        return float("inf")
    rel = np.linalg.norm(p - p[0], axis=1) / scale
    return float(np.max(rel))


def max_angmom_rel_error(traj: Trajectory) -> float:
    """max_t |L(t) - L(0)| / |L(0)|."""
    ang = angular_momentum_series(traj)
    l0 = float(np.linalg.norm(ang[0]))
    if l0 == 0.0:
        return float("inf")
    return float(np.max(np.linalg.norm(ang - ang[0], axis=1)) / l0)


# ---------------------------------------------------------------------------
# E structural gates (§6b) — 6 pre-registered categories, NO error threshold
# ---------------------------------------------------------------------------


def evaluate_structural_gates(
    *,
    traj: Trajectory,
    second_traj: Trajectory,
    config: SimulationConfig,
    sample_every: int,
    provenance_ok: bool,
    provenance_measured: str,
) -> list[dict[str, Any]]:
    """The 6 gate categories of design §6b for one E horizon.

    Frozen before any E run (correction #1): conservation bounds come from
    E_CONSERVATION_GATES (derived from Phase 1-3 + analysis, never from E's
    own observed error); E_pos/E_vel are NOT judged here at all.
    """
    arrays = (traj.times, traj.positions, traj.velocities)
    finite = all(bool(np.all(np.isfinite(a))) for a in arrays)

    g1 = gate(
        "1 numerical stability (all arrays finite)",
        threshold="all finite (no NaN/inf)",
        measured="finite" if finite else "non-finite present",
        reason="§6b item 1: stability gate, not accuracy; no E-derived threshold",
        passed=finite,
    )

    repro = (
        np.array_equal(traj.times, second_traj.times)
        and np.array_equal(traj.positions, second_traj.positions)
        and np.array_equal(traj.velocities, second_traj.velocities)
        and traj_output_hash(traj) == traj_output_hash(second_traj)
    )
    g2 = gate(
        "2 deterministic reproducibility (2 runs bitwise + equal hashes)",
        threshold="np.array_equal on all arrays + equal output_hash + equal config_hash",
        measured="equal" if repro else "MISMATCH",
        reason="§6b item 2 / §6d: determinism contract, pre-registered",
        passed=repro,
    )

    n_steps = config.n_steps
    expected_samples = n_steps // sample_every + 1
    expected_times = np.arange(expected_samples, dtype=np.float64) * sample_every * config.dt
    complete = (
        traj.n_samples == expected_samples
        and np.array_equal(traj.times, expected_times)
    )
    g3 = gate(
        "3 successful completion (n_steps + step*dt sample grid)",
        threshold=f"n_samples == {expected_samples} and times == step*{sample_every}*dt",
        measured=f"n_samples={traj.n_samples}, last_t={float(traj.times[-1]):.6f}s",
        reason="§6b item 3: completion gate, pre-registered from config",
        passed=complete,
    )

    e_meas = max_relative_energy_error(traj)
    g4a = gate(
        "4a conservation max|dE/E0|",
        threshold=E_CONSERVATION_GATES["energy_rel_max"],
        measured=e_meas,
        reason="§6b item 4: frozen stability bound (Phase-3 basis, NOT derived from E)",
        passed=e_meas <= E_CONSERVATION_GATES["energy_rel_max"],
    )
    p_meas = max_momentum_rel_error(traj)
    g4b = gate(
        "4b conservation max|P_rel|",
        threshold=E_CONSERVATION_GATES["momentum_rel_max"],
        measured=p_meas,
        reason=f"§6b item 4: frozen stability bound; P_rel = {MOMENTUM_SCALE_DEFINITION}",
        passed=p_meas <= E_CONSERVATION_GATES["momentum_rel_max"],
    )
    l_meas = max_angmom_rel_error(traj)
    g4c = gate(
        "4c conservation max|ΔL|/|L0|",
        threshold=E_CONSERVATION_GATES["angmom_rel_max"],
        measured=l_meas,
        reason="§6b item 4: frozen stability bound (Phase-3 RK4 basis, NOT derived from E)",
        passed=l_meas <= E_CONSERVATION_GATES["angmom_rel_max"],
    )

    g5 = gate(
        "5 valid metadata/provenance (§6d fields + kernel hashes == manifest)",
        threshold="all §6d fields present, kernel hashes match manifest",
        measured=provenance_measured,
        reason="§6b item 5: provenance gate, pre-registered",
        passed=provenance_ok,
    )

    g6 = gate(
        "6 absence of numerical failure (evidence: gates 1 + 3)",
        threshold="finite AND completed",
        measured="ok" if (finite and complete) else "failure evidence",
        reason="§6b item 6 (points at items 1 and 3 — no separate threshold)",
        passed=bool(finite and complete),
    )
    return [g1, g2, g3, g4a, g4b, g4c, g5, g6]


def gates_passed(gates: Sequence[dict[str, Any]]) -> bool:
    return all(g["passed"] for g in gates)


# ---------------------------------------------------------------------------
# Growth-law classification (§6e) — descriptive only, never a gate
# ---------------------------------------------------------------------------


def growth_classification(
    times: NDArray[np.float64], values: NDArray[np.float64]
) -> dict[str, Any]:
    """Fit linear c*t / power c*t^alpha / exponential c*e^(l*t) on t>0 samples.

    Discriminate only when best SSE <= GROWTH_SSE_RATIO x second SSE,
    else report 'no discrimination' (design §6e)."""
    mask = (times > 0.0) & np.isfinite(values)
    t = np.asarray(times[mask], dtype=np.float64)
    y = np.asarray(values[mask], dtype=np.float64)
    result: dict[str, Any] = {
        "n_samples_fit": int(t.size),
        "sse": {},
        "selected": None,
        "discriminated": False,
        "note": "",
    }
    if t.size < 3:
        result["note"] = "không phân biệt được — ít hơn 3 mẫu t>0, chỉ báo cáo series"
        return result

    def sse_of(pred: NDArray[np.float64]) -> float:
        r = y - pred
        return float(np.sum(r * r)) if np.all(np.isfinite(r)) else float("inf")

    sse: dict[str, float] = {}

    # linear c*t (OLS through origin)
    denom = float(np.sum(t * t))
    c_lin = float(np.sum(t * y) / denom) if denom > 0 else float("nan")
    sse["linear"] = sse_of(c_lin * t) if np.isfinite(c_lin) else float("inf")

    positive = y > 0.0
    if np.count_nonzero(positive) >= 3:
        tp, yp = t[positive], y[positive]
        logt, logy = np.log(tp), np.log(yp)
        var_t = float(np.var(logt))
        if var_t > 0.0:
            alpha = float(np.cov(logt, logy, bias=True)[0, 1] / var_t)
            log_c = float(np.mean(logy) - alpha * np.mean(logt))
            pred = np.exp(log_c) * np.power(t, alpha)
            sse["power"] = sse_of(pred)
        else:
            sse["power"] = float("inf")
        var_t2 = float(np.var(t))
        if var_t2 > 0.0:
            lam = float(np.cov(t, logy, bias=True)[0, 1] / var_t2)
            log_c2 = float(np.mean(logy) - lam * np.mean(t))
            with np.errstate(over="ignore"):
                pred = np.exp(log_c2 + lam * t)
            sse["exponential"] = sse_of(pred)
        else:
            sse["exponential"] = float("inf")
    else:
        sse["power"] = float("inf")
        sse["exponential"] = float("inf")

    result["sse"] = sse
    ranked = sorted(sse.items(), key=lambda kv: kv[1])
    valid = [kv for kv in ranked if np.isfinite(kv[1])]
    if len(valid) < 2:
        result["note"] = "không phân biệt được — fit không hội tụ, chỉ báo cáo series"
        return result
    (best_name, best_sse), (second_name, second_sse) = valid[0], valid[1]
    if second_sse > 0.0 and best_sse <= GROWTH_SSE_RATIO * second_sse:
        result["selected"] = best_name
        result["discriminated"] = True
        result["note"] = f"phân biệt được: {best_name} (SSE {best_sse:.6g} <= 0.1 x {second_sse:.6g})"
    else:
        result["note"] = "không phân biệt được — chỉ báo cáo series"
    return result


# ---------------------------------------------------------------------------
# OLS drift slope (diagnostic helper, informational)
# ---------------------------------------------------------------------------


def ols_slope(times: NDArray[np.float64], values: NDArray[np.float64]) -> float:
    """Least-squares slope of values vs times (same scale units per unit t)."""
    t = np.asarray(times, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    if t.size < 2 or float(np.var(t)) == 0.0:
        return float("nan")
    return float(np.cov(t, y, bias=True)[0, 1] / np.var(t))


def subset_barycentre(
    traj: Trajectory, names: Sequence[str]
) -> NDArray[np.float64]:
    """(M, 3) GM-weighted centre of a body subset (analysis.barycenter)."""
    from solar_ephemeris.analysis.barycenter import barycenter

    r_cm, _ = barycenter(traj, names)
    return r_cm
