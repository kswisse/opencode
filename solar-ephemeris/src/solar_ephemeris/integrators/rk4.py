"""Classical 4th-order Runge-Kutta for the first-order system
y = (q, v), dy/dt = (v, a(q, v, t)).

Purpose in the MASTERPLAN: independent numerical comparison against the
symplectic Verlet/leapfrog baseline, and the reference for timestep/error
trade-off analysis. Non-symplectic — energy behaviour is dissipation-free in
the short term but not bounded over very long horizons.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.integrators.base import Acceleration, Integrator, register_integrator


@register_integrator
class RK4(Integrator):
    name = "rk4"
    order = 4

    def step(
        self,
        q: NDArray[np.float64],
        v: NDArray[np.float64],
        dt: float,
        accel: Acceleration,
        t: float,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        q = np.asarray(q, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)

        k1_q = v
        k1_v = accel(q, v, t)

        k2_q = v + 0.5 * dt * k1_v
        k2_v = accel(q + 0.5 * dt * k1_q, v + 0.5 * dt * k1_v, t + 0.5 * dt)

        k3_q = v + 0.5 * dt * k2_v
        k3_v = accel(q + 0.5 * dt * k2_q, v + 0.5 * dt * k2_v, t + 0.5 * dt)

        k4_q = v + dt * k3_v
        k4_v = accel(q + dt * k3_q, v + dt * k3_v, t + dt)

        q1 = q + (dt / 6.0) * (k1_q + 2.0 * k2_q + 2.0 * k3_q + k4_q)
        v1 = v + (dt / 6.0) * (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v)
        return q1, v1
