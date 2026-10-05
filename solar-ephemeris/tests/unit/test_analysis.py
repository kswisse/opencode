"""Analysis-layer unit tests on SYNTHETIC trajectories.

No integration here: every signal is built by hand so the estimator's contract
(minima spacing vs winding, name-based lookup, bitwise grid requirement) is
checked against numbers known in closed form, independent of the engine.

Measured tolerances (2026-10-01):
  radial_period on cosine T=100, h=0.1   error < 1e-5 rel (assert 1e-3)
  angular_period on exact helix T=100    error < 1e-9 rel (assert 1e-6)
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.analysis import (
    angular_period,
    barycenter,
    distance_stats,
    radial_period,
    relative_energy_error,
    relative_state,
    total_energy,
    trajectory_difference,
)
from solar_ephemeris.analysis.orbit import DistanceStats
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.constants import G_SI
from solar_ephemeris.physics.state import StateMeta
from solar_ephemeris.simulation.engine import Trajectory, TrajectoryMeta


def make_traj(
    times,
    positions,
    velocities,
    body_names,
    gm,
    *,
    dt=1.0,
    sample_every=1,
    integrator="rk4",
    integrator_order=4,
):
    meta = TrajectoryMeta(
        state_meta=StateMeta(
            frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
            origin="barycenter(test)",
            epoch_jd=2451545.0,
            time_scale=TimeScale.TDB,
        ),
        integrator=integrator,
        integrator_order=integrator_order,
        dt=float(dt),
        sample_every=sample_every,
        n_steps=len(times) - 1,
        config_hash="0" * 64,
        software_version="test",
    )
    return Trajectory(
        times=np.asarray(times, dtype=np.float64),
        positions=np.asarray(positions, dtype=np.float64),
        velocities=np.asarray(velocities, dtype=np.float64),
        gm=np.asarray(gm, dtype=np.float64),
        body_names=tuple(body_names),
        meta=meta,
    )


def toy_traj(n_samples: int = 5) -> Trajectory:
    """3 named bodies, deterministic arbitrary values."""
    times = np.arange(n_samples, dtype=np.float64) * 2.0
    m = np.arange(n_samples, dtype=np.float64)[:, None, None]  # (M,1,1)
    pos = np.array(
        [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 5.0, 0.0]]
    ) + m  # (N,3) + (M,1,1) -> (M,N,3)
    vel = pos / 7.0 + 1.0
    return make_traj(
        times, pos, vel, ("Sun", "Earth", "Moon"), (3.0, 2.0, 1.0), dt=2.0
    )


# --- relative_state ---------------------------------------------------------


def test_relative_state_matches_manual_subtraction():
    traj = toy_traj()
    rel = relative_state(traj, "Earth", "Moon")
    np.testing.assert_array_equal(
        rel.r, traj.positions[:, 2, :] - traj.positions[:, 1, :]
    )
    np.testing.assert_array_equal(
        rel.v, traj.velocities[:, 2, :] - traj.velocities[:, 1, :]
    )
    np.testing.assert_array_equal(rel.times, traj.times)
    assert rel.primary == "Earth" and rel.secondary == "Moon"
    np.testing.assert_array_equal(rel.distance, np.linalg.norm(rel.r, axis=1))
    np.testing.assert_array_equal(rel.speed, np.linalg.norm(rel.v, axis=1))


def test_relative_state_rejects_bad_names():
    traj = toy_traj()
    with pytest.raises(ValueError, match="same body"):
        relative_state(traj, "Moon", "Moon")
    with pytest.raises(ValueError, match="not in trajectory"):
        relative_state(traj, "Earth", "Phobos")


# --- barycenter -------------------------------------------------------------


def test_barycenter_hand_computed_weights():
    times = np.array([0.0, 1.0])
    pos = np.zeros((2, 2, 3))
    pos[:, 1, 0] = 4.0  # body2 at x=4, body1 at origin, both samples
    vel = np.zeros((2, 2, 3))
    vel[:, 1, 1] = 8.0
    traj = make_traj(times, pos, vel, ("a", "b"), (3.0, 1.0))
    r_cm, v_cm = barycenter(traj)
    # (3*0 + 1*4)/4 = 1 ; (3*0 + 1*8)/4 = 2
    np.testing.assert_allclose(r_cm, [[1.0, 0.0, 0.0]] * 2, rtol=0, atol=1e-15)
    np.testing.assert_allclose(v_cm, [[0.0, 2.0, 0.0]] * 2, rtol=0, atol=1e-15)


def test_barycenter_single_body_is_the_body_itself():
    traj = toy_traj()
    r_cm, v_cm = barycenter(traj, ["Moon"])
    np.testing.assert_array_equal(r_cm, traj.positions[:, 2, :])
    np.testing.assert_array_equal(v_cm, traj.velocities[:, 2, :])


def test_barycenter_errors():
    traj = toy_traj()
    with pytest.raises(ValueError, match="non-empty"):
        barycenter(traj, [])
    with pytest.raises(ValueError, match="duplicate"):
        barycenter(traj, ["Moon", "Moon"])
    with pytest.raises(ValueError, match="not in trajectory"):
        barycenter(traj, ["Moon", "Phobos"])


# --- distance_stats ---------------------------------------------------------


def test_distance_stats_golden():
    stats = distance_stats(np.array([3.0, 1.0, 2.0]))
    assert stats.minimum == 1.0
    assert stats.maximum == 3.0
    assert stats.mean == 2.0
    assert stats.amplitude == 1.0  # (3-1)/2


def test_distance_stats_validation():
    with pytest.raises(ValueError, match="non-empty"):
        distance_stats(np.empty(0))
    with pytest.raises(ValueError, match="non-empty"):
        distance_stats(np.ones((2, 2)))
    with pytest.raises(ValueError, match="minimum must be > 0"):
        DistanceStats(minimum=0.0, maximum=1.0, mean=1.0, amplitude=1.0)
    with pytest.raises(ValueError, match="maximum < minimum"):
        DistanceStats(minimum=2.0, maximum=1.0, mean=1.5, amplitude=0.5)
    with pytest.raises(ValueError, match="must be finite"):
        DistanceStats(minimum=np.nan, maximum=1.0, mean=1.0, amplitude=1.0)


# --- radial_period ----------------------------------------------------------


def test_radial_period_on_clean_cosine():
    period = 100.0
    t = np.linspace(0.0, 300.0, 3001)  # h = 0.1, three minima at 50/150/250
    d = 10.0 + 2.0 * np.cos(2.0 * np.pi * t / period)
    assert radial_period(t, d) == pytest.approx(period, rel=1e-3)


def test_radial_period_errors():
    with pytest.raises(ValueError, match="matching"):
        radial_period(np.arange(10.0), np.arange(9.0))
    with pytest.raises(ValueError, match="at least 3 samples"):
        radial_period(np.array([0.0, 1.0]), np.array([1.0, 2.0]))
    t = np.linspace(0.0, 10.0, 100)  # strictly decreasing -> no local minimum
    with pytest.raises(ValueError, match=">= 2 distance minima"):
        radial_period(t, 5.0 - t)


# --- angular_period ---------------------------------------------------------


def test_angular_period_on_exact_helix():
    period = 100.0
    t = np.linspace(0.0, 500.0, 5001)  # exactly 5 turns
    theta = 2.0 * np.pi * t / period
    r = np.column_stack([np.cos(theta), np.sin(theta), np.zeros_like(t)])
    assert angular_period(t, r) == pytest.approx(period, rel=1e-6)


def test_angular_period_errors():
    period = 100.0
    t = np.linspace(0.0, 50.0, 101)  # half a turn
    theta = 2.0 * np.pi * t / period
    r = np.column_stack([np.cos(theta), np.sin(theta), np.zeros_like(t)])
    with pytest.raises(ValueError, match="revolutions"):
        angular_period(t, r)
    with pytest.raises(ValueError, match=r"\(M, 3\)"):
        angular_period(t, r[:, :2])
    with pytest.raises(ValueError, match="at least 3 samples"):
        angular_period(np.array([0.0, 1.0]), np.ones((2, 3)))


# --- trajectory_difference --------------------------------------------------


def test_trajectory_difference_golden():
    traj = toy_traj()
    shifted = make_traj(
        traj.times,
        traj.positions + 7.0,
        traj.velocities,
        ("Sun", "Earth", "Moon"),
        (3.0, 2.0, 1.0),
        dt=2.0,
    )
    times, delta = trajectory_difference(shifted, traj, "Earth")
    np.testing.assert_array_equal(times, traj.times)
    np.testing.assert_array_equal(delta, np.full((5, 3), 7.0))


def test_trajectory_difference_grid_and_name_guards():
    a = toy_traj(5)
    b = toy_traj(6)  # different times, same bodies
    with pytest.raises(ValueError, match="sample times differ"):
        trajectory_difference(a, b, "Earth")
    c = make_traj(
        a.times, a.positions[:, :2, :], a.velocities[:, :2, :], ("Sun", "Earth"),
        (3.0, 2.0), dt=2.0,
    )
    with pytest.raises(ValueError, match="not in trajectory"):
        trajectory_difference(a, c, "Moon")


# --- energy diagnostics -----------------------------------------------------


def test_total_energy_hand_computed():
    # two point masses at distance 4 m, speed 1 m/s each, gm = 2.0 each.
    # NB: r=2 + v=1 + GM=2 would be an exact circular orbit with E == 0,
    # which relative_energy_error deliberately rejects as undefined.
    times = np.array([0.0, 1.0])
    pos = np.zeros((2, 2, 3))
    pos[:, 0, 0] = -2.0
    pos[:, 1, 0] = 2.0
    vel = np.zeros((2, 2, 3))
    vel[:, 0, 1] = 1.0
    vel[:, 1, 1] = -1.0
    traj = make_traj(times, pos, vel, ("a", "b"), (2.0, 2.0))
    e = total_energy(traj)
    m = 2.0 / G_SI
    expected = 2 * (0.5 * m * 1.0**2) - (G_SI * m * m) / 4.0
    assert expected != 0.0
    np.testing.assert_allclose(e, [expected, expected], rtol=1e-15)
    np.testing.assert_allclose(relative_energy_error(traj), [0.0, 0.0], atol=1e-16)


def test_relative_energy_error_rejects_zero_energy():
    # exact circular orbit (v^2 = GM/r): E = 0 exactly -> undefined relative error
    times = np.array([0.0, 1.0])
    pos = np.zeros((2, 2, 3))
    pos[:, 0, 0] = -1.0
    pos[:, 1, 0] = 1.0
    vel = np.zeros((2, 2, 3))
    vel[:, 0, 1] = 1.0  # v=1, r=2, GM=2 => v^2 = GM/r
    vel[:, 1, 1] = -1.0
    traj = make_traj(times, pos, vel, ("a", "b"), (2.0, 2.0))
    assert total_energy(traj)[0] == 0.0
    with pytest.raises(ValueError, match="undefined"):
        relative_energy_error(traj)
