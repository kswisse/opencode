"""Display-unit helpers for the viz layer - constants come from source modules (R10).

Axes default to SI (m, m/s); AU / km-s^{-1} labels are opt-in through these
helpers. The conversion constants are IMPORTED from their modules of record
(``physics.constants.AU_M``, ``ephemeris.units.KM_TO_M``) - never retyped
here (R10/R11, KTD7). No matplotlib at module import time.
"""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from solar_ephemeris.ephemeris.units import KM_TO_M
from solar_ephemeris.physics.constants import AU_M

#: Unit tokens for axis labels.
M_LABEL: Final[str] = "m"
AU_LABEL: Final[str] = "au"
MS_LABEL: Final[str] = "m/s"
KMS_LABEL: Final[str] = "km/s"

_POSITION_UNITS: Final[tuple[str, ...]] = (M_LABEL, AU_LABEL)
_VELOCITY_UNITS: Final[tuple[str, ...]] = (MS_LABEL, KMS_LABEL)


def m_to_au(values: ArrayLike) -> NDArray[np.float64] | np.float64:
    """metres -> AU (divide by the exact IAU 2012 B2 metre value)."""
    return np.asarray(values, dtype=np.float64) / AU_M


def au_to_m(values: ArrayLike) -> NDArray[np.float64] | np.float64:
    """AU -> metres."""
    return np.asarray(values, dtype=np.float64) * AU_M


def ms_to_kms(values: ArrayLike) -> NDArray[np.float64] | np.float64:
    """m/s -> km/s (the single visible /KM_TO_M factor)."""
    return np.asarray(values, dtype=np.float64) / KM_TO_M


def kms_to_ms(values: ArrayLike) -> NDArray[np.float64] | np.float64:
    """km/s -> m/s."""
    return np.asarray(values, dtype=np.float64) * KM_TO_M


def position_label(unit: str = M_LABEL) -> str:
    """Axis label for a position quantity: ``position (m)`` / ``position (au)``."""
    if unit not in _POSITION_UNITS:
        raise ValueError(f"position unit {unit!r} must be one of {_POSITION_UNITS}")
    return f"position ({unit})"


def velocity_label(unit: str = MS_LABEL) -> str:
    """Axis label for a velocity quantity: ``velocity (m/s)`` / ``velocity (km/s)``."""
    if unit not in _VELOCITY_UNITS:
        raise ValueError(f"velocity unit {unit!r} must be one of {_VELOCITY_UNITS}")
    return f"velocity ({unit})"
