"""Conservation diagnostics: energy, linear momentum, angular momentum.

Formulas are written in GM form (MASTERPLAN / units-and-frames.md section 2):
the common factor 1/G is dropped because every assertion is a RATIO, so it
cannot affect any threshold.

    E  = sum_i 1/2 * GM_i * |v_i|^2  -  sum_{i<j} GM_i*GM_j / r_ij     [m^5/s^4 / G = J]
    P  = sum_i (GM_i/G) * v_i
    L  = sum_i (GM_i/G) * (r_i x v_i)   (origin = barycenter of the active set)

Setup: circular two-body orbit at 1 AU, dt = P/1000 (~3.16e4 s), N = 2.

Calibration rule: thresholds = 10-100 x measured value, never looser than the
analytic bound listed below. Measured (Sun-Earth @ 1 AU, dt = P/1000):
  Verlet max|dE/E0| (1 P)     = 3.9e-10  (bounded oscillation; general analytic
                                          bound O((omega*dt)^2) ~ 4e-5)
  Verlet slope*P/|E0|         = 2.8e-16  (no secular trend — fp noise)
  RK4   max|dE/E0| (1 P)      = 1.7e-12
  RK4   max|dE/E0| (2 P)      = 3.4e-12
  max|P|/scale                = 2.0e-20 (Verlet), 1.0e-20 (RK4)
  max|dL|/|L0|                = 2.5e-15 (Verlet), 8.5e-13 (RK4)

INTERPRETATION (do not misread): a bounded oscillation of E in Verlet is the
symplectic signature, NOT instability. Only the regression SLOPE of E(t) is a
drift; test_n2 measures the slope separately from test_n1's amplitude.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.physics.constants import G_SI
from solar_ephemeris.physics.gravity import newtonian_acceleration
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine, Trajectory
from solar_ephemeris.physics.state import State, StateMeta
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

# Phase 5 gap 1 (design §7): momentum diagnostics promoted to source; this
# file now imports the one shared definition (same formulas as before).
from solar_ephemeris.analysis.momentum import (
    angular_momentum_series,
    momentum_series,
)

EPOCH = 2451545.0


def make_state(ic) -> State:
    return State(
        positions=ic.positions0.copy(),
        velocities=ic.velocities0.copy(),
        body_names=("Sun", "Earth"),
        meta=StateMeta(
            frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
            origin="barycenter(Sun, Earth)",
            epoch_jd=EPOCH,
            time_scale=TimeScale.TDB,
        ),
    )


def energy_series(traj: Trajectory) -> np.ndarray:
    """(M,) energy in GM units (factor 1/G dropped)."""
    speed2 = np.sum(traj.velocities**2, axis=2)  # (M, N)
    ke = 0.5 * np.sum(traj.gm[None, :] * speed2, axis=1)
    n = traj.n_bodies
    pe = np.zeros(traj.n_samples)
    for i in range(n):
        for j in range(i + 1, n):
            r = np.linalg.norm(
                traj.positions[:, i, :] - traj.positions[:, j, :], axis=1
            )
            pe -= traj.gm[i] * traj.gm[j] / r
    return ke + pe


def run_period(two_body_sun_earth, integrator: str, *, periods: float = 1.0) -> Trajectory:
    ic = two_body_sun_earth
    dt = ic.period / 1000.0
    cfg = SimulationConfig(
        bodies=("Sun", "Earth"),
        integrator=integrator,
        dt=dt,
        duration=periods * ic.period,
        epoch_jd=EPOCH,
    )
    return SimulationEngine(cfg).run(make_state(ic), sample_every=1)


def relative_energy_error(traj: Trajectory) -> np.ndarray:
    e = energy_series(traj)
    return np.abs(e - e[0]) / np.abs(e[0])


@pytest.fixture(scope="module")
def verlet_one_period(two_body_sun_earth) -> Trajectory:
    return run_period(two_body_sun_earth, "verlet")


@pytest.fixture(scope="module")
def rk4_one_period(two_body_sun_earth) -> Trajectory:
    return run_period(two_body_sun_earth, "rk4")


def test_n1_verlet_energy_oscillation_bounded(verlet_one_period):
    # measured 3.9e-10; general analytic bound O((omega*dt)^2) ~ 4e-5 — the
    # threshold sits 25x above measured and 4e4x below the analytic ceiling.
    max_rel = float(np.max(relative_energy_error(verlet_one_period)))
    assert max_rel < 1e-8, f"measured {max_rel:.3e}"


def test_n2_verlet_has_no_secular_energy_drift(verlet_one_period):
    """Regression slope of E(t) — distinguishes bounded oscillation from drift."""
    traj = verlet_one_period
    e = energy_series(traj)
    t = traj.times
    slope = float(np.polyfit(t, e, 1)[0])
    e0 = abs(float(e[0]))
    drift_over_period = abs(slope) * traj.times[-1] / e0
    # measured 2.8e-16 (fp noise floor); 1e-12 still catches any real drift
    assert drift_over_period < 1e-12, f"measured slope*P/|E0| = {drift_over_period:.3e}"


def test_n3_rk4_energy_is_flat(rk4_one_period):
    max_rel = float(np.max(relative_energy_error(rk4_one_period)))
    assert max_rel < 1e-10, f"measured {max_rel:.3e}"


@pytest.mark.parametrize("integrator", ["verlet", "rk4"])
def test_n4_linear_momentum_conserved(two_body_sun_earth, integrator):
    traj = run_period(two_body_sun_earth, integrator)
    p = momentum_series(traj)
    masses = traj.gm / G_SI
    v_scale = float(np.max(np.linalg.norm(traj.velocities, axis=2)))
    scale = float(np.sum(masses) * v_scale)
    max_p = float(np.max(np.linalg.norm(p, axis=1)))
    assert max_p / scale < 1e-12, f"measured {max_p / scale:.3e}"


def test_n5a_verlet_angular_momentum(verlet_one_period):
    traj = verlet_one_period
    l = angular_momentum_series(traj)
    l0 = float(np.linalg.norm(l[0]))
    drift = float(np.max(np.linalg.norm(l - l[0], axis=1)))
    assert drift / l0 < 1e-12, f"measured {drift / l0:.3e}"


def test_n5b_rk4_angular_momentum(rk4_one_period):
    traj = rk4_one_period
    l = angular_momentum_series(traj)
    l0 = float(np.linalg.norm(l[0]))
    drift = float(np.max(np.linalg.norm(l - l[0], axis=1)))
    assert drift / l0 < 1e-11, f"measured {drift / l0:.3e}"


def test_n6_rk4_energy_over_two_periods(two_body_sun_earth):
    traj = run_period(two_body_sun_earth, "rk4", periods=2.0)
    max_rel = float(np.max(relative_energy_error(traj)))
    assert max_rel < 1e-10, f"measured {max_rel:.3e}"
