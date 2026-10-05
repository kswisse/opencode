"""Non-fatal data gaps - one machine-readable shape for the viz layer.

A gap is what the charts show instead of raising: a missing comparison,
an unreadable npz, a reused record whose target is gone. Gaps follow the
same one-dict-per-finding style as the run gate (see experiments._common.gate).
"""

from __future__ import annotations

from typing import Iterable, Mapping

#: Every gap carries exactly these keys, in this order.
GAP_KEYS = ("name", "reason", "detail", "source_path")


def make_gap(name: str, *, reason: str, detail: str, source_path: str) -> dict:
    """Build one gap dict. Keyword-only so reason/detail/source_path stay explicit."""
    return {
        "name": name,
        "reason": reason,
        "detail": detail,
        "source_path": source_path,
    }


class DataGapError(Exception):
    """Raised when data is unusable; .gaps carries the structured findings.

    A DataGapError replaces a bare exception wherever the viz layer touches
    files: the caller either renders the gap or reports .report, never
    scrubs a traceback.
    """

    def __init__(self, gaps: Iterable[Mapping] | Mapping):
        if isinstance(gaps, Mapping):
            gaps = [gaps]
        self.gaps: list[dict] = [
            {key: str(gap[key]) for key in GAP_KEYS} for gap in gaps
        ]
        super().__init__("; ".join(f"{g['name']}: {g['detail']}" for g in self.gaps))

    @property
    def report(self) -> dict:
        return {"gaps": self.gaps}
