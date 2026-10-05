"""End-to-end synthetic chain (mandate 15, requirement 16) — kernel-free.

Scripted full path BEFORE any real-kernel test:
fixture → ic.py (reference-ingested ICs) → SimulationEngine.run →
provider query at et0+t (interior samples exercise cubic Hermite) →
recenter/normalize → assert_compatible → metrics → comparison record.

Structure, provenance and determinism are asserted; error MAGNITUDES are
not — thresholds for those come later, measured-first, in the staged real
validation (Inc 7b). The one physical fact asserted here is exact by
construction: sample t=0 compares an IC built from the reference against the
reference itself, so E_pos[0] must be bit-exact zero.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from solar_ephemeris.ephemeris.comparison import compare_trajectory, write_comparison_record
from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.ic import reference_state_to_model_state
from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine

JD_J2000 = 2451545.0
BODIES = ("Sun", "Earth")
DT = 3600.0  # 1 h
DURATION = 86400.0  # 1 day — start epoch + 1 d stays inside the fixture grid
IC_SOURCE = "reference-ingested via ephemeris/ic.py from recorded DE440 fixture"


@pytest.fixture(scope="module")
def fixture() -> FixtureReference:
    return FixtureReference()


def _config() -> SimulationConfig:
    return SimulationConfig(
        bodies=BODIES,
        integrator="rk4",
        dt=DT,
        duration=DURATION,
        epoch_jd=JD_J2000,
        time_scale=TimeScale.TDB,
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        reference_dataset="JPL DE440 (de440s.bsp fixture)",
    )


def _run(fixture: FixtureReference):
    config = _config()
    ic = reference_state_to_model_state(fixture, bodies=BODIES, epoch_jd=JD_J2000)
    engine = SimulationEngine(config)
    traj = engine.run(ic, sample_every=4)  # samples at 0, 4, 8, … 24 h
    return engine, ic, traj


def test_full_chain_produces_comparison(fixture: FixtureReference) -> None:
    _engine, _ic, traj = _run(fixture)
    assert traj.meta.state_meta.frame is ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC
    assert traj.meta.state_meta.origin == "barycenter(Sun, Earth)"
    assert traj.meta.state_meta.epoch_jd == JD_J2000
    assert traj.meta.state_meta.time_scale is TimeScale.TDB
    assert traj.meta.config_hash == _config().config_hash()  # reproducible
    assert traj.meta.integrator == "rk4" and traj.meta.dt == DT
    # sample_every=4, n_steps=24 → 1 initial + 6 sampled
    assert traj.n_samples == 7 and list(traj.times) == [
        0.0, 14400.0, 28800.0, 43200.0, 57600.0, 72000.0, 86400.0
    ]

    result = compare_trajectory(traj, fixture, body="Earth", ic_source=IC_SOURCE)

    # Requirement 16: the record asserts ICs are reference-derived.
    assert result.model_metadata["ic_source"] == IC_SOURCE
    assert "reference-ingested" in result.model_metadata["ic_source"]
    assert result.model_metadata["config_hash"] == traj.meta.config_hash

    # Interior samples (4 h, 8 h …) fall between daily fixture samples, so
    # the chain above necessarily exercised cubic-Hermite interpolation.
    assert result.times_s.shape == traj.times.shape
    assert result.position_error.shape == traj.times.shape
    assert np.all(np.isfinite(result.position_error))
    assert np.all(np.isfinite(result.velocity_error))
    assert np.all(np.isfinite(result.relative_position_error))
    assert result.position_stats.n_samples == traj.n_samples
    assert result.position_stats.max == float(np.max(result.position_error))
    assert result.velocity_stats.max == float(np.max(result.velocity_error))

    # t=0: model IC == reference state through the same transform → exact 0.
    assert result.position_error[0] == 0.0
    assert result.velocity_error[0] == 0.0
    assert result.relative_position_error[0] == 0.0

    # Provenance answers "which DE440 data generated this result?"
    prov = result.reference_metadata
    assert prov.reference_name == "JPL DE440"
    assert prov.kernel_sha256 == DE440S_MANIFEST.sha256
    assert prov.kernel_filename == DE440S_MANIFEST.filename
    assert result.transform.startswith("translation SSB(0)")
    assert "no rotation" in result.transform


def test_chain_is_deterministic(fixture: FixtureReference) -> None:
    _, _, traj_a = _run(fixture)
    _, _, traj_b = _run(fixture)
    assert np.array_equal(traj_a.positions, traj_b.positions)
    assert np.array_equal(traj_a.velocities, traj_b.velocities)
    res_a = compare_trajectory(traj_a, fixture, body="Earth", ic_source=IC_SOURCE)
    res_b = compare_trajectory(traj_b, fixture, body="Earth", ic_source=IC_SOURCE)
    assert np.array_equal(res_a.position_error, res_b.position_error)
    assert np.array_equal(res_a.velocity_error, res_b.velocity_error)


def test_comparison_record_written_from_chain(
    tmp_path: Path, fixture: FixtureReference
) -> None:
    _, _, traj = _run(fixture)
    result = compare_trajectory(traj, fixture, body="Earth", ic_source=IC_SOURCE)
    out = tmp_path / "comparison_record.json"
    write_comparison_record(result, out)
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["reference_metadata"]["kernel_sha256"] == DE440S_MANIFEST.sha256
    assert back["reference_metadata"]["reference_name"] == "JPL DE440"
    assert back["model_metadata"]["ic_source"] == IC_SOURCE
    assert back["model_metadata"]["integrator"] == "rk4"
    assert back["model_metadata"]["dt"] == DT
    assert back["body"] == "Earth"
    assert len(back["position_error"]) == len(back["times_s"])


def test_six_controls_recorded_in_model_metadata(fixture: FixtureReference) -> None:
    # Requirement 16: every control of the run is in the record — epoch,
    # bodies, IC source, integrator, dt, duration/steps, kernel (reference
    # side), frame, center/origin, timescale, units.
    _, _, traj = _run(fixture)
    result = compare_trajectory(traj, fixture, body="Earth", ic_source=IC_SOURCE)
    md = result.model_metadata
    assert md["epoch_jd"] == JD_J2000
    assert md["body_names"] == list(BODIES)
    assert md["ic_source"] == IC_SOURCE
    assert md["integrator"] == "rk4"
    assert md["dt"] == DT
    assert md["n_steps"] == 24
    assert md["frame"] == "active_bodies_barycentric"
    assert md["origin"] == "barycenter(Sun, Earth)"
    assert md["time_scale"] == "TDB"
    assert md["length_unit"] == "m" and md["velocity_unit"] == "m/s"
    assert result.reference_metadata.kernel_sha256 == DE440S_MANIFEST.sha256
