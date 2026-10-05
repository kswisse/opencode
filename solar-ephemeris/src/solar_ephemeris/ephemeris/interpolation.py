"""Deterministic cubic-Hermite interpolation of sampled reference states.

Primary comparison path does NOT interpolate: the SPK is evaluated by SPICE
at exact epochs. This module exists for *sampled* reference data — the
recorded fixture backend and any batch capture — using cubic Hermite on
sampled positions AND velocities:

- C¹-continuous, exact for cubics, O(h⁴) position error on an interval,
- consumes the velocity component we already carry (no finite differences),
- fully deterministic: same et in → bit-identical out (stateless evaluation).

Strict contract (requirement 11):
- epochs must be strictly increasing (duplicates and non-monotonic grids are
  rejected with :class:`InterpolationError`),
- evaluation domain is the closed interval [t₀, t_N]: endpoints exact,
  anything outside raises — **zero extrapolation**,
- an epoch equal to a sample returns that sample bit-exact (no rounding
  through the polynomial).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.ephemeris.types import InterpolationError


class CubicHermiteInterpolator:
    """C¹ cubic Hermite on a strictly-increasing sampled grid.

    Parameters
    ----------
    epochs:
        (n,) sample times, strictly increasing, n >= 2.
    positions:
        (n, 3) positions at those epochs (any consistent unit).
    velocities:
        (n, 3) velocities at those epochs (unit/time matching ``positions``).
    """

    def __init__(
        self,
        epochs: NDArray[np.float64],
        positions: NDArray[np.float64],
        velocities: NDArray[np.float64],
    ) -> None:
        et = np.asarray(epochs, dtype=np.float64)
        pos = np.asarray(positions, dtype=np.float64)
        vel = np.asarray(velocities, dtype=np.float64)
        if et.ndim != 1 or et.size < 2:
            raise InterpolationError(f"epochs must be 1-D with n >= 2, got shape {et.shape}")
        if pos.shape != (et.size, 3) or vel.shape != (et.size, 3):
            raise InterpolationError(
                f"positions/velocities must have shape ({et.size}, 3), "
                f"got {pos.shape} / {vel.shape}"
            )
        if not (np.all(np.isfinite(et)) and np.all(np.isfinite(pos)) and np.all(np.isfinite(vel))):
            raise InterpolationError("sample grid contains NaN/inf")
        if not np.all(np.diff(et) > 0.0):
            if np.any(np.diff(et) == 0.0):
                raise InterpolationError("duplicate epochs in sample grid")
            raise InterpolationError("epochs must be strictly increasing (non-monotonic grid)")
        self._et = et
        self._pos = pos
        self._vel = vel

    @property
    def epochs(self) -> NDArray[np.float64]:
        return self._et

    @property
    def domain(self) -> tuple[float, float]:
        """Closed evaluation domain [t₀, t_N] (no extrapolation beyond it)."""
        return float(self._et[0]), float(self._et[-1])

    def _locate(self, t: float) -> int:
        """Index i such that epochs[i] <= t <= epochs[i+1]; -1 if t is a sample."""
        i = int(np.searchsorted(self._et, t, side="right") - 1)
        if 0 <= i < self._et.size and t == self._et[i]:
            return -1  # exact sample hit
        lo, hi = self.domain
        if t < lo or t > hi:
            raise InterpolationError(
                f"et={t!r} outside sample domain [{lo!r}, {hi!r}]; "
                "extrapolation is forbidden"
            )
        # t strictly inside: searchsorted right-1 gives the bracketing left index
        if i < 0 or i >= self._et.size - 1:
            raise InterpolationError(f"internal bracket error for et={t!r}")
        return i

    def evaluate(
        self, et: float | NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Position and velocity at ``et`` (scalar or array).

        Exact sample epochs return the stored values bit-exact; interior
        points use the Hermite cubic of the bracketing interval.
        """
        scalar = np.isscalar(et) or (isinstance(et, np.ndarray) and et.ndim == 0)
        ts = np.atleast_1d(np.asarray(et, dtype=np.float64))
        if not np.all(np.isfinite(ts)):
            raise InterpolationError("query epochs contain NaN/inf")

        positions = np.empty((ts.size, 3), dtype=np.float64)
        velocities = np.empty((ts.size, 3), dtype=np.float64)
        for k, t in enumerate(ts):
            i = self._locate(float(t))
            if i == -1:  # exact sample: bit-exact passthrough
                j = int(np.searchsorted(self._et, t, side="right") - 1)
                positions[k] = self._pos[j]
                velocities[k] = self._vel[j]
                continue
            t0, t1 = float(self._et[i]), float(self._et[i + 1])
            h = t1 - t0
            s = (float(t) - t0) / h
            s2, s3 = s * s, s * s * s
            h00 = 2.0 * s3 - 3.0 * s2 + 1.0
            h10 = s3 - 2.0 * s2 + s
            h01 = -2.0 * s3 + 3.0 * s2
            h11 = s3 - s2
            p0, p1 = self._pos[i], self._pos[i + 1]
            v0, v1 = self._vel[i], self._vel[i + 1]
            positions[k] = h00 * p0 + h * (h10 * v0) + h01 * p1 + h * (h11 * v1)
            # d/dt of the Hermite basis (chain rule: (1/h)·d/ds)
            d00 = (6.0 * s2 - 6.0 * s) / h
            d10 = (3.0 * s2 - 4.0 * s + 1.0)
            d01 = (-6.0 * s2 + 6.0 * s) / h
            d11 = (3.0 * s2 - 2.0 * s)
            velocities[k] = d00 * p0 + d10 * v0 + d01 * p1 + d11 * v1

        if scalar:
            return positions[0], velocities[0]
        return positions, velocities
