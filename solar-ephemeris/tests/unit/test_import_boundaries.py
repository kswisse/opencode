"""Import boundaries: SPICE isolation and layer rules (requirement 4).

Enforced by AST scan, not convention:

1. ``spiceypy``/``cspice`` may be imported ONLY in
   ``ephemeris/spice_backend.py``.
2. Core packages (physics, frames, integrators, simulation, analysis) must
   not import ``solar_ephemeris.ephemeris`` or SPICE at all.
3. Backend-agnostic ephemeris modules must not import SPICE (they talk to
   the ``ReferenceProvider`` protocol only).
4. ``frames/identifiers.py`` stays Layer 0 (no intra-project imports).
5. Belt-and-braces: a clean subprocess importing core + the ephemeris
   package must end with ``spiceypy`` absent from ``sys.modules``.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "solar_ephemeris"
SPICE_ROOTS = frozenset({"spiceypy", "cspice"})
ALLOWED_SPICE_FILES = frozenset({"ephemeris/spice_backend.py"})
CORE_PREFIXES = ("physics", "frames", "integrators", "simulation", "analysis")


def _source_files() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if "__pycache__" not in p.parts)


def _rel(path: Path) -> str:
    return path.relative_to(SRC).as_posix()


def _package_of(path: Path) -> list[str]:
    """Package parts for relative-import resolution (file's containing package)."""
    parts = _rel(path)[:-3].split("/")  # strip ".py"
    module_parts = ["solar_ephemeris", *parts]
    if module_parts[-1] == "__init__":
        module_parts = module_parts[:-1]
        return module_parts
    return module_parts[:-1]


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import — resolve against the package
                base = _package_of(path)
                drop = node.level - 1
                if drop:
                    base = base[: len(base) - drop]
                suffix = node.module.split(".") if node.module else []
                found.append(".".join([*base, *suffix]))
            elif node.module:
                found.append(node.module)
    return found


def test_spice_imported_only_in_spice_backend() -> None:
    violations: list[str] = []
    for path in _source_files():
        if any(mod.split(".")[0] in SPICE_ROOTS for mod in _imported_modules(path)):
            if _rel(path) not in ALLOWED_SPICE_FILES:
                violations.append(_rel(path))
    assert violations == [], f"SPICE imported outside spice_backend.py: {violations}"


def test_core_packages_never_import_ephemeris_or_spice() -> None:
    violations: list[str] = []
    for prefix in CORE_PREFIXES:
        for path in sorted((SRC / prefix).rglob("*.py")):
            for mod in _imported_modules(path):
                root = mod.split(".")[0]
                if root in SPICE_ROOTS or mod == "solar_ephemeris.ephemeris" or mod.startswith(
                    "solar_ephemeris.ephemeris."
                ):
                    violations.append(f"{_rel(path)} -> {mod}")
    assert violations == [], f"forbidden core imports: {violations}"


def test_ephemeris_modules_are_backend_agnostic() -> None:
    violations: list[str] = []
    for path in sorted((SRC / "ephemeris").rglob("*.py")):
        if _rel(path) in ALLOWED_SPICE_FILES:
            continue
        for mod in _imported_modules(path):
            if mod.split(".")[0] in SPICE_ROOTS:
                violations.append(f"{_rel(path)} -> {mod}")
    assert violations == [], f"non-backend modules import SPICE: {violations}"


def test_identifiers_stays_layer_zero() -> None:
    for mod in _imported_modules(SRC / "frames" / "identifiers.py"):
        assert not mod.startswith("solar_ephemeris"), mod


def test_core_import_does_not_load_spiceypy() -> None:
    code = (
        "import sys; "
        "import solar_ephemeris.physics.state, solar_ephemeris.simulation.engine, "
        "solar_ephemeris.analysis, solar_ephemeris.ephemeris; "
        "print('SPICE_LOADED' if 'spiceypy' in sys.modules else 'CLEAN')"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SRC.parent), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120
    )
    assert proc.returncode == 0, proc.stderr
    assert "CLEAN" in proc.stdout, f"spiceypy loaded on core import: {proc.stdout}"
