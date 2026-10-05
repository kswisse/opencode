"""Model initial conditions (Phase 3): Sun-Earth-Moon + generic circular
two-body, as constructor-built ICs — never hard-coded acceleration hacks.

Scope honesty (docs/methodology/phase3-earth-moon.md):

- These are SYNTHETIC, self-consistent-to-monopole-order initial conditions at
  a J2000 label epoch, NOT a real DE440 state vector. Phase 3 demonstrates the
  physics model; it does not validate against JPL (that is Phase 4).
- Sun-Earth-Moon construction:
    1. Earth+Moon barycentre (EMB) is placed on an exact two-body circular
       orbit about the Sun with Omega = sqrt((GM_S + GM_EM) / R^3).
    2. Earth and Moon are split about the EMB with the exact two-body circular
       mutual rate omega_EM = sqrt(GM_EM / a^3), positions/velocities weighted
       by GM (inverse-mass weighting, the GM-only mass analogue).
    3. The Sun row is recomputed from the split so that the total GM-weighted
       centre of mass is zero to floating-point accuracy in THIS frame.
- The Sun-Earth-Moon solution is not closed-form: the solar tidal term
  (~1.1 % of the mutual acceleration at a = 3.844e8 m) makes the initial
  condition deviate immediately, producing bounded epicyclic breathing inside
  the Hill sphere (~1.5e9 m). That is physics, not a defect.

Alignment note: all builders put body 1 on +x with +y velocity (the
``make_circular_orbit`` convention of tests/conftest.py), so Model A and Model
B runs share one orientation and one barycentric origin up to O(GM_M/GM_S *
a) ~ 1.3 m — quantified in the perturbation tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.constants import (
    AU_M,
    GM_EARTH,
    GM_EARTH_MOON_BARYCENTER,
    GM_MOON,
    GM_SUN,
    JD_J2000,
)
from solar_ephemeris.physics.state import State, StateMeta

#: Mean Earth-Moon distance used as the PHASE-3 MODEL PARAMETER (m).
#: Not a DE440 state: Phase 3 proves the model, Phase 4 ingests real states.
EARTH_MOON_DISTANCE_M: float = 3.844e8


def _barycentric_meta(origin: str, epoch_jd: float) -> StateMeta:
    return StateMeta(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin=origin,
        epoch_jd=epoch_jd,
        time_scale=TimeScale.TDB,
    )


@dataclass(frozen=True, slots=True)
class CircularTwoBodyIC:
    """Exact two-body circular IC with caller-chosen body names."""

    positions: NDArray[np.float64]  # (2, 3), m
    velocities: NDArray[np.float64]  # (2, 3), m/s
    body_names: tuple[str, str]
    gm: NDArray[np.float64]  # (2,)
    omega: float  # rad/s, orbital angular rate
    period: float  # s
    separation: float  # m

    def state(self, *, epoch_jd: float = JD_J2000) -> State:
        return State(
            positions=self.positions,
            velocities=self.velocities,
            body_names=self.body_names,
            meta=_barycentric_meta(
                f"barycenter({self.body_names[0]}, {self.body_names[1]})",
                epoch_jd,
            ),
        )


def make_circular_two_body_ic(
    gm1: float,
    gm2: float,
    separation: float,
    *,
    names: tuple[str, str] = ("body1", "body2"),
) -> CircularTwoBodyIC:
    """Mirror of the tests/conftest ``make_circular_orbit`` math, in source,
    with caller-chosen names (needed for Model A runs: ("Sun", "Earth") or
    ("Sun", "EMB"))."""
    if not (separation > 0.0 and gm1 > 0.0 and gm2 > 0.0):
        raise ValueError("gm1, gm2 and separation must all be > 0")
    if names[0] == names[1]:
        raise ValueError(f"body names must differ, got {names!r}")
    total = gm1 + gm2
    omega = float(np.sqrt(total / separation**3))
    period = float(2.0 * np.pi / omega)
    r1 = gm2 / total * separation
    r2 = gm1 / total * separation
    positions = np.array([[r1, 0.0, 0.0], [-r2, 0.0, 0.0]], dtype=np.float64)
    velocities = np.array(
        [[0.0, omega * r1, 0.0], [0.0, -omega * r2, 0.0]], dtype=np.float64
    )
    return CircularTwoBodyIC(
        positions=positions,
        velocities=velocities,
        body_names=names,
        gm=np.array([gm1, gm2], dtype=np.float64),
        omega=omega,
        period=period,
        separation=float(separation),
    )


@dataclass(frozen=True, slots=True)
class SunEarthMoonIC:
    """Three-body IC: Sun, Earth, Moon (see module docstring, steps 1-3)."""

    positions: NDArray[np.float64]  # (3, 3), m — order: Sun, Earth, Moon
    velocities: NDArray[np.float64]  # (3, 3), m/s
    body_names: tuple[str, str, str] = ("Sun", "Earth", "Moon")
    gm: NDArray[np.float64] = field(
        default_factory=lambda: np.array([GM_SUN, GM_EARTH, GM_MOON], dtype=np.float64)
    )
    omega_emb: float = 0.0  # heliocentric rate of the EMB, rad/s
    omega_em: float = 0.0  # mutual Earth-Moon rate, rad/s
    separation: float = 0.0  # Sun-EMB distance R, m
    moon_distance: float = 0.0  # modelled Earth-Moon distance a, m

    @property
    def period_emb(self) -> float:
        return float(2.0 * np.pi / self.omega_emb)

    @property
    def period_em(self) -> float:
        return float(2.0 * np.pi / self.omega_em)

    @property
    def origin(self) -> str:
        return "barycenter(Sun, Earth, Moon)"

    def state(self, *, epoch_jd: float = JD_J2000) -> State:
        return State(
            positions=self.positions,
            velocities=self.velocities,
            body_names=self.body_names,
            meta=_barycentric_meta(self.origin, epoch_jd),
        )


def make_sun_earth_moon_ic(
    *,
    moon_distance: float = EARTH_MOON_DISTANCE_M,
    separation: float = AU_M,
) -> SunEarthMoonIC:
    if not (moon_distance > 0.0 and separation > 0.0):
        raise ValueError("moon_distance and separation must be > 0")
    gm_em = GM_EARTH_MOON_BARYCENTER
    total = GM_SUN + gm_em
    omega_emb = float(np.sqrt(total / separation**3))
    omega_em = float(np.sqrt(gm_em / moon_distance**3))

    # Step 1: EMB circular orbit, Sun/EMB split (two-body convention).
    r_sun1 = gm_em / total * separation
    r_emb2 = GM_SUN / total * separation
    r_sun = np.array([r_sun1, 0.0, 0.0])
    v_sun = np.array([0.0, omega_emb * r_sun1, 0.0])
    r_emb = np.array([-r_emb2, 0.0, 0.0])
    v_emb = np.array([0.0, -omega_emb * r_emb2, 0.0])

    # Step 2: split Earth/Moon about the EMB (GM = inverse-mass weighting).
    d0 = np.array([moon_distance, 0.0, 0.0])
    d_dot = np.array([0.0, omega_em * moon_distance, 0.0])
    f_m = GM_MOON / gm_em
    f_e = GM_EARTH / gm_em
    r_earth = r_emb - f_m * d0
    r_moon = r_emb + f_e * d0
    v_earth = v_emb - f_m * d_dot
    v_moon = v_emb + f_e * d_dot

    # Step 3: recompute the Sun row from the split => total COM = 0 exactly
    # (to rounding). Algebraically identical to step 1; done on the split so
    # the invariant holds for whatever the split produced.
    r_sun = -(GM_EARTH * r_earth + GM_MOON * r_moon) / GM_SUN
    v_sun = -(GM_EARTH * v_earth + GM_MOON * v_moon) / GM_SUN

    positions = np.stack([r_sun, r_earth, r_moon])
    velocities = np.stack([v_sun, v_earth, v_moon])
    return SunEarthMoonIC(
        positions=positions,
        velocities=velocities,
        gm=np.array([GM_SUN, GM_EARTH, GM_MOON], dtype=np.float64),
        omega_emb=omega_emb,
        omega_em=omega_em,
        separation=float(separation),
        moon_distance=float(moon_distance),
    )
