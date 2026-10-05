"""Shared fixtures: circular two-body initial conditions + analytic solution.

CLASSIC BUG GUARD: the orbital angular velocity of a two-body circular orbit
uses the TOTAL gravitational parameter:

    omega = sqrt((GM1 + GM2) / R^3)

Using only GM1 (or putting body 1 at distance R from the barycenter instead of
r1 = GM2/(GM1+GM2)*R) makes the initial conditions NOT an exact solution, which
turns convergence/conservation tests red for the wrong reason.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.bodies import BodyRegistry
from solar_ephemeris.physics.constants import AU_M, GM_EARTH, GM_SUN
from solar_ephemeris.physics.state import State, StateMeta


def barycentric_meta(**over) -> StateMeta:
    base = dict(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin="barycenter(inline)",
        epoch_jd=2451545.0,
        time_scale=TimeScale.SI,
    )
    base.update(over)
    return StateMeta(**base)


def _rotz(theta: float) -> np.ndarray:
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


@dataclass(frozen=True, slots=True)
class CircularOrbitIC:
    """Exact two-body circular orbit in the barycentric frame."""

    gm1: float
    gm2: float
    separation: float  # R, m
    omega: float  # rad/s
    period: float  # s
    positions0: np.ndarray  # (2, 3), m
    velocities0: np.ndarray  # (2, 3), m/s

    @property
    def gm(self) -> np.ndarray:
        return np.array([self.gm1, self.gm2], dtype=np.float64)

    @property
    def origin(self) -> str:
        return "barycenter(body1, body2)"

    def state_at(self, t: float, *, epoch_jd: float = 2451545.0) -> State:
        """Analytic solution: rigid rotation of the initial configuration."""
        rot = _rotz(self.omega * t)
        return State(
            positions=(rot @ self.positions0.T).T,
            velocities=(rot @ self.velocities0.T).T,
            body_names=("body1", "body2"),
            meta=barycentric_meta(origin=self.origin, epoch_jd=epoch_jd),
        )

    def exact_at(self, t: float) -> tuple[np.ndarray, np.ndarray]:
        rot = _rotz(self.omega * t)
        return (rot @ self.positions0.T).T, (rot @ self.velocities0.T).T


def make_circular_orbit(gm1: float, gm2: float, separation: float) -> CircularOrbitIC:
    total = gm1 + gm2
    omega = np.sqrt(total / separation**3)
    period = 2.0 * np.pi / omega
    r1 = gm2 / total * separation
    r2 = gm1 / total * separation
    pos0 = np.array(
        [[r1, 0.0, 0.0], [-r2, 0.0, 0.0]],
        dtype=np.float64,
    )
    vel0 = np.array(
        [[0.0, omega * r1, 0.0], [0.0, -omega * r2, 0.0]],
        dtype=np.float64,
    )
    return CircularOrbitIC(
        gm1=gm1,
        gm2=gm2,
        separation=separation,
        omega=float(omega),
        period=float(period),
        positions0=pos0,
        velocities0=vel0,
    )


@pytest.fixture
def registry() -> BodyRegistry:
    return BodyRegistry.default()


@pytest.fixture
def circular_orbit():
    """Factory: circular_orbit(gm1, gm2, R) -> CircularOrbitIC."""
    return make_circular_orbit


@pytest.fixture(scope="session")
def two_body_sun_earth() -> CircularOrbitIC:
    """Sun-Earth circular orbit at 1 AU (synthetic IC, not a real epoch state)."""
    return make_circular_orbit(GM_SUN, GM_EARTH, AU_M)


# --- Phase 3: Sun-Earth-Moon -------------------------------------------------
# IC construction lives in SOURCE (simulation/initial_conditions.py) so the
# perturbation experiments are reproducible outside this file; only the
# fixture exposure is added here.


@pytest.fixture(scope="session")
def sun_earth_moon():
    """Sun-Earth-Moon IC (mutual rate omega_EM, EMB on a circular orbit)."""
    from solar_ephemeris.simulation.initial_conditions import make_sun_earth_moon_ic

    return make_sun_earth_moon_ic()
