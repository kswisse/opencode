"""Timestep convergence: observed order of accuracy against the exact
two-body circular solution (rigid rotation at omega = sqrt((GM1+GM2)/R^3)).

Error norm:  E(dt) = max_i ||r_num,i(T_end) - r_exact,i(T_end)||  (m)
Horizon:     T_end = P/4,  dt_k = T_end / n_k,  n in {25, 50, 100, 200}
Order:       p = log2(E(dt) / E(dt/2))

Measured values (Sun-Earth @ 1 AU, see git history / docstrings):
  RK4    errors: 4.16e4 -> 2.49e3 -> 1.52e2 -> 9.41 m,  p in [4.02, 4.06]
  Verlet errors: 1.48e8 -> 3.71e7 -> 9.27e6 -> 2.32e6 m,  p in [2.00, 2.00]
  floor: 1 AU * 2^-52 = 3.3e-5 m — errors stay far above it.

If p leaves the window, suspect the IC (omega must use GM1+GM2) or a
half-kick velocity before doubting the integrator itself.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.physics.gravity import newtonian_acceleration
from solar_ephemeris.integrators.base import Integrator, get_integrator

N_VALUES = (25, 50, 100, 200)


def endpoint_error(integ: Integrator, ic, n: int, horizon: float) -> float:
    """Integrate to `horizon` with n steps; return max body position error (m)."""
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


def observed_orders(errors: list[float]) -> list[float]:
    return [np.log2(errors[k] / errors[k + 1]) for k in range(len(errors) - 1)]


@pytest.fixture(scope="module")
def rk4_errors(two_body_sun_earth) -> list[float]:
    integ = get_integrator("rk4")
    horizon = two_body_sun_earth.period / 4.0
    return [endpoint_error(integ, two_body_sun_earth, n, horizon) for n in N_VALUES]


def test_rk4_errors_strictly_decrease(rk4_errors):
    for k in range(len(rk4_errors) - 1):
        assert rk4_errors[k + 1] < rk4_errors[k]


def test_rk4_fourth_order_convergence(rk4_errors):
    orders = observed_orders(rk4_errors)
    for p in orders:
        assert 3.5 <= p <= 4.5, f"observed order {p:.3f} outside [3.5, 4.5]: {orders}"


@pytest.fixture(scope="module")
def verlet_errors(two_body_sun_earth) -> list[float]:
    integ = get_integrator("verlet")
    horizon = two_body_sun_earth.period / 4.0
    return [endpoint_error(integ, two_body_sun_earth, n, horizon) for n in N_VALUES]


def test_verlet_errors_strictly_decrease(verlet_errors):
    for k in range(len(verlet_errors) - 1):
        assert verlet_errors[k + 1] < verlet_errors[k]


def test_verlet_second_order_convergence(verlet_errors):
    orders = observed_orders(verlet_errors)
    for p in orders:
        assert 1.5 <= p <= 2.5, f"observed order {p:.3f} outside [1.5, 2.5]: {orders}"


def test_both_integrators_share_the_same_timestep_sweep(rk4_errors, verlet_errors):
    # Comparable timesteps for identical physical inputs (MASTERPLAN Experiment B).
    assert len(rk4_errors) == len(verlet_errors) == len(N_VALUES)
    # RK4 is more accurate per step at every step size in this sweep.
    for e_rk4, e_v in zip(rk4_errors, verlet_errors):
        assert e_rk4 < e_v


def test_rk4_errors_well_above_roundoff_floor(rk4_errors):
    floor_m = 1.5e11 * 2.0**-52  # ~3.3e-5 m at 1 AU
    assert rk4_errors[-1] > 1.0e3 * floor_m
