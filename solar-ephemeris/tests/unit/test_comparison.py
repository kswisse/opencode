"""Metrics + ComparisonResult (requirements 6, 12, 13) — synthetic FIRST.

All tests here run kernel-free against the recorded fixture: model states are
constructed to equal (or differ from) the reference by exactly known amounts,
so the metrics must reproduce 0 or the injected value — before any real-kernel
test exists (mandate 15: machine bugs first, physics later).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from solar_ephemeris import __version__
from solar_ephemeris.ephemeris.comparison import (
    ComparisonResult,
    assert_compatible,
    compare_trajectory,
    error_statistics,
    relative_error,
    write_comparison_record,
)
from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST
from solar_ephemeris.ephemeris.time import jd_tdb_to_et
from solar_ephemeris.ephemeris.types import MetadataMismatchError, UnknownBodyMappingError
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.frames.transforms import recenter_ssb_to_model
from solar_ephemeris.physics.constants import GM_EARTH, GM_SUN
from solar_ephemeris.physics.state import StateMeta
from solar_ephemeris.simulation.engine import Trajectory, TrajectoryMeta

JD_J2000 = 2451545.0
BODIES = ("Sun", "Earth")
GM = np.array([GM_SUN, GM_EARTH])
TIMES = np.array([0.0, 43200.0, 86400.0])  # 0 d, 0.5 d, 1 d — inside fixture grid


@pytest.fixture(scope="module")
def fixture() -> FixtureReference:
    return FixtureReference()


def _model_meta(epoch_jd: float = JD_J2000) -> StateMeta:
    return StateMeta(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin="barycenter(Sun, Earth)",
        epoch_jd=epoch_jd,
        time_scale=TimeScale.TDB,
    )


def _traj_meta(state_meta: StateMeta) -> TrajectoryMeta:
    return TrajectoryMeta(
        state_meta=state_meta,
        integrator="rk4",
        integrator_order=4,
        dt=86.4,
        sample_every=1,
        n_steps=int(TIMES.size),
        config_hash="synthetic-equal-reference",
        software_version=__version__,
    )


def _reference_recentered(fixture: FixtureReference, offset_pos=None, offset_vel=None):
    """Model trajectory equal to the (transformed) reference, ± known offsets."""
    et0 = jd_tdb_to_et(JD_J2000)
    pos = np.empty((len(TIMES), len(BODIES), 3))
    vel = np.empty_like(pos)
    for i, t in enumerate(TIMES):
        for k, name in enumerate(BODIES):
            st = fixture.state_at(body=name, et=et0 + float(t))
            pos[i, k] = st.position_m
            vel[i, k] = st.velocity_ms
        p, v, _, _ = recenter_ssb_to_model(pos[i], vel[i], GM, BODIES)
        pos[i], vel[i] = p, v
    if offset_pos is not None:
        pos = pos + np.asarray(offset_pos, dtype=np.float64)
    if offset_vel is not None:
        vel = vel + np.asarray(offset_vel, dtype=np.float64)
    traj = Trajectory(
        times=TIMES.copy(),
        positions=pos,
        velocities=vel,
        gm=GM.copy(),
        body_names=BODIES,
        meta=_traj_meta(_model_meta()),
    )
    return traj


def test_model_equals_reference_zero_error_bit_exact(fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    result = compare_trajectory(
        traj, fixture, body="Earth", ic_source="reference fixture (synthetic)"
    )
    # Bit-exact: identical inputs through identical code paths subtract to 0.
    assert np.array_equal(result.position_error, np.zeros(len(TIMES)))
    assert np.array_equal(result.velocity_error, np.zeros(len(TIMES)))
    assert np.array_equal(result.relative_position_error, np.zeros(len(TIMES)))
    assert result.position_stats.max == 0.0 and result.position_stats.mean == 0.0
    assert result.velocity_stats.max == 0.0


def test_known_position_offset_reproduced(fixture: FixtureReference) -> None:
    delta = np.array([3000.0, 4000.0, 0.0])
    traj = _reference_recentered(fixture, offset_pos=delta)
    result = compare_trajectory(
        traj, fixture, body="Earth", ic_source="synthetic +Δr"
    )
    # Expected |Δr| = 5000.0 m exactly; float64 grid at |r|~1.5e11 m is
    # ~3.3e-5 m per ULP, so the rounded (ref+Δ) differs by ≤ ~3e-5 m.
    assert np.allclose(result.position_error, 5000.0, rtol=0.0, atol=1e-4)
    assert np.allclose(result.relative_position_error, 5000.0 / np.linalg.norm(
        _reference_recentered(fixture).positions[:, 1, :], axis=1
    ), rtol=1e-12, atol=1e-15)


def test_known_velocity_offset_reproduced(fixture: FixtureReference) -> None:
    delta = np.array([3.0, 4.0, 0.0])
    traj = _reference_recentered(fixture, offset_vel=delta)
    result = compare_trajectory(
        traj, fixture, body="Earth", ic_source="synthetic +Δv"
    )
    # Expected |Δv| = 5 m/s; ULP at ~30 m/s is ~7e-15 m/s — far below atol.
    assert np.allclose(result.velocity_error, 5.0, rtol=0.0, atol=1e-9)
    assert result.position_stats.max < 1e-3  # position untouched by Δv


def test_stats_hand_computed() -> None:
    stats = error_statistics(np.array([1.0, 2.0, 3.0, 4.0]), percentiles=(95,))
    assert stats.mean == pytest.approx(2.5)
    assert stats.median == pytest.approx(2.5)
    assert stats.max == 4.0
    assert stats.percentiles["p95"] == pytest.approx(3.85)  # linear method
    assert stats.n_samples == 4


def test_percentile_configuration() -> None:
    stats = error_statistics(np.arange(1.0, 11.0), percentiles=(50, 95, 99))
    assert set(stats.percentiles) == {"p50", "p95", "p99"}
    assert stats.percentiles["p50"] == pytest.approx(5.5)
    assert stats.percentiles["p95"] == pytest.approx(9.55)
    assert stats.percentiles["p99"] == pytest.approx(9.91)


@pytest.mark.parametrize(
    "bad, match",
    [
        (np.array([]), "non-empty"),
        (np.zeros((2, 2)), "1-D"),
        (np.array([1.0, np.nan]), "NaN"),
        (np.array([1.0, np.inf]), "finite|NaN"),
    ],
)
def test_error_statistics_rejects_bad_arrays(bad, match) -> None:
    with pytest.raises(ValueError, match=match):
        error_statistics(bad)


@pytest.mark.parametrize("pct", [101, -1, 100.5])
def test_error_statistics_rejects_bad_percentiles(pct) -> None:
    with pytest.raises(ValueError, match="percentile"):
        error_statistics(np.array([1.0]), percentiles=(pct,))


def test_error_statistics_rejects_empty_or_duplicate_percentiles() -> None:
    with pytest.raises(ValueError, match="at least one"):
        error_statistics(np.array([1.0]), percentiles=())
    with pytest.raises(ValueError, match="duplicate"):
        error_statistics(np.array([1.0]), percentiles=(95, 95))


def test_relative_error_zero_denominator_guard() -> None:
    with pytest.raises(ValueError, match="denominator is zero"):
        relative_error(np.array([1.0, 2.0]), np.array([1.0, 0.0]))


def test_relative_error_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="shapes differ"):
        relative_error(np.array([1.0]), np.array([1.0, 2.0]))


# ---- 7-class mismatch matrix against assert_compatible (mandate 18) --------


def test_mismatch_body(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(_model_meta(), ref, body="Mars", transform="t")
    assert ei.value.field == "body"


def test_mismatch_frame_model_side(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    meta = StateMeta(
        frame=ReferenceFrame.SSB_ICRS,
        origin="barycenter(Sun, Earth)",
        epoch_jd=JD_J2000,
        time_scale=TimeScale.TDB,
    )
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(meta, ref, body="Earth", transform="t")
    assert ei.value.field == "frame"


def test_mismatch_frame_reference_side(fixture: FixtureReference) -> None:
    # Two-sided frame rule: even with a correct model frame, a reference state
    # not in SSB_ICRS is refused. ReferenceState enforces SSB_ICRS at
    # construction, so the gate is exercised by forcing the field on a frozen
    # instance (deliberately invalid stand-in, never a production path).
    ref = fixture.state_at(body="Earth", et=0.0)
    object.__setattr__(ref, "frame", ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC)
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(_model_meta(), ref, body="Earth", transform="t")
    assert ei.value.field == "frame"


def test_mismatch_center_missing_transform(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(_model_meta(), ref, body="Earth", transform=None)
    assert ei.value.field == "center"


def test_mismatch_epoch(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=43200.0)  # JD 2451545.5
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(_model_meta(epoch_jd=JD_J2000), ref, body="Earth", transform="t")
    assert ei.value.field == "epoch_jd"


def test_mismatch_time_scale(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    meta = StateMeta(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin="barycenter(Sun, Earth)",
        epoch_jd=JD_J2000,
        time_scale=TimeScale.UTC,
    )
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(meta, ref, body="Earth", transform="t")
    assert ei.value.field == "time_scale"


class _UnitStandIn:
    """StateMeta forbids non-m units at construction — stand-in exercises the
    comparison gate independently (belt-and-suspenders check)."""

    frame = ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC
    origin = "barycenter(Sun, Earth)"
    epoch_jd = JD_J2000
    time_scale = TimeScale.TDB

    def __init__(self, length_unit: str = "m", velocity_unit: str = "m/s") -> None:
        self.length_unit = length_unit
        self.velocity_unit = velocity_unit


def test_mismatch_length_unit(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(_UnitStandIn(length_unit="km"), ref, body="Earth", transform="t")
    assert ei.value.field == "length_unit"


def test_mismatch_velocity_unit(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    with pytest.raises(MetadataMismatchError) as ei:
        assert_compatible(
            _UnitStandIn(velocity_unit="km/s"), ref, body="Earth", transform="t"
        )
    assert ei.value.field == "velocity_unit"


def test_compatible_pair_passes(fixture: FixtureReference) -> None:
    ref = fixture.state_at(body="Earth", et=0.0)
    assert_compatible(_model_meta(), ref, body="Earth", transform="translation …")


# ---- end-to-end result serialization ---------------------------------------


def test_ic_source_required(fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    with pytest.raises(ValueError, match="ic_source"):
        compare_trajectory(traj, fixture, body="Earth", ic_source="  ")
    with pytest.raises(ValueError, match="ic_source"):
        compare_trajectory(traj, fixture, body="Earth", ic_source="")


def test_unmapped_body_rejected(fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    with pytest.raises(UnknownBodyMappingError):
        compare_trajectory(traj, fixture, body="PlanetX", ic_source="x")


def test_body_absent_from_trajectory_rejected(fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    with pytest.raises(MetadataMismatchError) as ei:
        compare_trajectory(traj, fixture, body="Mars", ic_source="x")
    assert ei.value.field == "body"


def test_result_to_dict_round_trip(fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    result = compare_trajectory(
        traj, fixture, body="Earth", ic_source="reference fixture (synthetic)",
        percentiles=(50, 95, 99),
    )
    payload = result.to_dict()
    text = json.dumps(payload, allow_nan=False)  # must be pure JSON, no NaN
    back = json.loads(text)
    assert back["body"] == "Earth"
    assert back["epoch_jd"] == JD_J2000
    assert back["model_metadata"]["ic_source"] == "reference fixture (synthetic)"
    assert back["model_metadata"]["integrator"] == "rk4"
    assert back["model_metadata"]["config_hash"] == "synthetic-equal-reference"
    assert back["reference_metadata"]["kernel_sha256"] == DE440S_MANIFEST.sha256
    assert back["reference_metadata"]["reference_name"] == "JPL DE440"
    assert back["transform"].startswith("translation SSB(0)")
    assert len(back["times_s"]) == len(TIMES)
    assert set(back["position_stats"]["percentiles"]) == {"p50", "p95", "p99"}
    assert back["position_stats"]["n_samples"] == len(TIMES)


def test_write_comparison_record(tmp_path: Path, fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    result = compare_trajectory(
        traj, fixture, body="Earth", ic_source="reference fixture (synthetic)"
    )
    out = tmp_path / "comparison_record.json"
    write_comparison_record(result, out)
    assert out.exists()
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back == result.to_dict()


def test_comparison_result_carries_full_provenance(fixture: FixtureReference) -> None:
    traj = _reference_recentered(fixture)
    result = compare_trajectory(
        traj, fixture, body="Earth", ic_source="reference fixture (synthetic)"
    )
    prov = result.reference_metadata
    assert prov.reference_name == "JPL DE440"
    assert prov.kernel_sha256 == DE440S_MANIFEST.sha256
    assert prov.kernel_filename == DE440S_MANIFEST.filename
    assert prov.reference_frame == "J2000" and prov.reference_center == 0
    assert isinstance(result, ComparisonResult)
