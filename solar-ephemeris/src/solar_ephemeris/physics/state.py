"""State vectors with an explicit frame/epoch/units metadata contract.

Invariant enforced by the constructor: a State cannot exist without knowing
frame, origin, epoch, time scale and units. This is what makes a later
Phase 4 comparison against DE440 checkable instead of silently mixed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale


@dataclass(frozen=True, slots=True)
class StateMeta:
    frame: ReferenceFrame
    origin: str  # explicit, e.g. "barycenter(Sun, Earth)"
    epoch_jd: float  # Julian date of the state, in `time_scale`
    time_scale: TimeScale
    length_unit: str = "m"
    time_unit: str = "s"
    velocity_unit: str = "m/s"
    gm_unit: str = "m^3/s^2"
    axis_note: str = (
        "right-handed inertial; axis alignment arbitrary in Phase 1-2 "
        "(ICRF from Phase 4)"
    )

    def __post_init__(self) -> None:
        if not self.origin:
            raise ValueError("StateMeta.origin must be a non-empty explicit description")
        if not np.isfinite(self.epoch_jd):
            raise ValueError(f"epoch_jd must be finite, got {self.epoch_jd!r}")
        if self.length_unit != "m":
            raise ValueError(f"Phase 1-2 requires length_unit='m', got {self.length_unit!r}")
        if self.time_unit != "s":
            raise ValueError(f"Phase 1-2 requires time_unit='s', got {self.time_unit!r}")
        if self.velocity_unit != "m/s":
            raise ValueError(f"velocity_unit must be 'm/s', got {self.velocity_unit!r}")
        if self.gm_unit != "m^3/s^2":
            raise ValueError(f"gm_unit must be 'm^3/s^2', got {self.gm_unit!r}")


def _as_positions(values: object, *, n_bodies: int | None, label: str) -> NDArray[np.float64]:
    arr = np.array(values, dtype=np.float64, copy=True)
    if arr.ndim != 2 or arr.shape[1] != 3:
        raise ValueError(f"{label} must have shape (N, 3), got {arr.shape}")
    if n_bodies is not None and arr.shape[0] != n_bodies:
        raise ValueError(
            f"{label} has {arr.shape[0]} rows but {n_bodies} body names were given"
        )
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{label} contains NaN or inf")
    return arr


@dataclass(frozen=True, slots=True)
class State:
    positions: NDArray[np.float64]  # (N, 3), m
    velocities: NDArray[np.float64]  # (N, 3), m/s
    body_names: tuple[str, ...]
    meta: StateMeta

    def __post_init__(self) -> None:
        names = tuple(self.body_names)
        if len(names) == 0:
            raise ValueError("body_names must not be empty")
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate body names: {names!r}")
        pos = _as_positions(self.positions, n_bodies=len(names), label="positions")
        vel = _as_positions(self.velocities, n_bodies=len(names), label="velocities")
        object.__setattr__(self, "positions", pos)
        object.__setattr__(self, "velocities", vel)
        object.__setattr__(self, "body_names", names)
        if not np.isfinite(self.meta.epoch_jd):
            raise ValueError("meta.epoch_jd must be finite")

    @property
    def n_bodies(self) -> int:
        return len(self.body_names)

    def barycenter(
        self, gm: NDArray[np.float64]
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """(r_cm, v_cm) weighted by GM; raises if gm shape mismatches."""
        gm = np.asarray(gm, dtype=np.float64)
        if gm.shape != (self.n_bodies,):
            raise ValueError(f"gm must have shape ({self.n_bodies},), got {gm.shape}")
        total = gm.sum()
        if not total > 0.0:
            raise ValueError("sum(gm) must be positive")
        r_cm = (gm[:, None] * self.positions).sum(axis=0) / total
        v_cm = (gm[:, None] * self.velocities).sum(axis=0) / total
        return r_cm, v_cm
