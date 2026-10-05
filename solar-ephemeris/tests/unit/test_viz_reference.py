"""U3 - read-only reference series lookup + KTD6 provider policy.

Requirements: R18, R12, R27; KTD2, KTD6, KTD5.

Covers the additive helper ``ephemeris/reference.py::lookup_reference_series``
(KTD2: same gate order + ``assert_compatible`` as ``compare_trajectory``,
``ComparisonResult`` schema untouched) and ``visualization/providers.py``
(KTD6: provider selection order, whole-series coverage check, typed
``DataGapError`` refusal instead of a truncated prefix).

Gate A cases are kernel-free AND results-free: synthetic epochs against the
recorded fixture. The two scenarios that read the real ``results/`` tree
(horizon_1d happy / horizon_30d refusal) carry the ``real_kernel`` marker -
the same R29 convention as ``test_viz_data.py``: the default run stays green
without the results tree, and neither needs a spice kernel. The live-kernel
branch (SpiceReference identity) lives in ``tests/real_kernel/test_viz_reference.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.reference import lookup_reference_series
from solar_ephemeris.ephemeris.types import MetadataMismatchError
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.state import StateMeta
from solar_ephemeris.visualization.gaps import GAP_KEYS, DataGapError
from solar_ephemeris.visualization.providers import (
    ReferenceSeries,
    reference_identity,
    resolve_reference_series,
    select_provider,
)

REPO = Path(__file__).resolve().parents[2]
REAL_RESULTS = REPO / "results"
J2000 = 2451545.0
DAY = 86400.0

#: Recorded fixture window: de440s_recorded.json samples span -1d .. +10d
#: around J2000 (closed interval -86400.0 .. 864000.0 s of ephemeris time).
FIXTURE_INTERVAL = (-DAY, 10.0 * DAY)

#: Every ReferenceMetadata field the fixture provenance must carry.
PROVENANCE_FIELDS = (
    "reference_name",
    "reference_version",
    "source",
    "kernel_filename",
    "kernel_md5",
    "kernel_sha256",
    "size_bytes",
    "retrieval_date",
    "kernel_coverage",
    "body_ids",
    "reference_frame",
    "reference_center",
    "time_standard",
    "native_position_unit",
    "native_velocity_unit",
    "spice_version",
    "software_version",
)

TRANSFORM = "translation SSB(0) -> barycenter(Sun, Earth) by GM-weighted barycentre of (Sun, Earth)"


def _epochs_from_days(days: list[float]) -> list[float]:
    return [J2000 + d for d in days]


def _model_meta(epoch_jd: float, **over) -> StateMeta:
    base = dict(
        frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
        origin="barycenter(Sun, Earth)",
        epoch_jd=epoch_jd,
        time_scale=TimeScale.TDB,
    )
    base.update(over)
    return StateMeta(**base)


def _record_epochs(rel: str, body: str = "Earth") -> tuple[list[float], str]:
    """Recorded per-sample epochs: record['epoch'] (JD) + comparison times_s."""
    path = REAL_RESULTS / rel / "experiment_record.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    epoch = float(record["epoch"])
    times = record["comparison"][body]["times_s"]
    return [epoch + t / DAY for t in times], str(path)


class _CountingFixture(FixtureReference):
    """Fixture that counts state_at fetches - proves all-or-nothing refusal."""

    def __init__(self) -> None:
        super().__init__()
        self.fetches = 0

    def state_at(self, *, body: str, et: float):
        self.fetches += 1
        return super().state_at(body=body, et=et)


# ---------------------------------------------------------------------------
# Happy: chain over every recorded epoch, fixture provenance complete (R18)
# ---------------------------------------------------------------------------


def test_resolve_returns_chain_for_every_epoch() -> None:
    provider = _CountingFixture()
    epochs = _epochs_from_days([-1.0, 0.0, 1.0, 9.0, 10.0])  # closed boundaries
    series = resolve_reference_series(
        provider, body="Earth", epochs_jd=epochs, source_path="synthetic"
    )
    assert isinstance(series, ReferenceSeries)
    assert series.body == "Earth"
    assert series.epochs_jd == tuple(epochs)
    assert len(series.states) == len(epochs)
    assert provider.fetches == len(epochs)
    for state, epoch in zip(series.states, epochs):
        assert state.body == "Earth" and state.naif_id == 399
        assert state.epoch_jd == pytest.approx(epoch, abs=1e-9)
        assert state.frame is ReferenceFrame.SSB_ICRS
        assert state.time_scale is TimeScale.TDB
        assert np.all(np.isfinite(state.position_m))
        assert set(state.provenance.to_dict()) >= set(PROVENANCE_FIELDS)


# ---------------------------------------------------------------------------
# KTD2: helper reuses compare_trajectory's gate order + assert_compatible
# ---------------------------------------------------------------------------


def test_helper_runs_assert_compatible_gate_before_returning() -> None:
    epochs = _epochs_from_days([0.0, 1.0, 2.0])
    states = lookup_reference_series(
        FixtureReference(),
        body="Earth",
        epochs_jd=epochs,
        model_meta=_model_meta(epochs[0]),
        transform=TRANSFORM,
    )
    assert len(states) == len(epochs)


def test_helper_assert_gate_rejects_epoch_mismatch() -> None:
    epochs = _epochs_from_days([0.0, 1.0])
    with pytest.raises(MetadataMismatchError) as exc:
        lookup_reference_series(
            FixtureReference(),
            body="Earth",
            epochs_jd=epochs,
            model_meta=_model_meta(J2000 + 0.5),
            transform=TRANSFORM,
        )
    assert exc.value.field == "epoch_jd"


def test_helper_assert_gate_rejects_missing_transform_descriptor() -> None:
    epochs = _epochs_from_days([0.0, 1.0])
    with pytest.raises(MetadataMismatchError) as exc:
        lookup_reference_series(
            FixtureReference(),
            body="Earth",
            epochs_jd=epochs,
            model_meta=_model_meta(epochs[0]),
        )
    assert exc.value.field == "center"


# ---------------------------------------------------------------------------
# Error: coverage shortfall refuses the WHOLE series (KTD5, no prefix)
# ---------------------------------------------------------------------------


def test_coverage_shortfall_refuses_whole_series_without_fetching() -> None:
    provider = _CountingFixture()
    epochs = _epochs_from_days([0.0, 30.0])
    with pytest.raises(DataGapError) as exc:
        resolve_reference_series(
            provider,
            body="Earth",
            epochs_jd=epochs,
            source_path="results/experiment_E/horizon_30d/experiment_record.json",
        )
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert gap["name"] == "reference coverage"
    assert repr(epochs[1]) in gap["detail"]  # the epoch beyond coverage, named
    assert "refusing to truncate" in gap["detail"]
    assert gap["source_path"].endswith("experiment_record.json")
    json.dumps(exc.value.report)  # machine-readable report, no raw exception
    assert provider.fetches == 0  # no partial chain is even attempted


def test_empty_epoch_list_is_data_gap() -> None:
    with pytest.raises(DataGapError) as exc:
        resolve_reference_series(
            FixtureReference(),
            body="Earth",
            epochs_jd=[],
            source_path="results/experiment_E/horizon_1d/experiment_record.json",
        )
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert "empty" in gap["detail"]


# ---------------------------------------------------------------------------
# R12: one figure carries ONE reference identity - fixture OR kernel sha256
# ---------------------------------------------------------------------------


def test_fixture_identity_never_carries_kernel_sha256() -> None:
    identity = reference_identity(FixtureReference())
    assert identity["reference_provider"] == "fixture"
    assert identity["reference_kernel"] == "fixture"
    assert identity["fixture_id"] == "de440s_recorded.json"
    assert identity["coverage"]["intervals"] == [list(FIXTURE_INTERVAL)]
    assert "kernel_sha256" not in identity
    json.dumps(identity)  # plain dict: merge into the sidecar as-is


# ---------------------------------------------------------------------------
# KTD6 selection order: spiceypy importable AND verify_kernel pass, else fixture
# ---------------------------------------------------------------------------


def test_unimportable_spiceypy_falls_back_to_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    # Block a fresh import of the SPICE backend: None in sys.modules makes
    # `import spiceypy` raise ImportError instead of leaking it raw.
    monkeypatch.delitem(sys.modules, "solar_ephemeris.ephemeris.spice_backend", raising=False)
    monkeypatch.setitem(sys.modules, "spiceypy", None)
    provider = select_provider(kernel_path=REPO / "kernels" / "de440s.bsp")
    assert isinstance(provider, FixtureReference)


def test_failed_kernel_verification_falls_back_to_fixture(tmp_path: Path) -> None:
    provider = select_provider(kernel_path=tmp_path / "absent.bsp")
    assert isinstance(provider, FixtureReference)


# ---------------------------------------------------------------------------
# Real results tree (R29: marked, read-only, kernel-free)
# ---------------------------------------------------------------------------


@pytest.mark.real_kernel
def test_real_horizon_1d_lookup_covers_every_recorded_epoch() -> None:
    epochs, source = _record_epochs("experiment_E/horizon_1d")
    series = resolve_reference_series(
        FixtureReference(), body="Earth", epochs_jd=epochs, source_path=source
    )
    assert len(series.states) == len(epochs) == 2
    assert series.identity["reference_provider"] == "fixture"
    assert series.identity["reference_kernel"] == "fixture"
    assert series.identity["coverage"]["intervals"] == [list(FIXTURE_INTERVAL)]
    assert "kernel_sha256" not in series.identity
    assert all(np.all(np.isfinite(s.position_m)) for s in series.states)
    provenance = series.states[0].provenance
    assert provenance.reference_name == "JPL DE440"
    assert set(provenance.to_dict()) >= set(PROVENANCE_FIELDS)


@pytest.mark.real_kernel
def test_real_horizon_30d_epochs_refused_as_one_data_gap() -> None:
    epochs, source = _record_epochs("experiment_E/horizon_30d")
    outside = [e for e in epochs if not FIXTURE_INTERVAL[0] <= (e - J2000) * DAY <= FIXTURE_INTERVAL[1]]
    assert outside, "record must exceed the fixture window for this scenario"
    with pytest.raises(DataGapError) as exc:
        resolve_reference_series(
            FixtureReference(), body="Earth", epochs_jd=epochs, source_path=source
        )
    assert len(exc.value.gaps) == 1
    gap = exc.value.gaps[0]
    assert set(gap) == set(GAP_KEYS)
    assert repr(outside[0]) in gap["detail"]
    json.dumps(exc.value.report)
