"""DE440-derived initial conditions (requirement 16, R4).

``reference_state_to_model_state`` is the ONLY sanctioned bridge from
reference states (SSB-centred, DE440) into a model initial ``State``:
per-body ``get_state`` → translation-only recenter by the project's own GMs
→ ``State(frame=ACTIVE_BODIES_BARYCENTRIC, …, axis_note=ICRF…)``.

The axis_note is an orientation claim (plan §6.2): model axes are
ICRF-aligned iff the initial conditions came from here. Synthetic circular
ICs are orientation-mismatched by construction (body-1-on-+x convention) and
must never be presented as reference-derived — which is why ``ic_source`` in
the comparison layer is a required, recorded string, never inferred.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from solar_ephemeris.ephemeris.mapping import naif_id
from solar_ephemeris.ephemeris.reference import ReferenceProvider, get_state
from solar_ephemeris.frames.identifiers import ReferenceFrame, TimeScale
from solar_ephemeris.frames.transforms import recenter_ssb_to_model
from solar_ephemeris.physics.constants import (
    GM_BY_BODY,
    GM_EARTH_MOON_BARYCENTER,
)
from solar_ephemeris.physics.state import State, StateMeta

ICRF_AXIS_NOTE = "ICRF-aligned (derived from DE440 reference states)"


def _gm_for(bodies: tuple[str, ...]) -> NDArray[np.float64]:
    """Project GMs for the configuration (the weights the model will use).

    ``EMB`` is a valid mapping target (NAIF 3) but is not a GM_BY_BODY key —
    its gravitational parameter is the derived Earth+Moon sum; every other
    mapped body comes straight from the DE440-sourced table.
    """
    values: list[float] = []
    for name in bodies:
        if name in GM_BY_BODY:
            values.append(GM_BY_BODY[name])
        elif name == "EMB":
            values.append(GM_EARTH_MOON_BARYCENTER)
        else:
            raise KeyError(
                f"no project GM for body {name!r}; add it to "
                "physics.constants.GM_BY_BODY with provenance before using it "
                "in initial conditions"
            )
    return np.array(values, dtype=np.float64)


def reference_state_to_model_state(
    provider: ReferenceProvider,
    *,
    bodies: Sequence[str],
    epoch_jd: float,
) -> State:
    """Build a model-frame initial ``State`` from reference states.

    Steps: validate the body list → per-body ``get_state`` (façade: mapping,
    frame, center, TDB and coverage all checked) → ``recenter_ssb_to_model``
    (translation only, project-GM weights) → ``State`` with explicit
    ``origin=barycenter(...)`` and the ICRF axis_note.

    Raises:
        ValueError: empty or duplicate body list.
        UnknownBodyMappingError: a body has no NAIF mapping.
        CoverageError / TimeScaleMismatchError / …: from the façade.
    """
    names = tuple(bodies)
    if not names:
        raise ValueError("bodies must be non-empty")
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate bodies: {names!r}")

    pos = np.empty((len(names), 3), dtype=np.float64)
    vel = np.empty((len(names), 3), dtype=np.float64)
    for i, name in enumerate(names):
        naif_id(name)  # explicit mapping gate (requirement 5), before query
        state = get_state(provider, body=name, epoch_jd=epoch_jd)
        pos[i] = state.position_m
        vel[i] = state.velocity_ms

    gm = _gm_for(names)
    pos_rel, vel_rel, _r_origin, _v_origin = recenter_ssb_to_model(pos, vel, gm, names)
    return State(
        positions=pos_rel,
        velocities=vel_rel,
        body_names=names,
        meta=StateMeta(
            frame=ReferenceFrame.ACTIVE_BODIES_BARYCENTRIC,
            origin=f"barycenter({', '.join(names)})",
            epoch_jd=epoch_jd,
            time_scale=TimeScale.TDB,
            axis_note=ICRF_AXIS_NOTE,
        ),
    )
