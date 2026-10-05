"""Frozen run-set tables for the multi-run figures V7/V8/V9 (KTD8).

Every tuple is a COPY of a frozen Phase-5 grid and is asserted against
``experiments/_common.py`` by ``tests/unit/test_viz_api_multi_run.py`` - the
tables may not drift after a run observes a number (design correction #1).

V6 needs no run-set: one ``plot_conservation`` figure consumes one
``trajectory.npz``. Stdlib only - no numpy, no matplotlib (R29).
"""

from __future__ import annotations

#: A1 grid: dt = (P/4)/n over both integrators (design 3.1 row A1).
A1_N_VALUES: tuple[int, ...] = (25, 50, 100, 200)
A1_INTEGRATORS: tuple[str, ...] = ("rk4", "verlet")
A1_RUNSET: tuple[str, ...] = tuple(
    f"{integrator}_n{n}" for integrator in A1_INTEGRATORS for n in A1_N_VALUES
)

#: A2 dt lattice (also the divisor grid of B's ref-lattice, design 3.1).
A2_DIVISORS: tuple[int, ...] = (500, 1000, 2000, 4000)
A2_RUNSET: tuple[str, ...] = tuple(f"d{divisor}" for divisor in A2_DIVISORS)

#: experiment_B stores its lattice under a subdirectory of the same names.
B_LATTICE_REL: str = "ref_lattice"

#: Experiment C: four tier signals + the two registered halving controls.
V8_TIER_DIRS: tuple[str, ...] = ("tier_T1", "tier_T2", "tier_T3", "tier_T4")
V8_CONTROL_DIRS: tuple[str, ...] = ("control_T2_dt2", "control_T3_dt2")
V8_RUNSET: tuple[str, ...] = V8_TIER_DIRS + V8_CONTROL_DIRS

#: Experiment E horizons, days (design 3.1 row E), gated 1 -> 30 -> 90 -> 365.
E_HORIZON_DAYS: tuple[int, ...] = (1, 30, 90, 365)
V9_RUNSET: tuple[str, ...] = tuple(f"horizon_{days}d" for days in E_HORIZON_DAYS)
