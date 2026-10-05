"""get_state façade: validation order, coverage gate, provider honesty.

The façade is the only public query entry (reference.py). Every rejection
class fires BEFORE a state is produced; the fixture backend is the concrete
provider here because the façade must be provable kernel-free.
"""

from __future__ import annotations

import pytest

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.reference import ReferenceProvider, get_state
from solar_ephemeris.ephemeris.types import (
    CoverageError,
    FrameUnsupportedError,
    TimeScaleMismatchError,
    UnknownBodyMappingError,
)
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

# Fixture sample domain: et ∈ [-86400, 864000] → JD 2451544.0 .. 2451555.0
JD_LOWER = 2451544.0
JD_UPPER = 2451555.0
JD_J2000 = 2451545.0


@pytest.fixture(scope="module")
def provider() -> FixtureReference:
    return FixtureReference()


def test_provider_satisfies_protocol(provider: FixtureReference) -> None:
    assert isinstance(provider, ReferenceProvider)
    assert provider.metadata.reference_name == "JPL DE440"


def test_get_state_returns_full_metadata(provider: FixtureReference) -> None:
    state = get_state(provider, body="Earth", epoch_jd=JD_J2000)
    assert state.body == "Earth"
    assert state.naif_id == 399
    assert state.epoch_jd == JD_J2000
    assert state.frame is ReferenceFrame.SSB_ICRS
    assert state.center == "ssb(0)"
    assert state.time_scale is TimeScale.TDB
    assert state.position_m.shape == (3,) and state.velocity_ms.shape == (3,)
    assert state.provenance.reference_name == "JPL DE440"
    assert state.provenance.kernel_sha256
    assert state.provenance.kernel_coverage is not None


def test_wrong_frame_rejected_first(provider: FixtureReference) -> None:
    with pytest.raises(FrameUnsupportedError, match="SSB_ICRS"):
        get_state(
            provider,
            body="Earth",
            epoch_jd=JD_J2000,
            frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        )


def test_wrong_center_rejected(provider: FixtureReference) -> None:
    with pytest.raises(FrameUnsupportedError, match="ssb"):
        get_state(
            provider, body="Earth", epoch_jd=JD_J2000, center="barycenter(Sun, Earth)"
        )


@pytest.mark.parametrize("scale", [TimeScale.UTC, TimeScale.TT, TimeScale.SI])
def test_non_tdb_refused_never_converted(provider: FixtureReference, scale) -> None:
    with pytest.raises(TimeScaleMismatchError, match="not TDB"):
        get_state(provider, body="Earth", epoch_jd=JD_J2000, time_scale=scale)


def test_time_check_precedes_body_check(provider: FixtureReference) -> None:
    # Order: frame → center → time_scale → body → coverage (requirement 6).
    with pytest.raises(TimeScaleMismatchError):
        get_state(
            provider, body="body1", epoch_jd=JD_J2000, time_scale=TimeScale.UTC
        )


def test_unknown_body_rejected(provider: FixtureReference) -> None:
    with pytest.raises(UnknownBodyMappingError):
        get_state(provider, body="body1", epoch_jd=JD_J2000)


def test_coverage_exact_boundaries_allowed(provider: FixtureReference) -> None:
    get_state(provider, body="Earth", epoch_jd=JD_LOWER)  # exact lower, no raise
    get_state(provider, body="Earth", epoch_jd=JD_UPPER)  # exact upper, no raise


@pytest.mark.parametrize("jd", [2451543.9, 2451555.1])
def test_coverage_outside_rejected(provider: FixtureReference, jd: float) -> None:
    with pytest.raises(CoverageError, match="outside kernel coverage"):
        get_state(provider, body="Earth", epoch_jd=jd)


def test_interior_epoch_interpolates_deterministically(provider: FixtureReference) -> None:
    jd = JD_J2000 + 0.5  # halfway between daily samples
    a = get_state(provider, body="Earth", epoch_jd=jd)
    b = get_state(provider, body="Earth", epoch_jd=jd)
    assert a.epoch_jd == jd
    assert (a.position_m == b.position_m).all() and (a.velocity_ms == b.velocity_ms).all()
    # Interpolated interior state differs from both neighbouring samples.
    s0 = get_state(provider, body="Earth", epoch_jd=JD_J2000)
    s1 = get_state(provider, body="Earth", epoch_jd=JD_J2000 + 1.0)
    assert not (a.position_m == s0.position_m).all()
    assert not (a.position_m == s1.position_m).all()
