"""Interpolation matrix (requirement 11): exactness, rejections, determinism.

Interior accuracy uses sample grids drawn from exact cubic polynomials —
cubic Hermite reproduces cubics identically in exact arithmetic, so the only
residual is float round-off (asserted at rtol=1e-10, measured ~1e-13).
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.ephemeris.interpolation import CubicHermiteInterpolator
from solar_ephemeris.ephemeris.types import InterpolationError

# Analytic cubic: p(t) = c0 + c1 t + c2 t^2 + c3 t^3 (per component), v = dp/dt.
C0 = np.array([1.0, -2.0, 3.0])
C1 = np.array([0.5, 4.0, -1.5])
C2 = np.array([-0.01, 0.02, 0.005])
C3 = np.array([1e-4, -2e-4, 3e-5])
GRID = np.array([0.0, 10.0, 20.0, 30.0])


def analytic_p(t: float) -> np.ndarray:
    return C0 + C1 * t + C2 * t**2 + C3 * t**3


def analytic_v(t: float) -> np.ndarray:
    return C1 + 2.0 * C2 * t + 3.0 * C3 * t**2


def make_poly_grid() -> CubicHermiteInterpolator:
    pos = np.array([analytic_p(t) for t in GRID])
    vel = np.array([analytic_v(t) for t in GRID])
    return CubicHermiteInterpolator(GRID, pos, vel)


def test_exact_epoch_is_bit_equal() -> None:
    interp = make_poly_grid()
    for i, t in enumerate(GRID):
        p, v = interp.evaluate(float(t))
        assert np.array_equal(p, analytic_p(t))  # stored sample, passthrough
        assert np.array_equal(v, analytic_v(t))


def test_interior_points_match_analytic_cubic() -> None:
    interp = make_poly_grid()
    for t in (5.0, 15.0, 25.0, 0.1, 29.999):
        p, v = interp.evaluate(t)
        # Hermite is exact for cubics; residual is float round-off only.
        assert np.allclose(p, analytic_p(t), rtol=1e-10, atol=1e-10), t
        assert np.allclose(v, analytic_v(t), rtol=1e-10, atol=1e-10), t


def test_vector_query_matches_scalar_queries() -> None:
    interp = make_poly_grid()
    ts = np.array([1.25, 7.5, 12.0, 29.0])
    p_vec, v_vec = interp.evaluate(ts)
    assert p_vec.shape == (4, 3) and v_vec.shape == (4, 3)
    for k, t in enumerate(ts):
        p_s, v_s = interp.evaluate(float(t))
        assert np.array_equal(p_vec[k], p_s)
        assert np.array_equal(v_vec[k], v_s)


def test_endpoints_are_exact_samples() -> None:
    interp = make_poly_grid()
    p_lo, _ = interp.evaluate(GRID[0])
    p_hi, _ = interp.evaluate(GRID[-1])
    assert np.array_equal(p_lo, analytic_p(GRID[0]))
    assert np.array_equal(p_hi, analytic_p(GRID[-1]))
    assert interp.domain == (0.0, 30.0)


@pytest.mark.parametrize("t", [-0.001, 30.001])
def test_outside_domain_forbidden(t: float) -> None:
    interp = make_poly_grid()
    with pytest.raises(InterpolationError, match="extrapolation is forbidden"):
        interp.evaluate(t)


def test_duplicate_epochs_rejected() -> None:
    with pytest.raises(InterpolationError, match="duplicate"):
        CubicHermiteInterpolator(
            np.array([0.0, 10.0, 10.0]),
            np.zeros((3, 3)),
            np.zeros((3, 3)),
        )


def test_non_monotonic_grid_rejected() -> None:
    with pytest.raises(InterpolationError, match="strictly increasing"):
        CubicHermiteInterpolator(
            np.array([0.0, 10.0, 5.0]),
            np.zeros((3, 3)),
            np.zeros((3, 3)),
        )


def test_single_sample_grid_rejected() -> None:
    with pytest.raises(InterpolationError, match="n >= 2"):
        CubicHermiteInterpolator(np.array([0.0]), np.zeros((1, 3)), np.zeros((1, 3)))


def test_shape_and_finiteness_validation() -> None:
    with pytest.raises(InterpolationError, match="shape"):
        CubicHermiteInterpolator(GRID, np.zeros((4, 2)), np.zeros((4, 3)))
    bad = GRID.copy()
    bad[2] = np.nan
    with pytest.raises(InterpolationError, match="NaN"):
        CubicHermiteInterpolator(bad, np.zeros((4, 3)), np.zeros((4, 3)))


def test_repeatability_is_bit_identical() -> None:
    interp = make_poly_grid()
    p1, v1 = interp.evaluate(7.31)
    p2, v2 = interp.evaluate(7.31)
    assert np.array_equal(p1, p2) and np.array_equal(v1, v2)


def test_query_epochs_must_be_finite() -> None:
    interp = make_poly_grid()
    with pytest.raises(InterpolationError, match="NaN"):
        interp.evaluate(np.array([1.0, np.nan]))
