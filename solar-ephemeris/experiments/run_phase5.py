"""Phase 5 experiment driver — one subcommand per mandated step (design §11).

Run from the repo root:

    python -m experiments.run_phase5 <cmd>

    a1            step 3  — A1 convergence grid + B synthetic metrics
    baseline      step 4  — freeze the numerical baseline (A1 results)
    a2            step 5  — A2 DE440 dt-lattice + 3-part analysis
    bref          step 5  — B ref-lattice (Verlet on the P_SE divisors)
    e1 / e30      step 6  — E horizons 1 d / 30 d (structural gates only)
    freeze-gates  step 7  — echo the frozen gates (no new thresholds)
    c             step 8  — tier experiment + registered dt/2 controls
    d             step 9  — DE440 validation runs (formal + report-only)
    e90           step 10 — E horizon 90 d
    e365          step 12 — E horizon 365 d

Every run writes a machine-readable record under ``results/``.
Kernel-using subcommands fail loudly when de440s.bsp is missing (never skip).
An E structural-gate failure exits non-zero — STOP the horizon chain.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))  # src layout without an installed package

import numpy as np  # noqa: E402

from experiments._common import (  # noqa: E402
    A2_DIVISORS,
    A2_FLOOR_RATIO,
    C_CONTROL_SAMPLE_EVERY,
    C_SAMPLE_EVERY,
    C_SIGNAL_FACTOR,
    DESIGN_DOC,
    DT_EM,
    DT_SE,
    E_CONSERVATION_GATES,
    E_HORIZON_DAYS,
    E_SAMPLE_EVERY,
    EPOCH_JD,
    FLOOR_SAFETY_FACTOR,
    IC_SOURCE_ANALYTIC,
    IC_SOURCE_REFERENCE,
    MOMENTUM_SCALE_DEFINITION,
    N_VALUES,
    P_EM_S,
    P_SE_S,
    REFERENCE_DATASET_STR,
    ROUNDOFF_FLOOR_M,
    RK4_ORDER_WINDOW,
    STAGE10_BANDS,
    STAGE9_BANDS,
    TIERS,
    TIER_T1,
    TIER_T2,
    TIER_T3,
    TIER_T4,
    VERLET_DRIFT_MAX,
    VERLET_ORDER_WINDOW,
    endpoint_error,
    evaluate_structural_gates,
    experiment_record,
    gate,
    gates_passed,
    growth_classification,
    max_momentum_rel_error,
    max_relative_energy_error,
    observed_orders,
    ols_slope,
    provenance_fields_present,
    run_reproducible,
    subset_barycentre,
    synthetic_sun_earth_ic,
    write_record,
)
from solar_ephemeris.analysis.compare import trajectory_difference  # noqa: E402
from solar_ephemeris.analysis.energy import relative_energy_error  # noqa: E402
from solar_ephemeris.analysis.momentum import angular_momentum_series  # noqa: E402
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale  # noqa: E402
from solar_ephemeris.integrators import get_integrator  # noqa: E402
from solar_ephemeris.simulation.configuration import SimulationConfig  # noqa: E402

RESULTS = ROOT / "results"
D_S = 86400.0


# ---------------------------------------------------------------------------
# Kernel access (lazy import; fail loudly, never skip)
# ---------------------------------------------------------------------------


def _require_kernel():
    from solar_ephemeris.ephemeris.kernel_manifest import (
        DE440S_MANIFEST,
        default_kernel_path,
    )
    from solar_ephemeris.ephemeris.spice_backend import SpiceReference

    path = default_kernel_path()
    if not path.is_file():
        raise SystemExit(
            f"reference kernel missing: {path} — download de440s.bsp and verify "
            "sha256 against kernel_manifest.py (fail, never skip)"
        )
    ref = SpiceReference(path)
    meta = ref.metadata
    if (
        meta.kernel_md5 != DE440S_MANIFEST.md5
        or meta.kernel_sha256 != DE440S_MANIFEST.sha256
    ):
        raise SystemExit("kernel hashes do not match manifest — refusing to run")
    return ref


def _ref_ic(provider, bodies):
    from solar_ephemeris.ephemeris.ic import reference_state_to_model_state

    return reference_state_to_model_state(
        provider, bodies=list(bodies), epoch_jd=EPOCH_JD
    )


def _compare(traj, provider, body: str) -> dict:
    from solar_ephemeris.ephemeris.comparison import compare_trajectory

    result = compare_trajectory(
        traj, provider, body=body, ic_source=IC_SOURCE_REFERENCE
    )
    return result


def _ref_meta() -> tuple[str, str]:
    return "J2000", "SSB(0)"


# ---------------------------------------------------------------------------
# Step 3: A1 + B synthetic
# ---------------------------------------------------------------------------


def cmd_a1() -> None:
    ic = synthetic_sun_earth_ic()
    horizon = ic.period / 4.0
    state = ic.state()
    all_errors: dict[str, list[float]] = {}
    osc: dict[str, list[float]] = {}
    drifts: dict[str, list[float]] = {}
    runtimes: dict[str, list[float]] = {}

    for integ_name in ("rk4", "verlet"):
        integ = get_integrator(integ_name)
        errors: list[float] = []
        osc_n: list[float] = []
        drift_n: list[float] = []
        rt_n: list[float] = []
        for n in N_VALUES:
            err = endpoint_error(integ, ic, n, horizon)
            err_rep = endpoint_error(integ, ic, n, horizon)
            assert err == err_rep, "endpoint_error not reproducible (scalar)"
            cfg = SimulationConfig(
                bodies=("Sun", "Earth"),
                integrator=integ_name,
                dt=horizon / n,
                duration=horizon,
                epoch_jd=EPOCH_JD,
            )
            out = RESULTS / "experiment_A1" / f"{integ_name}_n{n}"
            rr = run_reproducible(cfg, state, out, sample_every=1)
            traj = rr["traj"]
            erel = relative_energy_error(traj)
            max_osc = float(np.max(erel))
            drift_per_orbit = ols_slope(traj.times, erel) * ic.period
            ang = angular_momentum_series(traj)
            l0 = float(np.linalg.norm(ang[0]))
            l_dev = float(np.max(np.linalg.norm(ang - ang[0], axis=1)) / l0)
            gates = [
                gate(
                    "A1 error above 1000x roundoff floor",
                    threshold=FLOOR_SAFETY_FACTOR * ROUNDOFF_FLOOR_M,
                    measured=err,
                    reason="§6a.3: floor REUSED from Phase 1-2 policy "
                    f"(1.5e11 * 2^-52 = {ROUNDOFF_FLOOR_M:.3e} m); never fitted",
                    passed=err > FLOOR_SAFETY_FACTOR * ROUNDOFF_FLOOR_M,
                ),
                gate(
                    "reproducible (2 runs bitwise + equal output_hash)",
                    threshold="np.array_equal + equal hashes",
                    measured="equal",
                    reason="§6d: every standard config runs twice",
                    passed=bool(rr["reproducible"]),
                ),
            ]
            rec = experiment_record(
                f"A1/{integ_name}/n={n}",
                cfg,
                initial_condition_source=IC_SOURCE_ANALYTIC,
                output_hash_value=rr["output_hash"],
                second_output_hash=rr["second_output_hash"],
                reproducible=bool(rr["reproducible"]),
                runtime_s=rr["runtime_s"],
                run_record=rr["run_record"],
                reference_frame="analytic two-body exact (rigid rotation)",
                reference_origin="barycenter(Sun, Earth)",
                gates=gates,
                extra={
                    "endpoint_error_m": err,
                    "horizon_s": horizon,
                    "horizon_periods": 0.25,
                    "energy_max_rel_osc": max_osc,
                    "energy_drift_per_orbit": drift_per_orbit,
                    "angmom_rel_dev_max": l_dev,
                    "interpretation_note": (
                        "A1: pure integration error against the analytic "
                        "solution (design §4 group A) — the only experiment "
                        "allowed to call its number 'numerical error'."
                    ),
                },
            )
            write_record(out / "experiment_record.json", rec)
            errors.append(err)
            osc_n.append(max_osc)
            drift_n.append(drift_per_orbit)
            rt_n.append(float(sum(rr["runtime_s"])))

        orders = observed_orders(errors)
        window = RK4_ORDER_WINDOW if integ_name == "rk4" else VERLET_ORDER_WINDOW
        gates = [
            gate(
                "errors strictly decrease along the frozen grid",
                threshold="errors[k+1] < errors[k] for all k",
                measured=errors,
                reason="§6a.1: strict decrease on the pre-registered grid",
                passed=all(errors[k + 1] < errors[k] for k in range(len(errors) - 1)),
            ),
            gate(
                f"observed order within window {window}",
                threshold=list(window),
                measured=orders,
                reason="§6a.2: order theory (RK4 4th / Verlet 2nd), "
                "accepted Phase-1 measured [4.02,4.06]/[2.00,2.00]",
                passed=all(window[0] <= p <= window[1] for p in orders),
            ),
            gate(
                "final error above 1000x roundoff floor",
                threshold=FLOOR_SAFETY_FACTOR * ROUNDOFF_FLOOR_M,
                measured=errors[-1],
                reason="§6a.3 / R-S6: estimation above the frozen floor",
                passed=errors[-1] > FLOOR_SAFETY_FACTOR * ROUNDOFF_FLOOR_M,
            ),
        ]
        write_record(
            RESULTS / "experiment_A1" / f"{integ_name}_orders.json",
            {
                "experiment_id": f"A1/{integ_name}/orders",
                "n_values": list(N_VALUES),
                "errors_m": errors,
                "observed_orders": orders,
                "order_window": list(window),
                "roundoff_floor_m": ROUNDOFF_FLOOR_M,
                "gates": gates,
                "all_passed": gates_passed(gates),
            },
        )
        all_errors[integ_name] = errors
        osc[integ_name] = osc_n
        drifts[integ_name] = drift_n
        runtimes[integ_name] = rt_n

    # --- B synthetic summary (same dataset, §3.1 row B) --------------------
    per_n = []
    for i, n in enumerate(N_VALUES):
        per_n.append(
            {
                "n": n,
                "rk4_endpoint_m": all_errors["rk4"][i],
                "verlet_endpoint_m": all_errors["verlet"][i],
                "rk4_smaller_endpoint": all_errors["rk4"][i] < all_errors["verlet"][i],
                "rk4_energy_max_osc": osc["rk4"][i],
                "verlet_energy_max_osc": osc["verlet"][i],
                "rk4_flatter_energy": osc["rk4"][i] <= osc["verlet"][i],
                "rk4_runtime_s": runtimes["rk4"][i],
                "verlet_runtime_s": runtimes["verlet"][i],
            }
        )
    write_record(
        RESULTS / "experiment_B" / "synthetic_summary.json",
        {
            "experiment_id": "B/synthetic",
            "config": "same as A1 (analytic Sun-Earth, horizon P/4, grid N_VALUES)",
            "per_n": per_n,
            "observations": {
                "H_B2_rk4_endpoint_smaller_each_dt": all(
                    r["rk4_smaller_endpoint"] for r in per_n
                ),
                "H_B1_rk4_energy_flatter_each_dt": all(
                    r["rk4_flatter_energy"] for r in per_n
                ),
                "energy_drift_per_orbit": drifts,
            },
            "note": (
                "observations only — no overall ranking (design §3.1 row B); "
                "runtime informational, never optimized (§8)"
            ),
        },
    )

    # --- B one-period Verlet drift gate (§6b: drift < 1e-12 on one P) ------
    for integ_name in ("verlet", "rk4"):
        cfg = SimulationConfig(
            bodies=("Sun", "Earth"),
            integrator=integ_name,
            dt=ic.period / 1000.0,
            duration=ic.period,
            epoch_jd=EPOCH_JD,
        )
        out = RESULTS / "experiment_B" / f"one_period_{integ_name}"
        rr = run_reproducible(cfg, state, out, sample_every=1)
        traj = rr["traj"]
        erel = relative_energy_error(traj)
        max_osc = float(np.max(erel))
        drift = ols_slope(traj.times, erel) * ic.period
        if integ_name == "verlet":
            gates = [
                gate(
                    "Verlet energy drift over one P below Phase-3 bound",
                    threshold=VERLET_DRIFT_MAX,
                    measured=drift,
                    reason="§6b: accepted Phase-3 slope bound (measured 2.8e-16); "
                    "drift = OLS slope of E(t)/|E0| x P",
                    passed=bool(drift <= VERLET_DRIFT_MAX),
                )
            ]
        else:
            gates = [
                gate(
                    "RK4 one-period run recorded (diagnostic, no drift gate)",
                    threshold="record only",
                    measured=drift,
                    reason="§6b drift gate applies to Verlet; RK4 reported for comparison",
                    passed=True,
                )
            ]
        write_record(
            out / "experiment_record.json",
            experiment_record(
                f"B/one_period/{integ_name}",
                cfg,
                initial_condition_source=IC_SOURCE_ANALYTIC,
                output_hash_value=rr["output_hash"],
                second_output_hash=rr["second_output_hash"],
                reproducible=bool(rr["reproducible"]),
                runtime_s=rr["runtime_s"],
                run_record=rr["run_record"],
                reference_frame="analytic two-body exact (rigid rotation)",
                reference_origin="barycenter(Sun, Earth)",
                gates=gates,
                extra={
                    "energy_max_rel_osc": max_osc,
                    "energy_drift_per_orbit": drift,
                    "one_period_energy_max_rel_error": float(np.max(erel)),
                },
            ),
        )

    print("A1 + B synthetic complete ->", RESULTS / "experiment_A1", RESULTS / "experiment_B")


# ---------------------------------------------------------------------------
# Step 4: freeze the numerical baseline
# ---------------------------------------------------------------------------


def cmd_baseline() -> None:
    import json

    a1: dict = {}
    for integ_name in ("rk4", "verlet"):
        raw = (RESULTS / "experiment_A1" / f"{integ_name}_orders.json").read_text(
            encoding="utf-8"
        )
        a1[integ_name] = json.loads(raw)
    b_one_period: dict = {}
    for name in ("verlet", "rk4"):
        rec = RESULTS / "experiment_B" / f"one_period_{name}" / "experiment_record.json"
        if rec.is_file():
            data = json.loads(rec.read_text(encoding="utf-8"))
            b_one_period[name] = {
                "gates": data.get("gates", []),
                "energy_max_rel_osc": data.get("energy_max_rel_osc"),
                "energy_drift_per_orbit": data.get("energy_drift_per_orbit"),
            }
    payload = {
        "experiment_id": "baseline/frozen",
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source": "design §11 step 4 (freeze numerical baseline) — "
        "values BELOW are frozen before A2/E/C/D judging",
        "design_contract": str(DESIGN_DOC),
        "roundoff_floor_m": ROUNDOFF_FLOOR_M,
        "roundoff_floor_formula": "1.5e11 * 2^-52 (Phase 1-2 contract, reuse only)",
        "floor_safety_factor": FLOOR_SAFETY_FACTOR,
        "order_windows": {
            "rk4": list(RK4_ORDER_WINDOW),
            "verlet": list(VERLET_ORDER_WINDOW),
        },
        "e_conervation_gates": E_CONSERVATION_GATES,
        "verlet_drift_max_per_period": VERLET_DRIFT_MAX,
        "c_signal_factor": C_SIGNAL_FACTOR,
        "a2_floor_ratio_rule": A2_FLOOR_RATIO,
        "a1": a1,
        "b_one_period": b_one_period,
    }
    path = write_record(RESULTS / "baseline_frozen.json", payload)
    print("baseline frozen ->", path)


# ---------------------------------------------------------------------------
# Step 5: A2 (RK4 dt-lattice vs DE440) + 3-part analysis
# ---------------------------------------------------------------------------


def _a2_or_bref(integ_name: str, out_sub: str, exp_id: str) -> dict[str, float]:
    provider = _require_kernel()
    state = _ref_ic(provider, TIER_T1)
    frame, origin = _ref_meta()
    d_values: dict[str, float] = {}
    for d in A2_DIVISORS:
        dt = P_SE_S / d
        cfg = SimulationConfig(
            bodies=TIER_T1,
            integrator=integ_name,
            dt=dt,
            duration=7 * D_S,
            epoch_jd=EPOCH_JD,
            reference_dataset=REFERENCE_DATASET_STR,
        )
        out = RESULTS / out_sub / f"d{d}"
        rr = run_reproducible(cfg, state, out, sample_every=1)
        traj = rr["traj"]
        cmp = _compare(traj, provider, "Earth")
        gates = [
            gate(
                "E_pos[0] == 0 exactly (DE440-derived IC)",
                threshold="0.0 exact",
                measured=float(cmp.position_error[0]),
                reason="§6c / H_D1: reference-ingested IC starts on DE440",
                passed=bool(cmp.position_error[0] == 0.0),
            ),
            gate(
                "reproducible (2 runs bitwise + equal output_hash)",
                threshold="np.array_equal + equal hashes",
                measured="equal",
                reason="§6d",
                passed=bool(rr["reproducible"]),
            ),
            gate(
                "all arrays finite",
                threshold="finite",
                measured="finite"
                if np.all(np.isfinite(traj.positions))
                else "non-finite",
                reason="§6b item 1 (structural, applies to every run)",
                passed=bool(np.all(np.isfinite(traj.positions))),
            ),
        ]
        write_record(
            out / "experiment_record.json",
            experiment_record(
                f"{exp_id}/d={d}",
                cfg,
                initial_condition_source=IC_SOURCE_REFERENCE,
                output_hash_value=rr["output_hash"],
                second_output_hash=rr["second_output_hash"],
                reproducible=bool(rr["reproducible"]),
                runtime_s=rr["runtime_s"],
                run_record=rr["run_record"],
                reference_frame=frame,
                reference_origin=origin,
                comparison=cmp.to_dict(),
                gates=gates,
                extra={
                    "divisor": d,
                    "energy_max_rel": max_relative_energy_error(traj),
                    "interpretation_note": (
                        "model/reference discrepancy — NEVER called "
                        "'integrator error' (§6c / R-S4); A1 owns that term."
                    ),
                },
            ),
        )
        d_values[str(d)] = float(cmp.position_stats.max)
    return d_values


def cmd_a2() -> None:
    d_values = _a2_or_bref("rk4", "experiment_A2", "A2")
    divs = sorted(A2_DIVISORS)
    intervals = []
    for k in range(len(divs) - 1):
        d_k, d_next = divs[k], divs[k + 1]
        ratio = d_values[str(d_k)] / d_values[str(d_next)]
        intervals.append(
            {
                "from_divisor": d_k,
                "to_divisor": d_next,
                "dt_from": P_SE_S / d_k,
                "dt_to": P_SE_S / d_next,
                "ratio_Dk_over_Dk1": ratio,
                "classification": (
                    "convergence-resolved"
                    if ratio >= A2_FLOOR_RATIO
                    else "floor-dominated"
                ),
            }
        )
    analysis = {
        "experiment_id": "A2/analysis",
        "headline_metric": "max E_pos (Earth) vs DE440, 7 d, RK4",
        "D_by_divisor_m": d_values,
        "ratios": intervals,
        "report": {
            "part_i_observed_numerical_convergence_regime": [
                i for i in intervals if i["classification"] == "convergence-resolved"
            ],
            "part_ii_plateau_floor_regime": [
                i for i in intervals if i["classification"] == "floor-dominated"
            ],
            "part_iii_interpretation": (
                "Floor-dominated intervals are the model/reference floor "
                "(the T1 config omits the Moon and other planets; the "
                "reference carries them) — plateau ≠ failed convergence; "
                "the floor is NEVER called integration error (§6a.4, R-S4). "
                "Descriptive rule frozen before the run: D_k/D_{k+1} < 2 ⇒ "
                "floor-dominated. No 2^p acceptance on total discrepancy "
                "(correction #2)."
            ),
        },
        "no_2p_acceptance": True,
    }
    path = write_record(RESULTS / "experiment_A2" / "analysis.json", analysis)
    print("A2 complete ->", path)


# ---------------------------------------------------------------------------
# Step 5 (tail): B ref-lattice (Verlet) + B record completion
# ---------------------------------------------------------------------------


def cmd_bref() -> None:
    d_values = _a2_or_bref("verlet", "experiment_B/ref_lattice", "B/ref")
    # Complete the B record: Verlet vs RK4 at identical dt (A2 numbers).
    rk4_values: dict[str, float] = {}
    for d in A2_DIVISORS:
        rec_file = RESULTS / "experiment_A2" / f"d{d}" / "experiment_record.json"
        import json

        rec = json.loads(rec_file.read_text(encoding="utf-8"))
        rk4_values[str(d)] = float(rec["comparison"]["position_stats"]["max"])
    per_d = []
    for d in A2_DIVISORS:
        per_d.append(
            {
                "divisor": d,
                "rk4_max_E_pos_m": rk4_values[str(d)],
                "verlet_max_E_pos_m": d_values[str(d)],
                "rk4_smaller": rk4_values[str(d)] < d_values[str(d)],
            }
        )
    write_record(
        RESULTS / "experiment_B" / "ref_summary.json",
        {
            "experiment_id": "B/ref",
            "config": "DE440-derived IC, Sun-Earth, 7 d, dt = P_SE/divisor, "
            "same grid both integrators (§3.1 row B)",
            "per_divisor": per_d,
            "observations": {
                "H_B2_rk4_endpoint_smaller_each_dt": all(p["rk4_smaller"] for p in per_d)
            },
            "note": (
                "model/reference discrepancy for both wings — no overall "
                "ranking claim (§3.1 row B); record completes after A2 (§11)."
            ),
        },
    )
    print("B ref-lattice complete ->", RESULTS / "experiment_B")


# ---------------------------------------------------------------------------
# Step 6/10/12: E horizons
# ---------------------------------------------------------------------------


def cmd_e(days: int) -> None:
    assert days in E_HORIZON_DAYS, f"horizon {days} d not in frozen {E_HORIZON_DAYS}"
    provider = _require_kernel()
    state = _ref_ic(provider, TIER_T2)
    frame, origin = _ref_meta()
    cfg = SimulationConfig(
        bodies=TIER_T2,
        integrator="rk4",
        dt=DT_EM,
        duration=days * D_S,
        epoch_jd=EPOCH_JD,
        reference_dataset=REFERENCE_DATASET_STR,
    )
    out = RESULTS / "experiment_E" / f"horizon_{days}d"
    rr = run_reproducible(cfg, state, out, sample_every=E_SAMPLE_EVERY)
    traj, second = rr["traj"], rr["traj_second"]

    comparisons = {}
    for body in ("Earth", "Moon"):
        comparisons[body] = _compare(traj, provider, body).to_dict()

    rec = experiment_record(
        f"E/{days}d",
        cfg,
        initial_condition_source=IC_SOURCE_REFERENCE,
        output_hash_value=rr["output_hash"],
        second_output_hash=rr["second_output_hash"],
        reproducible=bool(rr["reproducible"]),
        runtime_s=rr["runtime_s"],
        run_record=rr["run_record"],
        reference_frame=frame,
        reference_origin=origin,
        comparison=comparisons,
        extra={
            "horizon_days": days,
            "sample_every": E_SAMPLE_EVERY,
            "no_error_acceptance_threshold": (
                "E is gated ONLY by the 6 structural categories of §6b "
                "(correction #1); E_pos/E_vel are reported, never judged."
            ),
            "conservation_bounds_frozen_in": str(DESIGN_DOC),
            "momentum_scale_definition": MOMENTUM_SCALE_DEFINITION,
        },
    )
    from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST

    kernel_ok = (
        provider.metadata.kernel_md5 == DE440S_MANIFEST.md5
        and provider.metadata.kernel_sha256 == DE440S_MANIFEST.sha256
    )
    fields_ok = provenance_fields_present(rec)
    gates = evaluate_structural_gates(
        traj=traj,
        second_traj=second,
        config=cfg,
        sample_every=E_SAMPLE_EVERY,
        provenance_ok=bool(fields_ok and kernel_ok),
        provenance_measured=(
            f"fields={'ok' if fields_ok else 'missing'}, "
            f"kernel_hashes={'match' if kernel_ok else 'MISMATCH'}"
        ),
    )
    rec["gates"] = gates
    rec["all_structural_gates_passed"] = gates_passed(gates)

    earth_pos = np.array(comparisons["Earth"]["position_error"], dtype=np.float64)
    growth = growth_classification(traj.times, earth_pos)
    rec["growth_classification"] = growth

    write_record(out / "experiment_record.json", rec)
    print(
        f"E {days}d: structural gates "
        f"{'ALL PASS' if gates_passed(gates) else 'FAIL'} -> {out}"
    )
    if not gates_passed(gates):
        for g in gates:
            if not g["passed"]:
                print("  FAIL:", g["name"], "| measured:", g["measured"])
        raise SystemExit(
            "STOP: E structural gate failed at "
            f"{days} d — investigate before continuing the horizon chain (§6b)"
        )


# ---------------------------------------------------------------------------
# Step 7: freeze/echo the operational gates (no new thresholds)
# ---------------------------------------------------------------------------


def cmd_freeze_gates() -> None:
    import json

    evidence = {}
    for days in (1, 30):
        rec_file = RESULTS / "experiment_E" / f"horizon_{days}d" / "experiment_record.json"
        if not rec_file.is_file():
            raise SystemExit(f"missing E {days}d record — run e{days} first (§11 order)")
        rec = json.loads(rec_file.read_text(encoding="utf-8"))
        evidence[f"{days}d"] = {
            "all_structural_gates_passed": rec.get("all_structural_gates_passed"),
            "gate_names": [g["name"] for g in rec.get("gates", [])],
        }
    payload = {
        "experiment_id": "freeze/operational-gates",
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source": "design §6b/§6a — constants COPIED, never re-derived; "
        "step 7 of §11 forbids deriving any threshold from observed error",
        "e_conervation_gates": E_CONSERVATION_GATES,
        "e_has_error_acceptance_threshold": False,
        "momentum_scale_definition": MOMENTUM_SCALE_DEFINITION,
        "verlet_drift_max_per_period": VERLET_DRIFT_MAX,
        "c_signal_factor": C_SIGNAL_FACTOR,
        "a1_order_windows": {"rk4": list(RK4_ORDER_WINDOW), "verlet": list(VERLET_ORDER_WINDOW)},
        "roundoff_floor_m": ROUNDOFF_FLOOR_M,
        "stage9_bands_phase4": {k: list(v) for k, v in STAGE9_BANDS.items()},
        "stage10_bands_phase4": {k: list(v) for k, v in STAGE10_BANDS.items()},
        "a2_floor_ratio_rule": A2_FLOOR_RATIO,
        "growth_sse_ratio": 0.1,
        "evidence_after_observation": evidence,
    }
    path = write_record(RESULTS / "gates_frozen.json", payload)
    print("gates frozen/echoed ->", path)


# ---------------------------------------------------------------------------
# Step 8: C — tier ladder + registered controls
# ---------------------------------------------------------------------------


def _max_delta(a_traj, b_traj, body: str) -> float:
    _, delta = trajectory_difference(a_traj, b_traj, body)
    return float(np.max(np.linalg.norm(delta, axis=1)))


def cmd_c() -> None:
    provider = _require_kernel()
    frame, origin = _ref_meta()
    tiers: dict[str, dict] = {}
    controls: dict[str, dict] = {}

    for tier_name, bodies in TIERS.items():
        state = _ref_ic(provider, bodies)
        cfg = SimulationConfig(
            bodies=bodies,
            integrator="rk4",
            dt=DT_EM,
            duration=30 * D_S,
            epoch_jd=EPOCH_JD,
            reference_dataset=REFERENCE_DATASET_STR,
        )
        out = RESULTS / "experiment_C" / f"tier_{tier_name}"
        rr = run_reproducible(cfg, state, out, sample_every=C_SAMPLE_EVERY)
        comparisons = {"Earth": _compare(rr["traj"], provider, "Earth").to_dict()}
        if "Moon" in bodies:
            comparisons["Moon"] = _compare(rr["traj"], provider, "Moon").to_dict()
        gates = [
            gate(
                "E_pos[0] == 0 exactly (DE440-derived IC)",
                threshold="0.0 exact",
                measured=float(comparisons["Earth"]["position_error"][0]),
                reason="§6c / H_D1",
                passed=bool(comparisons["Earth"]["position_error"][0] == 0.0),
            ),
            gate(
                "reproducible (2 runs bitwise + equal output_hash)",
                threshold="np.array_equal + equal hashes",
                measured="equal",
                reason="§6d",
                passed=bool(rr["reproducible"]),
            ),
        ]
        write_record(
            out / "experiment_record.json",
            experiment_record(
                f"C/{tier_name}",
                cfg,
                initial_condition_source=IC_SOURCE_REFERENCE,
                output_hash_value=rr["output_hash"],
                second_output_hash=rr["second_output_hash"],
                reproducible=bool(rr["reproducible"]),
                runtime_s=rr["runtime_s"],
                run_record=rr["run_record"],
                reference_frame=frame,
                reference_origin=origin,
                comparison=comparisons,
                gates=gates,
                extra={
                    "tier": tier_name,
                    "sample_every": C_SAMPLE_EVERY,
                    "shared_dt_all_tiers": DT_EM,
                    "dt_rule": "P_EM/1000 — one dt for every tier (§5, R-S2)",
                },
            ),
        )
        tiers[tier_name] = rr

    for tier_name in ("T2", "T3"):
        bodies = TIERS[tier_name]
        state = _ref_ic(provider, bodies)
        cfg = SimulationConfig(
            bodies=bodies,
            integrator="rk4",
            dt=DT_EM / 2.0,
            duration=30 * D_S,
            epoch_jd=EPOCH_JD,
            reference_dataset=REFERENCE_DATASET_STR,
        )
        out = RESULTS / "experiment_C" / f"control_{tier_name}_dt2"
        rr = run_reproducible(
            cfg, state, out, sample_every=C_CONTROL_SAMPLE_EVERY
        )
        comparisons = {"Earth": _compare(rr["traj"], provider, "Earth").to_dict()}
        if "Moon" in bodies:
            comparisons["Moon"] = _compare(rr["traj"], provider, "Moon").to_dict()
        write_record(
            out / "experiment_record.json",
            experiment_record(
                f"C/control/{tier_name}@dt/2",
                cfg,
                initial_condition_source=IC_SOURCE_REFERENCE,
                output_hash_value=rr["output_hash"],
                second_output_hash=rr["second_output_hash"],
                reproducible=bool(rr["reproducible"]),
                runtime_s=rr["runtime_s"],
                run_record=rr["run_record"],
                reference_frame=frame,
                reference_origin=origin,
                comparison=comparisons,
                gates=[
                    gate(
                        "reproducible (2 runs bitwise + equal output_hash)",
                        threshold="np.array_equal + equal hashes",
                        measured="equal",
                        reason="§6d",
                        passed=bool(rr["reproducible"]),
                    )
                ],
                extra={
                    "tier": tier_name,
                    "dt": DT_EM / 2.0,
                    "sample_every": C_CONTROL_SAMPLE_EVERY,
                    "control_purpose": (
                        "registered dt/2 control — sample times match the "
                        "main grid exactly (steps 200k of dt/2 = steps 100k "
                        "of dt) so trajectory_difference applies directly (§3.1 row C)"
                    ),
                },
            ),
        )
        controls[tier_name] = rr

    # --- signals + controls ----------------------------------------------
    pairs = (("T1", "T2"), ("T2", "T3"), ("T3", "T4"))
    analysis: dict = {
        "experiment_id": "C/analysis",
        "criterion": f"signal >= {C_SIGNAL_FACTOR} x control (frozen §3.1 row C)",
        "control_assignment_rule": (
            "signal(T_a <-> T_b) judged against the control of the UPPER "
            "tier T_b; T3<->T4 borrowing T3 is pre-registered explicitly, "
            "T1<->T2 and T2<->T3 follow the same rule (recorded here before judging)."
        ),
        "signals": [],
        "all_resolved": True,
    }
    for a, b in pairs:
        bodies_a, bodies_b = TIERS[a], TIERS[b]
        common = [x for x in bodies_a if x in bodies_b]
        ctrl_tier = b if b in controls else {"T4": "T3"}[b]  # upper tier; T4↔T3 borrows T3 (pre-registered)
        entry: dict = {"pair": f"{a}<->{b}", "common_bodies": common, "metrics": []}
        for body in ("Earth", "Moon"):
            if body not in common:
                continue
            signal = _max_delta(tiers[a]["traj"], tiers[b]["traj"], body)
            control = _max_delta(
                tiers[ctrl_tier]["traj"], controls[ctrl_tier]["traj"], body
            )
            passed = signal >= C_SIGNAL_FACTOR * control
            entry["metrics"].append(
                {
                    "metric": f"max|Δ{body}| between tiers (m)",
                    "signal_m": signal,
                    "control_tier": ctrl_tier,
                    "control_m": control,
                    "threshold_factor": C_SIGNAL_FACTOR,
                    "resolved": passed,
                }
            )
            analysis["all_resolved"] = bool(analysis["all_resolved"] and passed)
        # subset barycentre signal + control
        sa = subset_barycentre(tiers[a]["traj"], common)
        sb = subset_barycentre(tiers[b]["traj"], common)
        if sa.shape == sb.shape:
            signal_bc = float(np.max(np.linalg.norm(sa - sb, axis=1)))
            ca = subset_barycentre(tiers[ctrl_tier]["traj"], common)
            cb = subset_barycentre(controls[ctrl_tier]["traj"], common)
            control_bc = float(np.max(np.linalg.norm(ca - cb, axis=1)))
            entry["metrics"].append(
                {
                    "metric": f"max|Δbarycentre{common}| (m)",
                    "signal_m": signal_bc,
                    "control_tier": ctrl_tier,
                    "control_m": control_bc,
                    "threshold_factor": C_SIGNAL_FACTOR,
                    "resolved": signal_bc >= C_SIGNAL_FACTOR * control_bc,
                }
            )
        analysis["signals"].append(entry)

    analysis["conclusion"] = (
        "all adjacent-tier signals exceed 10x the registered halving control"
        if analysis["all_resolved"]
        else "signal not numerically resolved (§3.1 row C: report the phrase, "
        "never lower the 10x criterion, never force a physical interpretation)"
    )
    path = write_record(RESULTS / "experiment_C" / "analysis.json", analysis)
    print("C complete ->", path)


# ---------------------------------------------------------------------------
# Step 9: D — DE440 validation (formal stage9/10 + report-only)
# ---------------------------------------------------------------------------


def _stage_bands_gate(
    bands: dict[str, tuple[float, float]], stats: dict, *, stage: str
) -> list[dict]:
    gates = []
    pmax = float(stats["position_stats"]["max"])
    lo, hi = bands["E_pos"]
    gates.append(
        gate(
            f"{stage} max E_pos band",
            threshold=[lo, hi],
            measured=pmax,
            reason="Phase-4 stage threshold (measured 2026-10-03, ceiling 100x); "
            "reused unchanged — no post-hoc number",
            passed=lo <= pmax <= hi,
        )
    )
    vmax = float(stats["velocity_stats"]["max"])
    lo_v, hi_v = bands["E_vel"]
    gates.append(
        gate(
            f"{stage} max E_vel band",
            threshold=[lo_v, hi_v],
            measured=vmax,
            reason="Phase-4 stage threshold, reused unchanged",
            passed=lo_v <= vmax <= hi_v,
        )
    )
    if "E_rel_max" in bands:
        rel = max(float(x) for x in stats["relative_position_error"])
        lo_r, hi_r = bands["E_rel_max"]
        gates.append(
            gate(
                f"{stage} max relative position error ceiling",
                threshold=hi_r,
                measured=rel,
                reason="Phase-4 stage9 ceiling (100x measured 3.4486e-5), reused",
                passed=rel <= hi_r,
            )
        )
    return gates


def cmd_d() -> None:
    provider = _require_kernel()
    frame, origin = _ref_meta()
    runs = (
        # name, bodies, dt, days, sample_every, formal stage bands or None
        ("T1_7d", TIER_T1, DT_SE, 7, 1, "stage9", STAGE9_BANDS),
        ("T2_7d", TIER_T2, DT_EM, 7, 4, "stage10", STAGE10_BANDS),
        ("T3_7d", TIER_T3, DT_EM, 7, 4, "report-only", None),
        ("T1_30d", TIER_T1, DT_SE, 30, 1, "report-only", None),
    )
    for name, bodies, dt, days, se, label, bands in runs:
        state = _ref_ic(provider, bodies)
        cfg = SimulationConfig(
            bodies=bodies,
            integrator="rk4",
            dt=dt,
            duration=days * D_S,
            epoch_jd=EPOCH_JD,
            reference_dataset=REFERENCE_DATASET_STR,
        )
        out = RESULTS / "experiment_D" / name
        rr = run_reproducible(cfg, state, out, sample_every=se)
        cmp = _compare(rr["traj"], provider, "Earth")
        stats = cmp.to_dict()
        expected_samples = cfg.n_steps // se + 1
        gates = [
            gate(
                "E_pos[0] == 0 exactly (DE440-derived IC, H_D1)",
                threshold="0.0 exact",
                measured=float(cmp.position_error[0]),
                reason="§6c / H_D1 — pre-registered hypothesis, valid at every tier",
                passed=bool(cmp.position_error[0] == 0.0),
            ),
            gate(
                "sample count matches grid",
                threshold=expected_samples,
                measured=int(cmp.position_stats.n_samples),
                reason="completion gate (step*se*dt grid)",
                passed=int(cmp.position_stats.n_samples) == expected_samples,
            ),
            gate(
                "reproducible (2 runs bitwise + equal output_hash)",
                threshold="np.array_equal + equal hashes",
                measured="equal",
                reason="§6d",
                passed=bool(rr["reproducible"]),
            ),
        ]
        if bands is not None:
            gates.extend(_stage_bands_gate(bands, stats, stage=label))
        write_record(
            out / "experiment_record.json",
            experiment_record(
                f"D/{name}",
                cfg,
                initial_condition_source=IC_SOURCE_REFERENCE,
                output_hash_value=rr["output_hash"],
                second_output_hash=rr["second_output_hash"],
                reproducible=bool(rr["reproducible"]),
                runtime_s=rr["runtime_s"],
                run_record=rr["run_record"],
                reference_frame=frame,
                reference_origin=origin,
                comparison=stats,
                gates=gates,
                extra={
                    "run_label": label,
                    "formal_acceptance": bands is not None,
                    "report_only_note": (
                        "numbers + interpretation only; NO new threshold "
                        "invented (§3.1 row D, ambiguity #4)"
                        if bands is None
                        else "Phase-4 stage9/10 bands reused unchanged"
                    ),
                    "sample_every": se,
                    "kernel_manifest_audit": "config reference_dataset == "
                    + REFERENCE_DATASET_STR
                    + "; kernel hashes verified at load",
                },
            ),
        )

    # 30 d report-only T2/T3: REUSE the C runs (identical config by design).
    import json

    for tier_name in ("T2", "T3"):
        c_file = RESULTS / "experiment_C" / f"tier_{tier_name}" / "experiment_record.json"
        c_rec = json.loads(c_file.read_text(encoding="utf-8"))
        bodies = TIERS[tier_name]
        cfg = SimulationConfig(
            bodies=bodies,
            integrator="rk4",
            dt=DT_EM,
            duration=30 * D_S,
            epoch_jd=EPOCH_JD,
            reference_dataset=REFERENCE_DATASET_STR,
        )
        assert (
            c_rec["configuration_hash"] == cfg.config_hash()
        ), "C tier config drifted — D reuse requires identical config"
        write_record(
            RESULTS / "experiment_D" / f"{tier_name}_30d" / "experiment_record.json",
            {
                "schema_version": 1,
                "experiment_id": f"D/{tier_name}_30d",
                "reused_from": f"experiment_C/tier_{tier_name}",
                "run_label": "report-only",
                "formal_acceptance": False,
                "configuration_hash": cfg.config_hash(),
                "output_hash": c_rec["output_hash"],
                "initial_condition_source": IC_SOURCE_REFERENCE,
                "comparison": c_rec["comparison"],
                "note": (
                    "D 30 d runs are report-only: numbers + interpretation "
                    "only, no pass/fail (§3.1 row D); this record points at "
                    "the byte-identical C run (same config_hash)."
                ),
                "design_contract": str(DESIGN_DOC),
            },
        )
    print("D complete ->", RESULTS / "experiment_D")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="experiments.run_phase5")
    parser.add_argument(
        "command",
        choices=[
            "a1", "baseline", "a2", "bref",
            "e1", "e30", "freeze-gates", "c", "d", "e90", "e365",
        ],
    )
    args = parser.parse_args(argv)
    cmds = {
        "a1": cmd_a1,
        "baseline": cmd_baseline,
        "a2": cmd_a2,
        "bref": cmd_bref,
        "e1": lambda: cmd_e(1),
        "e30": lambda: cmd_e(30),
        "freeze-gates": cmd_freeze_gates,
        "c": cmd_c,
        "d": cmd_d,
        "e90": lambda: cmd_e(90),
        "e365": lambda: cmd_e(365),
    }
    cmds[args.command]()


if __name__ == "__main__":
    main()
