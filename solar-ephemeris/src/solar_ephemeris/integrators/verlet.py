"""Velocity Verlet (leapfrog-family symplectic integrator), order 2.

Purpose in the MASTERPLAN: long-term orbital behaviour, conservation and
stability analysis — a physically interpretable, bounded-energy-drift baseline.
Not universally superior to RK4: it is cheaper per step and symplectic, but
lower order, so at identical step count RK4 wins on accuracy while Verlet wins
on long-horizon energy behaviour.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.integrators.base import Acceleration, Integrator, register_integrator


@register_integrator
class VelocityVerlet(Integrator):
    name = "verlet"
    order = 2

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

        a0 = accel(q, v, t)
        v_half = v + 0.5 * dt * a0
        q1 = q + dt * v_half
        a1 = accel(q1, v_half, t + dt)
        v1 = v_half + 0.5 * dt * a1
        return q1, v1
