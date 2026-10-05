"""Real-kernel reference lookup for V3 (Gate B: ``pytest -m real_kernel``).

Integration case for U3: ``results/experiment_C/tier_T2`` (30 d span, its
epochs reach ~27.3 d - far beyond the recorded fixture's -1d..+10d window)
must resolve through the KTD6 policy to the live ``SpiceReference``, and the
returned identity must carry the kernel sha256 pinned in
``kernel_manifest.py`` while carrying no fixture id (R12: one reference
identity per figure).

Skip policy note: the repo-wide real-kernel convention is "missing kernel
FAILS, never skips" (tests/real_kernel/test_spice_backend.py), but the U3
wave contract mandates a clean ``pytest.skip`` when spiceypy or the kernel
is unavailable. This file follows the wave contract and reports which path
was taken.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.real_kernel

pytest.importorskip("spiceypy", reason="U3 wave contract: skip cleanly without spiceypy")

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference  # noqa: E402
from solar_ephemeris.ephemeris.kernel_manifest import (  # noqa: E402
    DE440S_MANIFEST,
    default_kernel_path,
)
from solar_ephemeris.ephemeris.spice_backend import SpiceReference  # noqa: E402
from solar_ephemeris.visualization.gaps import DataGapError  # noqa: E402
from solar_ephemeris.visualization.providers import (  # noqa: E402
    resolve_reference_series,
    select_provider,
)

REPO = Path(__file__).resolve().parents[2]
REAL_RESULTS = REPO / "results"
J2000 = 2451545.0
DAY = 86400.0
FIXTURE_HI_S = 10.0 * DAY  # recorded fixture window ends at +10d


def _require_kernel() -> Path:
    kernel = default_kernel_path()
    if not kernel.is_file():
        pytest.skip(
            f"DE440 kernel absent at {kernel} - U3 wave contract: skip, "
            "retrieve from https://naif.jpl.nasa.gov/pub/naif/generic_kernels/"
            "spk/planets/de440s.bsp to run the kernel branch"
        )
    return kernel


def _tier_t2_epochs(body: str = "Earth") -> tuple[list[float], str]:
    path = REAL_RESULTS / "experiment_C" / "tier_T2" / "experiment_record.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    epoch = float(record["epoch"])
    times = record["comparison"][body]["times_s"]
    return [epoch + t / DAY for t in times], str(path)


def test_select_provider_picks_spice_when_import_and_verify_pass() -> None:
    provider = select_provider(kernel_path=_require_kernel())
    assert isinstance(provider, SpiceReference)


def test_tier_t2_series_resolves_via_spice_with_manifest_sha256() -> None:
    provider = select_provider(kernel_path=_require_kernel())
    epochs, source = _tier_t2_epochs()
    # Premise of this scenario: the recorded epochs exceed the fixture window.
    assert len(epochs) == 11
    assert (epochs[-1] - J2000) * DAY > FIXTURE_HI_S

    series = resolve_reference_series(
        provider, body="Earth", epochs_jd=epochs, source_path=source
    )
    assert len(series.states) == len(epochs)
    assert all(np.all(np.isfinite(s.position_m)) for s in series.states)

    identity = series.identity
    assert identity["reference_provider"] == "spice"
    assert identity["reference_kernel"] == DE440S_MANIFEST.filename
    assert identity["kernel_sha256"] == DE440S_MANIFEST.sha256
    # R12: kernel identity only - never a fixture id, never both.
    assert "fixture_id" not in identity
    assert identity.get("coverage") is None
    assert all(
        s.provenance.kernel_sha256 == DE440S_MANIFEST.sha256 for s in series.states
    )


def test_same_tier_t2_epochs_are_refused_by_the_fixture() -> None:
    """The contrast case: without the kernel this figure is a data gap."""
    epochs, source = _tier_t2_epochs()
    with pytest.raises(DataGapError) as exc:
        resolve_reference_series(
            FixtureReference(), body="Earth", epochs_jd=epochs, source_path=source
        )
    assert len(exc.value.gaps) == 1
    json.dumps(exc.value.report)
