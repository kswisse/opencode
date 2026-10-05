"""Coverage boundaries and provenance/state construction contracts.

Coverage semantics are the anti-extrapolation guard (requirement 10):
closed intervals, endpoints allowed, outside raises — the same 5-point matrix
that later gates the real kernel (inside / exact-lower / exact-upper /
outside-lower / outside-upper).
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST
from solar_ephemeris.ephemeris.types import (
    Coverage,
    CoverageError,
    FrameUnsupportedError,
    ReferenceMetadata,
    ReferenceState,
    TimeScaleMismatchError,
)
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

LO, HI = -4_734_072_000.0, 4_735_368_000.0


def make_metadata(**over) -> ReferenceMetadata:
    base = dict(
        reference_name="JPL DE440",
        reference_version="DE440, integrated 2020-06-25",
        source="NAIF de440s.bsp; Park et al. (2021)",
        kernel_filename=DE440S_MANIFEST.filename,
        kernel_md5=DE440S_MANIFEST.md5,
        kernel_sha256=DE440S_MANIFEST.sha256,
        size_bytes=DE440S_MANIFEST.size_bytes,
        retrieval_date="2026-10-03",
        kernel_coverage=Coverage(intervals=((LO, HI),)),
        body_ids=DE440S_MANIFEST.body_ids,
        reference_frame="J2000",
        reference_center=0,
        time_standard="TDB — SPICE ephemeris time, s past J2000 TDB",
        native_position_unit="km",
        native_velocity_unit="km/s",
        spice_version="8.2.0",
    )
    base.update(over)
    return ReferenceMetadata(**base)


def make_state(**over) -> ReferenceState:
    base = dict(
        body="Earth",
        naif_id=399,
        epoch_jd=2451545.0,
        frame=ReferenceFrame.SSB_ICRS,
        center="ssb(0)",
        time_scale=TimeScale.TDB,
        position_m=np.array([-2.6e10, 1.3e11, 5.6e10]),
        velocity_ms=np.array([-29.7e3, -4.5e3, 0.1]),
        provenance=make_metadata(),
    )
    base.update(over)
    return ReferenceState(**base)


# --- Coverage: the 5-point boundary matrix (requirement 10) ---------------


def test_coverage_inside() -> None:
    cov = Coverage(intervals=((LO, HI),))
    assert cov.contains(0.0) is True


def test_coverage_exact_lower_boundary() -> None:
    cov = Coverage(intervals=((LO, HI),))
    assert cov.contains(LO) is True
    cov.require_contains(LO)  # must not raise


def test_coverage_exact_upper_boundary() -> None:
    cov = Coverage(intervals=((LO, HI),))
    assert cov.contains(HI) is True
    cov.require_contains(HI)  # must not raise


def test_coverage_outside_lower_raises() -> None:
    cov = Coverage(intervals=((LO, HI),))
    assert cov.contains(LO - 1.0) is False
    with pytest.raises(CoverageError, match="outside kernel coverage"):
        cov.require_contains(LO - 1.0)


def test_coverage_outside_upper_raises() -> None:
    cov = Coverage(intervals=((LO, HI),))
    assert cov.contains(HI + 1.0) is False
    with pytest.raises(CoverageError, match="outside kernel coverage"):
        cov.require_contains(HI + 1.0)


def test_coverage_multi_interval() -> None:
    cov = Coverage(intervals=((0.0, 10.0), (20.0, 30.0)))
    assert cov.contains(5.0) and cov.contains(25.0)
    assert not cov.contains(15.0)
    with pytest.raises(CoverageError):
        cov.require_contains(15.0)
    assert cov.start == 0.0 and cov.end == 30.0


@pytest.mark.parametrize(
    "intervals",
    [
        (),  # empty
        ((10.0, 0.0),),  # lo > hi
        ((0.0, 1.0), (0.5, 2.0)),  # overlapping
        ((10.0, 20.0), (0.0, 5.0)),  # unsorted
        ((0.0, float("nan")),),  # non-finite
    ],
)
def test_coverage_validation_rejects(intervals) -> None:
    with pytest.raises(ValueError):
        Coverage(intervals=intervals)


def test_coverage_dict_round_trip() -> None:
    cov = Coverage(intervals=((LO, HI), (HI, HI)))
    assert Coverage.from_dict(cov.to_dict()) == cov


# --- ReferenceMetadata: provenance pins (requirements 1, 2) ---------------


def test_metadata_round_trip_preserves_all_fields() -> None:
    meta = make_metadata()
    restored = ReferenceMetadata.from_dict(meta.to_dict())
    assert restored == meta
    assert set(meta.to_dict()) >= {
        "reference_name",
        "kernel_sha256",
        "kernel_coverage",
        "retrieval_date",
        "reference_frame",
        "reference_center",
        "time_standard",
        "native_position_unit",
        "native_velocity_unit",
        "spice_version",
        "software_version",
        "body_ids",
    }


def test_metadata_rejects_reference_substitution() -> None:
    with pytest.raises(ValueError, match="substitution forbidden"):
        make_metadata(reference_name="JPL DE441")


def test_metadata_rejects_non_ssb_center() -> None:
    with pytest.raises(ValueError, match="reference_center"):
        make_metadata(reference_center=1)


def test_metadata_rejects_non_km_native_units() -> None:
    with pytest.raises(ValueError, match="native_position_unit"):
        make_metadata(native_position_unit="m")
    with pytest.raises(ValueError, match="native_velocity_unit"):
        make_metadata(native_velocity_unit="m/s")


def test_metadata_rejects_malformed_sha256() -> None:
    with pytest.raises(ValueError, match="kernel_sha256"):
        make_metadata(kernel_sha256="abc")


# --- ReferenceState: frame/center/time pins (requirements 3, 6, 8) -------


def test_state_requires_ssb_icrs_frame() -> None:
    with pytest.raises(FrameUnsupportedError):
        make_state(frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC)


def test_state_requires_ssb_center() -> None:
    with pytest.raises(FrameUnsupportedError, match="ssb"):
        make_state(center="barycenter(Sun, Earth)")


def test_state_rejects_non_tdb_time_scale() -> None:
    with pytest.raises(TimeScaleMismatchError):
        make_state(time_scale=TimeScale.SI)


def test_state_rejects_bad_shapes_and_nan() -> None:
    with pytest.raises(ValueError, match="shape"):
        make_state(position_m=np.zeros(2))
    with pytest.raises(ValueError, match="NaN"):
        make_state(velocity_ms=np.array([0.0, np.nan, 0.0]))


def test_state_copies_arrays() -> None:
    pos = np.array([1.0, 2.0, 3.0])
    vel = np.array([4.0, 5.0, 6.0])
    state = make_state(position_m=pos, velocity_ms=vel)
    pos[0] = -1.0
    vel[0] = -1.0
    assert state.position_m[0] == 1.0
    assert state.velocity_ms[0] == 4.0


def test_state_carries_provenance() -> None:
    state = make_state()
    assert state.provenance.reference_name == "JPL DE440"
    assert state.provenance.kernel_sha256 == DE440S_MANIFEST.sha256
