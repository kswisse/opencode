"""Total mechanical energy of a recorded trajectory — a DIAGNOSTIC only.

    E(t) = sum_i 1/2 m_i |v_i|^2  -  sum_{i<j} G m_i m_j / r_ij
    with m_i = GM_i / G

The project's GM-only rule (units-and-frames §1) holds for the FORCE path;
this function converts GM to mass solely for bookkeeping so the number is
comparable to textbook energy definitions. The result is never fed back into
dynamics — nothing in ``physics/`` or ``integrators/`` may import it for
stepping, and tests treat it as the convergence/conservation observable.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.physics.constants import G_SI
from solar_ephemeris.simulation.engine import Trajectory


def total_energy(traj: Trajectory) -> NDArray[np.float64]:
    """Specific bookkeeping units: J-equivalent of GM/G masses (one per sample).

    Returns ``(M,)`` — total energy at each recorded sample. Complexity is
    O(M N^2); intended for diagnostics, not hot paths.
    """
    mass = traj.gm / G_SI  # kg — bookkeeping only (see module docstring)
    kinetic = 0.5 * np.sum(mass * np.sum(traj.velocities**2, axis=2), axis=1)
    potential = np.zeros(traj.n_samples, dtype=np.float64)
    for i in range(traj.n_bodies):
        for j in range(i + 1, traj.n_bodies):
            r = np.linalg.norm(
                traj.positions[:, i, :] - traj.positions[:, j, :], axis=1
            )
            potential -= mass[i] * mass[j] * G_SI / r
    return kinetic + potential


def relative_energy_error(traj: Trajectory) -> NDArray[np.float64]:
    """``|E(t) - E(0)| / |E(0)|`` — the conservation observable used by tests."""
    e = total_energy(traj)
    e0 = float(e[0])
    if e0 == 0.0:
        raise ValueError("E(0) == 0 — relative energy error undefined")
    return np.abs((e - e0) / e0)
