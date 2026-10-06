"""``FigureSpec`` rows and the ``FIGURE_REGISTRY`` of Fig-01..Fig-13 (R25)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class FigureSpec:
    """One row of the HTD figure table (design doc, "Bộ figure cụ thể")."""

    id: str
    title: str
    feature: str
    function: str
    records: str
    source: str
    variant: str
    state: str


#: R25 - Fig-01..Fig-13, fields verbatim from the HTD table.
#: ``variant`` is the same full-§6d record for all. The dict is derived
#: from the tuple so each figure id exists exactly once.
_FIGURE_SPECS: Final[tuple[FigureSpec, ...]] = (
    FigureSpec(
        id="fig-01",
        title="Quỹ đạo hệ trong SSB-ICRS (XY, AU)",
        feature="V1",
        function="plot_trajectory",
        records="results/experiment_C/tier_T*",
        source="npz trực tiếp",
        variant="full §6d",
        state="kernel-agnostic",
    ),
    FigureSpec(
        id="fig-02",
        title="Zoom quỹ đạo Đất–Trăng",
        feature="V1",
        function="plot_trajectory",
        records="results/experiment_C/tier_T2",
        source="npz trực tiếp",
        variant="full §6d",
        state="kernel-agnostic",
    ),
    FigureSpec(
        id="fig-03",
        title="Bố cục 3D tĩnh 10 body",
        feature="V2",
        function="plot_trajectory",
        records="results/experiment_C/tier_T4",
        source="npz trực tiếp",
        variant="full §6d",
        state="kernel-agnostic",
    ),
    FigureSpec(
        id="fig-04",
        title="Model vs DE440 (Đất)",
        feature="V3",
        function="plot_model_vs_reference",
        records="results/experiment_C/tier_T2",
        source="lookup read-only (KTD6)",
        variant="full §6d",
        state="cần kernel",
    ),
    FigureSpec(
        id="fig-05",
        title="Model vs fixture (V3 kernel-free)",
        feature="V3",
        function="plot_model_vs_reference",
        records="results/experiment_E/horizon_1d",
        source="lookup read-only (KTD6)",
        variant="full §6d",
        state="kernel-free",
    ),
    FigureSpec(
        id="fig-06",
        title="Lỗi vị trí theo thời gian (formal D 7d)",
        feature="V4",
        function="plot_position_error",
        records="results/experiment_D/T{1,2}_7d",
        source="payload stored (normalize)",
        variant="full §6d",
        state="stored",
    ),
    FigureSpec(
        id="fig-07",
        title="Lỗi vị trí per-body theo tier (+gap 8 body)",
        feature="V4",
        function="plot_position_error",
        records="results/experiment_C/tier_T*",
        source="payload stored (normalize)",
        variant="full §6d",
        state="stored",
    ),
    FigureSpec(
        id="fig-08",
        title="Lỗi vận tốc per-body",
        feature="V5",
        function="plot_velocity_error",
        records="results/experiment_C/tier_T*",
        source="payload stored (normalize)",
        variant="full §6d",
        state="stored",
    ),
    FigureSpec(
        id="fig-09",
        title="Conservation: năng lượng/động lượng/động lượng góc",
        feature="V6",
        function="plot_conservation",
        records="results/experiment_C/tier_T2",
        source="npz + analysis (derived)",
        variant="full §6d",
        state="derived",
    ),
    FigureSpec(
        id="fig-10",
        title="Convergence A1: lỗi cuối vs N + observed orders + floor",
        feature="V7",
        function="plot_convergence",
        records="results/experiment_A1/* + *_orders.json",
        source="*_orders.json, analysis.json",
        variant="full §6d",
        state="aggregate",
    ),
    FigureSpec(
        id="fig-11",
        title="A2 divisor ratios + B ref-lattice (cảnh báo floor-dominated)",
        feature="V7",
        function="plot_convergence",
        records="results/experiment_A2/analysis.json, results/experiment_B/ref_summary.json",
        source="*_orders.json, analysis.json",
        variant="full §6d",
        state="aggregate",
    ),
    FigureSpec(
        id="fig-12",
        title="Ảnh hưởng số body (signal vs control)",
        feature="V8",
        function="plot_body_count",
        records="results/experiment_C/* + analysis.json",
        source="payload stored + signals",
        variant="full §6d",
        state="stored",
    ),
    FigureSpec(
        id="fig-13",
        title="Lỗi theo horizon 1/30/90/365d + annotation phân biệt",
        feature="V9",
        function="plot_horizon_error",
        records="results/experiment_E/horizon_*",
        source="payload stored + growth_class",
        variant="full §6d",
        state="stored",
    ),
)

FIGURE_REGISTRY: Final[dict[str, FigureSpec]] = {spec.id: spec for spec in _FIGURE_SPECS}
