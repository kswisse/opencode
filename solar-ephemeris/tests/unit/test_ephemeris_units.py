"""Unit contract: exact ×1000 conversions with SEPARATE position/velocity goldens.

Golden values recorded once from the identity-verified kernel
(``de440s.bsp``, sha256 ``c1c7feea…0a49f2``, 2026-10-03) via
``spkezr('Earth', 0.0, 'J2000', 'NONE', 'SOLAR SYSTEM BARYCENTER')``:
geometric state at J2000 TDB, native km / km/s.

R2 guard: dropping the position conversion fails the position golden;
dropping the velocity conversion fails the velocity golden (a position
golden cannot catch a velocity-only bug — hence both).
"""

from __future__ import annotations

import numpy as np
import pytest

from solar_ephemeris.ephemeris.types import UnitError
from solar_ephemeris.ephemeris.units import KM_TO_M, from_native

# Recorded from the verified kernel (provenance above).
EARTH_POS_KM_J2000 = np.array(
    [-27566740.482806046, 132361381.15354352, 57418653.286251314]
)
EARTH_VEL_KMS_J2000 = np.array(
    [-29.78494749849545, -5.029753814914289, -2.1806450690318697]
)


def test_km_to_m_is_exact_si_prefix() -> None:
    assert KM_TO_M == 1000.0
    got = from_native([1.0, -2.5, 0.0], native_unit="km")
    assert np.array_equal(got, [1000.0, -2500.0, 0.0])


def test_km_per_s_to_m_per_s_is_exact_separate_path() -> None:
    got = from_native([1.0, -2.5, 0.0], native_unit="km/s")
    assert np.array_equal(got, [1000.0, -2500.0, 0.0])


def test_si_passthrough_copies() -> None:
    src = np.array([1.0, 2.0, 3.0])
    for unit in ("m", "m/s"):
        got = from_native(src, native_unit=unit)
        assert np.array_equal(got, src)
        assert got is not src


def test_unknown_unit_raises_never_infers() -> None:
    with pytest.raises(UnitError, match="unknown native unit"):
        from_native([1.0], native_unit="furlong")
    with pytest.raises(UnitError):
        from_native([1.0], native_unit="")


def test_position_golden_earth_ssb_j2000() -> None:
    # Window [1.46e11, 1.52e11] m: Earth near perihelion at J2000 (measured
    # 1.4688894e11 m). If the km->m conversion were deleted, this would read
    # 1.46889e8 m and fail.
    pos_m = from_native(EARTH_POS_KM_J2000, native_unit="km")
    r = float(np.linalg.norm(pos_m))
    assert 1.46e11 <= r <= 1.52e11, f"|r| = {r!r} m outside golden window"


def test_velocity_golden_earth_ssb_j2000() -> None:
    # Window [29000, 31000] m/s: Earth speed near perihelion (measured
    # 30285.26 m/s). A missing velocity conversion gives 30.29 m/s and fails
    # — independent of the position golden.
    vel_ms = from_native(EARTH_VEL_KMS_J2000, native_unit="km/s")
    speed = float(np.linalg.norm(vel_ms))
    assert 29000.0 <= speed <= 31000.0, f"|v| = {speed!r} m/s outside golden window"


def test_conversion_is_exact_not_approximate() -> None:
    value = 149597870.70000002  # 1 AU in km (stored value)
    assert from_native([value], native_unit="km")[0] == value * 1000.0
