"""One adapter over the three real comparison shapes in results/ (R14).

- flat      - single-body error series, ``{"body": ..., "position_error": [...]}``
              (experiment_A2/d1000)
- per_body  - map of body -> error series (experiment_C/tier_T2)
- absent    - no comparison at all (experiment_B/one_period_rk4)

Charts consume ``NormalizedComparison.by_body`` and never re-inspect raw
JSON; an unrecognized shape becomes a data gap, not a guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .gaps import DataGapError, make_gap


@dataclass(frozen=True, slots=True)
class BodyErrors:
    """One body's error series, extracted from either raw shape."""

    body: str
    times_s: Any
    position_error: Any
    velocity_error: Any


@dataclass(frozen=True, slots=True)
class NormalizedComparison:
    by_body: dict[str, BodyErrors]
    absent: bool
    shape: str  # "flat" | "per_body" | "absent"


def _series(entry: Mapping, body: str, source_path: str) -> BodyErrors:
    if "position_error" not in entry:
        raise DataGapError(
            make_gap(
                "comparison",
                reason="unrecognized shape",
                detail=f"series for {body!r} has no position_error array",
                source_path=source_path,
            )
        )
    return BodyErrors(
        body=str(entry.get("body", body)),
        times_s=entry.get("times_s"),
        position_error=entry["position_error"],
        velocity_error=entry.get("velocity_error"),
    )


def normalize_comparison(record: Mapping, *, source_path: str = "") -> NormalizedComparison:
    """Normalize record["comparison"] (R14); absence is a state, not an error."""
    comparison = record.get("comparison")
    if comparison is None:
        return NormalizedComparison(by_body={}, absent=True, shape="absent")

    if not isinstance(comparison, Mapping):
        raise DataGapError(
            make_gap(
                "comparison",
                reason="unrecognized shape",
                detail=f"comparison is {type(comparison).__name__}, expected object or null",
                source_path=source_path,
            )
        )

    if "position_error" in comparison:
        body = comparison.get("body")
        if not body:
            raise DataGapError(
                make_gap(
                    "comparison",
                    reason="unrecognized shape",
                    detail="flat comparison has no body key",
                    source_path=source_path,
                )
            )
        return NormalizedComparison(
            by_body={str(body): _series(comparison, str(body), source_path)},
            absent=False,
            shape="flat",
        )

    by_body: dict[str, BodyErrors] = {}
    for name, entry in comparison.items():
        if not isinstance(entry, Mapping):
            raise DataGapError(
                make_gap(
                    "comparison",
                    reason="unrecognized shape",
                    detail=f"entry for {name!r} is {type(entry).__name__}, expected object",
                    source_path=source_path,
                )
            )
        by_body[str(name)] = _series(entry, str(name), source_path)
    if not by_body:
        raise DataGapError(
            make_gap(
                "comparison",
                reason="unrecognized shape",
                detail="comparison object is neither a flat series nor a body->series map",
                source_path=source_path,
            )
        )
    return NormalizedComparison(by_body=by_body, absent=False, shape="per_body")
