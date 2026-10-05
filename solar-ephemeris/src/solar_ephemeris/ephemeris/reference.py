"""Provider protocol and the one public entry point for reference queries.

Every reference query — live kernel or recorded fixture — goes through
:func:`get_state`, which validates BEFORE anything is fetched (requirement 6
spirit: refuse incompatible metadata, never convert silently):

1. frame must be ``SSB_ICRS`` (the reference is SSB/J2000 by construction;
   translation to a model origin belongs to ``frames/transforms.py``),
2. center must be the kernel-native ``ssb(0)``,
3. time scale must be TDB (conversion deliberately unimplemented),
4. body must have an explicit NAIF mapping (never index-guessed),
5. epoch must be inside the provider's measured coverage (never extrapolate),

and the returned :class:`ReferenceState` is honesty-checked (body, NAIF ID,
epoch) before being handed to the caller. This module never imports SPICE.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from solar_ephemeris.ephemeris.mapping import naif_id
from solar_ephemeris.ephemeris.time import et_to_jd_tdb, jd_tdb_to_et, require_tdb
from solar_ephemeris.ephemeris.types import (
    REFERENCE_CENTER_DESC,
    Coverage,
    FrameUnsupportedError,
    ReferenceMetadata,
    ReferenceState,
)
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale


@runtime_checkable
class ReferenceProvider(Protocol):
    """Anything that can produce provenance-carrying reference states.

    Implementations: ``fixture_backend.FixtureReference`` (recorded JSON,
    kernel-free) and ``spice_backend.SpiceReference`` (live DE440 kernel).
    """

    @property
    def metadata(self) -> ReferenceMetadata:
        """Provenance of the underlying reference data."""
        ...

    @property
    def coverage(self) -> Coverage:
        """Measured coverage in SPICE ephemeris time (TDB s past J2000)."""
        ...

    def state_at(self, *, body: str, et: float) -> ReferenceState:
        """State at an exact, already-validated ephemeris time.

        Implementations return SSB_ICRS / TDB / ``ssb(0)`` states (enforced by
        the :class:`ReferenceState` constructor) and must re-check coverage.
        """
        ...


def get_state(
    provider: ReferenceProvider,
    *,
    body: str,
    epoch_jd: float,
    frame: ReferenceFrame = ReferenceFrame.SSB_ICRS,
    center: str = REFERENCE_CENTER_DESC,
    time_scale: TimeScale = TimeScale.TDB,
) -> ReferenceState:
    """Validated reference query: metadata gate first, then fetch, then audit.

    Raises :class:`~solar_ephemeris.ephemeris.types.FrameUnsupportedError`,
    :class:`~solar_ephemeris.ephemeris.types.TimeScaleMismatchError`,
    :class:`~solar_ephemeris.ephemeris.types.UnknownBodyMappingError`, and
    :class:`~solar_ephemeris.ephemeris.types.CoverageError` — in that order —
    before any state is produced.
    """
    if frame is not ReferenceFrame.SSB_ICRS:
        raise FrameUnsupportedError(
            f"reference states live in {ReferenceFrame.SSB_ICRS!r}, got {frame!r}; "
            "re-center/transform at the comparison boundary (frames/transforms.py), "
            "never by redefining the reference query"
        )
    if center != REFERENCE_CENTER_DESC:
        raise FrameUnsupportedError(
            f"reference center must be kernel-native {REFERENCE_CENTER_DESC!r}, "
            f"got {center!r}; translate explicitly at the comparison boundary"
        )
    require_tdb(time_scale, context="get_state")
    naif = naif_id(body)  # UnknownBodyMappingError if unmapped

    et = jd_tdb_to_et(epoch_jd)
    provider.coverage.require_contains(et)

    state = provider.state_at(body=body, et=et)

    # Honesty audit: the provider must return exactly what was asked for.
    if state.body != body or state.naif_id != naif:
        raise FrameUnsupportedError(
            f"provider returned body {state.body!r} (ID {state.naif_id}) for "
            f"requested {body!r} (ID {naif}) — provider/mapping disagreement"
        )
    if state.epoch_jd != et_to_jd_tdb(et):
        raise ValueError(
            f"provider returned epoch {state.epoch_jd!r}, expected "
            f"{et_to_jd_tdb(et)!r} for et={et!r}"
        )
    return state
