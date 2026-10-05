"""Real-kernel ingestion (Increment 7a — Gate B: ``pytest -m real_kernel``).

Default runs deselect this module via pyproject ``addopts`` (user-signed-off
policy); Gate B runs it explicitly. Every test needs the identity-verified
``kernels/de440s.bsp`` — a missing kernel is a FAILURE with retrieval
instructions, never a skip (asserted below by construction).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import spiceypy as sp

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST, default_kernel_path
from solar_ephemeris.ephemeris.reference import get_state
from solar_ephemeris.ephemeris.spice_backend import SpiceReference
from solar_ephemeris.ephemeris.time import et_to_jd_tdb
from solar_ephemeris.ephemeris.types import (
    CoverageError,
    KernelIntegrityError,
    UnknownBodyMappingError,
)
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale

pytestmark = pytest.mark.real_kernel

KERNEL = default_kernel_path()
RETRIEVAL_HINT = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp"


def _require_kernel() -> Path:
    if not KERNEL.is_file():
        pytest.fail(
            f"reference kernel missing: {KERNEL} — download from "
            f"{RETRIEVAL_HINT} and verify sha256 against kernel_manifest.py "
            "(real-kernel tests fail, never skip)"
        )
    return KERNEL


@pytest.fixture(scope="module")
def spice_ref() -> SpiceReference:
    return SpiceReference(_require_kernel())


@pytest.fixture(scope="module")
def fixture() -> FixtureReference:
    return FixtureReference()


def test_load_verifies_identity_and_metadata(spice_ref: SpiceReference) -> None:
    m = spice_ref.metadata
    assert m.reference_name == "JPL DE440"
    assert m.kernel_sha256 == DE440S_MANIFEST.sha256
    assert m.kernel_md5 == DE440S_MANIFEST.md5
    assert m.kernel_filename == DE440S_MANIFEST.filename
    assert m.size_bytes == DE440S_MANIFEST.size_bytes
    assert m.reference_frame == "J2000" and m.reference_center == 0
    assert m.native_position_unit == "km" and m.native_velocity_unit == "km/s"
    assert m.time_standard.startswith("TDB")
    assert m.spice_version and m.software_version
    # spkobj measured live == pinned manifest body list
    assert m.body_ids == tuple(sorted(DE440S_MANIFEST.body_ids))
    # spkcov union measured live == pinned window (exact float equality)
    assert spice_ref.coverage.intervals == (DE440S_MANIFEST.coverage_et,)
    assert spice_ref.coverage.contains(0.0)  # J2000 inside window


def test_missing_kernel_fails_with_retrieval_instructions(tmp_path: Path) -> None:
    with pytest.raises(KernelIntegrityError) as ei:
        SpiceReference(tmp_path / "absent.bsp")
    message = str(ei.value)
    assert "kernel file not found" in message
    assert "download from https://naif.jpl.nasa.gov" in message  # recovery hint


def test_truncated_kernel_rejected(tmp_path: Path) -> None:
    src = _require_kernel()
    head = tmp_path / "de440s.bsp"
    with src.open("rb") as fh, head.open("wb") as out:
        out.write(fh.read(4096))
    with pytest.raises(KernelIntegrityError) as ei:
        SpiceReference(head)
    assert "size mismatch" in str(ei.value)


def test_corrupted_same_size_kernel_rejected(tmp_path: Path) -> None:
    # Same size, flipped byte → reaches the MD5 stage → hash mismatch.
    src = _require_kernel()
    corrupted = tmp_path / "de440s.bsp"
    blob = bytearray(src.read_bytes())
    blob[src.stat().st_size // 2] ^= 0xFF
    corrupted.write_bytes(bytes(blob))
    with pytest.raises(KernelIntegrityError) as ei:
        SpiceReference(corrupted)
    assert "MD5 mismatch" in str(ei.value)
    assert "NAIF/manifest" in str(ei.value)


def test_wrong_solution_filename_refused_by_manifest() -> None:
    # de441/de442 must be refused at manifest level (R6 — no silent
    # substitution), independent of any file on disk.
    from dataclasses import replace

    from solar_ephemeris.ephemeris.kernel_manifest import KernelManifest

    with pytest.raises(ValueError, match="not a DE440 kernel"):
        replace(DE440S_MANIFEST, filename="de441.bsp")


def test_live_state_at_sample_point_matches_fixture_bit_exact(
    spice_ref: SpiceReference, fixture: FixtureReference
) -> None:
    live = spice_ref.state_at(body="Earth", et=0.0)
    recorded = fixture.state_at(body="Earth", et=0.0)
    # Same kernel, same spkezr call → identical bits (no interpolation here).
    assert np.array_equal(live.position_m, recorded.position_m)
    assert np.array_equal(live.velocity_ms, recorded.velocity_ms)
    assert live.epoch_jd == recorded.epoch_jd


# Fixed interior probe set — the same 26 probes measured on 2026-10-03:
# max |interp - native| = 62.578 m (pos), 2.216e-3 m/s (vel).
_INTERIOR_PROBES = tuple(
    base + off
    for base in (-86400.0, 0.0, 86400.0, 432000.0)
    for off in (3600, 7200, 12345, 43199, 86399, 360000, 863999)
    if -86400.0 <= base + off <= 864000.0
)


def test_interior_interpolation_vs_native_within_measured_bound(
    spice_ref: SpiceReference, fixture: FixtureReference
) -> None:
    """Documented interpolation error bound (plan §8).

    Cubic Hermite on the daily fixture grid vs SPICE native Type-2
    Chebyshev evaluation at interior epochs. Measured max over this exact
    probe set (2026-10-03): 62.578 m / 2.216e-3 m/s. Bounds = ~96x/99x the
    measured maximum — headroom for platform/version float differences, NOT
    calibrated against the test (reason recorded here with the measurement).
    """
    max_dp = 0.0
    max_dv = 0.0
    assert len(_INTERIOR_PROBES) == 26
    for et in _INTERIOR_PROBES:
        live = spice_ref.state_at(body="Earth", et=et)
        recorded = fixture.state_at(body="Earth", et=et)
        max_dp = max(max_dp, float(np.linalg.norm(live.position_m - recorded.position_m)))
        max_dv = max(max_dv, float(np.linalg.norm(live.velocity_ms - recorded.velocity_ms)))
    assert max_dp <= 6000.0, f"interpolation position deviation {max_dp} m > 6000 m"
    assert max_dv <= 0.22, f"interpolation velocity deviation {max_dv} m/s > 0.22 m/s"


def test_lsk_free_time_operation(spice_ref: SpiceReference) -> None:
    # TDB in, TDB out: no leap-second kernel is ever loaded or needed.
    assert sp.ktotal("leapseconds") == 0
    state = spice_ref.state_at(body="Earth", et=0.0)
    assert state.epoch_jd == et_to_jd_tdb(0.0) == 2451545.0
    assert state.time_scale is TimeScale.TDB
    assert sp.ktotal("leapseconds") == 0  # still none after queries


def test_state_at_rejects_unmapped_body(spice_ref: SpiceReference) -> None:
    with pytest.raises(UnknownBodyMappingError):
        spice_ref.state_at(body="PlanetX", et=0.0)


def test_state_at_rejects_outside_coverage(spice_ref: SpiceReference) -> None:
    lo, hi = spice_ref.coverage.intervals[0]
    spice_ref.state_at(body="Earth", et=lo)  # exact boundary: allowed
    spice_ref.state_at(body="Earth", et=hi)
    with pytest.raises(CoverageError, match="outside kernel coverage"):
        spice_ref.state_at(body="Earth", et=hi + 1.0)
    with pytest.raises(CoverageError, match="outside kernel coverage"):
        spice_ref.state_at(body="Earth", et=lo - 1.0)


def test_state_contract_and_provenance(spice_ref: SpiceReference) -> None:
    state = spice_ref.state_at(body="Earth", et=0.0)
    assert state.body == "Earth" and state.naif_id == 399
    assert state.frame is ReferenceFrame.SSB_ICRS
    assert state.center == "ssb(0)"
    assert state.time_scale is TimeScale.TDB
    assert state.provenance is spice_ref.metadata
    assert state.provenance.reference_name == "JPL DE440"
    assert state.position_m.shape == (3,) and np.all(np.isfinite(state.position_m))
    # km→m happened (a dropped ×1000 would land at ~1.47e8 m, far outside)
    assert 1.4e11 <= float(np.linalg.norm(state.position_m)) <= 1.6e11


def test_golden_canaries_live(spice_ref: SpiceReference) -> None:
    # Wrong-ID / wrong-unit regression on the LIVE path (requirement 5/9).
    earth = spice_ref.state_at(body="Earth", et=0.0)
    moon = spice_ref.state_at(body="Moon", et=0.0)
    r_es = float(np.linalg.norm(earth.position_m))
    v_e = float(np.linalg.norm(earth.velocity_ms))
    r_em = float(np.linalg.norm(moon.position_m - earth.position_m))
    assert 1.46e11 <= r_es <= 1.52e11, r_es
    assert 29000.0 <= v_e <= 31000.0, v_e
    assert 3.56e8 <= r_em <= 4.07e8, r_em


def test_facade_works_interchangeably_with_live_provider(
    spice_ref: SpiceReference,
) -> None:
    # The same get_state() façade drives both backends (protocol, not class).
    state = get_state(spice_ref, body="Earth", epoch_jd=2451545.0)
    assert state.frame is ReferenceFrame.SSB_ICRS
    assert state.time_scale is TimeScale.TDB
    assert state.provenance.reference_name == "JPL DE440"
    assert state.provenance.kernel_sha256 == DE440S_MANIFEST.sha256


def test_jupiter_uses_barycentre_id_not_absent_planetcentre(
    spice_ref: SpiceReference,
) -> None:
    # The measured trap: SPICE NAME 'Jupiter' -> 599, which does not exist
    # in de440s.bsp (SPKINSUFFDATA). Our mapping queries 5 (system
    # barycentre), which does.
    from solar_ephemeris.ephemeris.mapping import naif_id

    assert naif_id("Jupiter") == 5
    state = spice_ref.state_at(body="Jupiter", et=0.0)
    assert state.naif_id == 5
    # Measured at et=0: 7.4170e11 m (Jupiter perihelion side, ~4.96 AU);
    # band [7.3e11, 7.6e11]. A 599 query would have raised SPKINSUFFDATA,
    # not returned a value — this test proves the mapping picks 5.
    assert 7.3e11 <= float(np.linalg.norm(state.position_m)) <= 7.6e11
