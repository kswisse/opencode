"""Configuration-driven simulation description (reproducibility contract).

Two distinct concepts, deliberately separated:

- ``config_hash``: hash of the PHYSICS/NUMERICS-affecting fields only. Two runs
  with the same hash must produce bitwise-identical arrays.
- Run metadata (timestamp, software version, file paths): lives in the runner's
  ``RunRecord``, never in the config — otherwise every run would hash
  differently and reproducibility could never be demonstrated.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, fields

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

_KNOWN_INTEGRATORS = frozenset({"verlet", "rk4"})

# Fields hashed into config_hash. Phase 1-2: every config field influences the
# numerical output (run metadata is not part of SimulationConfig at all).
_HASHED_FIELDS = frozenset(
    {
        "bodies",
        "integrator",
        "dt",
        "duration",
        "epoch_jd",
        "time_scale",
        "frame",
        "reference_dataset",
        "random_seed_if_any",
        "guard_m",
    }
)


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    bodies: tuple[str, ...]
    integrator: str  # "verlet" | "rk4"
    dt: float  # s, > 0
    duration: float  # s, >= dt
    epoch_jd: float  # Julian date of the initial state
    time_scale: TimeScale = TimeScale.TDB
    frame: ReferenceFrame = ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC
    reference_dataset: str | None = None  # filled from Phase 4 on
    random_seed_if_any: int | None = None  # None in Phase 1-2 (pure determinism)
    guard_m: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "bodies", tuple(self.bodies))
        self.validate()

    def validate(self) -> None:
        if not self.bodies:
            raise ValueError("bodies must be non-empty")
        if len(set(self.bodies)) != len(self.bodies):
            raise ValueError(f"duplicate bodies: {self.bodies!r}")
        if not math.isfinite(self.dt) or self.dt <= 0.0:
            raise ValueError(f"dt must be finite and > 0, got {self.dt!r}")
        if not math.isfinite(self.duration) or self.duration < self.dt:
            raise ValueError(
                f"duration must be finite and >= dt ({self.dt}), got {self.duration!r}"
            )
        if not math.isfinite(self.epoch_jd):
            raise ValueError(f"epoch_jd must be finite, got {self.epoch_jd!r}")
        if self.integrator not in _KNOWN_INTEGRATORS:
            raise ValueError(
                f"unknown integrator {self.integrator!r}; "
                f"available: {sorted(_KNOWN_INTEGRATORS)}"
            )
        if not (self.guard_m > 0.0):
            raise ValueError(f"guard_m must be > 0, got {self.guard_m!r}")

    @property
    def n_steps(self) -> int:
        """Number of integration steps (round() so duration/dt slop is stable)."""
        return int(round(self.duration / self.dt))

    def to_dict(self) -> dict:
        out = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, (TimeScale, ReferenceFrame)):
                value = str(value)
            elif isinstance(value, tuple):
                value = list(value)
            out[f.name] = value
        return out

    @classmethod
    def from_dict(cls, d: dict) -> SimulationConfig:
        known = {f.name for f in fields(cls)}
        unknown = set(d) - known
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        payload = dict(d)
        if "bodies" in payload:
            payload["bodies"] = tuple(payload["bodies"])
        return cls(**payload)

    def config_hash(self) -> str:
        payload = {k: self.to_dict()[k] for k in sorted(_HASHED_FIELDS)}
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
