"""Staged real validation (Increment 7b — Gate B).

Stage order is mandated by the brief (§14): load → metadata verify →
1 body / 1 epoch → multiple epochs → units → frame/center → body IDs →
interpolation-vs-native → **controlled Sun–Earth** → **Sun–Earth–Moon**
(with the Earth–Moon distance metric).

Threshold policy (plan §10 row 7b, checklist G): every threshold below was
MEASURED FIRST on 2026-10-03 (this machine, de440s.bsp MD5
3917ee56769db332790c751e2168843d, spiceypy 8.2.0) and the
docstring records *threshold / measured / reason*. Ceilings are ~100× the
measurement (regression guard: units, frames, wrong body, broken
transform); floors are ~measured/100 (guard against a silently trivial
comparison, e.g. a body compared with itself or an empty subtraction).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import spiceypy as sp

from solar_ephemeris.ephemeris.comparison import (
    ComparisonResult,
    compare_trajectory,
    write_comparison_record,
)
from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.ic import reference_state_to_model_state
from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST, default_kernel_path
from solar_ephemeris.ephemeris.mapping import BODY_TO_NAIF
from solar_ephemeris.ephemeris.reference import get_state
from solar_ephemeris.ephemeris.spice_backend import SpiceReference
from solar_ephemeris.ephemeris.time import et_to_jd_tdb, jd_tdb_to_et
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine

pytestmark = pytest.mark.real_kernel

KERNEL = default_kernel_path()
J2000 = 2451545.0
IC_SOURCE = "reference-ingested via ephemeris/ic.py (live de440s.bsp)"

#: Orbital periods used for the dt choices (s), documented in the doc.
P_SE_S = 365.256363004 * 86400.0  # Earth mean orbital period (Julian yr)
P_EM_S = 27.321661 * 86400.0  # Moon mean orbital period


def _require_kernel() -> Path:
    if not KERNEL.is_file():
        pytest.fail(
            f"reference kernel missing: {KERNEL} — download from "
            "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/"
            "de440s.bsp and verify sha256 against kernel_manifest.py "
            "(real-kernel tests fail, never skip)"
        )
    return KERNEL


@pytest.fixture(scope="module")
def spice_ref() -> SpiceReference:
    return SpiceReference(_require_kernel())


# ---------------------------------------------------------------------------
# Stage 1: load
# ---------------------------------------------------------------------------


def test_stage1_load(spice_ref: SpiceReference) -> None:
    """Identity gate: load succeeded only if size + MD5 + SHA-256 matched."""
    assert spice_ref.path.is_file()
    assert spice_ref.metadata.kernel_sha256 == DE440S_MANIFEST.sha256
    assert spice_ref.metadata.kernel_md5 == DE440S_MANIFEST.md5
    assert spice_ref.path.stat().st_size == DE440S_MANIFEST.size_bytes


# ---------------------------------------------------------------------------
# Stage 2: metadata verify
# ---------------------------------------------------------------------------


def test_stage2_metadata_verify(spice_ref: SpiceReference) -> None:
    """Every provenance field present and pinned to the DE440 contract."""
    meta = spice_ref.metadata.to_dict()
    required = {
        "reference_name",
        "reference_version",
        "source",
        "kernel_filename",
        "kernel_md5",
        "kernel_sha256",
        "size_bytes",
        "retrieval_date",
        "kernel_coverage",
        "body_ids",
        "reference_frame",
        "reference_center",
        "time_standard",
        "native_position_unit",
        "native_velocity_unit",
        "spice_version",
        "software_version",
    }
    assert required <= set(meta)
    assert meta["reference_name"] == "JPL DE440"
    assert meta["kernel_filename"] == "de440s.bsp"
    assert meta["reference_frame"] == "J2000"
    assert meta["reference_center"] == 0
    assert meta["native_position_unit"] == "km"
    assert meta["native_velocity_unit"] == "km/s"
    assert meta["time_standard"].startswith("TDB")
    assert meta["kernel_coverage"]["intervals"] == [list(DE440S_MANIFEST.coverage_et)]
    assert tuple(meta["body_ids"]) == tuple(sorted(DE440S_MANIFEST.body_ids))


# ---------------------------------------------------------------------------
# Stage 3: one body, one epoch
# ---------------------------------------------------------------------------


def test_stage3_single_body_single_epoch(spice_ref: SpiceReference) -> None:
    state = get_state(spice_ref, body="Earth", epoch_jd=J2000)
    assert state.epoch_jd == J2000  # exact, same value in
    assert state.body == "Earth" and state.naif_id == 399
    assert np.all(np.isfinite(state.position_m))
    assert np.all(np.isfinite(state.velocity_ms))
    assert state.provenance is spice_ref.metadata


# ---------------------------------------------------------------------------
# Stage 4: multiple epochs
# ---------------------------------------------------------------------------


def test_stage4_multiple_epochs(spice_ref: SpiceReference) -> None:
    ets = (-43200.0, 0.0, 43200.0, 129600.0, 432000.0)
    states = [spice_ref.state_at(body="Earth", et=et) for et in ets]
    jds = [s.epoch_jd for s in states]
    assert jds == sorted(jds) and len(set(jds)) == len(jds)  # strictly increasing
    for et, s in zip(ets, states, strict=True):
        assert s.epoch_jd == et_to_jd_tdb(et)
    # states actually evolve (all-equal would mean a frozen backend)
    positions = np.array([s.position_m for s in states])
    assert np.any(np.diff(positions, axis=0) != 0.0)
    assert np.all(np.isfinite(positions))


# ---------------------------------------------------------------------------
# Stage 5: units (position AND velocity checked separately — checklist F)
# ---------------------------------------------------------------------------


def test_stage5_units_live(spice_ref: SpiceReference) -> None:
    """Provider output == raw spkezr × 1000, position and velocity apart.

    Deleting either conversion in spice_backend.py fails this test: raw
    spkezr speaks km / km/s, the provider must speak m / m/s.
    """
    et = 123456.0
    raw, _lt = sp.spkezr("399", et, "J2000", "NONE", "SOLAR SYSTEM BARYCENTER")
    state = spice_ref.state_at(body="Earth", et=et)
    np.testing.assert_array_equal(state.position_m, np.array(raw[:3]) * 1000.0)
    np.testing.assert_array_equal(state.velocity_ms, np.array(raw[3:]) * 1000.0)
    # scale sanity: forgetting ×1000 lands at ~1.5e8 m, not ~1.5e11 m
    assert 1.4e11 <= float(np.linalg.norm(state.position_m)) <= 1.6e11
    assert 29000.0 <= float(np.linalg.norm(state.velocity_ms)) <= 31000.0


# ---------------------------------------------------------------------------
# Stage 6: frame / center / time
# ---------------------------------------------------------------------------


def test_stage6_frame_center_time(spice_ref: SpiceReference) -> None:
    state = spice_ref.state_at(body="Earth", et=0.0)
    assert state.frame is ReferenceFrame.SSB_ICRS
    assert state.center == "ssb(0)"
    assert state.time_scale is TimeScale.TDB
    assert state.epoch_jd == J2000
    assert jd_tdb_to_et(state.epoch_jd) == 0.0  # exact inverse, no LSK


# ---------------------------------------------------------------------------
# Stage 7: body IDs — every mapped body resolves live against this kernel
# ---------------------------------------------------------------------------


def test_stage7_all_mapped_bodies_live(spice_ref: SpiceReference) -> None:
    assert len(BODY_TO_NAIF) == 12  # contract: Sun..Pluto + EMB
    for name, expected_id in BODY_TO_NAIF.items():
        state = spice_ref.state_at(body=name, et=0.0)
        assert state.naif_id == expected_id, name
        assert state.body == name
        assert np.all(np.isfinite(state.position_m)), name
        # solar-system sanity: every body is between ~1e8 m (Moon) and ~6e12 m (Pluto)
        assert 1.0e8 <= float(np.linalg.norm(state.position_m)) <= 6.0e12, name


# ---------------------------------------------------------------------------
# Stage 8: interpolation-vs-native (fixture Hermite vs live Type-2)
# ---------------------------------------------------------------------------

_STAGE8_PROBES = (12345.0, 475199.0, 760000.0)  # all strictly interior


def test_stage8_interpolation_vs_native(spice_ref: SpiceReference) -> None:
    """Measured-first bound (2026-10-03, fixture daily grid, Earth):

    threshold ≤ 6258 m / 0.23 m/s  ·  measured 62.5777 m @ et=475199,
    0.0022923 m/s @ et=760000  ·  reason: ceilings = 100× the max of these
    probes (cubic-Hermite O(h^4) on h=86400 s grid; absorbs platform float
    noise, catches grid/unit/interpolator regressions).
    """
    fixture = FixtureReference()
    max_dp = 0.0
    max_dv = 0.0
    for et in _STAGE8_PROBES:
        live = spice_ref.state_at(body="Earth", et=et)
        recorded = fixture.state_at(body="Earth", et=et)
        max_dp = max(max_dp, float(np.linalg.norm(live.position_m - recorded.position_m)))
        max_dv = max(max_dv, float(np.linalg.norm(live.velocity_ms - recorded.velocity_ms)))
    assert max_dp <= 6258.0, f"{max_dp} m > 6258 m (100x measured 62.5777 m)"
    assert max_dv <= 0.23, f"{max_dv} m/s > 0.23 m/s (100x measured 0.0022923 m/s)"


# ---------------------------------------------------------------------------
# Stage 9: controlled Sun–Earth comparison
# ---------------------------------------------------------------------------


def _run_comparison(
    bodies: tuple[str, ...], dt: float, sample_every: int
) -> ComparisonResult:
    config = SimulationConfig(
        bodies=bodies,
        integrator="rk4",
        dt=dt,
        duration=604800.0,  # 7 d (short interval, plan §10 row 7b)
        epoch_jd=J2000,
        time_scale=TimeScale.TDB,
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        reference_dataset="JPL DE440 (de440s.bsp live)",
    )
    provider = SpiceReference(_require_kernel())
    ic = reference_state_to_model_state(provider, bodies=bodies, epoch_jd=J2000)
    traj = SimulationEngine(config).run(ic, sample_every=sample_every)
    return compare_trajectory(
        traj, provider, body="Earth", ic_source=IC_SOURCE
    )


@pytest.fixture(scope="module")
def sun_earth_result() -> ComparisonResult:
    return _run_comparison(("Sun", "Earth"), P_SE_S / 1000.0, sample_every=1)


@pytest.fixture(scope="module")
def sun_earth_moon_result() -> ComparisonResult:
    return _run_comparison(("Sun", "Earth", "Moon"), P_EM_S / 1000.0, sample_every=4)


def _assert_controls(result: ComparisonResult, origin: str, dt: float) -> None:
    """Every control recorded (plan §10 row 7b / checklist D)."""
    m = result.model_metadata
    r = result.reference_metadata
    assert m["integrator"] == "rk4"
    assert m["dt"] == pytest.approx(dt, rel=1e-12)
    assert m["ic_source"] == IC_SOURCE
    assert "reference-ingested" in m["ic_source"]
    assert m["epoch_jd"] == J2000
    assert m["time_scale"] == "TDB"
    assert m["length_unit"] == "m" and m["velocity_unit"] == "m/s"
    assert m["origin"] == origin
    assert m["config_hash"] and m["software_version"]
    assert r.reference_name == "JPL DE440"
    assert r.kernel_sha256 == DE440S_MANIFEST.sha256
    assert r.reference_frame == "J2000" and r.reference_center == 0
    assert r.native_position_unit == "km" and r.native_velocity_unit == "km/s"
    assert r.time_standard.startswith("TDB")
    assert "no rotation" in result.transform
    assert result.transform.startswith("translation SSB(0) -> ")


def test_stage9_sun_earth_controlled(sun_earth_result: ComparisonResult) -> None:
    """Sun–Earth, RK4, dt = P_SE/1000 = 31558.1498 s, ≤ 7 d, ref-ingested ICs.

    Thresholds (measured 2026-10-03 → ceiling = 100×, floor = measured/100):

    - max E_pos: measured 5 073 209.53 m → ∈ [5.0e4, 5.1e8] m.
      Reason: the Sun–Earth model omits the Moon, whose differential pull on
      Earth (external to this config) dominates the divergence; ceilings
      catch unit/frame/transform regressions (O(1e9) artifacts), floors
      catch a trivially-broken comparison.
    - max E_vel: measured 16.4805 m/s → ∈ [0.16, 1650] m/s (same reasons).
    - max relative: measured 3.4486e-5 → ≤ 3.45e-3 (100×).
    - E_pos[0] == 0 exactly (reference-ingested ICs start on top of DE440).
    """
    res = sun_earth_result
    assert res.body == "Earth"
    assert res.epoch_jd == J2000
    assert res.times_s[0] == 0.0
    assert res.times_s[-1] <= 604800.0  # ≤ 7 d short interval
    assert res.position_error[0] == 0.0  # exact zero at t0
    assert res.velocity_error[0] == 0.0

    pmax = res.position_stats.max
    assert 5.0e4 <= pmax <= 5.1e8, f"SE max E_pos {pmax} outside measured band"
    vmax = res.velocity_stats.max
    assert 0.16 <= vmax <= 1650.0, f"SE max E_vel {vmax} outside measured band"
    assert res.relative_position_error.max() <= 3.45e-3
    # statistics are what the samples say (consistent with the arrays)
    assert pmax == float(np.max(res.position_error))
    assert res.position_stats.n_samples == res.position_error.size == 20
    assert "p95" in res.position_stats.percentiles

    _assert_controls(res, "barycenter(Sun, Earth)", P_SE_S / 1000.0)


def test_stage9_record_provenance_audit(
    sun_earth_result: ComparisonResult, tmp_path: Path
) -> None:
    """Checklist D automated: produced comparison_record.json holds every field."""
    record_path = tmp_path / "comparison_record.json"
    write_comparison_record(sun_earth_result, record_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    ref = record["reference_metadata"]
    for field in (
        "reference_name",
        "reference_version",
        "source",
        "kernel_filename",
        "kernel_md5",
        "kernel_sha256",
        "retrieval_date",
        "kernel_coverage",
        "body_ids",
        "reference_frame",
        "reference_center",
        "time_standard",
        "native_position_unit",
        "native_velocity_unit",
        "spice_version",
        "software_version",
    ):
        assert field in ref and ref[field] not in ("", None), field
    assert ref["reference_name"] == "JPL DE440"
    assert ref["kernel_md5"] == DE440S_MANIFEST.md5
    assert ref["kernel_sha256"] == DE440S_MANIFEST.sha256
    assert ref["reference_center"] == 0
    assert ref["native_position_unit"] == "km"
    assert ref["native_velocity_unit"] == "km/s"
    model = record["model_metadata"]
    assert model["config_hash"] and model["ic_source"] == IC_SOURCE
    assert "no rotation" in record["transform"]
    assert record["schema_version"] == 1
    assert record["position_stats"]["n_samples"] == 20


# ---------------------------------------------------------------------------
# Stage 10: Sun–Earth–Moon + Earth–Moon distance metric
# ---------------------------------------------------------------------------


def test_stage10_sun_earth_moon_controlled(
    sun_earth_moon_result: ComparisonResult,
) -> None:
    """Sun–Earth–Moon, RK4, dt = P_EM/1000 = 2360.5915 s, ≤ 7 d.

    Thresholds (measured 2026-10-03 → ceiling = 100×, floor = measured/100):

    - max E_pos (Earth): measured 15 033.85 m → ∈ [150.0, 1.51e6] m.
      Adding the Moon to the config removes the dominant SE divergence
      (lunar tide is internal now); the residual is planetary tidal terms
      + integrator error. Reason: same regression bands as stage 9.
    - max E_vel (Earth): measured 0.0487388 m/s → ∈ [4.8e-4, 4.88] m/s.
    - E_pos[0] == 0 exactly.
    """
    res = sun_earth_moon_result
    assert res.body == "Earth"
    assert res.times_s[-1] <= 604800.0
    assert res.position_error[0] == 0.0
    assert res.velocity_error[0] == 0.0

    pmax = res.position_stats.max
    assert 150.0 <= pmax <= 1.51e6, f"SEM max E_pos {pmax} outside measured band"
    vmax = res.velocity_stats.max
    assert 4.8e-4 <= vmax <= 4.88, f"SEM max E_vel {vmax} outside measured band"
    assert res.position_stats.n_samples == 65
    _assert_controls(res, "barycenter(Sun, Earth, Moon)", P_EM_S / 1000.0)


def test_stage10_earth_moon_distance_metric() -> None:
    """Moon-specific check (plan §10 row 7b): Earth–Moon distance model vs ref.

    Distance is origin- and frame-invariant, so the model COM-frame
    distances compare directly against raw SSB-frame reference differences.

    Thresholds (measured 2026-10-03 → ceiling = 100×, floor = measured/100):
    max |d_model − d_ref| measured 121.796 m over 65 samples → ∈ [1.2, 1.22e4] m.
    t=0 must be bit-equal (both sides start from the same DE440 states).
    Reference distance must stay in the physical Moon window all along.
    """
    config = SimulationConfig(
        bodies=("Sun", "Earth", "Moon"),
        integrator="rk4",
        dt=P_EM_S / 1000.0,
        duration=604800.0,
        epoch_jd=J2000,
        time_scale=TimeScale.TDB,
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        reference_dataset="JPL DE440 (de440s.bsp live)",
    )
    kernel = SpiceReference(_require_kernel())
    ic = reference_state_to_model_state(
        kernel, bodies=("Sun", "Earth", "Moon"), epoch_jd=J2000
    )
    traj = SimulationEngine(config).run(ic, sample_every=4)

    i_e = traj.body_names.index("Earth")
    i_m = traj.body_names.index("Moon")
    d_model = np.linalg.norm(traj.positions[:, i_e, :] - traj.positions[:, i_m, :], axis=1)

    et0 = jd_tdb_to_et(J2000)
    d_ref = np.array(
        [
            np.linalg.norm(
                kernel.state_at(body="Earth", et=et0 + float(t)).position_m
                - kernel.state_at(body="Moon", et=et0 + float(t)).position_m
            )
            for t in traj.times
        ]
    )

    assert d_model[0] == d_ref[0]  # bit-equal at t0 (measured 402448639.8873211)
    assert 3.56e8 <= d_ref.min() and d_ref.max() <= 4.07e8  # physical window
    dist_err = np.abs(d_model - d_ref)
    dmax = float(dist_err.max())
    assert 1.2 <= dmax <= 1.22e4, f"EM distance error {dmax} m outside measured band"
