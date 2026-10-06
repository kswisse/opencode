"""KTD6 provider policy + whole-series coverage gate for the V3 lookup (U3).

Selection flow (plan HTD): need a reference chain → is ``spiceypy``
importable? (no → ``FixtureReference``) → does ``verify_kernel`` pass?
(no → ``FixtureReference``) → ``SpiceReference`` carrying the kernel sha256 →
is every recorded epoch inside coverage? (no → ``DataGapError`` naming the
epoch beyond coverage: the whole series is refused, never a drawn prefix —
KTD5) → read-only chain of positions.

One figure carries exactly ONE reference identity (R12): fixture id +
coverage, OR the kernel sha256 — never both. Read-only: nothing here writes
files or executes simulation (R27).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from solar_ephemeris.ephemeris.fixture_backend import FixtureReference
from solar_ephemeris.ephemeris.kernel_manifest import default_kernel_path
from solar_ephemeris.ephemeris.reference import (
    ReferenceProvider,
    lookup_reference_series,
)
from solar_ephemeris.ephemeris.time import jd_tdb_to_et
from solar_ephemeris.ephemeris.types import KernelIntegrityError, ReferenceState
from solar_ephemeris.physics.state import StateMeta

from .gaps import DataGapError, make_gap


@dataclass(frozen=True, slots=True)
class ReferenceSeries:
    """Reference chain at the recorded epochs plus its one sidecar identity."""

    body: str
    epochs_jd: tuple[float, ...] | None  # None when the caller supplied ET
    states: tuple[ReferenceState, ...]
    identity: dict[str, object]  # plain dict: caller merges it into the sidecar


def reference_identity(provider: ReferenceProvider) -> dict[str, object]:
    """Sidecar identity: fixture id + coverage OR kernel sha256, never both (R12)."""
    if isinstance(provider, FixtureReference):
        return {
            "reference_provider": "fixture",
            "reference_kernel": "fixture",
            "fixture_id": provider.path.name,
            "coverage": provider.coverage.to_dict(),
        }
    return {
        "reference_provider": "spice",
        "reference_kernel": provider.metadata.kernel_filename,
        "kernel_sha256": provider.metadata.kernel_sha256,
    }


def select_provider(kernel_path: Path | str | None = None) -> ReferenceProvider:
    """KTD6 order: ``SpiceReference`` iff spiceypy imports AND verify_kernel passes.

    Every other outcome (spiceypy absent, kernel absent/modified) falls back
    to ``FixtureReference`` — the policy never leaks an ImportError or a
    KernelIntegrityError to the caller. A fixture that is itself unusable
    (missing or corrupt file) surfaces as ``DataGapError``, never a raw
    traceback (loader contract: every failure on disk is a data gap).
    """
    path = Path(kernel_path) if kernel_path is not None else default_kernel_path()

    def fallback() -> ReferenceProvider:
        try:
            return FixtureReference()
        except (OSError, ValueError) as exc:
            raise DataGapError(
                make_gap(
                    "reference fixture",
                    reason="unusable fixture",
                    detail=str(exc),
                    source_path=str(path),
                )
            ) from exc

    try:
        # Imported here, not at module scope: spiceypy must never load as a
        # side effect of importing the viz layer.
        from solar_ephemeris.ephemeris.spice_backend import SpiceReference
    except ImportError:
        return fallback()
    try:
        return SpiceReference(path)  # construction runs verify_kernel first
    except KernelIntegrityError:
        return fallback()


def resolve_reference_series(
    provider: ReferenceProvider,
    *,
    body: str,
    epochs_jd: Sequence[float] | None = None,
    epochs_et: Sequence[float] | None = None,
    source_path: str,
    model_meta: StateMeta | None = None,
    transform: str | None = None,
) -> ReferenceSeries:
    """Look up the whole recorded series, or refuse it whole (KTD6 / KTD5).

    Exactly one epoch scale must be given: ``epochs_jd`` (the caller holds
    JDs) or ``epochs_et`` (the model grid ``et0 + t`` — no per-sample JD
    round-trip, R9). Coverage for EVERY epoch is checked on the ET scale
    before the first state is fetched: a series that does not fit raises
    :class:`~solar_ephemeris.visualization.gaps.DataGapError`
    naming the epoch beyond coverage, so no caller can draw a prefix.
    ``model_meta``/``transform`` are forwarded to the KTD2 gate unchanged.
    """
    if (epochs_jd is None) == (epochs_et is None):
        raise ValueError("supply exactly one of epochs_jd / epochs_et")
    scale = "et" if epochs_et is not None else "epoch_jd"
    epochs = tuple(
        float(epoch) for epoch in (epochs_et if epochs_et is not None else epochs_jd)
    )
    if not epochs:
        raise DataGapError(
            make_gap(
                "reference epochs",
                reason="no recorded epochs",
                detail="recorded epoch list is empty; there is no reference series to look up",
                source_path=source_path,
            )
        )
    outside = [
        epoch
        for epoch in epochs
        if not provider.coverage.contains(
            epoch if scale == "et" else jd_tdb_to_et(epoch)
        )
    ]
    if outside:
        raise DataGapError(
            make_gap(
                "reference coverage",
                reason="epochs outside coverage",
                detail=(
                    f"{len(outside)} of {len(epochs)} recorded epochs fall outside "
                    f"provider coverage {provider.coverage.intervals} (TDB s past "
                    f"J2000); first outside {scale}={outside[0]!r}; refusing to "
                    "truncate the reference series (no prefix)"
                ),
                source_path=source_path,
            )
        )
    states = lookup_reference_series(
        provider,
        body=body,
        epochs_jd=None if epochs_et is not None else epochs,
        epochs_et=epochs if epochs_et is not None else None,
        model_meta=model_meta,
        transform=transform,
    )
    return ReferenceSeries(
        body=body,
        epochs_jd=None if epochs_et is not None else epochs,
        states=tuple(states),
        identity=reference_identity(provider),
    )
