import math

from solar_ephemeris.physics import constants as C


def test_fundamental_constant_literals():
    assert C.G_SI == 6.67430e-11
    assert C.AU_M == 149597870700.0
    assert C.C_SI == 299792458.0
    assert C.SECONDS_PER_DAY == 86400.0
    assert C.JD_J2000 == 2451545.0


def test_every_gm_has_nonempty_source():
    for name, gm in C.GM_BY_BODY.items():
        source = C.GM_SOURCES.get(name)
        assert source, f"GM for {name!r} has no provenance entry"
        assert len(source) > 10, f"provenance for {name!r} too short: {source!r}"


def test_every_gm_source_has_a_gm():
    for name in C.GM_SOURCES:
        assert name in C.GM_BY_BODY, f"orphan source entry: {name!r}"


def test_all_gm_positive_and_finite():
    for name, gm in C.GM_BY_BODY.items():
        assert math.isfinite(gm), name
        assert gm > 0.0, name


def test_sun_acceleration_dimensional_golden():
    # GM_SUN / AU_M^2 has units m^3/s^2 / m^2 = m/s^2.
    value = C.GM_SUN / C.AU_M**2
    assert math.isclose(value, 5.930083519997317e-3, rel_tol=1e-12)


def test_emb_is_earth_plus_moon():
    assert C.GM_EARTH_MOON_BARYCENTER == C.GM_EARTH + C.GM_MOON


def test_gm_earth_is_not_emb():
    # Guard against the classic DE440 mis-transcription: 403503.235625 km^3/s^2
    # is the Earth-Moon barycenter GM, not GM_Earth.
    assert not math.isclose(C.GM_EARTH, 4.03503235625e14, rel_tol=1e-9)


def test_unit_helpers():
    assert C.days_to_s(1.0) == 86400.0
    assert C.s_to_days(86400.0) == 1.0
    assert math.isclose(C.mass_from_gm(C.GM_EARTH) / 5.972e24, 1.0, rel_tol=1e-2)
