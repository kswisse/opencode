import numpy as np
import pytest

from solar_ephemeris.physics.constants import AU_M, GM_EARTH, GM_MOON, GM_SUN
from solar_ephemeris.physics.gravity import (
    CloseEncounterError,
    newtonian_acceleration,
    pairwise_accelerations,
)


def test_inverse_square_law():
    gm = np.array([GM_SUN, GM_EARTH])
    d = 1.5 * AU_M
    a_near = pairwise_accelerations(np.array([[0.0, 0, 0], [d, 0, 0]]), gm)
    a_far = pairwise_accelerations(np.array([[0.0, 0, 0], [2 * d, 0, 0]]), gm)
    ratio = np.linalg.norm(a_far[0]) / np.linalg.norm(a_near[0])
    assert ratio == pytest.approx(0.25, rel=1e-12)


def test_acceleration_direction():
    gm = np.array([GM_SUN, GM_EARTH])
    d = 3.0 * AU_M
    a = pairwise_accelerations(np.array([[0.0, 0, 0], [d, 0, 0]]), gm)
    # Body 0 is pulled toward body 1 (+x) with magnitude GM_2/d^2
    np.testing.assert_allclose(a[0], [GM_EARTH / d**2, 0.0, 0.0], rtol=1e-15)


def test_newtons_third_law_symmetry():
    gm = np.array([GM_SUN, GM_EARTH])
    d = 1.5 * AU_M
    a = pairwise_accelerations(np.array([[0.0, 0, 0], [d, 0, 0]]), gm)
    residual = np.linalg.norm(gm[0] * a[0] + gm[1] * a[1])
    scale = gm[0] * np.linalg.norm(a[0])
    assert residual / scale < 1e-13


def test_superposition_linearity():
    gm = np.array([GM_SUN, GM_EARTH, GM_MOON])
    pos = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0 * AU_M, 0.0, 0.0],
            [1.3 * AU_M, 0.4 * AU_M, 0.1 * AU_M],
        ]
    )
    a_all = pairwise_accelerations(pos, gm)
    # Acceleration of body 2 from bodies 0 and 1 computed separately
    a_from_0 = pairwise_accelerations(
        np.array([pos[2], pos[0]]), np.array([gm[2], gm[0]])
    )[0]
    a_from_1 = pairwise_accelerations(
        np.array([pos[2], pos[1]]), np.array([gm[2], gm[1]])
    )[0]
    np.testing.assert_allclose(a_all[2], a_from_0 + a_from_1, rtol=1e-14)


def test_dimensional_golden_sun_acceleration_at_1au():
    # GM_SUN / AU^2 in m/s^2 — locks both GM_SUN and AU_M
    value = GM_SUN / AU_M**2
    assert value == pytest.approx(5.930083519997317e-3, rel=1e-10)


def test_golden_matrix_three_bodies():
    """Independent fixed-value check (computed with a plain triple loop):
    catches index/transpose/sign errors that formula-level tests can miss."""
    gm = np.array([1.0e17, 2.0e16, 3.0e15])
    pos = np.array(
        [
            [1.0e11, 0.0, 0.0],
            [0.0, 2.0e11, 0.0],
            [0.0, 0.0, 3.0e11],
        ]
    )
    expected = np.array(
        [
            [-1.883722711805e-07, 3.577708764000e-07, 2.846049894152e-08],
            [8.944271909999e-07, -1.801655155759e-06, 1.920116063857e-08],
            [3.162277660168e-07, 8.533849172696e-08, -1.076691035641e-06],
        ]
    )
    got = pairwise_accelerations(pos, gm)
    np.testing.assert_allclose(got, expected, rtol=1e-12)


def test_coincident_bodies_raise():
    gm = np.array([GM_SUN, GM_EARTH])
    with pytest.raises(CloseEncounterError):
        pairwise_accelerations(np.array([[0.0, 0, 0], [0.0, 0, 0]]), gm)


def test_close_encounter_below_guard_raises():
    gm = np.array([GM_SUN, GM_EARTH])
    with pytest.raises(CloseEncounterError):
        pairwise_accelerations(
            np.array([[0.0, 0, 0], [0.5, 0, 0]]), gm, guard_m=1.0
        )


def test_output_dtype_shape_and_finiteness():
    gm = np.array([GM_SUN, GM_EARTH, GM_MOON])
    pos = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0 * AU_M, 0.0, 0.0],
            [0.0, 1.5 * AU_M, 0.0],
        ]
    )
    a = pairwise_accelerations(pos, gm)
    assert a.dtype == np.float64
    assert a.shape == (3, 3)
    assert np.all(np.isfinite(a))


def test_single_body_returns_zero_acceleration():
    a = pairwise_accelerations(np.array([[0.0, 0, 0]]), np.array([GM_SUN]))
    np.testing.assert_array_equal(a, np.zeros((1, 3)))


def test_shape_validation():
    gm = np.array([GM_SUN, GM_EARTH])
    with pytest.raises(ValueError):
        pairwise_accelerations(np.zeros(3), gm)
    with pytest.raises(ValueError):
        pairwise_accelerations(np.zeros((2, 3)), np.zeros(3))


def test_newtonian_acceleration_factory_ignores_velocity_and_time():
    gm = np.array([GM_SUN, GM_EARTH])
    accel = newtonian_acceleration(gm)
    q = np.array([[0.0, 0, 0], [1.5 * AU_M, 0, 0]])
    a1 = accel(q, None, 0.0)
    a2 = accel(q, np.full((2, 3), 999.0), 12345.0)
    np.testing.assert_array_equal(a1, a2)
    assert a1.shape == (2, 3)
