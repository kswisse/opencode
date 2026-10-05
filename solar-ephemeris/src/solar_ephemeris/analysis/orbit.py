"""Lunar-orbit diagnostics: distance statistics + two period estimators.

:func:`angular_period` (PRIMARY — the characteristic orbital period):

- theta(t) = atan2(r_y, r_x) of the relative position vector, unwrapped;
- period := 2*pi / |least-squares slope of theta(t)|
- requires >= 1.5 net revolutions over the span.
- Insensitive to the two-minima-per-revolution breathing of the Earth-Moon
  distance, so it answers "how long does one revolution take" directly.

:func:`radial_period` (SECONDARY — distance-dip spacing):

- mean spacing between successive LOCAL MINIMA of the distance series, each
  refined by a 3-point parabolic vertex (sub-sample timing, no model fit);
- requires >= 2 minima and quasi-uniform sampling (the engine's fixed
  ``step * dt`` grid guarantees the latter);
- on the Phase-3 model the solar-forced breathing produces TWO dips per
  revolution, so this returns ~14.4 d while the orbital period is ~27.0 d —
  the estimator reports what the samples show; tests assert both numbers
  side by side so the interpretation stays checkable.

Under-resolved timesteps make any estimator confidently wrong, which is why
:mod:`tests.numerical.test_moon_timestep` checks dt convergence alongside.

No smoothing, no detrending, no window functions: if the signal is too noisy
the estimator must fail loudly, not average the noise away.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class DistanceStats:
    minimum: float  # m
    maximum: float  # m
    mean: float  # m
    amplitude: float  # (max - min) / mean, dimensionless

    def __post_init__(self) -> None:
        for label, value in (
            ("minimum", self.minimum),
            ("maximum", self.maximum),
            ("mean", self.mean),
        ):
            if not np.isfinite(value):
                raise ValueError(f"{label} must be finite, got {value!r}")
        if not self.minimum > 0.0:
            raise ValueError(f"minimum must be > 0 (bound orbit), got {self.minimum!r}")
        if self.maximum < self.minimum:
            raise ValueError("maximum < minimum — malformed distance series")


def distance_stats(distance: NDArray[np.float64]) -> DistanceStats:
    d = np.asarray(distance, dtype=np.float64)
    if d.ndim != 1 or d.size == 0:
        raise ValueError(f"distance must be a non-empty (M,) array, got {d.shape}")
    lo = float(np.min(d))
    hi = float(np.max(d))
    mean = float(np.mean(d))
    return DistanceStats(minimum=lo, maximum=hi, mean=mean, amplitude=(hi - lo) / mean)


def _local_minima_times(
    times: NDArray[np.float64], distance: NDArray[np.float64]
) -> NDArray[np.float64]:
    interior = np.arange(1, times.size - 1)
    is_min = (distance[1:-1] < distance[:-2]) & (distance[1:-1] <= distance[2:])
    idx = interior[is_min]
    if idx.size == 0:
        return np.empty(0, dtype=np.float64)
    # Parabolic vertex through (t-h, d-), (t, d0), (t+h, d+) with the local
    # mean spacing h (sampling is quasi-uniform on the engine's step grid).
    t = times[idx]
    d0 = distance[idx]
    dm = distance[idx - 1]
    dp = distance[idx + 1]
    denom = dm - 2.0 * d0 + dp
    ok = denom > 0.0  # a true discrete minimum has positive curvature
    if not np.any(ok):
        return t[ok]
    h = float(np.mean(np.diff(times)))
    delta = 0.5 * (dm[ok] - dp[ok]) / denom[ok]
    delta = np.clip(delta, -1.0, 1.0)
    return t[ok] + delta * h


def radial_period(
    times: NDArray[np.float64], distance: NDArray[np.float64]
) -> float:
    """Mean time between successive distance minima (s). See module docstring.

    NOTE on interpretation: with solar-forced breathing the Earth-Moon distance
    shows TWO local minima per revolution (measured on the Phase-3 model: dip
    spacing ~14.4 d while the Moon completes a revolution in ~27.0 d). This
    estimator honestly reports dip spacing — for the characteristic ORBITAL
    period use :func:`angular_period`, which winds the relative-position angle.

    Raises ``ValueError`` if fewer than two minima are present.
    """
    t = np.asarray(times, dtype=np.float64)
    d = np.asarray(distance, dtype=np.float64)
    if t.ndim != 1 or d.ndim != 1 or t.shape != d.shape:
        raise ValueError(f"times and distance must be matching (M,), got {t.shape}/{d.shape}")
    if t.size < 3:
        raise ValueError("need at least 3 samples to locate a minimum")
    minima = _local_minima_times(t, d)
    if minima.size < 2:
        raise ValueError(
            f"need >= 2 distance minima for a period, found {minima.size} "
            "(shorten the span or fix the sampling)"
        )
    return float(np.mean(np.diff(minima)))


def angular_period(
    times: NDArray[np.float64],
    r: NDArray[np.float64],
    *,
    min_turns: float = 1.5,
) -> float:
    """Characteristic orbital period from the winding of the relative position
    vector (s).

    Estimator contract (no fitting of any force model):

    - theta(t) = atan2(r_y, r_x), unwrapped;
    - period = 2*pi / |slope| where slope is the least-squares slope of
      theta(t) — the mean angular rate of the relative motion;
    - requires at least ``min_turns`` net revolutions, else the number would be
      extrapolated from a fraction of a turn and ``ValueError`` is raised.

    This is the PRIMARY period estimator for Phase 3: it is insensitive to the
    two-minima-per-revolution breathing that defeats minima counting, and it
    measures exactly what "orbital period" means (one full revolution of the
    relative position vector).
    """
    t = np.asarray(times, dtype=np.float64)
    rv = np.asarray(r, dtype=np.float64)
    if t.ndim != 1 or rv.ndim != 2 or rv.shape[1] != 3 or rv.shape[0] != t.shape[0]:
        raise ValueError(f"r must be (M, 3) matching times (M,), got {rv.shape}/{t.shape}")
    if t.size < 3:
        raise ValueError("need at least 3 samples")
    theta = np.unwrap(np.arctan2(rv[:, 1], rv[:, 0]))
    turns = float((theta[-1] - theta[0]) / (2.0 * np.pi))
    if abs(turns) < min_turns:
        raise ValueError(
            f"span covers only {turns:.3f} revolutions (< {min_turns}) — "
            "extend the run before quoting a period"
        )
    slope = float(np.polyfit(t, theta, 1)[0])
    if slope == 0.0:
        raise ValueError("relative position vector does not wind — no orbit")
    return float(2.0 * np.pi / abs(slope))
