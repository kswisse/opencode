import numpy as np
import pytest

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.constants import GM_EARTH, GM_SUN
from solar_ephemeris.physics.state import State, StateMeta
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine, Trajectory

EPOCH = 2451545.0


def meta(**over) -> StateMeta:
    base = dict(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin="barycenter(Sun, Earth)",
        epoch_jd=EPOCH,
        time_scale=TimeScale.TDB,
    )
    base.update(over)
    return StateMeta(**base)


def config(**over) -> SimulationConfig:
    base = dict(
        bodies=("Sun", "Earth"),
        integrator="verlet",
        dt=60.0,
        duration=86400.0,  # 1440 steps
        epoch_jd=EPOCH,
    )
    base.update(over)
    return SimulationConfig(**base)


def sun_earth_state(ic) -> State:
    """IC from the circular-orbit fixture, labelled with real body names."""
    return State(
        positions=ic.positions0.copy(),
        velocities=ic.velocities0.copy(),
        body_names=("Sun", "Earth"),
        meta=meta(),
    )


def test_time_grid_is_multiplication_not_accumulation(two_body_sun_earth):
    traj = SimulationEngine(config()).run(sun_earth_state(two_body_sun_earth))
    n_steps = 1440
    assert traj.n_samples == n_steps + 1
    assert traj.times[0] == 0.0
    expected = np.arange(traj.n_samples) * 60.0
    np.testing.assert_array_equal(traj.times, expected)
    assert traj.times[-1] == 86400.0


def test_sample_every_controls_grid(two_body_sun_earth):
    cfg = config()
    traj = SimulationEngine(cfg).run(
        sun_earth_state(two_body_sun_earth), sample_every=10
    )
    n_steps = cfg.n_steps
    assert traj.n_samples == n_steps // 10 + 1
    np.testing.assert_array_equal(traj.times, np.arange(traj.n_samples) * 600.0)
    assert traj.meta.sample_every == 10


def test_state_reordered_to_config_body_order(two_body_sun_earth):
    ic = two_body_sun_earth
    swapped = State(
        positions=ic.positions0[::-1].copy(),
        velocities=ic.velocities0[::-1].copy(),
        body_names=("Earth", "Sun"),
        meta=meta(),
    )
    cfg = config()  # bodies = ("Sun", "Earth")
    traj = SimulationEngine(cfg).run(swapped)
    assert traj.body_names == ("Sun", "Earth")
    assert traj.gm[0] == GM_SUN
    assert traj.gm[1] == GM_EARTH
    # row 0 of the trajectory starts at the Sun position (row 1 of swapped input)
    np.testing.assert_array_equal(traj.positions[0, 0], ic.positions0[0])


def test_mismatched_body_set_rejected(two_body_sun_earth):
    bad = State(
        positions=np.zeros((3, 3)),
        velocities=np.zeros((3, 3)),
        body_names=("Sun", "Earth", "Moon"),
        meta=meta(origin="barycenter(Sun, Earth, Moon)"),
    )
    with pytest.raises(ValueError):
        SimulationEngine(config()).run(bad)


def test_frame_mismatch_rejected(two_body_sun_earth):
    state = State(
        positions=two_body_sun_earth.positions0.copy(),
        velocities=two_body_sun_earth.velocities0.copy(),
        body_names=("Sun", "Earth"),
        meta=meta(frame=ReferenceFrame.SSB_ICRS),
    )
    with pytest.raises(ValueError):
        SimulationEngine(config()).run(state)


def test_epoch_mismatch_rejected(two_body_sun_earth):
    state = State(
        positions=two_body_sun_earth.positions0.copy(),
        velocities=two_body_sun_earth.velocities0.copy(),
        body_names=("Sun", "Earth"),
        meta=meta(epoch_jd=EPOCH + 1.0),
    )
    with pytest.raises(ValueError):
        SimulationEngine(config()).run(state)


def test_sample_zero_velocity_is_exactly_initial(two_body_sun_earth):
    state = sun_earth_state(two_body_sun_earth)
    traj = SimulationEngine(config()).run(state)
    np.testing.assert_array_equal(traj.positions[0], state.positions)
    np.testing.assert_array_equal(traj.velocities[0], state.velocities)


