"""Phase-3 integration: Sun-Earth-Moon configuration through the WHOLE stack.

Requirement coverage (user's list 1-7):
  1. config builds for ["Sun","Earth","Moon"] AND ["Sun","Earth"]
  2. engine rejects unknown bodies instead of silently mislabelling
  3. body order follows the config; analysis is name-based across orders
  4. Moon GM flows through registry -> engine -> trajectory unchanged
  5. relative Earth-Moon state at epoch matches the IC analytically
  6. barycentre invariants (total COM at origin, EMB identity, EMB radius)
  7. determinism: same config + same IC -> bitwise-identical result,
     in memory AND through run_to_file/load_run

Measured tolerances (2026-10-01, 60 d RK4 run, dt = P_EM/1000, every 10th step):
  COM drift              max|sum GM r|/(GM_tot*R) < 1e-17   (assert 1e-15)
  EMB identity error     6.1e-4 m                           (assert 1e-3)
  EMB radius deviation   3.06e-6 rel (~450 m; O((a/R)^2) physics) (assert 1e-5)
  angular period         27.0255 d                          (window 26.5-27.6)
  distance amplitude     0.0354                             (assert < 0.04)
  radial/angular ratio   0.531                              (window 0.45-0.60)
  relative energy error  2.8e-15                            (assert < 1e-12)
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.analysis import angular_period, barycenter, distance_stats, radial_period, relative_energy_error, relative_state
from solar_ephemeris.physics.constants import (
    GM_EARTH,
    GM_EARTH_MOON_BARYCENTER,
    GM_MOON,
    GM_SUN,
    SECONDS_PER_DAY,
)
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine
from solar_ephemeris.simulation.initial_conditions import (
    EARTH_MOON_DISTANCE_M,
    make_circular_two_body_ic,
)
from solar_ephemeris.simulation.runner import load_run, run_to_file

# dt rule (documented in docs/methodology/phase3-earth-moon.md):
# the slowest dynamics that must stay resolved is the Earth-Moon orbit, so
P_EM = 2.0 * np.pi * np.sqrt(EARTH_MOON_DISTANCE_M**3 / GM_EARTH_MOON_BARYCENTER)
DT_RULE = P_EM / 1000.0  # ~2357 s, >= 1000 samples per lunar orbit
EPOCH_JD = 2451545.0


def make_cfg(bodies, duration, dt=DT_RULE, *, integrator="rk4", guard_m=1.0):
    return SimulationConfig(
        bodies=tuple(bodies),
        integrator=integrator,
        dt=dt,
        duration=duration,
        epoch_jd=EPOCH_JD,
        guard_m=guard_m,
    )


@pytest.fixture(scope="module")
def cfg60():
    return make_cfg(("Sun", "Earth", "Moon"), 60.0 * SECONDS_PER_DAY)


@pytest.fixture(scope="module")
def run60(cfg60, sun_earth_moon):
    engine = SimulationEngine(cfg60)
    return engine.run(sun_earth_moon.state(), sample_every=10)


# --- 1. both configurations build ------------------------------------------


def test_config_builds_for_both_required_body_sets():
    three = make_cfg(("Sun", "Earth", "Moon"), SECONDS_PER_DAY)
    two = make_cfg(("Sun", "Earth"), SECONDS_PER_DAY)
    assert three.n_steps >= 1 and two.n_steps >= 1
    assert three.config_hash() != two.config_hash()
    SimulationEngine(three)
    SimulationEngine(two)


# --- 2. unknown body rejected ----------------------------------------------


def test_engine_rejects_unknown_body():
    from solar_ephemeris.physics.bodies import UnknownBodyError

    with pytest.raises(UnknownBodyError):
        SimulationEngine(make_cfg(("Sun", "Luna"), SECONDS_PER_DAY))


# --- 3. body order follows the config --------------------------------------


def test_body_order_follows_config(sun_earth_moon):
    permuted = ("Moon", "Sun", "Earth")
    cfg = make_cfg(permuted, 10.0 * SECONDS_PER_DAY)
    engine = SimulationEngine(cfg)
    assert engine.bodies == permuted
    np.testing.assert_array_equal(
        engine.gm, [GM_MOON, GM_SUN, GM_EARTH]
    )
    traj = engine.run(sun_earth_moon.state(), sample_every=5)
    assert traj.body_names == permuted
    np.testing.assert_array_equal(traj.gm, [GM_MOON, GM_SUN, GM_EARTH])

    # ...and the physics is order-independent: the Earth-Moon relative
    # state must match a run in the default order (same grid, rtol covers
    # float accumulation-order noise only — far below any physical signal)
    cfg_def = make_cfg(("Sun", "Earth", "Moon"), 10.0 * SECONDS_PER_DAY)
    traj_def = SimulationEngine(cfg_def).run(
        sun_earth_moon.state(), sample_every=5
    )
    r_perm = relative_state(traj, "Earth", "Moon").r
    r_def = relative_state(traj_def, "Earth", "Moon").r
    np.testing.assert_allclose(r_perm, r_def, rtol=1e-10, atol=1e-3)


# --- 4. Moon GM reaches the trajectory -------------------------------------


def test_engine_and_trajectory_carry_exact_moon_gm(cfg60, sun_earth_moon):
    engine = SimulationEngine(cfg60)
    np.testing.assert_array_equal(engine.gm, [GM_SUN, GM_EARTH, GM_MOON])
    traj = engine.run(sun_earth_moon.state(), sample_every=10)
    np.testing.assert_array_equal(traj.gm, [GM_SUN, GM_EARTH, GM_MOON])
    np.testing.assert_array_equal(traj.gm[2], GM_MOON)


# --- 5. relative state at epoch --------------------------------------------


def test_relative_state_at_epoch(run60):
    rel = relative_state(run60, "Earth", "Moon")
    assert rel.distance[0] == pytest.approx(EARTH_MOON_DISTANCE_M, abs=1e-3)
    v_expected = float(np.sqrt(GM_EARTH_MOON_BARYCENTER / EARTH_MOON_DISTANCE_M))
    assert rel.speed[0] == pytest.approx(v_expected, rel=1e-12)
    np.testing.assert_array_equal(
        rel.r, run60.positions[:, 2, :] - run60.positions[:, 1, :]
    )


# --- 6. barycentre invariants ----------------------------------------------


def test_barycentre_invariants(run60):
    gm_tot = float(run60.gm.sum())
    r_all, _ = barycenter(run60)
    scale = max(np.linalg.norm(run60.positions, axis=2).max(), 1.0)
    assert np.abs(r_all).max() / gm_tot / scale < 1e-15

    r_emb, _ = barycenter(run60, ("Earth", "Moon"))
    # identity: EMB sits opposite the Sun at -GM_S/GM_EM (COM = 0)
    emb_from_sun = -(GM_SUN / GM_EARTH_MOON_BARYCENTER) * run60.positions[:, 0, :]
    assert np.abs(r_emb - emb_from_sun).max() < 1e-3  # measured 6.1e-4 m

    r_emb_sun = np.linalg.norm(r_emb, axis=1)
    # EMB is not an exact Kepler orbit: differential solar gravity across the
    # Earth-Moon axis perturbs it at O((a/R)^2) ~ 6.6e-6 — measured 3.06e-6
    # rel (~450 m) over 60 d. Bound: 1e-5.
    assert np.all(np.abs(r_emb_sun / 149597870700.0 - 1.0) < 1e-5)


# --- 7. determinism ---------------------------------------------------------


def test_determinism_in_memory(sun_earth_moon):
    cfg = make_cfg(("Sun", "Earth", "Moon"), 30.0 * SECONDS_PER_DAY)
    a = SimulationEngine(cfg).run(sun_earth_moon.state(), sample_every=5)
    b = SimulationEngine(cfg).run(sun_earth_moon.state(), sample_every=5)
    np.testing.assert_array_equal(a.times, b.times)
    np.testing.assert_array_equal(a.positions, b.positions)
    np.testing.assert_array_equal(a.velocities, b.velocities)
    assert a.meta.config_hash == b.meta.config_hash == cfg.config_hash()


def test_determinism_through_file_roundtrip(sun_earth_moon, tmp_path):
    cfg = make_cfg(("Sun", "Earth", "Moon"), 30.0 * SECONDS_PER_DAY)
    state = sun_earth_moon.state()
    engine = SimulationEngine(cfg)
    direct = engine.run(state, sample_every=5)
    run_to_file(cfg, state, tmp_path, sample_every=5)
    loaded, record = load_run(tmp_path)
    np.testing.assert_array_equal(loaded.times, direct.times)
    np.testing.assert_array_equal(loaded.positions, direct.positions)
    np.testing.assert_array_equal(loaded.velocities, direct.velocities)
    np.testing.assert_array_equal(loaded.gm, direct.gm)
    assert loaded.body_names == direct.body_names
    assert record.config_hash == cfg.config_hash()


# --- scientific diagnostics on the integrated model -------------------------


def test_lunar_orbit_diagnostics_60d(run60):
    rel = relative_state(run60, "Earth", "Moon")
    period = angular_period(rel.times, rel.r) / SECONDS_PER_DAY
    assert 26.5 < period < 27.6, f"measured {period:.4f} d"
    stats = distance_stats(rel.distance)
    assert stats.amplitude < 0.04, f"measured {stats.amplitude:.4f}"
    dip = radial_period(rel.times, rel.distance) / SECONDS_PER_DAY
    ratio = dip / period
    assert 0.45 < ratio < 0.60, (
        f"dip spacing {dip:.3f} d vs orbital {period:.3f} d — two dips/rev "
        "interpretation broken"
    )


def test_energy_conservation_60d_rk4(run60):
    err = float(np.max(relative_energy_error(run60)))
    assert err < 1e-12, f"measured {err:.3e}"
