"""Phase-3 Moon-perturbation experiment, requirement: "quantify, not eyeball".

Three models on ONE identical sampling grid (same dt/duration/every):

  B        Sun + Earth + Moon, full three-body dynamics (the subject)
  A_naive  Sun + Earth   (Earth's GM only)          — naive baseline
  A_lumped Sun + EMB     (GM_EARTH+GM_MOON lumped)  — apples-to-apples

Outputs are differences of positions of the SAME physical body:

  delta_earth(t) = r_E^B - r_E^A_naive
  delta_emb(t)   = r_EMB^B - r_EMB^A_lumped

Measured (2026-10-01, 60 d RK4, dt = P_EM/1000, every 10th step):
  max |delta_earth|  4.7025e6 m   (= 3.143e-5 AU), final 4.634e6, z == 0
  max |delta_emb|    4584.1 m (= final; mean 1579 m), starts at exactly 0
  max delta_emb/max delta_earth   9.75e-4
  Sun position naive-vs-B at t=0  5526.6 m  (frame/mass-definition offset:
      A_naive puts the Earth where the EMB definition of B puts the EMB,
      a GM_EM-vs-GM_E difference of R*(GM_EM-GM_E)/GM_S ~ 5.5 km — the
      reason A_lumped exists; it is NOT a dynamics signal)
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.analysis import barycenter, trajectory_difference
from solar_ephemeris.physics.bodies import BodyRegistry
from solar_ephemeris.physics.constants import (
    AU_M,
    GM_EARTH,
    GM_EARTH_MOON_BARYCENTER,
    GM_SUN,
    SECONDS_PER_DAY,
)
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine
from solar_ephemeris.simulation.initial_conditions import (
    EARTH_MOON_DISTANCE_M,
    make_circular_two_body_ic,
)

P_EM = 2.0 * np.pi * np.sqrt(EARTH_MOON_DISTANCE_M**3 / GM_EARTH_MOON_BARYCENTER)
DT = P_EM / 1000.0
EPOCH_JD = 2451545.0
DURATION = 60.0 * SECONDS_PER_DAY
SAMPLE_EVERY = 10


def _cfg(bodies: tuple[str, ...]) -> SimulationConfig:
    return SimulationConfig(
        bodies=bodies,
        integrator="rk4",
        dt=DT,
        duration=DURATION,
        epoch_jd=EPOCH_JD,
    )


@pytest.fixture(scope="module")
def models(sun_earth_moon):
    """Run the three models once; every test reads the same results."""
    state_b = sun_earth_moon.state()
    naive_ic = make_circular_two_body_ic(
        GM_SUN, GM_EARTH, AU_M, names=("Sun", "Earth")
    )
    lumped_ic = make_circular_two_body_ic(
        GM_SUN, GM_EARTH_MOON_BARYCENTER, AU_M, names=("Sun", "EMB")
    )
    lumped_registry = BodyRegistry(
        gm_map={"Sun": GM_SUN, "EMB": GM_EARTH_MOON_BARYCENTER}
    )

    b = SimulationEngine(_cfg(("Sun", "Earth", "Moon"))).run(
        state_b, sample_every=SAMPLE_EVERY
    )
    a_naive = SimulationEngine(_cfg(("Sun", "Earth"))).run(
        naive_ic.state(), sample_every=SAMPLE_EVERY
    )
    a_lumped = SimulationEngine(_cfg(("Sun", "EMB")), registry=lumped_registry).run(
        lumped_ic.state(), sample_every=SAMPLE_EVERY
    )
    return b, a_naive, a_lumped


@pytest.fixture(scope="module")
def deltas(models):
    b, a_naive, a_lumped = models
    # both comparisons are same-grid by construction (assert, don't assume)
    assert np.array_equal(b.times, a_naive.times)
    assert np.array_equal(b.times, a_lumped.times)
    t_earth, d_earth = trajectory_difference(b, a_naive, "Earth")
    # Model B has no body named "EMB" — its EMB is the GM-weighted centre
    # of Earth+Moon, differenced against A_lumped's literal EMB row
    emb_b, _ = barycenter(b, ("Earth", "Moon"))
    d_emb = emb_b - a_lumped.positions[:, 1, :]
    return t_earth, d_earth, d_emb


def test_sampling_grids_are_bitwise_identical(models):
    b, a_naive, a_lumped = models
    assert np.array_equal(b.times, a_naive.times)
    assert np.array_equal(b.times, a_lumped.times)
    assert b.n_samples == a_naive.n_samples == a_lumped.n_samples


def test_earth_displacement_is_quantified(deltas):
    _, d_earth, _ = deltas
    norms = np.linalg.norm(d_earth, axis=1)
    peak = float(norms.max())
    assert 4.6e6 < peak < 4.8e6, f"measured {peak:.1f} m"
    assert 2.9e-5 < peak / AU_M < 3.3e-5, f"measured {peak / AU_M:.3e} AU"
    # the signal evolves — it is not a constant frame offset (ptp ~ 6.8e4 m)
    assert np.ptp(norms) > 1e3


def test_earth_displacement_stays_in_the_ecliptic_plane(deltas):
    _, d_earth, _ = deltas
    np.testing.assert_array_equal(d_earth[:, 2], np.zeros(d_earth.shape[0]))


def test_emb_shift_is_two_orders_smaller(deltas):
    _, d_earth, d_emb = deltas
    emb_peak = float(np.linalg.norm(d_emb, axis=1).max())
    earth_peak = float(np.linalg.norm(d_earth, axis=1).max())
    assert emb_peak < 1e4, f"measured {emb_peak:.1f} m"
    assert emb_peak > 100.0, "perturbation must be a real signal, not zero"
    assert emb_peak / earth_peak < 2e-3, f"ratio {emb_peak / earth_peak:.3e}"


def test_lumped_comparison_starts_exactly_aligned(deltas):
    """A_lumped's EMB row IS Model B's EMB row at t=0 (same recipe), so any
    delta_emb growth after t=0 is dynamics, not a misaligned start."""
    _, _, d_emb = deltas
    np.testing.assert_array_equal(d_emb[0], np.zeros(3))


def test_naive_frame_systematic_at_epoch(models):
    """Quantifies why A_naive alone is not enough. The 5.5 km frame/mass
    offset shows up in the SUN row (and between B's EMB and naive's Earth);
    the EARTH row at t=0 instead starts ~4.67e6 m away — the Moon-forced
    wobble of Earth about the EMB (GM_M/GM_EM * a = 4.671e6 m) — so naive
    'Earth' and true Earth are never comparable at face value."""
    b, a_naive, _ = models
    sun_offset = float(
        np.linalg.norm(a_naive.positions[0, 0] - b.positions[0, 0])
    )
    assert 5.0e3 < sun_offset < 6.1e3, f"measured {sun_offset:.1f} m"

    emb_b, _ = barycenter(b, ("Earth", "Moon"))
    # naive's "Earth" sits where a GM_E point mass orbits — i.e. where B's
    # EMB definition puts the EMB, up to the GM_EM-vs-GM_E difference
    emb_offset = float(np.linalg.norm(emb_b[0] - a_naive.positions[0, 1]))
    assert 5.0e3 < emb_offset < 6.1e3, f"measured {emb_offset:.1f} m"

    earth_offset = float(
        np.linalg.norm(a_naive.positions[0, 1] - b.positions[0, 1])
    )
    assert 4.6e6 < earth_offset < 4.7e6, (
        f"measured {earth_offset:.1f} m — expected the Earth-EMB wobble "
        "amplitude 4.671e6 m minus the 5.5 km frame offset"
    )