def test_trajectory_metadata_complete(two_body_sun_earth):
    cfg = config(integrator="rk4")
    traj = SimulationEngine(cfg).run(sun_earth_state(two_body_sun_earth))
    m = traj.meta
    assert m.state_meta.frame == cfg.frame
    assert m.state_meta.origin == "barycenter(Sun, Earth)"
    assert m.state_meta.epoch_jd == cfg.epoch_jd
    assert m.state_meta.time_scale == cfg.time_scale
    assert m.state_meta.length_unit == "m"
    assert m.state_meta.gm_unit == "m^3/s^2"
    assert m.integrator == "rk4"
    assert m.integrator_order == 4
    assert m.dt == 60.0
    assert m.n_steps == 1440
    assert m.config_hash == cfg.config_hash()
    assert m.software_version
    assert m.schema_version == 1
    assert np.all(np.isfinite(traj.positions))
    assert np.all(np.isfinite(traj.velocities))


def test_trajectory_shapes(two_body_sun_earth):
    traj = SimulationEngine(config()).run(sun_earth_state(two_body_sun_earth))
    assert traj.positions.shape == (1441, 2, 3)
    assert traj.velocities.shape == (1441, 2, 3)
    assert traj.gm.shape == (2,)
    assert traj.n_bodies == 2


def test_force_seam_injectable_linear_motion(two_body_sun_earth):
    """A zero-force model must integrate to exact uniform rectilinear motion —
    proves the engine does not hard-code Newtonian gravity."""
    state = sun_earth_state(two_body_sun_earth)
    cfg = config()
    engine = SimulationEngine(cfg, accel=lambda q, v, t: np.zeros_like(q))
    traj = engine.run(state, sample_every=60)  # every hour
    # (M, N, 3): pos0 + vel0 * t
    expected = (
        state.positions[None, :, :]
        + traj.times[:, None, None] * state.velocities[None, :, :]
    )
    # Measured: max relative deviation 1.63e-14 — the stepper adds dt*v once
    # per step, so rounding accumulates (~n_steps * eps); the single-product
    # reference does not. Tolerance set at 10x measured, well below any
    # gravitational effect (GM_Earth perturbation on this orbit is ~1e-6
    # relative), so it cannot mask a force-model leak.
    np.testing.assert_allclose(traj.positions, expected, rtol=1e-13)
    np.testing.assert_allclose(
        traj.velocities,
        np.broadcast_to(state.velocities, traj.velocities.shape),
        rtol=1e-15,
    )


def test_propagate_endpoint_matches_run(two_body_sun_earth):
    cfg = config()
    state = sun_earth_state(two_body_sun_earth)
    engine = SimulationEngine(cfg)
    final = engine.propagate(state, cfg.n_steps)
    traj = engine.run(state, sample_every=cfg.n_steps)
    np.testing.assert_array_equal(final.positions, traj.positions[-1])
    np.testing.assert_array_equal(final.velocities, traj.velocities[-1])


def test_propagate_rejects_zero_steps(two_body_sun_earth):
    engine = SimulationEngine(config())
    with pytest.raises(ValueError):
        engine.propagate(sun_earth_state(two_body_sun_earth), 0)


def test_sample_every_validation(two_body_sun_earth):
    engine = SimulationEngine(config())
    with pytest.raises(ValueError):
        engine.run(sun_earth_state(two_body_sun_earth), sample_every=0)


def test_trajectory_rejects_bad_shapes():
    state_meta = meta()
    from solar_ephemeris.simulation.engine import TrajectoryMeta

    tm = TrajectoryMeta(
        state_meta=state_meta,
        integrator="verlet",
        integrator_order=2,
        dt=60.0,
        sample_every=1,
        n_steps=1,
        config_hash="0" * 64,
        software_version="test",
    )
    with pytest.raises(ValueError):
        Trajectory(
            times=np.array([0.0]),
            positions=np.zeros((1, 3)),  # missing body axis
            velocities=np.zeros((1, 2, 3)),
            gm=np.array([1.0]),
            body_names=("A",),
            meta=tm,
        )
    with pytest.raises(ValueError):
        Trajectory(
            times=np.array([0.0, 0.0]),  # not strictly increasing
            positions=np.zeros((2, 1, 3)),
            velocities=np.zeros((2, 1, 3)),
            gm=np.array([1.0]),
            body_names=("A",),
            meta=tm,
        )
    with pytest.raises(ValueError):
        Trajectory(
            times=np.array([0.0]),
            positions=np.full((1, 1, 3), np.nan),
            velocities=np.zeros((1, 1, 3)),
            gm=np.array([1.0]),
            body_names=("A",),
            meta=tm,
        )
