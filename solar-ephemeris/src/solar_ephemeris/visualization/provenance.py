"""Figure sidecar + deterministic write pipeline (R6-R8, KTD9, KTD7).

One record per figure vs many:

- single-record figures write the R6 record keys (experiment_id,
  configuration_hash, output_hash, bodies, epoch, duration, integrator,
  timestep, reference_dataset, reference_kernel + sha256) DIRECTLY on the
  sidecar;
- multi-record figures (V7/V8/V9) carry the same keys inside ``sources[]``,
  one entry per contributing record.

Write contract (KTD9): non-finite series raise ``DataGapError`` BEFORE any
file is touched (never a PNG without its sidecar); the sidecar is written
atomically (temp -> ``os.replace``) with ``sort_keys=True, allow_nan=False``
(write_record semantics, R7) and becomes final BEFORE the PNG is renamed
into place; same ``figure_id`` overwrites deterministically.

``figure_data_hash`` is SHA-256 over the plotted-array BYTES (name + shape +
float64 bytes - the ``output_hash`` construction, R8); the PNG sha256 is
auxiliary information only, never the identity. No matplotlib at module
import time (R29): its version is probed lazily at sidecar-build time.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

import numpy as np
from numpy.typing import ArrayLike

from solar_ephemeris import __version__

from .gaps import DataGapError, make_gap
from .style import STYLE_VERSION

#: Figures live outside the immutable evidence tree (KTD9).
RESULTS_DIRNAME: Final[str] = "results"

#: R6 - figure-level keys every sidecar carries.
FIGURE_KEYS: Final[tuple[str, ...]] = (
    "figure_id",
    "figure_data_hash",
    "source",
    "gaps",
    "style_version",
    "frame",
    "origin",
    "time_scale",
    "units",
    "software_version",
    "matplotlib_version",
    "generated_at",
)

#: R6 - record-level keys: top level for single-record figures, one entry
#: per record inside sources[] for multi-record figures. Absent/null fields
#: are simply not written (a reused record may lack some).
RECORD_KEYS: Final[tuple[str, ...]] = (
    "experiment_id",
    "configuration_hash",
    "output_hash",
    "bodies",
    "epoch",
    "duration",
    "integrator",
    "timestep",
    "reference_dataset",
    "reference_kernel",
    "kernel_sha256",
)

_SOURCES: Final[tuple[str, ...]] = ("stored", "derived", "aggregate")


def jsonable(obj: Any) -> Any:
    """Recursive converter: numpy scalars/arrays, tuples, Paths -> JSON-safe."""
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj


def figure_data_hash(named_arrays: Mapping[str, ArrayLike]) -> str:
    """SHA-256 over plotted-array bytes: name + shape + float64 bytes per
    array, in iteration order - the ``output_hash`` construction (R8), keyed
    by the series name instead of a fixed tuple."""
    h = hashlib.sha256()
    for name, arr in named_arrays.items():
        a = np.ascontiguousarray(arr, dtype=np.float64)
        h.update(str(name).encode("ascii"))
        h.update(str(a.shape).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def ensure_finite(named_arrays: Mapping[str, ArrayLike]) -> None:
    """Reject NaN/inf series as a data gap BEFORE any render/write (KTD9)."""
    offenders = []
    for name, arr in named_arrays.items():
        a = np.asarray(arr, dtype=np.float64)
        bad = int(np.count_nonzero(~np.isfinite(a)))
        if bad:
            offenders.append(f"{name} ({bad} non-finite of {a.size})")
    if offenders:
        raise DataGapError(
            make_gap(
                "plotted series",
                reason="non-finite values",
                detail="rejected before render: " + "; ".join(offenders),
                source_path="in-memory arrays",
            )
        )


def _matplotlib_version() -> str | None:
    """matplotlib.__version__ when installed, else None (probed lazily)."""
    try:
        import matplotlib
    except ImportError:
        return None
    return matplotlib.__version__


def _extract_record_keys(record: Mapping) -> dict[str, Any]:
    return {
        key: jsonable(record[key])
        for key in RECORD_KEYS
        if record.get(key) is not None
    }


def build_caption(sidecar: Mapping, *, extra: str | None = None) -> str:
    """Caption carrying the main R6/R13 provenance tokens of a sidecar."""
    gaps = sidecar.get("gaps") or ()
    parts = [
        str(sidecar["figure_id"]),
        f"source={sidecar['source']}",
        f"frame={sidecar['frame']}",
        f"origin={sidecar['origin']}",
        f"time_scale={sidecar['time_scale']}",
        f"units={sidecar['units']}",
        f"projection={sidecar.get('projection') or 'unspecified'}",
        f"data={str(sidecar['figure_data_hash'])[:12]}",
        f"gaps={len(gaps)}",
    ]
    if extra:
        parts.append(str(extra))
    return " | ".join(parts)


def build_sidecar(
    *,
    figure_id: str,
    source: str,
    frame: str,
    origin: str,
    time_scale: str,
    units: str,
    arrays: Mapping[str, ArrayLike],
    gaps: Sequence[Mapping] = (),
    records: Mapping | Sequence[Mapping] | None = None,
    projection: str | None = None,
    extra: Mapping[str, Any] | None = None,
    style_version: str = STYLE_VERSION,
) -> dict[str, Any]:
    """Assemble the R6 sidecar; non-finite ``arrays`` fail here (R7/KTD9)."""
    if source not in _SOURCES:
        raise ValueError(f"source {source!r} must be one of {_SOURCES}")
    ensure_finite(arrays)  # before render, before hash, before any file

    sidecar: dict[str, Any] = {
        "figure_id": figure_id,
        "figure_data_hash": figure_data_hash(arrays),
        "source": source,
        "gaps": [jsonable(gap) for gap in gaps],
        "style_version": style_version,
        "frame": frame,
        "origin": origin,
        "time_scale": time_scale,
        "units": units,
        "software_version": __version__,
        "matplotlib_version": _matplotlib_version(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if projection is not None:
        sidecar["projection"] = projection

    if records is not None:
        record_list = [records] if isinstance(records, Mapping) else list(records)
        if len(record_list) == 1:
            sidecar.update(_extract_record_keys(record_list[0]))
        elif len(record_list) > 1:
            sidecar["sources"] = [_extract_record_keys(r) for r in record_list]

    if extra:
        # Caller-supplied provenance the records do not carry (V3 provider
        # identity, growth annotations) - wins over record extraction.
        sidecar.update({str(k): jsonable(v) for k, v in extra.items()})

    sidecar["caption"] = build_caption(sidecar)
    return sidecar


def sidecar_path_for(png_path: Path) -> Path:
    """Sidecar of a PNG: same stem, ``.json`` (fig-01.png -> fig-01.json)."""
    return Path(png_path).with_suffix(".json")


def write_sidecar(path: Path, payload: Mapping) -> Path:
    """Write the sidecar atomically: temp -> replace, sort_keys, no NaN.

    A payload holding non-finite values is a DataGapError and writes nothing
    (R7 - allow_nan=False, surfaced as the viz terminal contract).
    """
    path = Path(path)
    try:
        text = json.dumps(
            jsonable(dict(payload)), indent=2, sort_keys=True, allow_nan=False
        )
    except ValueError as exc:
        raise DataGapError(
            make_gap(
                path.name,
                reason="non-finite sidecar payload",
                detail=f"{path} cannot be written: {exc}",
                source_path=str(path),
            )
        ) from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return path


def write_figure(
    fig: Any,
    *,
    png_path: Path,
    sidecar: Mapping,
    arrays: Mapping[str, ArrayLike],
) -> tuple[Path, Path]:
    """Save ``fig`` + sidecar with the KTD9 ordering guarantees.

    1. path contract: PNG outside ``results/`` (figures tree, KTD9);
    2. ``ensure_finite(arrays)`` - DataGapError before any file exists;
    3. PNG -> temp file, sha256 recorded as auxiliary info;
    4. sidecar written final (atomic) - the PNG only becomes visible after
       its sidecar exists, so a PNG-without-sidecar can never be observed;
    5. temp PNG -> replace into place (same figure_id overwrites).
    """
    png_path = Path(png_path)
    if RESULTS_DIRNAME in png_path.resolve().parts:
        raise ValueError(
            f"figures must be written outside the {RESULTS_DIRNAME}/ tree: {png_path}"
        )
    ensure_finite(arrays)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_png = png_path.with_name(png_path.name + ".tmp")
    try:
        fig.savefig(tmp_png, format="png")
        payload = dict(sidecar)
        payload["png_sha256"] = hashlib.sha256(tmp_png.read_bytes()).hexdigest()
        sc_path = write_sidecar(sidecar_path_for(png_path), payload)
    except BaseException:
        tmp_png.unlink(missing_ok=True)
        raise
    os.replace(tmp_png, png_path)
    return png_path, sc_path
