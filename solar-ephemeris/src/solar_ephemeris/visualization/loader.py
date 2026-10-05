"""Read-only record/trajectory loading for the viz layer (U2, R3/R5/R9).

Every failure on disk surfaces as a ``DataGapError`` carrying structured
gap dicts - the charts render a gap banner instead of a traceback.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from solar_ephemeris.simulation.runner import Trajectory, load_trajectory_npz

from .gaps import DataGapError, make_gap

RECORD_FILENAME = "experiment_record.json"
TRAJECTORY_FILENAME = "trajectory.npz"
RESULTS_DIRNAME = "results"

#: Section-6d provenance a complete record carries; a field that is absent
#: OR null counts as missing (surfaced in LoadedRecord.missing_provenance).
REQUIRED_PROVENANCE_FIELDS = (
    "experiment_id",
    "epoch",
    "bodies",
    "initial_condition_source",
    "integrator",
    "timestep",
    "duration",
    "reference_dataset",
    "reference_frame",
    "reference_origin",
    "time_scale",
    "units",
    "software_version",
    "configuration_hash",
    "output_hash",
)


@dataclass(frozen=True, slots=True)
class LoadedRecord:
    record_dir: Path  # requested dir, resolved (the source record)
    record: dict  # source record JSON as read
    resolved_dir: Path  # dir after following the reused_from chain
    resolved_record: dict  # record at resolved_dir
    reused_from: str | None  # source's declared target (relative), None if direct
    reused_chain: tuple[str, ...]  # every hop followed, in order
    missing_provenance: tuple[str, ...]  # REQUIRED fields absent/null in `record`


def _gap(name: str, reason: str, detail: str, source_path: Path) -> DataGapError:
    return DataGapError(make_gap(name, reason=reason, detail=detail, source_path=str(source_path)))


def _results_root(path: Path) -> Path:
    parts = path.parts
    if RESULTS_DIRNAME not in parts:
        raise _gap(
            f"{RESULTS_DIRNAME}/ directory",
            "outside results root",
            f"record path {path} is not inside a {RESULTS_DIRNAME}/ directory",
            path,
        )
    return Path(*parts[: parts.index(RESULTS_DIRNAME) + 1])


def _read_record_json(path: Path) -> dict:
    if not path.is_file():
        raise _gap(RECORD_FILENAME, "missing", f"{path} does not exist", path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _gap(RECORD_FILENAME, "unreadable", f"{path} cannot be read: {exc}", path)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _gap(RECORD_FILENAME, "unreadable", f"{path} is not valid JSON: {exc}", path)
    if not isinstance(payload, dict):
        raise _gap(
            RECORD_FILENAME,
            "unrecognized shape",
            f"{path} holds {type(payload).__name__}, expected a JSON object",
            path,
        )
    return payload


def _check_hash(source: dict, target: dict, source_path: Path) -> None:
    src_hash = source.get("configuration_hash")
    dst_hash = target.get("configuration_hash")
    if src_hash is None or dst_hash is None or src_hash != dst_hash:
        raise _gap(
            "configuration_hash",
            "configuration_hash mismatch",
            f"reused record has {src_hash!r}, target record has {dst_hash!r}",
            source_path,
        )


def _missing_provenance(record: dict) -> tuple[str, ...]:
    return tuple(field for field in REQUIRED_PROVENANCE_FIELDS if record.get(field) is None)


def load_record(record_dir: Path) -> LoadedRecord:
    """Read experiment_record.json, following reused_from redirects (R9).

    A direct record resolves to itself; a reused record resolves to its
    target after a configuration_hash equality check on every hop.
    """
    record_dir = Path(record_dir).resolve()
    root = _results_root(record_dir)
    source_record = _read_record_json(record_dir / RECORD_FILENAME)

    visited = {record_dir}
    chain: list[str] = []
    current_dir, current = record_dir, source_record

    while True:
        reused = current.get("reused_from")
        if reused is None:
            return LoadedRecord(
                record_dir=record_dir,
                record=source_record,
                resolved_dir=current_dir,
                resolved_record=current,
                reused_from=source_record.get("reused_from"),
                reused_chain=tuple(chain),
                missing_provenance=_missing_provenance(source_record),
            )
        if not isinstance(reused, str) or not reused.strip():
            raise _gap(
                "reused_from",
                "invalid redirect",
                f"reused_from is {reused!r}, expected a non-empty relative path",
                current_dir / RECORD_FILENAME,
            )
        target_dir = (root / reused).resolve()
        if not target_dir.is_relative_to(root):
            raise _gap(
                "reused_from",
                "redirect escapes results root",
                f"reused_from {reused!r} resolves outside {root}",
                current_dir / RECORD_FILENAME,
            )
        if target_dir in visited:
            raise _gap(
                "reused_from",
                "redirect cycle",
                f"reused_from chain loops back to {target_dir}",
                current_dir / RECORD_FILENAME,
            )
        target_record = _read_record_json(target_dir / RECORD_FILENAME)
        _check_hash(current, target_record, current_dir / RECORD_FILENAME)

        chain.append(reused)
        visited.add(target_dir)
        current_dir, current = target_dir, target_record


def load_trajectory_from(loaded: LoadedRecord) -> Trajectory:
    """Load the trajectory.npz of an already-resolved record (no re-read)."""
    npz_path = loaded.resolved_dir / TRAJECTORY_FILENAME
    if not npz_path.is_file():
        raise _gap(
            TRAJECTORY_FILENAME,
            "missing",
            f"{npz_path} not found; reused_from={loaded.reused_from or '(none)'} "
            f"resolved_dir={loaded.resolved_dir}",
            npz_path,
        )
    try:
        return load_trajectory_npz(npz_path)
    except (OSError, ValueError, KeyError) as exc:
        raise _gap(TRAJECTORY_FILENAME, "unreadable", str(exc), npz_path) from exc


def load_trajectory(record_dir: Path) -> Trajectory:
    """Load the trajectory.npz belonging to record_dir's resolved record."""
    return load_trajectory_from(load_record(record_dir))
