"""Deterministic run persistence: trajectory arrays + machine-readable record.

Layout of one run directory::

    <out_dir>/trajectory.npz   # arrays (times, positions, velocities, gm, meta)
    <out_dir>/run_record.json  # config + hash + software version + timestamp

DETERMINISM NOTE: ``np.savez`` writes a zip container with an embedded
timestamp, so the FILE BYTES differ between identical runs by design.
Reproducibility is asserted on the ARRAYS AFTER LOADING (np.array_equal) and
on ``config_hash`` — never on raw file bytes.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from solar_ephemeris import __version__
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.physics.state import State, StateMeta
from solar_ephemeris.simulation.configuration import SimulationConfig
from solar_ephemeris.simulation.engine import SimulationEngine, Trajectory, TrajectoryMeta

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class RunRecord:
    schema_version: int
    config: SimulationConfig
    config_hash: str
    software_version: str
    run_timestamp_utc: str  # deliberately NOT part of config_hash
    trajectory_file: str | None

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "config": self.config.to_dict(),
            "config_hash": self.config_hash,
            "software_version": self.software_version,
            "run_timestamp_utc": self.run_timestamp_utc,
            "trajectory_file": self.trajectory_file,
        }


def _traj_meta_to_json(meta: TrajectoryMeta) -> str:
    payload = asdict(meta)
    sm = payload.pop("state_meta")
    payload["state_meta"] = sm
    payload["state_meta"]["frame"] = str(sm["frame"])
    payload["state_meta"]["time_scale"] = str(sm["time_scale"])
    return json.dumps(payload, sort_keys=True)


def _traj_meta_from_json(blob: str) -> TrajectoryMeta:
    payload = json.loads(blob)
    sm = payload.pop("state_meta")
    state_meta = StateMeta(
        frame=ReferenceFrame(sm["frame"]),
        origin=sm["origin"],
        epoch_jd=sm["epoch_jd"],
        time_scale=TimeScale(sm["time_scale"]),
        length_unit=sm["length_unit"],
        time_unit=sm["time_unit"],
        velocity_unit=sm["velocity_unit"],
        gm_unit=sm["gm_unit"],
        axis_note=sm["axis_note"],
    )
    return TrajectoryMeta(state_meta=state_meta, **payload)


def run_to_file(
    config: SimulationConfig,
    initial: State,
    out_dir: Path,
    *,
    sample_every: int = 1,
    registry=None,
) -> RunRecord:
    """Engine.run -> <out_dir>/trajectory.npz + run_record.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = SimulationEngine(config, registry=registry)
    traj = engine.run(initial, sample_every=sample_every)

    np.savez(
        out_dir / "trajectory.npz",
        times=traj.times,
        positions=traj.positions,
        velocities=traj.velocities,
        gm=traj.gm,
        body_names=np.array(traj.body_names),
        traj_meta_json=np.array(_traj_meta_to_json(traj.meta)),
    )

    record = RunRecord(
        schema_version=SCHEMA_VERSION,
        config=config,
        config_hash=config.config_hash(),
        software_version=__version__,
        run_timestamp_utc=datetime.now(timezone.utc).isoformat(),
        trajectory_file="trajectory.npz",
    )
    payload = record.to_dict()
    (out_dir / "run_record.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return record


def load_run(out_dir: Path) -> tuple[Trajectory, RunRecord]:
    """Re-read a run directory, reconstructing Trajectory + RunRecord."""
    out_dir = Path(out_dir)
    raw = json.loads((out_dir / "run_record.json").read_text(encoding="utf-8"))
    record = RunRecord(
        schema_version=raw["schema_version"],
        config=SimulationConfig.from_dict(raw["config"]),
        config_hash=raw["config_hash"],
        software_version=raw["software_version"],
        run_timestamp_utc=raw["run_timestamp_utc"],
        trajectory_file=raw["trajectory_file"],
    )
    with np.load(out_dir / "trajectory.npz", allow_pickle=False) as data:
        traj = Trajectory(
            times=data["times"],
            positions=data["positions"],
            velocities=data["velocities"],
            gm=data["gm"],
            body_names=tuple(str(n) for n in data["body_names"]),
            meta=_traj_meta_from_json(str(data["traj_meta_json"])),
        )
    return traj, record
