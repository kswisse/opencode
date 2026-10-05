import numpy as np

from solar_ephemeris.physics.constants import AU_M, GM_EARTH, GM_MOON, GM_SUN
from solar_ephemeris.physics.gravity import pairwise_accelerations
from solar_ephemeris.physics.state import State


def test_centripetal_identity(two_body_sun_earth):
    ic = two_body_sun_earth
    a = pairwise_accelerations(ic.positions0, ic.gm)
    r1 = np.linalg.norm(ic.positions0[0])  # distance from barycenter
    assert np.isclose(np.linalg.norm(a[0]), ic.omega**2 * r1, rtol=1e-12)


def test_initial_conditions_place_barycenter_at_origin(two_body_sun_earth):
    ic = two_body_sun_earth
    total_gm = ic.gm1 + ic.gm2
    r_cm = (ic.gm[:, None] * ic.positions0).sum(axis=0) / total_gm
    v_cm = (ic.gm[:, None] * ic.velocities0).sum(axis=0) / total_gm
    assert np.linalg.norm(r_cm) / ic.separation < 1e-15
    assert np.linalg.norm(v_cm) / (ic.omega * ic.separation) < 1e-15


def test_relative_acceleration_magnitude(two_body_sun_earth):
    ic = two_body_sun_earth
    a = pairwise_accelerations(ic.positions0, ic.gm)
    a_rel = a[1] - a[0]
    expected = (ic.gm1 + ic.gm2) / ic.separation**2
    # direction: body 1 (at -x) is pulled toward body 0 (+x)
    assert a_rel[0] > 0.0
    assert np.isclose(np.linalg.norm(a_rel), expected, rtol=1e-12)


def test_no_hardcoded_system_configuration():
    """The same code path serves any body list; a far-away third body must not
    change the two-body result at floating-point precision."""
    reg_r = np.array([1.0 * AU_M, 0.0, 0.0])
    # Two-body: Sun + Earth
    a2 = pairwise_accelerations(
        np.array([[0.0, 0, 0], reg_r]), np.array([GM_SUN, GM_EARTH])
    )
    # Three-body with the Moon parked 1e6 AU away along +x
    a3 = pairwise_accelerations(
        np.array([[0.0, 0, 0], reg_r, [1.0e6 * AU_M, 0.0, 0.0]]),
        np.array([GM_SUN, GM_EARTH, GM_MOON]),
    )
    # Moon perturbs Earth's acceleration by (GM_M/GM_S)*(AU/1e6 AU)^2 ~ 4e-18
    np.testing.assert_allclose(a2[1], a3[1], rtol=1e-15)
    # and never sorts/reorders: Earth is still row 1
    assert np.linalg.norm(a3[1]) > 0.0


def test_state_barycenter_consistent_with_ic(two_body_sun_earth):
    ic = two_body_sun_earth
    state = ic.state_at(0.0)
    assert isinstance(state, State)
    r_cm, v_cm = state.barycenter(ic.gm)
    assert np.linalg.norm(r_cm) / ic.separation < 1e-15
    assert np.linalg.norm(v_cm) / (ic.omega * ic.separation) < 1e-15
