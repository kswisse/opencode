"""Project body name ↔ NAIF SPICE body ID mapping.

Authority: NAIF body name/ID mapping (``req/naif_ids.html``) cross-checked
against the actual segment list of the pinned ``de440s.bsp``
(``aa_summaries.txt``: segments 1..9, 10 w.r.t. 0; 199 w.r.t. 1;
299 w.r.t. 2; 301 w.r.t. 3; 399 w.r.t. 3 — NO 499/599/699/799/899/999).

Mapping rules (requirement 5 — explicit, never index-based guessing):

- ``Earth`` → 399 (solid Earth + atmosphere, GM = 398600.435507 km³/s²).
  Mapping to 3 (EMB) would silently compare the project's solid-Earth GM
  against the Earth-Moon barycentre — the exact systematic Phase 3
  quantified (5.5 km / 4.67×10⁶ m). Deliberately NOT 3.
- ``Moon`` → 301 (lunar center w.r.t. Earth, chain resolves to EMB→SSB).
- ``Mars``..``Pluto`` → 4..9 (system barycentres). The kernel has no
  499/599/... segments because the project's single point mass with *system*
  GM corresponds to the system barycentre; planet-center IDs would fail at
  query time, which is the desired behaviour.
- ``EMB`` → 3 (optional, for lumped-GM checks).
- Anything else (``body1``, ``inline``, synthetic names) raises
  :class:`UnknownBodyMappingError` — no silent fallback.
"""

from __future__ import annotations

from typing import Final

from solar_ephemeris.ephemeris.types import UnknownBodyMappingError
from solar_ephemeris.physics.constants import GM_BY_BODY

#: Project body name → NAIF ID. Exact content asserted by
#: ``tests/unit/test_ephemeris_mapping.py`` (wrong-ID canary).
BODY_TO_NAIF: Final[dict[str, int]] = {
    "Sun": 10,
    "Mercury": 199,
    "Venus": 299,
    "Earth": 399,
    "Moon": 301,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "EMB": 3,  # Earth-Moon barycentre (lumped GM_E+GM_M checks only)
}

#: Inverse map (IDs are unique across the table above).
NAIF_TO_BODY: Final[dict[int, str]] = {naif: name for name, naif in BODY_TO_NAIF.items()}


def naif_id(name: str) -> int:
    """NAIF ID for a project body name. Raises :class:`UnknownBodyMappingError`."""
    try:
        return BODY_TO_NAIF[name]
    except KeyError:
        raise UnknownBodyMappingError(
            f"no NAIF ID mapping for body {name!r}; add it to "
            "ephemeris/mapping.py explicitly (never guess IDs)"
        ) from None


def body_name(naif: int) -> str:
    """Project body name for a NAIF ID. Raises :class:`UnknownBodyMappingError`."""
    try:
        return NAIF_TO_BODY[int(naif)]
    except KeyError:
        raise UnknownBodyMappingError(
            f"NAIF ID {naif!r} is not a mapped project body"
        ) from None


def assert_registry_mappable(names: tuple[str, ...] | list[str]) -> None:
    """Raise if any configured body lacks a NAIF mapping (pre-comparison gate)."""
    for name in names:
        naif_id(name)


# Every physics-registry body must be mappable, or the reference pipeline
# could never compare a legal configuration.
_UNMAPPABLE = sorted(set(GM_BY_BODY) - set(BODY_TO_NAIF))
if _UNMAPPABLE:  # pragma: no cover — import-time contract, tested directly
    raise RuntimeError(f"GM_BY_BODY bodies lack NAIF mappings: {_UNMAPPABLE}")
