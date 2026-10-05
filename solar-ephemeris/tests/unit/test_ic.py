"""IC builder (requirement 16): reference → model-frame State, kernel-free.

Assertions are on the contract the comparison layer depends on: COM=0 at the
model origin, explicit origin string, ICRF axis_note, TDB/epoch provenance,
and bit-exact agreement with the manual get_state+recenter path.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.ic import ICRF_AXIS_NOTE, reference_state_to_model_state
from solar_ephemeris.ephemeris.reference import get_state
from solar_ephemeris.ephemeris.types import (
    CoverageError,
    UnknownBodyMappingError,
)
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.frames.transforms import barycentre, recenter_ssb_to_model
from solar_ephemeris.physics.constants import GM_BY_BODY, GM_EARTH_MOON_BARYCENTER

JD_J2000 = 2451545.0


@pytest.fixture(scope="module")
def fixture() -> FixtureReference:
    return FixtureReference()


def test_state_contract(fixture: FixtureReference) -> None:
    state = reference_state_to_model_state(
        fixture, bodies=("Sun", "Earth"), epoch_jd=JD_J2000
    )
    assert state.meta.frame is ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC
    assert state.meta.origin == "barycenter(Sun, Earth)"
    assert state.meta.epoch_jd == JD_J2000
    assert state.meta.time_scale is TimeScale.TDB
    assert state.meta.length_unit == "m" and state.meta.velocity_unit == "m/s"
    assert state.body_names == ("Sun", "Earth")
    assert state.positions.shape == (2, 3) and state.velocities.shape == (2, 3)


def test_axis_note_is_the_icrf_claim(fixture: FixtureReference) -> None:
    state = reference_state_to_model_state(
        fixture, bodies=("Sun", "Earth"), epoch_jd=JD_J2000
    )
    # The orientation claim lives here, NOT in any rotation of the data (R8):
    # translation-only + recorded provenance is the whole orientation story.
    assert state.meta.axis_note == ICRF_AXIS_NOTE
    assert ICRF_AXIS_NOTE == "ICRF-aligned (derived from DE440 reference states)"


def test_body_order_preserved(fixture: FixtureReference) -> None:
    state = reference_state_to_model_state(
        fixture, bodies=("Earth", "Sun"), epoch_jd=JD_J2000
    )
    assert state.body_names == ("Earth", "Sun")
    assert state.meta.origin == "barycenter(Earth, Sun)"


def test_com_zero_at_model_origin(fixture: FixtureReference) -> None:
    state = reference_state_to_model_state(
        fixture, bodies=("Sun", "Earth"), epoch_jd=JD_J2000
    )
    gm = np.array([GM_BY_BODY["Sun"], GM_BY_BODY["Earth"]])
    r_cm, v_cm = barycentre(gm, state.positions, state.velocities)
    # Measured 2026-10-03 (transform layer): residual ~3e-8 m; bound carries
    # ~6 decades of float-round-off headroom.
    assert np.linalg.norm(r_cm) < 1e-2, np.linalg.norm(r_cm)
    assert np.linalg.norm(v_cm) < 1e-10


def test_matches_manual_get_state_recenter_path(fixture: FixtureReference) -> None:
    bodies = ("Sun", "Earth", "Moon")
    state = reference_state_to_model_state(fixture, bodies=bodies, epoch_jd=JD_J2000)
    pos = np.array(
        [get_state(fixture, body=b, epoch_jd=JD_J2000).position_m for b in bodies]
    )
    vel = np.array(
        [get_state(fixture, body=b, epoch_jd=JD_J2000).velocity_ms for b in bodies]
    )
    gm = np.array([GM_BY_BODY[b] for b in bodies])
    pos_rel, vel_rel, _, _ = recenter_ssb_to_model(pos, vel, gm, bodies)
    assert np.array_equal(state.positions, pos_rel)  # bit-exact, same path
    assert np.array_equal(state.velocities, vel_rel)


def test_emb_uses_derived_earth_moon_gm(fixture: FixtureReference) -> None:
    from solar_ephemeris.ephemeris.ic import _gm_for

    state = reference_state_to_model_state(
        fixture, bodies=("Sun", "EMB"), epoch_jd=JD_J2000
    )
    assert state.body_names == ("Sun", "EMB")
    # EMB is mapped (NAIF 3) but not a GM_BY_BODY key — the derived sum is
    # used instead; substituting GM_EARTH here would shift the model origin.
    gm = _gm_for(("Sun", "EMB"))
    assert gm[1] == GM_EARTH_MOON_BARYCENTER
    assert GM_EARTH_MOON_BARYCENTER == pytest.approx(
        GM_BY_BODY["Earth"] + GM_BY_BODY["Moon"]
    )


def test_duplicate_bodies_rejected(fixture: FixtureReference) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        reference_state_to_model_state(
            fixture, bodies=("Sun", "Sun"), epoch_jd=JD_J2000
        )


def test_empty_bodies_rejected(fixture: FixtureReference) -> None:
    with pytest.raises(ValueError, match="non-empty"):
        reference_state_to_model_state(fixture, bodies=(), epoch_jd=JD_J2000)


def test_unmapped_body_rejected_before_query(fixture: FixtureReference) -> None:
    with pytest.raises(UnknownBodyMappingError):
        reference_state_to_model_state(
            fixture, bodies=("Sun", "PlanetX"), epoch_jd=JD_J2000
        )


def test_epoch_outside_coverage_rejected(fixture: FixtureReference) -> None:
    # Fixture grid starts at JD 2451544.0 — an earlier epoch must FAIL,
    # never extrapolate (the exact failure mode interpolation could hide).
    with pytest.raises(CoverageError, match="outside kernel coverage"):
        reference_state_to_model_state(
            fixture, bodies=("Sun", "Earth"), epoch_jd=2451543.0
        )
