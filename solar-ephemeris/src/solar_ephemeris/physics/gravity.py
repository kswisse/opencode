"""Newtonian pairwise gravitational accelerations.

Force law (MASTERPLAN scientific model):

    a_i = sum_{j != i} GM_j (r_j - r_i) / |r_j - r_i|^3

GM-only (never ``G * m``): DE440 GM values and CODATA G are not a
self-consistent pair, so mass-based evaluation would inject a silent
ppm-level systematic error.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


class CloseEncounterError(FloatingPointError):
    """Two distinct bodies came closer than ``guard_m`` — the inverse-cube
    acceleration is singular there. Raised instead of softening silently."""


def pairwise_accelerations(
    positions: NDArray[np.float64],  # (N, 3), m
    gm: NDArray[np.float64],  # (N,), m^3/s^2, aligned with body order
    *,
    guard_m: float = 1.0,
) -> NDArray[np.float64]:  # (N, 3), m/s^2
    q = np.asarray(positions, dtype=np.float64)
    gmv = np.asarray(gm, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] != 3:
        raise ValueError(f"positions must have shape (N, 3), got {q.shape}")
    n = q.shape[0]
    if gmv.shape != (n,):
        raise ValueError(f"gm must have shape ({n},), got {gmv.shape}")
    if guard_m <= 0.0:
        raise ValueError(f"guard_m must be > 0, got {guard_m!r}")
    if n <= 1:
        return np.zeros_like(q)

    # diff[i, j] = r_j - r_i
    diff = q[None, :, :] - q[:, None, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    off_diagonal = ~np.eye(n, dtype=bool)
    r = np.sqrt(r2)
    if np.any(r[off_diagonal] < guard_m):
        # mask off the diagonal first: r[i, i] == 0 would otherwise win the
        # arg in row-major order and the message would name a body as its own
        # partner (defect found during Phase-3 integration, guard behaviour
        # itself was always correct).
        i, j = np.argwhere(off_diagonal & (r < guard_m))[0]
        raise CloseEncounterError(
            f"bodies {int(i)} and {int(j)} closer than guard_m={guard_m} m"
        )
    inv_r3 = np.zeros_like(r2)
    inv_r3[off_diagonal] = 1.0 / r[off_diagonal] ** 3
    # a_i = sum_j GM_j * diff[i, j] / |r_j - r_i|^3  (diagonal j == i is 0)
    return np.einsum("ij,j,ijk->ik", inv_r3, gmv, diff)


def newtonian_acceleration(
    gm: NDArray[np.float64], *, guard_m: float = 1.0
):
    """Return a callable ``accel(q, v, t) -> a`` matching the integrator
    ``Acceleration`` protocol (structural typing — this module must NOT import
    ``solar_ephemeris.integrators``; the engine wires the two together).

    Newtonian gravity is velocity- and time-independent; ``v`` and ``t`` are
    accepted and ignored.
    """
    gm_arr = np.asarray(gm, dtype=np.float64)

    def accel(
        q: NDArray[np.float64],
        v: NDArray[np.float64] | None = None,
        t: float = 0.0,
    ) -> NDArray[np.float64]:
        return pairwise_accelerations(q, gm_arr, guard_m=guard_m)

    return accel
