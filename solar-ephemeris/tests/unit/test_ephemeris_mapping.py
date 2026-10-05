"""NAIF body-ID mapping: exact table, explicit failures, wrong-ID canaries.

The table is asserted as an exact dict literal (requirement 5): a single
deliberate Earth→3 or Moon→301→399 swap must fail here before any distance
test could ever be run against wrong bodies.
"""

from __future__ import annotations

import pytest

from solar_ephemeris.ephemeris.mapping import (
    BODY_TO_NAIF,
    NAIF_TO_BODY,
    assert_registry_mappable,
    body_name,
    naif_id,
)
from solar_ephemeris.ephemeris.types import UnknownBodyMappingError
from solar_ephemeris.physics.constants import GM_BY_BODY

#: Exact expected table. Authority: NAIF req/naif_ids.html cross-checked
#: against aa_summaries.txt segment list of de440s.bsp (no 499/599/699/...).
EXPECTED_TABLE = {
    "Sun": 10,
    "Mercury": 199,
    "Venus": 299,
    "Earth": 399,
    "Moon": 301,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "EMB": 3,
}


def test_table_matches_naif_authority_exactly() -> None:
    assert BODY_TO_NAIF == EXPECTED_TABLE


def test_earth_is_solid_earth_not_emb() -> None:
    # Deliberate: project GM_Earth is solid-Earth+atmosphere. Mapping to 3
    # (EMB) would compare against the wrong mass centre (Phase-3 systematic).
    assert naif_id("Earth") == 399
    assert naif_id("Earth") != 3


def test_moon_maps_to_lunar_center() -> None:
    assert naif_id("Moon") == 301
    assert naif_id("Moon") != 399
    assert naif_id("Moon") != 3


def test_planets_map_to_system_barycenters() -> None:
    # Kernel has no 499/599/699/799/899/999 segments; project point masses
    # carry system GM, so IDs 4..9 are the correct targets.
    assert naif_id("Mars") == 4
    assert naif_id("Jupiter") == 5
    assert naif_id("Saturn") == 6
    assert naif_id("Uranus") == 7
    assert naif_id("Neptune") == 8
    assert naif_id("Pluto") == 9
    for absent in (499, 599, 699, 799, 899, 999):
        assert absent not in NAIF_TO_BODY


def test_every_physics_registry_body_is_mappable() -> None:
    assert set(GM_BY_BODY) <= set(BODY_TO_NAIF)
    assert_registry_mappable(tuple(GM_BY_BODY))


def test_naif_id_returns_builtin_int() -> None:
    value = naif_id("Sun")
    assert type(value) is int
    assert value == 10


@pytest.mark.parametrize("name", ["body1", "body2", "inline", "De440", "earth"])
def test_unknown_body_raises(name: str) -> None:
    with pytest.raises(UnknownBodyMappingError):
        naif_id(name)


def test_unknown_naif_id_raises() -> None:
    with pytest.raises(UnknownBodyMappingError):
        body_name(499)  # planet-center ID deliberately absent from the kernel


def test_inverse_round_trip() -> None:
    for name, naif in BODY_TO_NAIF.items():
        assert body_name(naif) == name
        assert naif_id(name) == naif
