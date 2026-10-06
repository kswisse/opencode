"""Helpers shared by the single-run (V1-V5) and multi-run (V6-V9) figures.

No matplotlib at module scope - R29.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

import numpy as np

from .gaps import make_gap
from .loader import LoadedRecord
from .normalize import NormalizedComparison
from .style import role_style
from .units import (
    AU_LABEL,
    KMS_LABEL,
    m_to_au,
    ms_to_kms,
    position_label,
    velocity_label,
)


def _record_payload(loaded: LoadedRecord) -> dict:
    """R6 record keys from the REQUESTED record; kernel identity excluded.

    Stripping ``reference_kernel``/``kernel_sha256`` is the R12 rule: the
    figure's ONE reference identity comes from ``extra`` (lookup identity),
    never from a record that may name a different kernel. The R9 keys of
    ``_record_extra`` ride along so every ``sources[]`` entry can disclose
    its own redirect/completeness (RECORD_KEYS alone would drop them).
    """
    return {
        **{
            key: value
            for key, value in loaded.record.items()
            if key not in ("reference_kernel", "kernel_sha256")
        },
        **_record_extra(loaded),
    }


def _record_extra(loaded: LoadedRecord) -> dict:
    """Provenance the record keys do not carry: completeness + redirect (R9)."""
    extra: dict[str, object] = {
        "provenance_complete": not loaded.missing_provenance,
        "missing_provenance": list(loaded.missing_provenance),
    }
    if loaded.reused_from is not None:
        extra["reused_from"] = loaded.reused_from
        extra["reused_chain"] = list(loaded.reused_chain)
    return extra


_R9_KEYS: Final[tuple[str, ...]] = (
    "provenance_complete",
    "missing_provenance",
    "reused_from",
    "reused_chain",
)


def _attach_member_provenance(sidecar: dict, payloads: Sequence[dict]) -> None:
    """R9 disclosure of a multi-record figure (AE3): ``sources[]`` entries are
    filtered to RECORD_KEYS by ``build_sidecar``, so the per-member redirect /
    completeness keys are re-attached here; a single-member figure lands them
    at the top level, exactly like the one-record figures (V1-V6).
    """
    if not payloads:
        return
    entries = sidecar.get("sources")
    if entries is None:
        sidecar.update(
            {key: payloads[0][key] for key in _R9_KEYS if key in payloads[0]}
        )
        return
    for entry, payload in zip(entries, payloads):
        entry.update({key: payload[key] for key in _R9_KEYS if key in payload})


def _role_kwargs(role: str, index: int) -> dict:
    """Frozen role style; further series of the same role fade toward white.

    linestyle/marker never change (R15 grayscale distinction is path/marker
    only); only lightness separates series 1..n of one role.
    """
    kwargs = role_style(role)
    if index:
        from matplotlib.colors import to_rgba

        r, g, b, a = to_rgba(kwargs["color"])
        fade = min(0.6, 0.15 * index)
        kwargs["color"] = (
            r + (1.0 - r) * fade,
            g + (1.0 - g) * fade,
            b + (1.0 - b) * fade,
            a,
        )
    return kwargs


def _position_in(values: np.ndarray, unit: str) -> np.ndarray:
    """Positions to the display unit (SI default; AU opt-in, R10)."""
    position_label(unit)  # validates the token against the frozen table
    return m_to_au(values) if unit == AU_LABEL else np.asarray(values, dtype=np.float64)


def _velocity_in(values: np.ndarray, unit: str) -> np.ndarray:
    """Velocities to the display unit (SI default; km/s opt-in, R10)."""
    velocity_label(unit)
    return ms_to_kms(values) if unit == KMS_LABEL else np.asarray(values, dtype=np.float64)


def _stored_series(
    norm: NormalizedComparison,
    resolved: dict,
    kind: str,
    record_path: str,
    *,
    prefix: str = "",
    gaps: list[dict] | None = None,
) -> tuple[list[tuple[str, np.ndarray, np.ndarray]], list[dict]]:
    """Plotted series + gaps from a stored comparison (KTD10).

    ``flat`` is single-series by design (no missing-body gaps); ``per_body``
    earns one gap per record body that carries no series. Nothing usable ->
    the caller raises ``DataGapError`` instead of drawing an empty figure.
    ``prefix`` namespaces gap names for run-set figures (``<member>/<body>``);
    pass ``gaps`` to append into a caller-owned list.
    """
    attr = f"{kind}_error"
    out: list[dict] = gaps if gaps is not None else []
    series: list[tuple[str, np.ndarray, np.ndarray]] = []
    for name, entry in norm.by_body.items():
        values = getattr(entry, attr)
        if entry.times_s is None or values is None:
            out.append(
                make_gap(
                    f"{prefix}{name}",
                    reason="no stored error series",
                    detail=f"comparison for {name!r} carries no {attr} series",
                    source_path=record_path,
                )
            )
            continue
        series.append(
            (
                name,
                np.asarray(entry.times_s, dtype=np.float64),
                np.asarray(values, dtype=np.float64),
            )
        )
    if norm.shape == "per_body":
        for name in resolved.get("bodies") or ():
            if name not in norm.by_body:
                out.append(
                    make_gap(
                        f"{prefix}{name}",
                        reason="no stored error series",
                        detail=f"record body {name!r} has no comparison entry",
                        source_path=record_path,
                    )
                )
    return series, out


def _annotate_gaps(ax, gaps: Sequence[dict], limit: int = 8, detail: str = "") -> None:
    """Bottom-left gap banner (KTD5): the figure publishes WITH its gaps."""
    if not gaps:
        return
    shown = ", ".join(str(gap["name"]) for gap in gaps[:limit])
    ax.text(
        0.01,
        0.02,
        f"gaps: {len(gaps)}{detail} - {shown}",
        transform=ax.transAxes,
        va="bottom",
        fontsize=8,
    )


def _frame_tokens(payloads: Sequence[dict]) -> tuple[str, str, str]:
    """frame / origin / time_scale of a multi-record figure (first source)."""
    if not payloads:
        return "unspecified", "unspecified", "unspecified"
    first = payloads[0]
    return (
        str(first.get("reference_frame") or "unspecified"),
        str(first.get("reference_origin") or "unspecified"),
        str(first.get("time_scale") or "unspecified"),
    )


def _error_ylabel(kind: str, unit: str) -> str:
    """Axis label ``position (m)`` -> ``position error (m)`` (likewise velocity)."""
    if kind == "position":
        return position_label(unit).replace("position", "position error", 1)
    return velocity_label(unit).replace("velocity", "velocity error", 1)
