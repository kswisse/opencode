"""Physical and astronomical constants.

Unit policy: EVERY constant here carries its unit in the name or docstring.
Gravity code uses GM only (see docs/methodology/units-and-frames.md, section 2);
G appears solely in :func:`mass_from_gm`.

Sources
-------
- G, c: CODATA 2018 / SI definition (exact).
- AU: IAU 2012 resolution B2 (exact).
- GM values: JPL DE440, Park et al. (2021), AJ 161:105, Table 2
  "Planetary Masses Used in DE440 and DE441" (published in km^3/s^2,
  converted here to m^3/s^2 by multiplying by 1e9).
"""

from __future__ import annotations

from typing import Final

# --- Fundamental constants (SI) ---
G_SI: Final[float] = 6.67430e-11  # m^3 kg^-1 s^-2, CODATA 2018
C_SI: Final[float] = 299792458.0  # m/s, exact (SI definition)
AU_M: Final[float] = 149597870700.0  # m, exact (IAU 2012 B2)
SECONDS_PER_DAY: Final[float] = 86400.0  # s/day, exact
JD_J2000: Final[float] = 2451545.0  # Julian days at J2000.0 (TDB/TT neutral label)

# --- Gravitational parameters GM (m^3/s^2) ---
# Source for all: DE440, Park et al. (2021), Table 2 (km^3/s^2 x 1e9).
# NOTE: "Earth" is the solid-Earth+atmosphere value 398600.435507 km^3/s^2.
# The quantity 403503.235625 km^3/s^2 is GM_EARTH + GM_MOON (the Earth-Moon
# barycenter); do NOT use it as GM_Earth.
GM_SUN: Final[float] = 1.3271244004127942e20  # 132712440041.279419 km^3/s^2
GM_MERCURY: Final[float] = 2.2031868551e13  # 22031.868551 km^3/s^2
GM_VENUS: Final[float] = 3.24858592000e14  # 324858.592000 km^3/s^2
GM_EARTH: Final[float] = 3.98600435507e14  # 398600.435507 km^3/s^2
GM_MOON: Final[float] = 4.902800118e12  # 4902.800118 km^3/s^2
GM_MARS: Final[float] = 4.2828375816e13  # 42828.375816 km^3/s^2 (Mars system)
GM_JUPITER: Final[float] = 1.267127641e17  # 126712764.100000 km^3/s^2 (system)
GM_SATURN: Final[float] = 3.79405848418e16  # 37940584.841800 km^3/s^2 (system)
GM_URANUS: Final[float] = 5.7945564e15  # 5794556.400000 km^3/s^2 (system)
GM_NEPTUNE: Final[float] = 6.83652710058e15  # 6836527.100580 km^3/s^2 (system)
GM_PLUTO: Final[float] = 9.755e11  # 975.500000 km^3/s^2 (system)

GM_EARTH_MOON_BARYCENTER: Final[float] = (
    GM_EARTH + GM_MOON
)  # 403503.235625e9 m^3/s^2 — derived, NOT a DE440 table entry itself

#: Body name -> GM (m^3/s^2). Order is alphabetical-free: canonical registry order.
GM_BY_BODY: Final[dict[str, float]] = {
    "Sun": GM_SUN,
    "Mercury": GM_MERCURY,
    "Venus": GM_VENUS,
    "Earth": GM_EARTH,
    "Moon": GM_MOON,
    "Mars": GM_MARS,
    "Jupiter": GM_JUPITER,
    "Saturn": GM_SATURN,
    "Uranus": GM_URANUS,
    "Neptune": GM_NEPTUNE,
    "Pluto": GM_PLUTO,
}

#: Body name -> provenance string. Enforced by tests/unit/test_constants.py:
#: every key in GM_BY_BODY must appear here with a non-empty source.
GM_SOURCES: Final[dict[str, str]] = {
    "Sun": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Sun)",
    "Mercury": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Mercury; Konopliv et al. 2020)",
    "Venus": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Venus; Konopliv et al. 1999)",
    "Earth": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Earth, estimated from DE440)",
    "Moon": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Moon, estimated from DE440)",
    "Mars": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Mars System; Konopliv et al. 2016)",
    "Jupiter": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Jupiter System; SSD JPL 2020)",
    "Saturn": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Saturn System; SSD JPL 2020)",
    "Uranus": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Uranus System; Jacobson 2014)",
    "Neptune": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Neptune System; Jacobson 2009)",
    "Pluto": "DE440, Park et al. (2021), AJ 161:105, Table 2 (GM Pluto System; Brozovic et al. 2015)",
}


def mass_from_gm(gm: float) -> float:
    """kg — mass equivalent of a gravitational parameter.

    ONLY for energy/momentum bookkeeping that needs mass. Never feed the result
    back into gravity as ``G * m``: DE440 GM values and CODATA G are not a
    self-consistent pair (mixing them injects a ppm-level systematic error).
    """
    return gm / G_SI


def days_to_s(days: float) -> float:
    return days * SECONDS_PER_DAY


def s_to_days(seconds: float) -> float:
    return seconds / SECONDS_PER_DAY
