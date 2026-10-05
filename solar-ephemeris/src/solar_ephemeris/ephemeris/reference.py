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

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

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

if TYPE_CHECKING:  # annotation only; comparison imports this module at runtime
    from solar_ephemeris.physics.state import StateMeta


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


def lookup_reference_series(
    provider: ReferenceProvider,
    *,
    body: str,
    epochs_jd: Sequence[float],
    model_meta: StateMeta | None = None,
    transform: str | None = None,
) -> list[ReferenceState]:
    """Read-only chain of reference states at already-recorded epochs (KTD2).

    The additive neighbour of ``compare_trajectory``: the same gate ORDER —
    NAIF mapping first, then :func:`get_state`'s metadata gate per epoch
    (frame → center → TDB → mapping → coverage → honesty audit) — and, when
    the caller passes ``model_meta`` together with ``transform``, the same
    ``assert_compatible`` gate on the first state that ``compare_trajectory``
    runs before it subtracts anything. Nothing is subtracted here, nothing is
    written, and ``ComparisonResult`` (the committed record schema) is
    untouched.

    Any exception propagates before a chain can be returned — a refused
    lookup yields no states at all, never a truncated prefix (KTD5).
    """
    naif_id(body)  # unmapped body raises even when epochs_jd is empty
    states = [
        get_state(provider, body=body, epoch_jd=epoch_jd)
        for epoch_jd in epochs_jd
    ]
    if model_meta is not None and states:
        # Local import: comparison.py imports this module for the protocol,
        # so assert_compatible cannot be a module-level import here.
        from solar_ephemeris.ephemeris.comparison import assert_compatible

        assert_compatible(model_meta, states[0], body=body, transform=transform)
    return states
