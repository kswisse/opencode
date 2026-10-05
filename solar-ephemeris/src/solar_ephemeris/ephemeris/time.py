"""TDB time contract: representation change only, no timescale conversion.

Both endpoints of this pipeline are TDB (project default; SPICE ephemeris
time is TDB seconds past J2000), so the ONLY operation ever needed is a
Julian-date ↔ seconds representation change::

    et = (epoch_jd − 2451545.0) × 86400.0

No ΔT, no leap seconds, no TT−TDB: none exist between TDB and TDB, and no
calendar/UTC string parsing happens anywhere in Phase 4 (``str2et``-style
paths are deliberately avoided — SPICE needs a leap-second kernel for those;
we never load one).

Precision contract (R9): float64 ULP at 2451545.0 ≈ 4.03e-5 s. That
quantization is applied ONCE — when the single config epoch is converted —
and identically to both sides of a comparison, hence common-mode and
invisible to E_pos/E_vel. Query epochs are always built as
``et0 + t_s`` (:func:`sample_epochs_et`); no per-sample JD round trip feeds
a query. Any per-sample ``epoch_jd`` on a :class:`ReferenceState` is display
metadata derived from that exact ``et``, never an input to it.

Non-TDB callers are REFUSED (:func:`require_tdb`), never converted: time-scale
conversion is deliberately unimplemented (units-and-frames.md).
"""

from __future__ import annotations

from typing import Final

import numpy as np
from numpy.typing import ArrayLike, NDArray

from solar_ephemeris.ephemeris.types import TimeScaleMismatchError
from solar_ephemeris.frames.identifiers import TimeScale
from solar_ephemeris.physics.constants import JD_J2000, SECONDS_PER_DAY

#: Julian date of J2000.0 in TDB — the one epoch origin of the pipeline.
JD_J2000_TDB: Final[float] = JD_J2000  # 2451545.0 = 2000-01-01 12:00 TDB


def jd_tdb_to_et(epoch_jd: float) -> float:
    """TDB Julian date → SPICE ephemeris time (TDB s past J2000).

    Representation change ONLY — see module docstring. Exact at J2000:
    ``jd_tdb_to_et(2451545.0) == 0.0``.
    """
    if not np.isfinite(epoch_jd):
        raise ValueError(f"epoch_jd must be finite, got {epoch_jd!r}")
    return (epoch_jd - JD_J2000_TDB) * SECONDS_PER_DAY


def et_to_jd_tdb(et: float) -> float:
    """SPICE ephemeris time → TDB Julian date (display/provenance metadata).

    Never feed the result back into a query — see module docstring (R9).
    """
    if not np.isfinite(et):
        raise ValueError(f"et must be finite, got {et!r}")
    return et / SECONDS_PER_DAY + JD_J2000_TDB


def sample_epochs_et(epoch_jd: float, times_s: ArrayLike) -> NDArray[np.float64]:
    """Query epochs for a model sampling grid: ``et0 + t_s``, computed once.

    ``et0`` comes from the single config epoch; sample times are ADDED in
    seconds. There is deliberately no path that converts each sample to JD
    and back (per-sample float64-JD quantization ≈ 4.03e-5 s ≈ up to 1.2 m
    of Earth position would then be reintroduced).
    """
    times = np.asarray(times_s, dtype=np.float64)
    if times.ndim != 1:
        raise ValueError(f"times_s must be 1-D, got shape {times.shape}")
    if not np.all(np.isfinite(times)):
        raise ValueError("times_s contains NaN/inf")
    et0 = jd_tdb_to_et(epoch_jd)
    return et0 + times


def require_tdb(time_scale: TimeScale, *, context: str) -> None:
    """Refuse any non-TDB time scale (conversion is unimplemented by design)."""
    if time_scale is not TimeScale.TDB:
        raise TimeScaleMismatchError(
            f"{context}: time_scale {time_scale!r} is not TDB; the reference "
            "pipeline converts nothing — supply TDB (units-and-frames.md)"
        )
