"""Translation-only reference→model transform layer (requirement 8, R8).

Phase 4 compares states in the SSB-centred ICRS/J2000 frame. The model side
is SSB-centred too, but a *model-origin* comparison must translate reference
states from SSB to the model's own barycentric origin — a pure GM-weighted
translation. Deliberately rotation-free: J2000 and ICRS differ by ~0.02″
(R8), which is documented in ReferenceMetadata.reference_frame and NOT
corrected here; an unannounced rotation would be the worse error.

All GMs are the project's own physics.constants values — the same weights
the simulation uses — so translation and model dynamics share one source of
mass truth. Core module: must NOT import solar_ephemeris.ephemeris.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray


def barycentre(
    gm: NDArray[np.float64],
    positions: NDArray[np.float64],
    velocities: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """GM-weighted barycentre of a body set.

    Args:
        gm: (N,) gravitational parameters, kg m^3 s^-2, all > 0 (project GMs).
        positions: (N, 3) positions in a common SSB-centred frame, m.
        velocities: (N, 3) velocities in the same frame, m/s.

    Returns:
        (r_cm, v_cm): barycentre position (m) and velocity (m/s), shape (3,).
    """
    gm = np.asarray(gm, dtype=np.float64)
    positions = np.asarray(positions, dtype=np.float64)
    velocities = np.asarray(velocities, dtype=np.float64)
    if gm.ndim != 1 or positions.shape != velocities.shape:
        raise ValueError("gm must be (N,) and positions/velocities equal shapes")
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions/velocities must be (N, 3)")
    if gm.shape[0] != positions.shape[0]:
        raise ValueError("gm length must match body count")
    total = float(gm.sum())
    if not np.all(gm > 0) or total <= 0.0:
        raise ValueError("all GM must be positive and sum > 0")
    r_cm = (gm[:, None] * positions).sum(axis=0) / total
    v_cm = (gm[:, None] * velocities).sum(axis=0) / total
    return r_cm, v_cm


def recenter_ssb_to_model(
    ref_pos: NDArray[np.float64],
    ref_vel: NDArray[np.float64],
    gm: NDArray[np.float64],
    model_bodies: Sequence[str],
) -> tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Translate reference states from SSB to the model barycentric origin.

    Pure translation by the GM-weighted barycentre of ``model_bodies`` (the
    same configuration the simulation runs). No rotation is applied or
    available — see module docstring (R8).

    Args:
        ref_pos: (N, 3) reference positions relative to SSB, m.
        ref_vel: (N, 3) reference velocities relative to SSB, m/s.
        gm: (N,) project gravitational parameters for the same bodies/order.
        model_bodies: (N,) body names, diagnostics only (requirement 5).

    Returns:
        (pos_rel, vel_rel, r_origin, v_origin): states relative to the model
        origin, plus the origin's SSB position/velocity for provenance and
        the offset quantification tests.
    """
    ref_pos = np.asarray(ref_pos, dtype=np.float64)
    ref_vel = np.asarray(ref_vel, dtype=np.float64)
    gm = np.asarray(gm, dtype=np.float64)
    if len(model_bodies) != ref_pos.shape[0]:
        raise ValueError(
            f"model_bodies ({len(model_bodies)}) must match state rows ({ref_pos.shape[0]})"
        )
    r_origin, v_origin = barycentre(gm, ref_pos, ref_vel)
    pos_rel = ref_pos - r_origin  # component-wise translate; order preserved
    vel_rel = ref_vel - v_origin
    return pos_rel, vel_rel, r_origin, v_origin
