"""Time contract: exact J2000 anchor, ULP round-trip, TDB-only, no per-sample JD."""

from __future__ import annotations

import math

import numpy as np
import pytest

from solar_ephemeris.ephemeris.time import (
    JD_J2000_TDB,
    et_to_jd_tdb,
    jd_tdb_to_et,
    require_tdb,
    sample_epochs_et,
)
from solar_ephemeris.ephemeris.types import TimeScaleMismatchError
from solar_ephemeris.frames.identifiers import TimeScale
from solar_ephemeris.physics.constants import JD_J2000, SECONDS_PER_DAY

# Candidate epochs: J2000, the pinned kernel's coverage boundaries, and an
# arbitrary non-half-day JD (exercises rounding, not just exact halves).
ROUND_TRIP_CANDIDATES = [2396752.5, 2451544.5, 2451545.0, 2451545.5, 2460000.123457]


def test_j2000_anchors_exactly_zero() -> None:
    assert JD_J2000_TDB == JD_J2000 == 2451545.0
    assert jd_tdb_to_et(2451545.0) == 0.0
    assert et_to_jd_tdb(0.0) == 2451545.0


def test_one_day_offset_is_exact() -> None:
    assert jd_tdb_to_et(2451546.0) == SECONDS_PER_DAY
    assert jd_tdb_to_et(2451544.0) == -SECONDS_PER_DAY


@pytest.mark.parametrize("jd", ROUND_TRIP_CANDIDATES)
def test_round_trip_within_one_ulp(jd: float) -> None:
    # Precision contract (time.py docstring): <= 1 ULP at the JD magnitude.
    back = et_to_jd_tdb(jd_tdb_to_et(jd))
    assert abs(back - jd) <= math.ulp(jd), f"{jd!r} -> {back!r} exceeds 1 ULP"


def test_sample_epochs_is_et0_plus_t() -> None:
    epoch = 2451545.0
    times = np.array([0.0, 1.0, 86400.0, 604800.0])
    et0 = jd_tdb_to_et(epoch)
    got = sample_epochs_et(epoch, times)
    assert np.array_equal(got, et0 + times)  # bit-identical, no JD in the loop
    assert got[0] == 0.0


def test_sample_epochs_uses_one_conversion_not_per_sample_jd() -> None:
    # Adding t_s to et0 must differ from a per-sample JD round trip for at
    # least one non-representable sample — proving the loop path is absent.
    epoch = 2451545.0
    t = 12345.6789
    direct = jd_tdb_to_et(epoch) + t
    roundtrip = jd_tdb_to_et(et_to_jd_tdb(direct))
    assert direct != roundtrip  # they differ at ULP level for this sample
    assert sample_epochs_et(epoch, [t])[0] == direct


def test_sample_epochs_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="1-D"):
        sample_epochs_et(2451545.0, np.zeros((2, 2)))
    with pytest.raises(ValueError, match="NaN"):
        sample_epochs_et(2451545.0, [0.0, float("nan")])
    with pytest.raises(ValueError, match="finite"):
        jd_tdb_to_et(float("inf"))


def test_tdb_accepted_others_refused() -> None:
    require_tdb(TimeScale.TDB, context="test")  # must not raise
    for scale in (TimeScale.UTC, TimeScale.TT, TimeScale.SI):
        with pytest.raises(TimeScaleMismatchError, match="not TDB"):
            require_tdb(scale, context="test")
