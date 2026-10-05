"""Simulation engine — the ONLY module that wires the force model
(``physics.gravity``) to the integrators (``integrators``).

Boundary-normalization law: input states are aligned to the configured body
order BY NAME here, at the boundary, never inside the stepping loop, and a
state whose frame/epoch/time scale disagrees with the configuration is
rejected rather than silently relabelled.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris import __version__
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.integrators.base import Acceleration, get_integrator
from solar_ephemeris.physics.bodies import BodyRegistry
from solar_ephemeris.physics.gravity import newtonian_acceleration
from solar_ephemeris.physics.state import State, StateMeta
from solar_ephemeris.simulation.configuration import SimulationConfig


@dataclass(frozen=True, slots=True)
class TrajectoryMeta:
    state_meta: StateMeta
    integrator: str
    integrator_order: int
    dt: float
    sample_every: int
    n_steps: int
    config_hash: str
    software_version: str
    schema_version: int = 1


def _check_finite_nonempty(arr: np.ndarray, shape_tail: tuple[int, ...], label: str) -> None:
    if arr.ndim != len(shape_tail) + 1 or arr.shape[1:] != shape_tail:
        raise ValueError(f"{label} has shape {arr.shape}, expected (M, {shape_tail})")
    if arr.shape[0] == 0:
        raise ValueError(f"{label} must contain at least one sample")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{label} contains NaN or inf")


@dataclass(frozen=True, slots=True)
class Trajectory:
    times: NDArray[np.float64]  # (M,), seconds since epoch (NOT absolute JD)
    positions: NDArray[np.float64]  # (M, N, 3), m
    velocities: NDArray[np.float64]  # (M, N, 3), m/s
    gm: NDArray[np.float64]  # (N,), m^3/s^2, aligned with body_names
    body_names: tuple[str, ...]
    meta: TrajectoryMeta

    def __post_init__(self) -> None:
        names = tuple(self.body_names)
        if not names:
            raise ValueError("body_names must not be empty")
        times = np.array(self.times, dtype=np.float64, copy=True)
        pos = np.array(self.positions, dtype=np.float64, copy=True)
        vel = np.array(self.velocities, dtype=np.float64, copy=True)
        gm = np.array(self.gm, dtype=np.float64, copy=True)
        _check_finite_nonempty(times, (), "times")
        n = len(names)
        _check_finite_nonempty(pos, (n, 3), "positions")
        _check_finite_nonempty(vel, (n, 3), "velocities")
        if gm.shape != (n,):
            raise ValueError(f"gm must have shape ({n},), got {gm.shape}")
        if not np.all(gm > 0.0):
            raise ValueError("all gm values must be > 0")
        if not np.all(np.diff(times) > 0.0):
            raise ValueError("times must be strictly increasing")
        object.__setattr__(self, "times", times)
        object.__setattr__(self, "positions", pos)
        object.__setattr__(self, "velocities", vel)
        object.__setattr__(self, "gm", gm)
        object.__setattr__(self, "body_names", names)

    @property
    def n_samples(self) -> int:
        return int(self.times.shape[0])

    @property
    def n_bodies(self) -> int:
        return len(self.body_names)


class SimulationEngine:
    def __init__(
        self,
        config: SimulationConfig,
        registry: BodyRegistry | None = None,
        accel: Acceleration | None = None,
    ) -> None:
        self._config = config
        registry = registry or BodyRegistry.default()
        resolved = registry.resolve(config.bodies)
        self._bodies = tuple(b.name for b in resolved)
        self._gm = np.array([b.gm for b in resolved], dtype=np.float64)
        self._accel: Acceleration = (
            accel
            if accel is not None
            else newtonian_acceleration(self._gm, guard_m=config.guard_m)
        )
        self._integrator = get_integrator(config.integrator)

    @property
    def gm(self) -> NDArray[np.float64]:
        return self._gm.copy()

    @property
    def bodies(self) -> tuple[str, ...]:
        return self._bodies

    @property
    def config(self) -> SimulationConfig:
        return self._config

    def _align(self, state: State) -> State:
        """Reorder an input state to the configured body order BY NAME.

        Rejects mismatched body sets, frames, time scales and epochs instead of
        normalizing them silently (MASTERPLAN: never mix frames silently).
        """
        cfg = self._config
        if set(state.body_names) != set(self._bodies):
            raise ValueError(
                f"state bodies {state.body_names} do not match "
                f"configured bodies {self._bodies}"
            )
        if state.meta.frame != cfg.frame:
            raise ValueError(
                f"state frame {state.meta.frame} != config frame {cfg.frame}; "
                "transform explicitly before propagating"
            )
        if state.meta.time_scale != cfg.time_scale:
            raise ValueError(
                f"state time_scale {state.meta.time_scale} != "
                f"config time_scale {cfg.time_scale}"
            )
        if state.meta.epoch_jd != cfg.epoch_jd:
            raise ValueError(
                f"state epoch {state.meta.epoch_jd} != config epoch {cfg.epoch_jd}"
            )
        order = [state.body_names.index(name) for name in self._bodies]
        return State(
            positions=state.positions[order],
            velocities=state.velocities[order],
            body_names=self._bodies,
            meta=state.meta,
        )

    def propagate(self, initial: State, n_steps: int) -> State:
        """Integrate without recording a trajectory (endpoint-error tests)."""
        if n_steps < 1:
            raise ValueError(f"n_steps must be >= 1, got {n_steps}")
        state = self._align(initial)
        cfg = self._config
        integ = self._integrator
        q = state.positions
        v = state.velocities
        for step in range(1, n_steps + 1):
            q, v = integ.step(q, v, cfg.dt, self._accel, step * cfg.dt)
        return State(
            positions=q,
            velocities=v,
            body_names=self._bodies,
            meta=state.meta,
        )

    def run(self, initial: State, *, sample_every: int = 1) -> Trajectory:
        if sample_every < 1:
            raise ValueError(f"sample_every must be >= 1, got {sample_every}")
        state = self._align(initial)
        cfg = self._config
        integ = self._integrator
        n_steps = cfg.n_steps
        if n_steps < 1:
            raise ValueError("config duration/dt yields no integration steps")

        q = state.positions
        v = state.velocities

        times = [0.0]
        positions = [q.copy()]
        velocities = [v.copy()]
        for step in range(1, n_steps + 1):
            q, v = integ.step(q, v, cfg.dt, self._accel, step * cfg.dt)
            if step % sample_every == 0:
                times.append(step * cfg.dt)
                positions.append(q.copy())
                velocities.append(v.copy())

        meta = TrajectoryMeta(
            state_meta=StateMeta(
                frame=cfg.frame,
                origin=state.meta.origin,
                epoch_jd=cfg.epoch_jd,
                time_scale=cfg.time_scale,
            ),
            integrator=integ.name,
            integrator_order=integ.order,
            dt=cfg.dt,
            sample_every=sample_every,
            n_steps=n_steps,
            config_hash=cfg.config_hash(),
            software_version=__version__,
        )
        return Trajectory(
            times=np.array(times, dtype=np.float64),
            positions=np.array(positions, dtype=np.float64),
            velocities=np.array(velocities, dtype=np.float64),
            gm=self._gm.copy(),
            body_names=self._bodies,
            meta=meta,
        )
