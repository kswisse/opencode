"""Integrator interface — the force seam.

The integrator knows only the :class:`Acceleration` protocol; it never imports
``physics.gravity``. ``simulation.engine`` is the single module that wires the
two together, so the force model can change (general relativity corrections,
velocity-dependent terms) without touching any integrator.

NOTE (documented trade-off): the protocol signature includes ``v`` and ``t``
even though Newtonian gravity uses neither. If a future force model makes
acceleration velocity-dependent, velocity-Verlet becomes an approximate
splitting and is no longer strictly symplectic — a Phase 3+ consequence, not a
Phase 2 bug.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class Acceleration(Protocol):
    def __call__(
        self,
        q: NDArray[np.float64],  # (N, 3) positions, m
        v: NDArray[np.float64],  # (N, 3) velocities, m/s
        t: float,  # seconds since epoch
    ) -> NDArray[np.float64]:  # (N, 3) accelerations, m/s^2
        ...


class Integrator(ABC):
    """Stateless stepper: no cached acceleration, no hidden state.

    The extra acceleration evaluation this costs velocity-Verlet buys
    deterministic, cache-free reproducibility; caching ``a`` is a Phase 5+
    optimization allowed only if bitwise-determinism tests still pass.
    """

    name: ClassVar[str]
    order: ClassVar[int]

    @abstractmethod
    def step(
        self,
        q: NDArray[np.float64],
        v: NDArray[np.float64],
        dt: float,
        accel: Acceleration,
        t: float,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Advance (q, v) from time t to t + dt.

        Returns NEW arrays; inputs are never modified in place.
        The returned pair is at the SAME time level t + dt (never a
        half-kick velocity — recording that would inject an O(dt) error
        into every velocity comparison).
        """


_INTEGRATORS: dict[str, type[Integrator]] = {}


def register_integrator(cls: type[Integrator]) -> type[Integrator]:
    _INTEGRATORS[cls.name] = cls
    return cls


def get_integrator(name: str) -> Integrator:
    try:
        return _INTEGRATORS[name]()
    except KeyError:
        raise ValueError(
            f"unknown integrator {name!r}; available: {sorted(_INTEGRATORS)}"
        ) from None
