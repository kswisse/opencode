"""Static-first scientific visualization layer (Phase 6, KD2/KD3).

Import contract (R27/KTD3, enforced by ``tests/unit/test_viz_import_boundary``):
this package reads simulation/analysis output read-only — it never
instantiates ``SimulationEngine`` nor calls ``.run``/``.propagate``/``run_to_file``.

R29: importing this package must NOT import matplotlib — plotting happens only
inside individual ``plot_*`` modules, and render tests use ``importorskip`` so
Gate A stays green on machines without matplotlib.
"""

from __future__ import annotations
