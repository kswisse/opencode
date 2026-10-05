"""Phase-3 analysis layer: pure functions over recorded Trajectories.

Each submodule answers one scientific question from the Phase-3 scope:

- :mod:`.relative`   — Earth-Moon relative state (r_EM, v_EM, distance, speed)
- :mod:`.barycenter` — GM-weighted centre of any body subset
- :mod:`.orbit`      — distance statistics and radial (distance-minima) period
- :mod:`.compare`    — quantitative trajectory difference between two runs

Design rules (inherited from Phase 1-2):

- GM-only weighting — GM is the mass proxy everywhere (docs: units-and-frames).
- Names, never indices: bodies are addressed by their ``Trajectory.body_names``
  so a permuted configuration cannot silently swap Earth and Moon.
- No hidden smoothing/fitting: statistics are what the samples say, and
  :func:`orbit.radial_period` documents its estimator.
"""

from solar_ephemeris.analysis.barycenter import barycenter
from solar_ephemeris.analysis.compare import trajectory_difference
from solar_ephemeris.analysis.energy import relative_energy_error, total_energy
from solar_ephemeris.analysis.momentum import (
    angular_momentum_series,
    momentum_series,
)
from solar_ephemeris.analysis.orbit import (
    DistanceStats,
    angular_period,
    distance_stats,
    radial_period,
)
from solar_ephemeris.analysis.relative import RelativeState, relative_state

__all__ = [
    "DistanceStats",
    "RelativeState",
    "angular_momentum_series",
    "angular_period",
    "barycenter",
    "distance_stats",
    "momentum_series",
    "radial_period",
    "relative_energy_error",
    "relative_state",
    "total_energy",
    "trajectory_difference",
]
