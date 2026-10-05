"""Phase-3 requirement 8: is the timestep adequate for the Moon?

Rule under test (documented in docs/methodology/phase3-earth-moon.md):

    dt <= P_EM / 1000  (~2357 s) — the slowest dynamics that must stay
    resolved is the Earth-Moon orbit, NOT the Sun-Earth one.

The borrowed Sun-Earth step dt = P_SE/1000 (~31558 s) only gives ~74.7
samples per lunar orbit. Measurements (2026-10-01, endpoint at t = 2*P_EM):

  endpoint |Δr|, RK4 (div: Earth / Moon)
    250-500   7.046e-01 / 5.834e+01  m
    500-1000  3.956e-02 / 3.255e+00  m      ratios ~17.8 / ~17.9  (RK4 -> 16)
    1000-2000 2.475e-03 / 1.889e-01  m      ratios ~16.0 / ~17.2
  max |dE/E0| over 2*P_EM:
    RK4    rule 2.58e-15   borrowed 2.24e-11   ratio 8.69e3
    Verlet rule 8.02e-12   borrowed 1.25e-09   ratio 1.56e2
  angular period under borrowed dt: 27.0038 d vs 27.0255 d (rule) — only
  0.08 % off. The period metric is nearly blind to the bad step; ENERGY is
  the sensitive adequacy metric, which is why thresholds live there.
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.analysis import angular_period, relative_energy_error, relative_state
from solar_ephemeris.physics.constants import (
    AU_M,
    GM_EARTH,
    GM_EARTH_MOON_BARYCENTER,
    GM_SUN,
    SECONDS_PER_DAY,
)
from solar_ephemeris.physics.gravity import CloseEncounterError
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine
from solar_ephemeris.simulation.initial_conditions import EARTH_MOON_DISTANCE_M

P_EM = 2.0 * np.pi * np.sqrt(EARTH_MOON_DISTANCE_M**3 / GM_EARTH_MOON_BARYCENTER)
P_SE = 2.0 * np.pi * np.sqrt(AU_M**3 / (GM_SUN + GM_EARTH))
DT_RULE = P_EM / 1000.0
DT_BORROWED = P_SE / 1000.0
EPOCH_JD = 2451545.0


def make_cfg(dt, duration, *, integrator="rk4", guard_m=1.0):
    return SimulationConfig(
        bodies=("Sun", "Earth", "Moon"),
        integrator=integrator,
        dt=dt,
        duration=duration,
        epoch_jd=EPOCH_JD,
        guard_m=guard_m,
    )


# --- 8a. endpoint error shrinks with dt (same endpoint for every pair) ------


def test_endpoint_error_converges_monotonically(sun_earth_moon):
    """dt-halving at an EXACTLY aligned endpoint (duration = 2*P_EM makes
    n_steps = 2*div for every divisor — no time-offset contamination)."""
    state = sun_earth_moon.state()
    divs = (250, 500, 1000, 2000)
    endpoints: dict[int, np.ndarray] = {}
    for div in divs:
        dt = P_EM / div
        cfg = make_cfg(dt, duration=2.0 * P_EM)
        n = cfg.n_steps
        assert n == 2 * div, f"div {div}: n_steps {n} != {2 * div}"
        assert abs(n * dt - 2.0 * P_EM) < 1e-6, "endpoint times must coincide"
        endpoints[div] = SimulationEngine(cfg).propagate(state, n).positions

    for body, index in (("Earth", 1), ("Moon", 2)):
        diffs = [
            float(np.linalg.norm(endpoints[hi][index] - endpoints[lo][index]))
            for lo, hi in zip(divs, divs[1:])
        ]
        assert diffs[0] > diffs[1] > diffs[2], f"{body}: not monotone {diffs}"
        r1, r2 = diffs[0] / diffs[1], diffs[1] / diffs[2]
        # RK4 asymptotic ratio is 16; measured 16.0-17.9 -> bounds [8, 32]
        assert 8.0 < r1 < 32.0, f"{body}: ratio {r1:.2f}"
        assert 8.0 < r2 < 32.0, f"{body}: ratio {r2:.2f}"


# --- 8b/8c. energy under the recommended rule --------------------------------


@pytest.fixture(scope="module")
def rule_energy(sun_earth_moon):
    """max |dE/E0| over 2*P_EM at dt = P_EM/1000, keyed by integrator."""
    state = sun_earth_moon.state()
    out = {}
    for integrator in ("rk4", "verlet"):
        cfg = make_cfg(DT_RULE, 2.0 * P_EM, integrator=integrator)
        traj = SimulationEngine(cfg).run(state, sample_every=64)
        out[integrator] = float(np.max(relative_energy_error(traj)))
    return out


def test_rk4_energy_at_rule_dt(rule_energy):
    assert rule_energy["rk4"] < 1e-12, f"measured {rule_energy['rk4']:.3e}"


def test_verlet_energy_at_rule_dt(rule_energy):
    # symplectic Verlet has a bounded energy oscillation (Phase-2 bound 1e-8)
    assert rule_energy["verlet"] < 1e-8, f"measured {rule_energy['verlet']:.3e}"


# --- 8d/8e. borrowed Sun-Earth dt is NOT adequate ----------------------------


@pytest.fixture(scope="module")
def borrowed_energy(sun_earth_moon):
    state = sun_earth_moon.state()
    out = {}
    for integrator in ("rk4", "verlet"):
        cfg = make_cfg(DT_BORROWED, 2.0 * P_EM, integrator=integrator)
        traj = SimulationEngine(cfg).run(state, sample_every=4)
        out[integrator] = float(np.max(relative_energy_error(traj)))
    return out


def test_borrowed_dt_degrades_rk4_energy(rule_energy, borrowed_energy):
    # measured ratio 8.69e3 — the borrowed step loses ~4 orders of magnitude
    assert borrowed_energy["rk4"] > 100.0 * rule_energy["rk4"]


def test_borrowed_dt_degrades_verlet_energy(rule_energy, borrowed_energy):
    # measured ratio 1.56e2 — Verlet degrades too, just less dramatically
    assert borrowed_energy["verlet"] > 50.0 * rule_energy["verlet"]


# --- 8f. the period metric alone would have missed this ----------------------


def test_period_is_blind_where_energy_sees(sun_earth_moon):
    state = sun_earth_moon.state()
    cfg = make_cfg(DT_BORROWED, 2.0 * P_EM)
    traj = SimulationEngine(cfg).run(state, sample_every=1)
    rel = relative_state(traj, "Earth", "Moon")
    period_d = angular_period(rel.times, rel.r) / SECONDS_PER_DAY
    assert 26.5 < period_d < 27.6, f"borrowed-dt period {period_d:.4f} d"
    # ...while its energy is already >100x worse (checked in 8d): quoting a
    # plausible-looking period from an under-resolved run proves nothing.


# --- 8g. safety: existing close-encounter guard stays active ----------------


def test_close_encounter_guard_active_for_moon_config(sun_earth_moon):
    state = sun_earth_moon.state()
    # guard above the Earth-Moon distance (3.844e8 m) must trip immediately
    cfg = make_cfg(DT_RULE, 10.0 * DT_RULE, guard_m=4.0e8)
    with pytest.raises(CloseEncounterError):
        SimulationEngine(cfg).run(state, sample_every=1)
    # ...and a sane guard stays silent on the same configuration
    ok = make_cfg(DT_RULE, 10.0 * DT_RULE, guard_m=1.0e6)
    SimulationEngine(ok).run(state, sample_every=5)
