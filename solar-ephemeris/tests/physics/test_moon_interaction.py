"""Phase-3 physics tests: the Moon is a real gravitating body, not a label.

Golden accelerations below were produced by an INDEPENDENT plain-Python
double loop over the IC positions (no einsum, no project code) — if the
vectorised force path ever drifts, these numbers catch it.

Measured (2026-10-01, Sun-Earth-Moon IC at epoch):
  a_sun   = [-1.803002384633255e-08, 0, 0] m/s^2
  a_earth = [ 5.962893324048080e-03, 0, 0] m/s^2
  a_moon  = [ 3.262744231234440e-03, 0, 0] m/s^2
  Moon's pull on Earth = GM_M/a^2 = 3.317970...e-05 m/s^2
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.physics.constants import (
    GM_EARTH,
    GM_EARTH_MOON_BARYCENTER,
    GM_MOON,
    GM_SUN,
)
from solar_ephemeris.physics.gravity import newtonian_acceleration, pairwise_accelerations
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine
from solar_ephemeris.simulation.initial_conditions import EARTH_MOON_DISTANCE_M


@pytest.fixture(scope="module")
def ic(sun_earth_moon):
    return sun_earth_moon


def test_acceleration_golden_at_ic(ic):
    expected = np.array(
        [
            [-1.803002384633255e-08, 0.0, 0.0],
            [5.962893324048080e-03, 0.0, 0.0],
            [3.262744231234440e-03, 0.0, 0.0],
        ]
    )
    got = pairwise_accelerations(ic.positions, ic.gm)
    np.testing.assert_allclose(got, expected, rtol=1e-12)


def test_newtonian_wrapper_is_pairwise(ic):
    accel = newtonian_acceleration(ic.gm, guard_m=1.0)
    got = accel(ic.positions, None, 0.0)
    np.testing.assert_array_equal(got, pairwise_accelerations(ic.positions, ic.gm))


def test_moon_pull_on_earth_magnitude_and_direction(ic):
    """Isolating the Moon's term: |a_E(Moon)| == GM_M/a^2, along r_M-r_E."""
    full = pairwise_accelerations(ic.positions, ic.gm)
    no_moon = pairwise_accelerations(
        ic.positions, np.array([GM_SUN, GM_EARTH, GM_MOON]) * np.array([1.0, 1.0, 0.0])
    )
    d_moon = full[1] - no_moon[1]
    mag = float(np.linalg.norm(d_moon))
    assert mag == pytest.approx(GM_MOON / EARTH_MOON_DISTANCE_M**2, rel=1e-14)
    # direction: toward the Moon (positive projection on r_M - r_E)
    direction = ic.positions[2] - ic.positions[1]
    cos = float(np.dot(d_moon, direction) / (mag * np.linalg.norm(direction)))
    assert cos == pytest.approx(1.0, abs=1e-14)


def test_moon_restores_newton_third_law(ic):
    """Reaction pair = equal and opposite FORCES: GM_E*a_M(E) == -GM_M*a_E(M).
    (The accelerations themselves differ by the GM ratio ~81.3 — comparing
    them directly would be a physics error, caught here.)"""
    full = pairwise_accelerations(ic.positions, ic.gm)
    # remove Moon's gm to isolate its pull on Earth...
    no_moon = pairwise_accelerations(
        ic.positions, np.array([GM_SUN, GM_EARTH, 0.0])
    )
    # ...and Earth's gm to isolate its pull on the Moon
    no_earth = pairwise_accelerations(
        ic.positions, np.array([GM_SUN, 0.0, GM_MOON])
    )
    e_from_m = full[1] - no_moon[1]
    m_from_e = full[2] - no_earth[2]
    np.testing.assert_allclose(
        GM_MOON * m_from_e, -GM_EARTH * e_from_m, rtol=1e-12, atol=0.0
    )


def test_mutual_pull_is_exactly_pair_formula(ic):
    """Isolated Earth-Moon pair: relative acceleration == GM_EM/a^2 (the
    two-body reduction must hold to floating point, not approximately)."""
    isolated = pairwise_accelerations(ic.positions, np.array([0.0, GM_EARTH, GM_MOON]))
    rel = isolated[2] - isolated[1]
    assert float(np.linalg.norm(rel)) == pytest.approx(
        GM_EARTH_MOON_BARYCENTER / EARTH_MOON_DISTANCE_M**2, rel=1e-14
    )


@pytest.mark.parametrize(
    "bodies, expected_gm",
    [
        (("Sun", "Earth", "Moon"), (GM_SUN, GM_EARTH, GM_MOON)),
        (("Moon", "Sun", "Earth"), (GM_MOON, GM_SUN, GM_EARTH)),
        (("Earth", "Moon"), (GM_EARTH, GM_MOON)),
    ],
)
def test_engine_resolves_gm_in_config_order(bodies, expected_gm):
    cfg = SimulationConfig(
        bodies=bodies, integrator="rk4", dt=100.0, duration=100.0, epoch_jd=2451545.0
    )
    engine = SimulationEngine(cfg)
    assert engine.bodies == bodies
    np.testing.assert_array_equal(engine.gm, expected_gm)


def test_engine_rejects_unknown_body():
    cfg = SimulationConfig(
        bodies=("Sun", "Luna"), integrator="rk4", dt=100.0, duration=100.0,
        epoch_jd=2451545.0,
    )
    from solar_ephemeris.physics.bodies import UnknownBodyError

    with pytest.raises(UnknownBodyError):
        SimulationEngine(cfg)
