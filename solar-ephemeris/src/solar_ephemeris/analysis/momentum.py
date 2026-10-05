"""Linear and angular momentum series — diagnostics only (Phase 5 gap 1).

Promoted verbatim from ``tests/numerical/test_conservation.py`` (same
formulas, no behaviour change) so experiments reuse ONE definition instead
of writing their own (design ``phase5-experiment-design.md`` §7 row 1).

Both are diagnostics over a recorded Trajectory, GM-weighted (the project's
GM-only mass proxy, units-and-frames §1); nothing in ``physics/`` or
``integrators/`` may feed them back into dynamics.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.physics.constants import G_SI
from solar_ephemeris.simulation.engine import Trajectory


def momentum_series(traj: Trajectory) -> NDArray[np.float64]:
    """(M, 3) linear momentum in kg m/s."""
    masses = traj.gm / G_SI  # (N,)
    return np.einsum("n,mnc->mc", masses, traj.velocities)


def angular_momentum_series(traj: Trajectory) -> NDArray[np.float64]:
    """(M, 3) angular momentum about the trajectory origin, kg m^2/s."""
    masses = traj.gm / G_SI
    return np.einsum("n,mnc->mc", masses, np.cross(traj.positions, traj.velocities))
