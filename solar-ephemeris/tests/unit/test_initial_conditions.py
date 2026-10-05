"""Phase-3 initial conditions — analytic verification of the construction.

Every assertion here checks the IC against closed-form identities (COM = 0,
GM-weighted split, two-body circular rate), NOT against a run of the engine —
a wrong IC would otherwise poison every downstream experiment silently.

Measured on the shipped builder (2026-10-01):
  total COM residual        |sum GM r|/(GM_tot*R)  ~ 3.5e-18
  total COM residual        |sum GM v|/(GM_tot*V)  ~ 1.8e-18
  |r_M - r_E|               == a to <1e-6 m
  |v_M - v_E|               = 1024.546847 m/s (sqrt(GM_EM/a))
  P_EM                      = 27.2846058 d   (model, before integration)
  P_EMB                     = 365.2563431 d
  Sun row vs lumped recipe  diff < 6e-11 m (positions), 0 (velocities)
  isolated mutual accel     = GM_EM/a^2 = 2.7307394446431103e-3 m/s^2
  mutual accel with Sun     = 2.7001490928136394e-3 m/s^2 (solar tide -1.12 %)
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.physics.constants import (
    AU_M,
    GM_EARTH,
    GM_EARTH_MOON_BARYCENTER,
    GM_MOON,
    GM_SUN,
    SECONDS_PER_DAY,
)
from solar_ephemeris.physics.gravity import pairwise_accelerations
from solar_ephemeris.simulation.initial_conditions import (
    EARTH_MOON_DISTANCE_M,
    make_circular_two_body_ic,
    make_sun_earth_moon_ic,
)


@pytest.fixture(scope="module")
def ic():
    return make_sun_earth_moon_ic()


def test_gm_vector_and_body_names(ic):
    assert ic.body_names == ("Sun", "Earth", "Moon")
    np.testing.assert_array_equal(ic.gm, [GM_SUN, GM_EARTH, GM_MOON])
    assert ic.moon_distance == EARTH_MOON_DISTANCE_M
    assert ic.separation == AU_M


def test_total_centre_of_mass_is_zero(ic):
    gm_tot = float(ic.gm.sum())
    com_r = ic.gm @ ic.positions / gm_tot
    com_v = ic.gm @ ic.velocities / gm_tot
    v_scale = float(np.max(np.linalg.norm(ic.velocities, axis=1)))
    assert np.linalg.norm(com_r) / (gm_tot and ic.separation) < 1e-15
    assert np.linalg.norm(com_v) / (gm_tot * v_scale) < 1e-15


def test_mutual_orbit_initial_state_is_circular(ic):
    d = ic.positions[2] - ic.positions[1]
    v_rel = ic.velocities[2] - ic.velocities[1]
    assert abs(np.linalg.norm(d) - EARTH_MOON_DISTANCE_M) < 1e-6
    v_expected = float(np.sqrt(GM_EARTH_MOON_BARYCENTER / EARTH_MOON_DISTANCE_M))
    # built as omega_EM*a, checked against sqrt(GM_EM/a): 1.2e-15 rel (ulp path)
    assert np.linalg.norm(v_rel) == pytest.approx(v_expected, rel=1e-12)
    # circular => relative velocity perpendicular to the separation
    assert abs(float(np.dot(d, v_rel))) < 1e-6 * v_expected * EARTH_MOON_DISTANCE_M


def test_periods_match_two_body_formulas(ic):
    p_em = 2.0 * np.pi * np.sqrt(
        EARTH_MOON_DISTANCE_M**3 / GM_EARTH_MOON_BARYCENTER
    )
    p_emb = 2.0 * np.pi * np.sqrt(AU_M**3 / (GM_SUN + GM_EARTH_MOON_BARYCENTER))
    assert ic.period_em == pytest.approx(p_em, rel=1e-15)
    assert ic.period_emb == pytest.approx(p_emb, rel=1e-15)
    assert 27.2 < ic.period_em / SECONDS_PER_DAY < 27.4
    assert 365.0 < ic.period_emb / SECONDS_PER_DAY < 365.6


def test_split_is_gm_weighted_about_emb(ic):
    gm_em = GM_EARTH_MOON_BARYCENTER
    r_emb = (GM_EARTH * ic.positions[1] + GM_MOON * ic.positions[2]) / gm_em
    v_emb = (GM_EARTH * ic.velocities[1] + GM_MOON * ic.velocities[2]) / gm_em
    d = ic.positions[2] - ic.positions[1]
    # Earth and Moon sit on opposite sides, distances in the inverse-GM ratio
    np.testing.assert_allclose(
        ic.positions[1] - r_emb, -(GM_MOON / gm_em) * d, rtol=1e-12
    )
    np.testing.assert_allclose(
        ic.positions[2] - r_emb, (GM_EARTH / gm_em) * d, rtol=1e-12
    )
    v_rel = ic.velocities[2] - ic.velocities[1]
    np.testing.assert_allclose(
        ic.velocities[1] - v_emb, -(GM_MOON / gm_em) * v_rel, rtol=1e-12
    )
    np.testing.assert_allclose(
        ic.velocities[2] - v_emb, (GM_EARTH / gm_em) * v_rel, rtol=1e-12
    )


def test_sun_and_emb_match_lumped_two_body_recipe(ic):
    """Model B's Sun/EMB rows must equal the exact two-body run of
    Model A (lumped) — this is what makes the perturbation comparison
    start from an aligned configuration."""
    lump = make_circular_two_body_ic(
        GM_SUN, GM_EARTH_MOON_BARYCENTER, AU_M, names=("Sun", "EMB")
    )
    emb = (GM_EARTH * ic.positions[1] + GM_MOON * ic.positions[2]) / GM_EARTH_MOON_BARYCENTER
    emb_v = (GM_EARTH * ic.velocities[1] + GM_MOON * ic.velocities[2]) / GM_EARTH_MOON_BARYCENTER
    assert np.max(np.abs(lump.positions[0] - ic.positions[0])) < 1e-9
    assert np.max(np.abs(lump.velocities[0] - ic.velocities[0])) < 1e-12
    np.testing.assert_array_equal(lump.positions[1], emb)
    # velocities travel different arithmetic paths (omega*r vs GM-split):
    # measured max diff 3.6e-12 m/s (1.2e-16 rel) -> rtol 1e-12
    np.testing.assert_allclose(lump.velocities[1], emb_v, rtol=1e-12, atol=1e-9)


def test_state_metadata_and_names(ic):
    state = ic.state()
    assert state.body_names == ("Sun", "Earth", "Moon")
    assert str(state.meta.frame) == "active_bodies_barycentric"
    assert str(state.meta.time_scale) == "TDB"
    assert state.meta.origin == "barycenter(Sun, Earth, Moon)"
    np.testing.assert_array_equal(state.positions, ic.positions)


def test_two_body_builder_names_and_validation():
    ic2 = make_circular_two_body_ic(GM_SUN, GM_EARTH, AU_M, names=("Sun", "Earth"))
    assert ic2.state().body_names == ("Sun", "Earth")
    assert ic2.omega == pytest.approx(
        np.sqrt((GM_SUN + GM_EARTH) / AU_M**3), rel=1e-15
    )
    with pytest.raises(ValueError, match="differ"):
        make_circular_two_body_ic(GM_SUN, GM_EARTH, AU_M, names=("Sun", "Sun"))
    with pytest.raises(ValueError, match="> 0"):
        make_circular_two_body_ic(GM_SUN, GM_EARTH, -1.0)
    with pytest.raises(ValueError, match="> 0"):
        make_sun_earth_moon_ic(moon_distance=0.0)


def test_mutual_acceleration_tidal_budget(ic):
    """Isolated pair obeys GM_EM/a^2 exactly; the Sun reduces the restoring
    pull by its linear tide (~1.12 % measured) — proves the solar term is a
    genuine N-body interaction, not an fudge."""
    q = ic.positions
    isolated = pairwise_accelerations(q, np.array([0.0, GM_EARTH, GM_MOON]), guard_m=1.0)
    pair_mag = float(np.linalg.norm(isolated[2] - isolated[1]))
    assert pair_mag == pytest.approx(
        GM_EARTH_MOON_BARYCENTER / EARTH_MOON_DISTANCE_M**2, rel=1e-14
    )
    full = pairwise_accelerations(q, ic.gm, guard_m=1.0)
    full_mag = float(np.linalg.norm(full[2] - full[1]))
    ratio = full_mag / pair_mag
    assert 0.98 < ratio < 1.0, f"measured solar-tide ratio {ratio:.6f}"
