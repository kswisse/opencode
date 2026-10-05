"""Configurable body registry: name -> gravitational parameter GM.

This module holds DATA, never a default system configuration. Which bodies a
simulation runs is decided by ``SimulationConfig.bodies``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from solar_ephemeris.physics.constants import GM_BY_BODY, GM_SOURCES


class UnknownBodyError(KeyError):
    """Raised when a requested body name is not in the registry."""


@dataclass(frozen=True, slots=True)
class Body:
    name: str
    gm: float  # m^3/s^2, SI, always > 0
    source: str = ""  # provenance string for the GM value

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Body name must be non-empty")
        if not (self.gm > 0.0):
            raise ValueError(f"GM for {self.name!r} must be > 0, got {self.gm!r}")


class BodyRegistry:
    """Mutable-at-construction registry of bodies.

    Order is significant only where the caller supplies it (:meth:`resolve`
    preserves the caller's sequence exactly and never sorts).
    """

    def __init__(
        self,
        gm_map: Mapping[str, float] | None = None,
        sources: Mapping[str, str] | None = None,
    ) -> None:
        sources = dict(sources or {})
        gm_map = dict(gm_map or {})
        self._bodies: dict[str, Body] = {}
        for name, gm in gm_map.items():
            self._bodies[name] = Body(name=name, gm=gm, source=sources.get(name, ""))

    @classmethod
    def default(cls) -> BodyRegistry:
        """Registry pre-loaded with DE440 GM values for all known bodies."""
        return cls(gm_map=GM_BY_BODY, sources=GM_SOURCES)

    def register(self, name: str, gm: float, source: str = "") -> None:
        if name in self._bodies:
            raise ValueError(f"Body {name!r} already registered")
        self._bodies[name] = Body(name=name, gm=gm, source=source)

    def get(self, name: str) -> Body:
        try:
            return self._bodies[name]
        except KeyError:
            raise UnknownBodyError(name) from None

    def __contains__(self, name: object) -> bool:
        return name in self._bodies

    def names(self) -> tuple[str, ...]:
        return tuple(self._bodies)

    def resolve(self, names: Sequence[str]) -> tuple[Body, ...]:
        """Return bodies in the EXACT order given. Raises on unknown/duplicate."""
        seen: set[str] = set()
        out: list[Body] = []
        for name in names:
            if name in seen:
                raise ValueError(f"Duplicate body name in configuration: {name!r}")
            seen.add(name)
            out.append(self.get(name))
        return tuple(out)
