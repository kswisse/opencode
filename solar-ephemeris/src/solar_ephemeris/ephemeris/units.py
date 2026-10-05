"""Unit normalization from SPICE-native units — conversion kept visible.

SPK standard output is km / km/s (NAIF SPK docs); the project is SI
(m, m/s) everywhere. The ×1000 factor appears exactly once, here, as an
explicit multiplication by :data:`KM_TO_M` — never inferred from variable
names, never implicit (requirement 9; risk R2).

Deleting either conversion line must turn a test red: positions and
velocities are golden-checked separately, because a position golden cannot
catch a velocity-only bug.
"""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from solar_ephemeris.ephemeris.types import UnitError

#: Exact SI prefix: 1 km = 1000 m.
KM_TO_M: Final[float] = 1000.0

_KM_POSITION: Final[str] = "km"
_KM_VELOCITY: Final[str] = "km/s"
_M_POSITION: Final[str] = "m"
_M_VELOCITY: Final[str] = "m/s"


def from_native(values: ArrayLike, *, native_unit: str) -> NDArray[np.float64]:
    """Convert an array declared in ``native_unit`` to project SI units.

    ``native_unit`` must be stated by the caller (the backend contract);
    unknown units raise :class:`UnitError` instead of being guessed.
    """
    arr = np.asarray(values, dtype=np.float64)
    if native_unit in (_KM_POSITION, _KM_VELOCITY):
        return arr * KM_TO_M  # THE visible ×1000 conversion (positions AND velocities)
    if native_unit in (_M_POSITION, _M_VELOCITY):
        return arr.copy()
    raise UnitError(
        f"unknown native unit {native_unit!r}; expected one of "
        f"{(_KM_POSITION, _KM_VELOCITY, _M_POSITION, _M_VELOCITY)}"
    )
