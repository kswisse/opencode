"""Live DE440 ingestion — the ONLY module allowed to import spiceypy.

Enforced by an AST test (``tests/unit/test_import_boundaries.py``): any
other file importing ``spiceypy``/``cspice`` fails the suite.

Identity before data (requirement 1): construction runs ``verify_kernel``
(exists → size → MD5 → SHA-256), then ``spkobj`` and ``spkcov`` are
cross-checked against the pinned manifest — a substituted, truncated, or
wrong-solution kernel fails here, before any state is queried.

Time (requirement 7, plan §7): epochs are computed by the project
(``jd_tdb_to_et``) and handed to SPICE as float ET seconds — no time
strings, no ``str2et``, no leap-second kernel. TDB in, TDB out; the
``ktotal("leapseconds") == 0`` test proves no LSK is ever needed.

Query contract: ``spkezr(str(naif_id), et, "J2000", "NONE",
"SOLAR SYSTEM BARYCENTER")`` — explicit NAIF IDs (the SPICE *name*
"Jupiter" resolves to absent planet-centre 599 on this kernel — measured
trap during recording), geometric states (no light-time/aberration), native
km/km/s converted through ``units.from_native`` (the ×1000 is visible in
this file).
"""

from __future__ import annotations

from pathlib import Path

import spiceypy as sp

from solar_ephemeris import __version__
from solar_ephemeris.ephemeris.kernel_manifest import (
    DE440S_MANIFEST,
    KernelManifest,
    verify_kernel,
)
from solar_ephemeris.ephemeris.mapping import naif_id
from solar_ephemeris.ephemeris.time import et_to_jd_tdb
from solar_ephemeris.ephemeris.types import (
    Coverage,
    KernelIntegrityError,
    ReferenceMetadata,
    ReferenceState,
)
from solar_ephemeris.ephemeris.units import from_native
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

#: SPICE query constants (geometric, J2000, SSB) — the recorded fixture was
#: captured under exactly these conditions (fixture request block).
QUERY_FRAME = "J2000"
QUERY_ABERRATION = "NONE"
QUERY_OBSERVER = "SOLAR SYSTEM BARYCENTER"


class SpiceReference:
    """``ReferenceProvider`` over a live, identity-verified DE440 SPK."""

    def __init__(
        self, kernel_path: Path | str, manifest: KernelManifest = DE440S_MANIFEST
    ) -> None:
        path = Path(kernel_path)
        verify_kernel(path, manifest)  # KernelIntegrityError + retrieval hint

        sp.furnsh(str(path))  # global CSPICE pool; idempotent per path
        try:
            ids = tuple(sorted(int(i) for i in sp.spkobj(str(path))))
            expected = tuple(sorted(manifest.body_ids))
            if ids != expected:
                raise KernelIntegrityError(
                    f"spkobj body ids {ids} != manifest {expected} for {path.name}"
                )
            lo, hi = self._union_coverage(path, manifest)
            if (lo, hi) != manifest.coverage_et:
                raise KernelIntegrityError(
                    f"spkcov coverage {(lo, hi)} != manifest "
                    f"{manifest.coverage_et} for {path.name}"
                )
        except KernelIntegrityError:
            sp.unload(str(path))  # do not leave a rejected file in the pool
            raise

        self._path = path
        self._coverage = Coverage(intervals=((lo, hi),))
        self._metadata = ReferenceMetadata(
            reference_name=manifest.reference_name,
            reference_version=manifest.reference_version,
            source=(
                f"{manifest.source_citation}; live query via spiceypy "
                "(ephemeris/spice_backend.py)"
            ),
            kernel_filename=manifest.filename,
            kernel_md5=manifest.md5,
            kernel_sha256=manifest.sha256,
            size_bytes=manifest.size_bytes,
            retrieval_date=manifest.retrieval_date,
            kernel_coverage=self._coverage,
            body_ids=ids,
            reference_frame=QUERY_FRAME,
            reference_center=0,
            time_standard="TDB — SPICE ephemeris time, s past J2000 TDB",
            native_position_unit="km",
            native_velocity_unit="km/s",
            spice_version=sp.__version__,
            software_version=__version__,
        )

    @staticmethod
    def _union_coverage(
        path: Path, manifest: KernelManifest
    ) -> tuple[float, float]:
        """min/max over ``spkcov`` for every manifest target (measured, not
        assumed). Empty targets are skipped; a Spice error is an integrity
        failure, not a partial load."""
        lo, hi = float("inf"), float("-inf")
        try:
            for target in manifest.body_ids:
                cell = sp.spkcov(str(path), int(target))
                for i in range(cell.card):
                    value = float(cell[i])
                    lo, hi = min(lo, value), max(hi, value)
        except sp.SpiceError as exc:  # pragma: no cover - defensive
            raise KernelIntegrityError(
                f"spkcov failed on {path.name}: {exc}"
            ) from exc
        if not (lo < hi):
            raise KernelIntegrityError(f"no coverage segments in {path.name}")
        return lo, hi

    @property
    def metadata(self) -> ReferenceMetadata:
        return self._metadata

    @property
    def coverage(self) -> Coverage:
        return self._coverage

    @property
    def path(self) -> Path:
        return self._path

    def state_at(self, *, body: str, et: float) -> ReferenceState:
        """Live geometric state (re-checks mapping + coverage per call so
        direct protocol use — e.g. ``compare_trajectory`` — stays safe)."""
        nid = naif_id(body)
        self._coverage.require_contains(et)
        state, _lt = sp.spkezr(
            str(nid),
            float(et),
            QUERY_FRAME,
            QUERY_ABERRATION,
            QUERY_OBSERVER,
        )
        position_m = from_native(state[:3], native_unit=self._metadata.native_position_unit)
        velocity_ms = from_native(
            state[3:], native_unit=self._metadata.native_velocity_unit
        )
        return ReferenceState(
            body=body,
            naif_id=nid,
            epoch_jd=et_to_jd_tdb(float(et)),
            frame=ReferenceFrame.SSB_ICRS,
            center="ssb(0)",
            time_scale=TimeScale.TDB,
            position_m=position_m,
            velocity_ms=velocity_ms,
            provenance=self._metadata,
        )
