"""Fixture backend: provenance pins, golden canaries, load strictness, determinism.

The golden canaries are the wrong-ID regression (requirement 5): the fixture
was recorded by querying explicit NAIF IDs, so a swapped mapping at record
time — or a swapped table now — puts Earth/Moon/Sun distances outside
textbook windows. They also re-run the ×1000 unit regression through the
full state-construction path (requirement 9).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.kernel_manifest import DE440S_MANIFEST
from solar_ephemeris.ephemeris.mapping import BODY_TO_NAIF
from solar_ephemeris.ephemeris.reference import get_state

JD_J2000 = 2451545.0


@pytest.fixture(scope="module")
def fixture() -> FixtureReference:
    # Missing/corrupt fixture = hard failure (FileNotFoundError/ValueError),
    # never a skip.
    return FixtureReference()


def test_provenance_matches_manifest_pins(fixture: FixtureReference) -> None:
    m = fixture.metadata
    assert m.reference_name == "JPL DE440"
    assert m.kernel_filename == DE440S_MANIFEST.filename
    assert m.kernel_md5 == DE440S_MANIFEST.md5
    assert m.kernel_sha256 == DE440S_MANIFEST.sha256
    assert m.size_bytes == DE440S_MANIFEST.size_bytes
    assert m.retrieval_date == DE440S_MANIFEST.retrieval_date
    assert m.kernel_coverage.intervals == (DE440S_MANIFEST.coverage_et,)
    assert m.body_ids == tuple(sorted(DE440S_MANIFEST.body_ids))
    assert m.reference_frame == "J2000" and m.reference_center == 0
    assert m.native_position_unit == "km" and m.native_velocity_unit == "km/s"
    assert m.time_standard.startswith("TDB")
    assert "tools/record_reference_fixture.py" in m.source
    assert m.spice_version and m.software_version


def test_fixture_covers_every_mapped_body(fixture: FixtureReference) -> None:
    assert set(fixture.bodies) == set(BODY_TO_NAIF)


def test_fixture_coverage_domain(fixture: FixtureReference) -> None:
    # Recorded grid: et = -1 d .. +10 d around J2000.
    assert fixture.coverage.start == -86400.0
    assert fixture.coverage.end == 864000.0


def test_golden_canary_earth_sun_distance(fixture: FixtureReference) -> None:
    earth = get_state(fixture, body="Earth", epoch_jd=JD_J2000)
    r = float(np.linalg.norm(earth.position_m))
    # Window [1.46e11, 1.52e11] m (near perihelion at J2000; measured
    # 1.4688894e11 m at recording). Fails if km->m conversion or body-ID
    # mapping is wrong (1.46889e8 m / off-body states respectively).
    assert 1.46e11 <= r <= 1.52e11, f"|Earth-SSB| = {r!r} m outside canary window"


def test_golden_canary_earth_speed(fixture: FixtureReference) -> None:
    earth = get_state(fixture, body="Earth", epoch_jd=JD_J2000)
    speed = float(np.linalg.norm(earth.velocity_ms))
    # [29000, 31000] m/s (measured 30285.26 m/s at J2000); catches a
    # velocity-conversion bug independently of the position canary.
    assert 29000.0 <= speed <= 31000.0, f"|v_Earth| = {speed!r} m/s outside window"


def test_golden_canary_earth_moon_distance(fixture: FixtureReference) -> None:
    earth = get_state(fixture, body="Earth", epoch_jd=JD_J2000)
    moon = get_state(fixture, body="Moon", epoch_jd=JD_J2000)
    d = float(np.linalg.norm(moon.position_m - earth.position_m))
    # [3.56e8, 4.07e8] m: lunar-distance range (measured 4.02449e8 m at
    # J2000 recording). A Moon→399 or Moon→3 mapping lands far outside.
    assert 3.56e8 <= d <= 4.07e8, f"|Moon-Earth| = {d!r} m outside canary window"


def test_two_instances_are_bit_identical() -> None:
    a, b = FixtureReference(), FixtureReference()
    sa = get_state(a, body="Jupiter", epoch_jd=JD_J2000 + 0.25)
    sb = get_state(b, body="Jupiter", epoch_jd=JD_J2000 + 0.25)
    assert np.array_equal(sa.position_m, sb.position_m)
    assert np.array_equal(sa.velocity_ms, sb.velocity_ms)


def test_missing_fixture_fails_loud(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="never a skip"):
        FixtureReference(tmp_path / "absent.json")


def _tampered(tmp_path: Path, mutate) -> FixtureReference:
    src = FixtureReference().path
    payload = json.loads(Path(src).read_text(encoding="utf-8"))
    mutate(payload)
    dst = tmp_path / "tampered.json"
    dst.write_text(json.dumps(payload), encoding="utf-8")
    return FixtureReference(dst)


def test_wrong_schema_version_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _tampered(tmp_path, lambda p: p.update(schema_version=99))


def test_light_time_corrected_fixture_refused(tmp_path: Path) -> None:
    # A fixture recorded under different request conditions must never mix in.
    with pytest.raises(ValueError, match="refusing to mix"):
        _tampered(tmp_path, lambda p: p["request"].update(abcorr="LT+S"))


def test_wrong_request_frame_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="refusing to mix"):
        _tampered(tmp_path, lambda p: p["request"].update(frame="IAU_EARTH"))


def test_shuffled_samples_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        _tampered(tmp_path, lambda p: p["samples"].reverse())
