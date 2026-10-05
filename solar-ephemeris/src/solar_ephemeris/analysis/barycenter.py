"""GM-weighted centre of a body subset (or of the whole system).

GM is the mass proxy everywhere in this project (units-and-frames §1), so the
weighted mean is

    r_cm(t) = sum_i GM_i r_i(t) / sum_i GM_i

which equals the true centre of mass to the same consistency level the force
model itself uses. In ``ACTIVE_BODIES_BARYCENTRIC`` the full-system barycentre
must stay at the origin — that invariant is what :func:`barycenter` lets tests
verify directly on recorded trajectories (one result per sample).

Returns per-sample arrays ``(M, 3)``: barycentre analysis on a trajectory is a
time series, not a single point.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.simulation.engine import Trajectory


def barycenter(
    traj: Trajectory, names: Sequence[str] | None = None
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """GM-weighted centre of ``names`` (default: every body).

    Returns ``(r_cm, v_cm)``, each ``(M, 3)`` in metres / m per second.
    Raises ``ValueError`` on an unknown or empty name set.
    """
    names = tuple(names) if names is not None else traj.body_names
    if not names:
        raise ValueError("names must be non-empty")
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate names: {names!r}")
    idx: list[int] = []
    for name in names:
        try:
            idx.append(traj.body_names.index(name))
        except ValueError:
            raise ValueError(
                f"body {name!r} not in trajectory (have {traj.body_names})"
            ) from None
    weights = traj.gm[idx]
    total = float(weights.sum())
    if not total > 0.0:
        raise ValueError("sum(gm) must be positive")
    r_cm = np.einsum("k,mkj->mj", weights, traj.positions[:, idx, :]) / total
    v_cm = np.einsum("k,mkj->mj", weights, traj.velocities[:, idx, :]) / total
    return r_cm, v_cm
