"""Record the reference fixture from the identity-verified DE440 kernel.

Run ONCE after installing the kernel (Gate A setup, documented in
docs/methodology/phase4-jpl-validation.md)::

    python tools/record_reference_fixture.py

Sequence (identity before data):
1. verify_kernel() against the pinned manifest (sha256/md5/size) — a
   substituted kernel can never be recorded;
2. spkobj / spkcov cross-checked against the manifest;
3. independent golden probe at J2000 (Earth-Sun distance, Earth speed,
   Earth-Moon distance must sit in textbook windows) — recorded states are
   validated against values that do NOT come from this pipeline;
4. daily sample grid, et = -1 d .. +10 d around J2000, for every mapped
   body, via spkezr(target, et, 'J2000', 'NONE', 'SOLAR SYSTEM BARYCENTER')
   (geometric states, no light-time/stellar aberration);
5. JSON written with full ReferenceMetadata provenance.

The script fails hard at every mismatch — there is no "record anyway" path.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import spiceypy as sp  # noqa: E402  (tools/ is outside the src import boundary)

from solar_ephemeris import __version__  # noqa: E402
from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST, verify_kernel  # noqa: E402
from solar_ephemeris.ephemeris.mapping import BODY_TO_NAIF, naif_id  # noqa: E402
from solar_ephemeris.ephemeris.types import Coverage, ReferenceMetadata  # noqa: E402
from solar_ephemeris.ephemeris.fixture_backend import (  # noqa: E402
    EXPECTED_REQUEST,
    FIXTURE_SCHEMA_VERSION,
)

DAY = 86400.0
GRID_ET = [(-1 + k) * DAY for k in range(12)]  # -1 d .. +10 d around J2000

# Independent textbook windows (NOT derived from this pipeline) used as the
# recording-time golden probe.
GOLDEN_R_EARTH_SUN_M = (1.46e11, 1.52e11)  # near perihelion at J2000
GOLDEN_V_EARTH_MS = (29000.0, 31000.0)  # ~30.29 km/s near perihelion
GOLDEN_R_EARTH_MOON_M = (3.56e8, 4.07e8)  # lunar distance range


def _vec(values) -> list[float]:
    return [float(x) for x in values]


def record(kernel: Path, out: Path) -> None:
    verify_kernel(kernel, DE440S_MANIFEST)  # identity gate (requirement 1)
    sp.furnsh(str(kernel))

    body_ids = tuple(sorted(int(i) for i in sp.spkobj(str(kernel))))
    if body_ids != tuple(sorted(DE440S_MANIFEST.body_ids)):
        raise SystemExit(f"spkobj {body_ids} != manifest {DE440S_MANIFEST.body_ids}")

    cov_cell = sp.spkcov(str(kernel), 399)
    measured = [float(cov_cell[i]) for i in range(cov_cell.card)]
    if measured != list(DE440S_MANIFEST.coverage_et):
        raise SystemExit(f"spkcov {measured} != manifest {list(DE440S_MANIFEST.coverage_et)}")

    # Golden probe at J2000, independent of the recorded grid.
    # NOTE: query by explicit NAIF IDs, never by SPICE names — SPICE resolves
    # the NAME "Jupiter" to 599 (absent from this kernel), while our mapping
    # targets 5 (system barycentre). This is the requirement-5 trap live.
    earth, _ = sp.spkezr(str(naif_id("Earth")), 0.0, "J2000", "NONE", "SOLAR SYSTEM BARYCENTER")
    moon_e, _ = sp.spkezr(str(naif_id("Moon")), 0.0, "J2000", "NONE", str(naif_id("Earth")))
    r_es = math.sqrt(sum(float(x) ** 2 for x in earth[:3])) * 1000.0
    v_e = math.sqrt(sum(float(x) ** 2 for x in earth[3:])) * 1000.0
    r_em = math.sqrt(sum(float(x) ** 2 for x in moon_e[:3])) * 1000.0
    for label, value, window in (
        ("|Earth-SSB|", r_es, GOLDEN_R_EARTH_SUN_M),
        ("|v_Earth|", v_e, GOLDEN_V_EARTH_MS),
        ("|Moon-Earth|", r_em, GOLDEN_R_EARTH_MOON_M),
    ):
        if not window[0] <= value <= window[1]:
            raise SystemExit(f"golden probe failed: {label}={value} outside {window}")

    provenance = ReferenceMetadata(
        reference_name=DE440S_MANIFEST.reference_name,
        reference_version=DE440S_MANIFEST.reference_version,
        source=(
            f"{DE440S_MANIFEST.source_citation}; fixture recorded 2026-10-03 via "
            f"spiceypy {sp.__version__} (tools/record_reference_fixture.py; "
            "spkezr J2000/NONE/SOLAR SYSTEM BARYCENTER, daily grid -1d..+10d)"
        ),
        kernel_filename=DE440S_MANIFEST.filename,
        kernel_md5=DE440S_MANIFEST.md5,
        kernel_sha256=DE440S_MANIFEST.sha256,
        size_bytes=DE440S_MANIFEST.size_bytes,
        retrieval_date=DE440S_MANIFEST.retrieval_date,
        kernel_coverage=Coverage(intervals=(DE440S_MANIFEST.coverage_et,)),
        body_ids=body_ids,
        reference_frame="J2000",
        reference_center=0,
        time_standard="TDB — SPICE ephemeris time, s past J2000 TDB",
        native_position_unit="km",
        native_velocity_unit="km/s",
        spice_version=sp.__version__,
        software_version=__version__,
    )

    names = sorted(BODY_TO_NAIF)
    samples = []
    for et in GRID_ET:
        states: dict[str, dict[str, list[float]]] = {}
        for name in names:
            # Explicit NAIF ID as target (see golden-probe note): SPICE names
            # would resolve Mars..Pluto to absent planet-center IDs 499..999.
            state, _lt = sp.spkezr(
                str(naif_id(name)), et, EXPECTED_REQUEST["frame"],
                EXPECTED_REQUEST["abcorr"], EXPECTED_REQUEST["center"],
            )
            states[name] = {"pos": _vec(state[:3]), "vel": _vec(state[3:])}
        samples.append({"et": et, "states": states})
        print(f"  recorded et={et:+.0f} ({len(names)} bodies)")

    payload = {
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "provenance": provenance.to_dict(),
        "request": dict(EXPECTED_REQUEST),
        "bodies": names,
        "samples": samples,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(samples)} samples x {len(names)} bodies)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", type=Path, default=Path("kernels/de440s.bsp"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("tests/fixtures/reference/de440s_recorded.json"),
    )
    args = parser.parse_args()
    record(args.kernel, args.out)


if __name__ == "__main__":
    main()
