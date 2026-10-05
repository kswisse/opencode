"""Long-horizon stability + timestep sensitivity.

Horizon: 10 orbital periods at dt = P/1000 (10 000 steps) for both
integrators, plus a deliberately coarse step (dt = P/10) to prove the error
metric actually responds to the timestep (a sanity check against an error
formula that could silently saturate).

Interpretation guard: Verlet's energy may oscillate but must not trend; the
slope assertion below is what distinguishes the two.

Measured (Sun-Earth @ 1 AU, dt = P/1000, 10 periods, run 2026-10-01):
  Verlet max|dE/E0|   = 3.9e-10   (bounded oscillation, same amplitude as 1 P)
  Verlet slope*10P/E0 = 5.1e-15   (fp noise — no secular drift)
  Verlet closure/R    = 8.3e-4    (orbit still closes after 10 revs)
  RK4   max|dE/E0|    = 1.7e-11
  dt sensitivity: E(dt=P/10) / E(dt=P/1000) = 1.2e10 (RK4 energy error)
"""

from __future__ import annotations

import numpy as np

from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine

from numerical.test_conservation import (  # shared helpers, measured in I10
    EPOCH,
    energy_series,
    make_state,
    relative_energy_error,
)


def run_custom_dt(ic, integrator: str, dt: float, *, periods: float = 1.0):
    cfg = SimulationConfig(
        bodies=("Sun", "Earth"),
        integrator=integrator,
        dt=dt,
        duration=periods * ic.period,
        epoch_jd=EPOCH,
    )
    return SimulationEngine(cfg).run(make_state(ic), sample_every=1)


def energy_drift_slope_relative(traj) -> float:
    """|slope| * horizon / |E0| — secular drift, oscillation-blind."""
    e = energy_series(traj)
    slope = float(np.polyfit(traj.times, e, 1)[0])
    return abs(slope) * traj.times[-1] / abs(float(e[0]))


def test_verlet_ten_periods_bounded_energy(two_body_sun_earth):
    ic = two_body_sun_earth
    traj = run_custom_dt(ic, "verlet", ic.period / 1000.0, periods=10.0)
    assert traj.n_samples == 10001
    max_rel = float(np.max(relative_energy_error(traj)))
    # measured 3.9e-10 over 10 P (same bounded amplitude as 1 P); threshold
    # 1e-6 is 2500x above measured but 10 000x below the design ceiling 1e-2,
    # so any real growth of the oscillation trips it.
    assert max_rel < 1e-6, f"measured {max_rel:.3e}"


def test_verlet_ten_periods_no_secular_drift(two_body_sun_earth):
    ic = two_body_sun_earth
    traj = run_custom_dt(ic, "verlet", ic.period / 1000.0, periods=10.0)
    drift = energy_drift_slope_relative(traj)
    # measured 5.1e-15 (fp noise); 1e-10 catches any genuine secular trend
    assert drift < 1e-10, f"measured slope*10P/|E0| = {drift:.3e}"


def test_verlet_orbit_still_closes_after_ten_periods(two_body_sun_earth):
    ic = two_body_sun_earth
    traj = run_custom_dt(ic, "verlet", ic.period / 1000.0, periods=10.0)
    closure = float(
        np.max(np.linalg.norm(traj.positions[-1] - traj.positions[0], axis=1))
    ) / ic.separation
    assert closure < 1e-2, f"measured closure/R = {closure:.3e}"


def test_rk4_ten_periods_energy(two_body_sun_earth):
    ic = two_body_sun_earth
    traj = run_custom_dt(ic, "rk4", ic.period / 1000.0, periods=10.0)
    max_rel = float(np.max(relative_energy_error(traj)))
    assert max_rel < 1e-8, f"measured {max_rel:.3e}"


def test_error_metric_responds_to_timestep(two_body_sun_earth):
    """A coarse step must be dramatically worse than a fine one — this catches
    an error metric that has saturated, is comparing to itself, or an
    integrator that ignores dt."""
    ic = two_body_sun_earth
    coarse = run_custom_dt(ic, "rk4", ic.period / 10.0)
    fine = run_custom_dt(ic, "rk4", ic.period / 1000.0)
    e_coarse = float(np.max(relative_energy_error(coarse)))
    e_fine = float(np.max(relative_energy_error(fine)))
    assert e_coarse > 100.0 * e_fine, (
        f"coarse {e_coarse:.3e} not 100x fine {e_fine:.3e}"
    )
