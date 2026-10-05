"""Deterministic reproducibility: identical config + identical IC must yield
bitwise-identical arrays.

Rules encoded here:
- compare ARRAYS AFTER LOADING (np.array_equal), never npz file bytes
  (the zip container embeds a timestamp);
- config_hash equality is the reproducibility key;
- a changed dt MUST change the output (guards against a test that would
  pass even if the integrator ignored its configuration).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.state import State, StateMeta
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine
from solar_ephemeris.simulation.runner import load_run, run_to_file

EPOCH = 2451545.0


def make_config(**over) -> SimulationConfig:
    base = dict(
        bodies=("Sun", "Earth"),
        integrator="rk4",
        dt=120.0,
        duration=43200.0,  # 360 steps
        epoch_jd=EPOCH,
    )
    base.update(over)
    return SimulationConfig(**base)


def make_state(ic) -> State:
    return State(
        positions=ic.positions0.copy(),
        velocities=ic.velocities0.copy(),
        body_names=("Sun", "Earth"),
        meta=StateMeta(
            frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
            origin="barycenter(Sun, Earth)",
            epoch_jd=EPOCH,
            time_scale=TimeScale.TDB,
        ),
    )


def test_two_in_memory_runs_are_bitwise_identical(two_body_sun_earth):
    cfg = make_config()
    state = make_state(two_body_sun_earth)
    t1 = SimulationEngine(cfg).run(state, sample_every=10)
    t2 = SimulationEngine(make_config()).run(make_state(two_body_sun_earth), sample_every=10)
    np.testing.assert_array_equal(t1.positions, t2.positions)
    np.testing.assert_array_equal(t1.velocities, t2.velocities)
    np.testing.assert_array_equal(t1.times, t2.times)
    assert t1.meta.config_hash == t2.meta.config_hash


def test_file_runs_reproduce_bitwise(tmp_path, two_body_sun_earth):
    cfg = make_config()
    state = make_state(two_body_sun_earth)
    r1 = run_to_file(cfg, state, tmp_path / "run1", sample_every=10)
    r2 = run_to_file(make_config(), make_state(two_body_sun_earth), tmp_path / "run2", sample_every=10)

    traj1, rec1 = load_run(tmp_path / "run1")
    traj2, rec2 = load_run(tmp_path / "run2")

    np.testing.assert_array_equal(traj1.positions, traj2.positions)
    np.testing.assert_array_equal(traj1.velocities, traj2.velocities)
    np.testing.assert_array_equal(traj1.times, traj2.times)
    np.testing.assert_array_equal(traj1.gm, traj2.gm)

    assert r1.config_hash == r2.config_hash
    assert rec1.config_hash == rec2.config_hash
    assert rec1.config == rec2.config
    # only the timestamp may differ
    same = {
        k: (rec1.to_dict()[k], rec2.to_dict()[k])
        for k in rec1.to_dict()
        if k != "run_timestamp_utc"
    }
    for k, (a, b) in same.items():
        assert a == b, f"RunRecord field {k} differs between identical runs"


def test_config_hash_stable_across_disk_roundtrip(tmp_path, two_body_sun_earth):
    cfg = make_config()
    run_to_file(cfg, make_state(two_body_sun_earth), tmp_path / "r", sample_every=50)
    traj, rec = load_run(tmp_path / "r")
    assert rec.config_hash == cfg.config_hash()
    assert traj.meta.config_hash == cfg.config_hash()
    assert rec.config == cfg


def test_changing_dt_changes_output(two_body_sun_earth):
    t_a = SimulationEngine(make_config(dt=120.0)).run(
        make_state(two_body_sun_earth), sample_every=10
    )
    t_b = SimulationEngine(make_config(dt=240.0)).run(
        make_state(two_body_sun_earth), sample_every=10
    )
    assert not np.array_equal(t_a.positions, t_b.positions)
    assert t_a.meta.config_hash != t_b.meta.config_hash


def test_record_json_is_machine_readable(tmp_path, two_body_sun_earth):
    run_to_file(make_config(), make_state(two_body_sun_earth), tmp_path / "r")
    raw = json.loads((tmp_path / "r" / "run_record.json").read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1
    assert raw["config"]["integrator"] == "rk4"
    assert raw["config"]["bodies"] == ["Sun", "Earth"]
    assert raw["config"]["time_scale"] == "TDB"
    assert raw["config"]["frame"] == "active_bodies_barycentric"
    assert len(raw["config_hash"]) == 64
    assert Path(raw["trajectory_file"]).name == "trajectory.npz"
    assert raw["software_version"]
    assert raw["run_timestamp_utc"]
