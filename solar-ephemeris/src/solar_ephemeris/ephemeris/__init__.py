"""JPL DE440 reference pipeline (MASTERPLAN Phase 4).

Public, backend-agnostic API. **No spiceypy import happens at package import
time** — only ``ephemeris.spice_backend`` may touch SPICE (enforced by
``tests/unit/test_import_boundaries.py``); everything else works against the
``ReferenceProvider`` protocol, so the recorded-fixture backend and the live
kernel backend are interchangeable.

Module map (Phase 4 increments):
- ``types``           — provenance/state/coverage types + exceptions
- ``mapping``         — project name ↔ NAIF ID (explicit, never guessed)
- ``kernel_manifest`` — pinned kernel identity (sha256/md5/size/coverage)
- ``time`` / ``units`` — TDB representation change and km→m (visible ×1000)
- ``reference``       — provider protocol + ``get_state`` façade
- ``fixture_backend`` / ``spice_backend`` — recorded fixture / live SPICE
- ``interpolation``   — cubic Hermite on sampled reference points (no extrapolation)
- ``comparison``      — compatibility gate, metrics, ComparisonResult, record I/O
- ``ic``              — reference-derived initial conditions
"""

from __future__ import annotations

from solar_ephemeris.ephemeris.comparison import (
    ComparisonResult,
    ErrorStatistics,
    assert_compatible,
    compare_trajectory,
    error_statistics,
    relative_error,
    write_comparison_record,
)
from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.ic import ICRF_AXIS_NOTE, reference_state_to_model_state
from solar_ephemeris.ephemeris.interpolation import CubicHermiteInterpolator
from solar_ephemeris.ephemeris.kernel_manifest import (
    DE440S_MANIFEST,
    KernelManifest,
    default_kernel_path,
    verify_kernel,
)
from solar_ephemeris.ephemeris.mapping import (
    BODY_TO_NAIF,
    NAIF_TO_BODY,
    body_name,
    naif_id,
)
from solar_ephemeris.ephemeris.reference import ReferenceProvider, get_state
from solar_ephemeris.ephemeris.time import (
    JD_J2000_TDB,
    et_to_jd_tdb,
    jd_tdb_to_et,
    require_tdb,
    sample_epochs_et,
)
from solar_ephemeris.ephemeris.types import (
    NATIVE_POSITION_UNIT,
    NATIVE_VELOCITY_UNIT,
    REFERENCE_CENTER,
    REFERENCE_FRAME,
    REFERENCE_NAME,
    Coverage,
    CoverageError,
    EphemerisError,
    FrameUnsupportedError,
    InterpolationError,
    KernelIntegrityError,
    MetadataMismatchError,
    ReferenceMetadata,
    ReferenceState,
    TimeScaleMismatchError,
    UnitError,
    UnknownBodyMappingError,
)
from solar_ephemeris.ephemeris.units import KM_TO_M, from_native

__all__ = [
    "BODY_TO_NAIF",
    "DE440S_MANIFEST",
    "JD_J2000_TDB",
    "KM_TO_M",
    "NAIF_TO_BODY",
    "NATIVE_POSITION_UNIT",
    "NATIVE_VELOCITY_UNIT",
    "REFERENCE_CENTER",
    "REFERENCE_FRAME",
    "REFERENCE_NAME",
    "ComparisonResult",
    "Coverage",
    "CoverageError",
    "CubicHermiteInterpolator",
    "ErrorStatistics",
    "EphemerisError",
    "FixtureReference",
    "FrameUnsupportedError",
    "ICRF_AXIS_NOTE",
    "InterpolationError",
    "KernelIntegrityError",
    "KernelManifest",
    "MetadataMismatchError",
    "ReferenceMetadata",
    "ReferenceProvider",
    "ReferenceState",
    "TimeScaleMismatchError",
    "UnitError",
    "UnknownBodyMappingError",
    "assert_compatible",
    "body_name",
    "compare_trajectory",
    "default_kernel_path",
    "error_statistics",
    "et_to_jd_tdb",
    "from_native",
    "get_state",
    "jd_tdb_to_et",
    "naif_id",
    "reference_state_to_model_state",
    "relative_error",
    "require_tdb",
    "sample_epochs_et",
    "verify_kernel",
    "write_comparison_record",
]
