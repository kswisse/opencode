"""Frame and time-scale identifiers (Layer 0: no intra-project imports).

Extending an enum with a NEW member per phase is allowed; renaming or
removing an existing member is NOT (it would silently change the meaning of
stored metadata).
"""

from __future__ import annotations

from enum import StrEnum


class ReferenceFrame(StrEnum):
    # Phase 1-2: origin = barycenter of EXACTLY the bodies being propagated
    # (the active subset), axes inertial and aligned with the initial
    # conditions, right-handed. This is the only frame in which
    # sum(m*v) = 0 and angular momentum is conserved for the chosen subset.
    # NOTE: subset barycenter != solar system barycenter (other planets are
    # absent); Phase 4 introduces SSB_ICRS and frames/transforms.py converts
    # explicitly at the comparison boundary.
    ACTIVE_BODIES_BARYCENTRIC = "active_bodies_barycentric"
    # Phase 4: solar-system barycenter + ICRF axes (DE440/SPICE native).
    SSB_ICRS = "ssb_icrs"


class TimeScale(StrEnum):
    TDB = "TDB"  # default; DE440/SPICE produce TDB
    TT = "TT"
    UTC = "UTC"  # includes leap seconds — do not mix with TDB/TT silently
    SI = "SI"  # uniform seconds for synthetic two-body tests; no conversion
