"""Reference-data types, coverage, and Phase-4 exceptions.

This module is the metadata spine of the reference pipeline: a reference state
can never exist without the full provenance needed to audit it — "never just
six floats" (MASTERPLAN Phase 4, requirement 3).

No spiceypy in this module: types are backend-agnostic (the provider protocol
lives in :mod:`solar_ephemeris.ephemeris.reference`; only
``ephemeris/spice_backend.py`` may import SPICE).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris import __version__
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

#: The ONE canonical reference of Phase 4. Any provenance record naming a
#: different reference is rejected at construction (requirement 1: no silent
#: substitution of DE441/DE442/Horizons/...).
REFERENCE_NAME: Final[str] = "JPL DE440"

#: SPICE SPK native units (NAIF SPK docs: SPK records are km / km/s).
NATIVE_POSITION_UNIT: Final[str] = "km"
NATIVE_VELOCITY_UNIT: Final[str] = "km/s"

#: Frame/center as produced by the SPICE ingestion path
#: (``spkezr(..., "J2000", "NONE", "SOLAR SYSTEM BARYCENTER")``).
REFERENCE_FRAME: Final[str] = "J2000"
REFERENCE_CENTER: Final[int] = 0  # NAIF ID of the solar-system barycenter
REFERENCE_CENTER_DESC: Final[str] = "ssb(0)"
TIME_STANDARD: Final[str] = "TDB — SPICE ephemeris time, s past J2000 TDB"


# --------------------------------------------------------------------------
# Exceptions (all reference-pipeline problems; ValueError-compatible where
# the project already uses ValueError for contract violations)
# --------------------------------------------------------------------------


class EphemerisError(Exception):
    """Base class for every Phase-4 reference-pipeline error."""


class UnknownBodyMappingError(EphemerisError, KeyError):
    """A project body name has no NAIF ID mapping (never index-based guessing)."""


class MetadataMismatchError(EphemerisError, ValueError):
    """Model/reference metadata disagree — raised BEFORE any subtraction."""

    def __init__(self, field: str, model_value: object, reference_value: object) -> None:
        self.field = field
        self.model_value = model_value
        self.reference_value = reference_value
        super().__init__(
            f"metadata mismatch on {field!r}: model={model_value!r} "
            f"reference={reference_value!r}; reconcile explicitly before comparison"
        )


class CoverageError(EphemerisError, ValueError):
    """Epoch outside kernel coverage — never extrapolates."""


class TimeScaleMismatchError(EphemerisError, ValueError):
    """Non-TDB time scale presented to the reference pipeline.

    Conversions are deliberately unimplemented (units-and-frames.md): TDB in,
    TDB out; anything else is refused, never converted ad hoc.
    """


class FrameUnsupportedError(EphemerisError, ValueError):
    """Frame/center pair not supported by the reference pipeline."""


class UnitError(EphemerisError, ValueError):
    """Unknown native unit — units are declared, never inferred from names."""


class InterpolationError(EphemerisError, ValueError):
    """Interpolation contract violated (non-monotonic, duplicate, out of range)."""


class KernelIntegrityError(EphemerisError, ValueError):
    """Kernel missing or failing identity verification (size/md5/sha256)."""


# --------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Coverage:
    """Closed coverage intervals in SPICE ephemeris time (TDB s past J2000).

    Boundary semantics are part of the contract (MASTERPLAN mandate 10):
    evaluation is allowed at *exact* interval endpoints; anything outside —
    including one ULP beyond — raises :class:`CoverageError` via
    :meth:`require_contains`. Extrapolation never happens silently.
    """

    intervals: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        if not self.intervals:
            raise ValueError("Coverage must contain at least one interval")
        normalized: list[tuple[float, float]] = []
        prev_hi = -np.inf
        for iv in self.intervals:
            if len(iv) != 2:
                raise ValueError(f"coverage interval must be (lo, hi), got {iv!r}")
            lo, hi = float(iv[0]), float(iv[1])
            if not (np.isfinite(lo) and np.isfinite(hi)):
                raise ValueError(f"coverage interval must be finite, got {(lo, hi)!r}")
            if lo > hi:
                raise ValueError(f"coverage interval start > end: {(lo, hi)!r}")
            if lo < prev_hi:
                raise ValueError(
                    "coverage intervals must be sorted and non-overlapping, "
                    f"got {iv!r} after {prev_hi!r}"
                )
            normalized.append((lo, hi))
            prev_hi = hi
        object.__setattr__(self, "intervals", tuple(normalized))

    @property
    def start(self) -> float:
        """Earliest covered ephemeris time (s, TDB past J2000)."""
        return self.intervals[0][0]

    @property
    def end(self) -> float:
        """Latest covered ephemeris time (s, TDB past J2000)."""
        return self.intervals[-1][1]

    def contains(self, et: float) -> bool:
        """True iff ``et`` lies in a closed interval [lo, hi]."""
        return any(lo <= et <= hi for lo, hi in self.intervals)

    def require_contains(self, et: float) -> None:
        """Raise :class:`CoverageError` unless ``et`` is covered."""
        if not self.contains(et):
            raise CoverageError(
                f"ephemeris time et={et!r} outside kernel coverage "
                f"{self.intervals} (TDB s past J2000); refusing to extrapolate"
            )

    def to_dict(self) -> dict[str, Any]:
        return {"intervals": [[lo, hi] for lo, hi in self.intervals]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Coverage:
        return cls(intervals=tuple((float(a), float(b)) for a, b in data["intervals"]))


# --------------------------------------------------------------------------
# Provenance and reference states
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReferenceMetadata:
    """Full provenance of one reference-data source (requirement 2, all fields).

    A record that cannot answer "exactly which DE440 data produced this?"
    cannot be constructed: ``reference_name`` is pinned to
    :data:`REFERENCE_NAME`, units/frame/center/time standard are pinned to the
    SPICE SPK contract, and the kernel identity fields must be well-formed.
    """

    reference_name: str
    reference_version: str
    source: str
    kernel_filename: str
    kernel_md5: str
    kernel_sha256: str
    size_bytes: int
    retrieval_date: str  # ISO-8601 date
    kernel_coverage: Coverage  # MEASURED at load, cross-checked vs manifest
    body_ids: tuple[int, ...]  # from spkobj (actual kernel)
    reference_frame: str
    reference_center: int
    time_standard: str
    native_position_unit: str
    native_velocity_unit: str
    spice_version: str
    software_version: str = __version__

    def __post_init__(self) -> None:
        if self.reference_name != REFERENCE_NAME:
            raise ValueError(
                f"reference_name must be {REFERENCE_NAME!r} (canonical Phase-4 "
                f"reference; substitution forbidden), got {self.reference_name!r}"
            )
        if len(self.kernel_md5) != 32 or any(c not in "0123456789abcdef" for c in self.kernel_md5):
            raise ValueError(f"kernel_md5 must be 32 lowercase hex chars, got {self.kernel_md5!r}")
        if len(self.kernel_sha256) != 64 or any(
            c not in "0123456789abcdef" for c in self.kernel_sha256
        ):
            raise ValueError(
                f"kernel_sha256 must be 64 lowercase hex chars, got {self.kernel_sha256!r}"
            )
        if self.size_bytes <= 0:
            raise ValueError(f"size_bytes must be > 0, got {self.size_bytes!r}")
        if not self.retrieval_date:
            raise ValueError("retrieval_date must be non-empty (ISO-8601)")
        if not self.body_ids:
            raise ValueError("body_ids must not be empty")
        if self.reference_frame != REFERENCE_FRAME:
            raise ValueError(
                f"reference_frame must be {REFERENCE_FRAME!r}, got {self.reference_frame!r}"
            )
        if self.reference_center != REFERENCE_CENTER:
            raise ValueError(
                f"reference_center must be {REFERENCE_CENTER} (SSB), "
                f"got {self.reference_center!r}"
            )
        if not self.time_standard.startswith("TDB"):
            raise ValueError(f"time_standard must be TDB-based, got {self.time_standard!r}")
        if self.native_position_unit != NATIVE_POSITION_UNIT:
            raise ValueError(
                f"native_position_unit must be {NATIVE_POSITION_UNIT!r} (SPK standard), "
                f"got {self.native_position_unit!r}"
            )
        if self.native_velocity_unit != NATIVE_VELOCITY_UNIT:
            raise ValueError(
                f"native_velocity_unit must be {NATIVE_VELOCITY_UNIT!r} (SPK standard), "
                f"got {self.native_velocity_unit!r}"
            )
        object.__setattr__(self, "body_ids", tuple(int(i) for i in self.body_ids))

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference_name": self.reference_name,
            "reference_version": self.reference_version,
            "source": self.source,
            "kernel_filename": self.kernel_filename,
            "kernel_md5": self.kernel_md5,
            "kernel_sha256": self.kernel_sha256,
            "size_bytes": self.size_bytes,
            "retrieval_date": self.retrieval_date,
            "kernel_coverage": self.kernel_coverage.to_dict(),
            "body_ids": list(self.body_ids),
            "reference_frame": self.reference_frame,
            "reference_center": self.reference_center,
            "time_standard": self.time_standard,
            "native_position_unit": self.native_position_unit,
            "native_velocity_unit": self.native_velocity_unit,
            "spice_version": self.spice_version,
            "software_version": self.software_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReferenceMetadata:
        payload = dict(data)
        payload["kernel_coverage"] = Coverage.from_dict(payload["kernel_coverage"])
        payload["body_ids"] = tuple(payload["body_ids"])
        return cls(**payload)


def _vec3(values: object, label: str) -> NDArray[np.float64]:
    arr = np.array(values, dtype=np.float64, copy=True)
    if arr.shape != (3,):
        raise ValueError(f"{label} must have shape (3,), got {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{label} contains NaN or inf")
    return arr


@dataclass(frozen=True, slots=True)
class ReferenceState:
    """One reference body state at one epoch — metadata attached, never bare floats.

    Invariants enforced here (requirements 3, 6, 8):
    - ``frame`` is :attr:`ReferenceFrame.SSB_ICRS` (SSB-relative, J2000 axes):
      translation to any model origin happens ONLY in
      ``frames/transforms.py`` at the comparison boundary, never in this type.
    - ``time_scale`` is TDB (no conversions anywhere in the pipeline).
    - ``provenance`` is present and complete.
    """

    body: str
    naif_id: int
    epoch_jd: float  # TDB Julian date of this state
    frame: ReferenceFrame
    center: str
    time_scale: TimeScale
    position_m: NDArray[np.float64]  # (3,), m, SSB-relative
    velocity_ms: NDArray[np.float64]  # (3,), m/s, SSB-relative
    provenance: ReferenceMetadata

    def __post_init__(self) -> None:
        if not self.body:
            raise ValueError("body must be non-empty")
        if not np.isfinite(self.epoch_jd):
            raise ValueError(f"epoch_jd must be finite, got {self.epoch_jd!r}")
        if self.frame is not ReferenceFrame.SSB_ICRS:
            raise FrameUnsupportedError(
                f"ReferenceState.frame must be {ReferenceFrame.SSB_ICRS!r}, got "
                f"{self.frame!r}; re-centering belongs to frames/transforms.py"
            )
        if self.center != REFERENCE_CENTER_DESC:
            raise FrameUnsupportedError(
                f"ReferenceState.center must be {REFERENCE_CENTER_DESC!r} (kernel "
                f"native), got {self.center!r}; translate explicitly at the "
                "comparison boundary instead of redefining the reference origin"
            )
        if self.time_scale is not TimeScale.TDB:
            raise TimeScaleMismatchError(
                f"ReferenceState.time_scale must be TDB, got {self.time_scale!r}; "
                "time-scale conversion is deliberately unimplemented"
            )
        object.__setattr__(self, "position_m", _vec3(self.position_m, "position_m"))
        object.__setattr__(self, "velocity_ms", _vec3(self.velocity_ms, "velocity_ms"))
