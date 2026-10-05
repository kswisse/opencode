"""Import boundary: viz không bao giờ thực thi simulation (R27, KTD3).

AST scan theo cấu trúc ``tests/unit/test_import_boundaries.py``, quét cây
``visualization/``:

1. Cấm token thực thi: import/nstantiate ``SimulationEngine``, gọi ``.run(``/
   ``.propagate(``, ``run_to_file``, ``run_reproducible``, ``run_phase5``.
2. Allow-list import nội dự án: chỉ ``physics``, ``frames``, ``simulation``,
   ``ephemeris``, ``analysis`` (viz đọc ``Trajectory`` dataclass từ
   ``simulation.engine`` — cấm tuyệt đối sẽ tự thà chính nó vì 5/7 module
   ``analysis/`` hard-import ``Trajectory``).
3. Import ``solar_ephemeris.visualization`` không được load matplotlib
   (R29 — Gate A xanh trên máy chưa cài matplotlib).

Kernel-free, không import matplotlib trong chính module test này.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "solar_ephemeris"
VIZ = SRC / "visualization"

FORBIDDEN_NAMES = frozenset({"SimulationEngine", "run_to_file", "run_reproducible", "run_phase5"})
FORBIDDEN_CALL_ATTRS = frozenset({"run", "propagate"})
ALLOWED_PROJECT_ROOTS = frozenset({"physics", "frames", "simulation", "ephemeris", "analysis"})


def _source_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.rglob("*.py") if "__pycache__" not in p.parts)


def _rel(path: Path, directory: Path) -> str:
    return path.relative_to(directory).as_posix()


def _package_of(path: Path) -> list[str]:
    """Package parts for relative-import resolution (file's containing package)."""
    parts = _rel(path, SRC)[:-3].split("/")  # strip ".py"
    module_parts = ["solar_ephemeris", *parts]
    if module_parts[-1] == "__init__":
        return module_parts[:-1]
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


def _scan(directory: Path) -> list[str]:
    """Return violations found by AST scan over every .py file under directory."""
    violations: list[str] = []
    for path in _source_files(directory):
        label = _rel(path, directory)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for mod in _imported_modules(path):
            parts = mod.split(".")
            if parts[0] == "solar_ephemeris":
                if len(parts) > 1 and parts[1] not in ALLOWED_PROJECT_ROOTS:
                    violations.append(f"{label} -> forbidden project import {mod}")
            if any(p in FORBIDDEN_NAMES for p in parts):
                violations.append(f"{label} -> forbidden import {mod}")
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in FORBIDDEN_NAMES:
                        violations.append(f"{label}:{node.lineno} -> forbidden import name {alias.name!r}")
            if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
                violations.append(f"{label}:{node.lineno} -> forbidden name {node.id!r}")
            elif isinstance(node, ast.Attribute):
                if node.attr in FORBIDDEN_NAMES:
                    violations.append(f"{label}:{node.lineno} -> forbidden attribute {node.attr!r}")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in FORBIDDEN_CALL_ATTRS:
                    violations.append(f"{label}:{node.lineno} -> forbidden call .{node.func.attr}(")
    return violations


def test_visualization_tree_passes_ast_scan() -> None:
    assert VIZ.is_dir(), f"visualization package not scaffolded: {VIZ}"
    violations = _scan(VIZ)
    assert violations == [], f"viz executes simulation: {violations}"


def test_fake_viz_file_using_simulation_engine_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "fake_engine.py").write_text(
        "from solar_ephemeris.simulation.engine import SimulationEngine\n"
        "engine = SimulationEngine()\n",
        encoding="utf-8",
    )
    assert _scan(tmp_path), "AST scan missed SimulationEngine usage"


def test_fake_viz_file_calling_run_to_file_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "fake_run.py").write_text(
        "def save(engine):\n    engine.run_to_file('out.json')\n",
        encoding="utf-8",
    )
    assert _scan(tmp_path), "AST scan missed run_to_file call"


def test_fake_viz_file_importing_experiments_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "fake_exp.py").write_text(
        "import experiments.run_phase5\n",
        encoding="utf-8",
    )
    assert _scan(tmp_path), "AST scan missed experiments.run_phase5 import"


def test_allowed_intra_project_imports_pass_scan(tmp_path: Path) -> None:
    (tmp_path / "clean.py").write_text(
        "from solar_ephemeris.simulation.engine import Trajectory\n"
        "from solar_ephemeris.ephemeris import kernel_manifest\n"
        "from solar_ephemeris import analysis\n",
        encoding="utf-8",
    )
    assert _scan(tmp_path) == [], "allow-listed imports wrongly flagged"


def test_viz_package_imports_clean_of_matplotlib() -> None:
    code = (
        "import sys; "
        "import solar_ephemeris.visualization; "
        "print('MATPLOTLIB_LOADED' if 'matplotlib' in sys.modules else 'CLEAN')"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SRC.parent), *([env["PYTHONPATH"]] if env.get("PYTHONPATH") else [])]
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=120
    )
    assert proc.returncode == 0, proc.stderr
    assert "CLEAN" in proc.stdout, f"matplotlib loaded on viz package import: {proc.stdout}"


def test_boundary_test_module_itself_does_not_import_matplotlib() -> None:
    mods = _imported_modules(Path(__file__).resolve())
    assert "matplotlib" not in mods, "boundary test must stay importable without matplotlib"
