"""Relative two-body state extracted from a recorded trajectory.

Answers the Phase-3 requirement:

    r_EM = r_Moon - r_Earth,  v_EM = v_Moon - v_Earth

plus distance/time diagnostics. Everything is name-based; an unknown body name
or a name repeated as primary==secondary raises instead of silently returning
zeros.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.simulation.engine import Trajectory


@dataclass(frozen=True, slots=True)
class RelativeState:
    times: NDArray[np.float64]  # (M,), s since epoch
    r: NDArray[np.float64]  # (M, 3), m — r = r_secondary - r_primary
    v: NDArray[np.float64]  # (M, 3), m/s
    primary: str
    secondary: str

    def __post_init__(self) -> None:
        times = np.asarray(self.times, dtype=np.float64)
        r = np.asarray(self.r, dtype=np.float64)
        v = np.asarray(self.v, dtype=np.float64)
        if r.ndim != 2 or r.shape[1] != 3 or r.shape != v.shape:
            raise ValueError(f"r and v must both be (M, 3), got {r.shape} / {v.shape}")
        if times.ndim != 1 or times.shape[0] != r.shape[0]:
            raise ValueError("times must be (M,) matching r")
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "r", r)
        object.__setattr__(self, "v", v)

    @property
    def distance(self) -> NDArray[np.float64]:  # (M,), m
        return np.linalg.norm(self.r, axis=1)

    @property
    def speed(self) -> NDArray[np.float64]:  # (M,), m/s
        return np.linalg.norm(self.v, axis=1)


def _index(traj: Trajectory, name: str) -> int:
    try:
        return traj.body_names.index(name)
    except ValueError:
        raise ValueError(
            f"body {name!r} not in trajectory (have {traj.body_names})"
        ) from None


def relative_state(traj: Trajectory, primary: str, secondary: str) -> RelativeState:
    """``RelativeState`` of ``secondary`` seen from ``primary``."""
    if primary == secondary:
        raise ValueError(f"primary and secondary are the same body: {primary!r}")
    i = _index(traj, primary)
    j = _index(traj, secondary)
    return RelativeState(
        times=traj.times,
        r=traj.positions[:, j, :] - traj.positions[:, i, :],
        v=traj.velocities[:, j, :] - traj.velocities[:, i, :],
        primary=primary,
        secondary=secondary,
    )
