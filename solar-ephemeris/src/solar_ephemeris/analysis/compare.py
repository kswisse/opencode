"""Quantitative difference between two runs of the same physical body.

Used by the Phase-3 Moon-perturbation experiment: Model B minus Model A on a
named body, over identical sample times.

Contract:

- both trajectories must carry ``name``;
- sample times must be BITWISE identical (``np.array_equal``). Runs built from
  the same dt/duration/sample_every satisfy this because the engine computes
  times as ``step * dt`` with no accumulation; anything else is a different
  sampling grid and mixing them would silently interpolate.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.simulation.engine import Trajectory


def _index(traj: Trajectory, name: str) -> int:
    try:
        return traj.body_names.index(name)
    except ValueError:
        raise ValueError(
            f"body {name!r} not in trajectory (have {traj.body_names})"
        ) from None


def trajectory_difference(
    traj_a: Trajectory, traj_b: Trajectory, name: str
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """``(times, delta)`` with delta = r_a - r_b for ``name``, shape (M, 3), m."""
    i = _index(traj_a, name)
    j = _index(traj_b, name)
    if not np.array_equal(traj_a.times, traj_b.times):
        raise ValueError(
            "sample times differ between trajectories — align the sampling "
            "grids before differencing (never interpolate silently)"
        )
    return traj_a.times, traj_a.positions[:, i, :] - traj_b.positions[:, j, :]
