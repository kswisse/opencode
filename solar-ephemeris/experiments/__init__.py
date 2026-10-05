"""Phase 5 experiment package (design phase5-experiment-design.md §7 rows 2-4).

``_common`` is importable WITHOUT a kernel (no spiceypy import at module
scope); the driver ``run_phase5`` imports SPICE lazily inside the
kernel-using subcommands.
"""
