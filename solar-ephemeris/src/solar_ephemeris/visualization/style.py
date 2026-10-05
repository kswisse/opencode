"""Frozen style roles + pinned rcParams for every figure (R15, R13, KTD7).

ONE style module owns rcParams / DPI / size / font (KTD7): nothing else in
the project may set them. The five semantic roles are grayscale-safe by
construction - each carries a UNIQUE (linestyle, marker) pair, so the roles
stay distinguishable without any colour (R15).

matplotlib is imported LAZILY, inside ``style_context()``: importing this
module (or the whole ``visualization`` package) never loads matplotlib, so
Gate A stays green without matplotlib (R29). Role specs are plain data -
usable as artist kwargs without matplotlib present.
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np
from numpy.typing import ArrayLike

#: Bump whenever ROLES or RC_PARAMS changes (written into every sidecar).
STYLE_VERSION: Final[str] = "1"

#: Frozen order of the five semantic roles (R15).
ROLE_ORDER: Final[tuple[str, ...]] = (
    "model",
    "reference",
    "error",
    "control",
    "signal",
)

#: Frozen role table (plan HTD). Each role has a UNIQUE (linestyle, marker)
#: pair - grayscale distinction is path/marker, never colour alone.
ROLES: Final[dict[str, dict[str, Any]]] = {
    # kết quả tích phân của ta: solid + thick + open circle
    "model": {
        "color": "#0072B2",
        "linestyle": "-",
        "linewidth": 2.4,
        "marker": "o",
        "markersize": 6.0,
        "markerfacecolor": "none",
    },
    # DE440/fixture: dash-dot, no marker
    "reference": {
        "color": "#000000",
        "linestyle": "-.",
        "linewidth": 1.6,
        "marker": "None",
        "markersize": 6.0,
        "markerfacecolor": "none",
    },
    # chuỗi lỗi / sai số: solid + thin + square
    "error": {
        "color": "#D55E00",
        "linestyle": "-",
        "linewidth": 1.0,
        "marker": "s",
        "markersize": 5.0,
        "markerfacecolor": "none",
    },
    # đường điều khiển (C controls): dashed + triangle
    "control": {
        "color": "#009E73",
        "linestyle": "--",
        "linewidth": 1.6,
        "marker": "^",
        "markersize": 6.0,
        "markerfacecolor": "none",
    },
    # tín hiệu khoa học cần thấy (C signals): dotted + x-cross
    "signal": {
        "color": "#E69F00",
        "linestyle": ":",
        "linewidth": 1.8,
        "marker": "x",
        "markersize": 6.0,
        "markerfacecolor": "none",
    },
}

#: THE single place rcParams/DPI/size/font are pinned (KTD7).
RC_PARAMS: Final[dict[str, Any]] = {
    "figure.figsize": (7.2, 4.5),
    "figure.dpi": 100,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.family": "sans-serif",
    "font.size": 10.0,
    "axes.labelsize": 11.0,
    "axes.titlesize": 12.0,
    "legend.fontsize": 9.0,
    "lines.linewidth": 1.5,
}


def role_style(role: str) -> dict[str, Any]:
    """Artist kwargs for one semantic role; unknown roles raise (table frozen)."""
    try:
        return dict(ROLES[role])
    except KeyError:
        raise ValueError(
            f"unknown style role {role!r}; frozen roles are {ROLE_ORDER}"
        ) from None


def style_context() -> Any:
    """``matplotlib.rc_context`` bound to the pinned RC_PARAMS (lazy import)."""
    import matplotlib

    return matplotlib.rc_context(RC_PARAMS)


def truthful_limits(
    *arrays: ArrayLike,
    include_zero: bool = False,
    pad: float = 0.05,
) -> tuple[float, float]:
    """Axis limits that never cut the signal or the zero baseline (R13).

    Finite values only; expands to contain 0.0 when ``include_zero`` (error /
    conservation panels where y=0 is the claim), then pads each side by
    ``pad`` x span so no point sits on the frame edge. No smoothing, no
    autoscale tricks - just faithful limits.
    """
    pieces = [np.asarray(arr, dtype=np.float64).ravel() for arr in arrays]
    if pieces:
        flat = np.concatenate(pieces)
        finite = flat[np.isfinite(flat)]
    else:
        finite = np.empty(0, dtype=np.float64)
    if finite.size == 0:
        raise ValueError("truthful_limits: no finite values to bound")
    lo, hi = float(finite.min()), float(finite.max())
    if include_zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    span = hi - lo
    if span <= 0.0:
        span = max(abs(hi), 1.0)
    return lo - pad * span, hi + pad * span
