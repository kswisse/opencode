"""Recorded-fixture reference backend — kernel-free and spiceypy-free.

Serves reference states from a JSON file recorded ONCE from the
identity-verified kernel by ``tools/record_reference_fixture.py`` (full
provenance inside the file). Two paths:

- query epoch == a recorded sample → stored native km values returned
  bit-exact, then converted by :func:`~solar_ephemeris.ephemeris.units.from_native`;
- interior epoch → cubic Hermite on the sample grid
  (:class:`~solar_ephemeris.ephemeris.interpolation.CubicHermiteInterpolator`),
  still in native units, converted once at the end.

Load is strict: schema, provenance, and the recorded request contract
(frame J2000 / abcorr NONE / center SSB / km, km/s) must all match — a
fixture recorded under different conditions is refused rather than silently
mixed. Missing or corrupt fixtures make tests FAIL, never skip.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.ephemeris.interpolation import CubicHermiteInterpolator
from solar_ephemeris.ephemeris.mapping import BODY_TO_NAIF, naif_id
from solar_ephemeris.ephemeris.time import et_to_jd_tdb
from solar_ephemeris.ephemeris.types import (
    REFERENCE_CENTER_DESC,
    REFERENCE_FRAME,
    Coverage,
    ReferenceMetadata,
    ReferenceState,
)
from solar_ephemeris.ephemeris.units import from_native
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

FIXTURE_SCHEMA_VERSION: Final[int] = 1

#: The request contract under which the fixture was recorded. Any deviation
#: (e.g. light-time-corrected states) invalidates the file — refuse it.
EXPECTED_REQUEST: Final[dict[str, str]] = {
    "frame": "J2000",
    "abcorr": "NONE",
    "center": "SOLAR SYSTEM BARYCENTER",
    "position_unit": "km",
    "velocity_unit": "km/s",
}

#: Default fixture location (repo-relative), recorded once per kernel identity.
def _default_path() -> Path:
    # Path(__file__): src/solar_ephemeris/ephemeris/fixture_backend.py → project root.
    return Path(__file__).resolve().parents[3] / "tests/fixtures/reference/de440s_recorded.json"


class FixtureReference:
    """ReferenceProvider backed by a recorded JSON fixture."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else _default_path()
        if not self._path.is_file():
            raise FileNotFoundError(
                f"reference fixture not found: {self._path} — record it with "
                "python tools/record_reference_fixture.py (a missing fixture is "
                "a failure, never a skip)"
            )
        payload: dict[str, Any] = json.loads(self._path.read_text(encoding="utf-8"))
        self._validate_payload(payload)

        self._metadata = ReferenceMetadata.from_dict(payload["provenance"])
        samples = payload["samples"]
        ets = np.array([float(s["et"]) for s in samples], dtype=np.float64)
        if not np.all(np.diff(ets) > 0.0):
            raise ValueError("fixture samples must be strictly increasing in et")

        body_names = tuple(payload["bodies"])
        for name in body_names:
            naif_id(name)  # fixture keys must be explicitly mapped names
        self._bodies = body_names

        self._ets = ets
        self._pos: dict[str, NDArray[np.float64]] = {}
        self._vel: dict[str, NDArray[np.float64]] = {}
        self._interp: dict[str, CubicHermiteInterpolator] = {}
        for name in body_names:
            pos = np.array([s["states"][name]["pos"] for s in samples], dtype=np.float64)
            vel = np.array([s["states"][name]["vel"] for s in samples], dtype=np.float64)
            if pos.shape != (ets.size, 3) or vel.shape != (ets.size, 3):
                raise ValueError(f"fixture states for {name!r} have wrong shape")
            self._pos[name] = pos
            self._vel[name] = vel
            self._interp[name] = CubicHermiteInterpolator(ets, pos, vel)

        # Fixture coverage = recorded sample domain (closed), distinct from
        # ReferenceMetadata.kernel_coverage (the full kernel window).
        self._coverage = Coverage(intervals=((float(ets[0]), float(ets[-1])),))

    @staticmethod
    def _validate_payload(payload: dict[str, Any]) -> None:
        version = payload.get("schema_version")
        if version != FIXTURE_SCHEMA_VERSION:
            raise ValueError(
                f"fixture schema_version {version!r} != {FIXTURE_SCHEMA_VERSION}"
            )
        request = payload.get("request", {})
        for key, expected in EXPECTED_REQUEST.items():
            got = request.get(key)
            if got != expected:
                raise ValueError(
                    f"fixture recorded under request {key}={got!r}, expected "
                    f"{expected!r}; refusing to mix reference conditions"
                )
        missing = {"bodies", "provenance", "samples"} - set(payload)
        if missing:
            raise ValueError(f"fixture missing keys: {sorted(missing)}")
        if len(payload["samples"]) < 2:
            raise ValueError("fixture needs >= 2 samples for interpolation")

    @property
    def metadata(self) -> ReferenceMetadata:
        return self._metadata

    @property
    def coverage(self) -> Coverage:
        return self._coverage

    @property
    def bodies(self) -> tuple[str, ...]:
        return self._bodies

    @property
    def path(self) -> Path:
        return self._path

    def state_at(self, *, body: str, et: float) -> ReferenceState:
        """State at an exact ephemeris time (validated by the get_state façade;
        coverage is re-checked here so direct calls stay safe too)."""
        naif_id(body)  # UnknownBodyMappingError if the fixture uses unmapped names
        if body not in self._interp:
            raise ValueError(
                f"body {body!r} is mapped but absent from fixture {self._path.name}; "
                "re-record with tools/record_reference_fixture.py"
            )
        self._coverage.require_contains(et)
        pos_km, vel_kms = self._interp[body].evaluate(et)
        return ReferenceState(
            body=body,
            naif_id=naif_id(body),
            epoch_jd=et_to_jd_tdb(et),
            frame=ReferenceFrame.SSB_ICRS,
            center=REFERENCE_CENTER_DESC,
            time_scale=TimeScale.TDB,
            position_m=from_native(pos_km, native_unit="km"),
            velocity_ms=from_native(vel_kms, native_unit="km/s"),
            provenance=self._metadata,
        )
