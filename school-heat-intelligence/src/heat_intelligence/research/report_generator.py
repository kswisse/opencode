"""Research report generator.

Generates a Markdown research analysis report that automatically
distinguishes between synthetic and measured data findings.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading


def _determine_data_type(data: List[ZoneReading]) -> str:
    """Determine if data is synthetic, measured, or mixed."""
    if not data:
        return "unknown"
    provenances = set(r.provenance for r in data)
    if provenances == {ProvenanceFlag.SYNTHETIC}:
        return "synthetic"
    if provenances == {ProvenanceFlag.MEASURED}:
        return "measured"
    return "mixed"


def _data_type_label(data_type: str) -> str:
    labels = {
        "synthetic": "SYNTHETIC (MÔ PHỎNG)",
        "measured": "MEASURED (THỰC TẾ)",
        "mixed": "MIXED (KẾT HỢP)",
        "unknown": "UNKNOWN",
    }
    return labels.get(data_type, "UNKNOWN")


def _data_type_warning(data_type: str) -> str:
    warnings = {
        "synthetic": (
            "KẾT QUẢ DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THỰC NGHIỆM.\n"
            "All results are from synthetic data — NOT empirical findings."
        ),
        "measured": (
            "KẾT QUẢ DỮ LIỆU THỰC TẾ — CẦN XÁC NHẬN BẰNG PHÂN TÍCH THÊM.\n"
            "Results are from measured data but have not been peer-reviewed."
        ),
        "mixed": (
            "KẾT QUẢ KẾT HỢP DỮ LIỆU MÔ PHỎNG VÀ THỰC TẾ.\n"
            "Results combine synthetic and measured data — interpret with caution."
        ),
    }
    return warnings.get(data_type, "Data type unknown.")


def generate_report(
    data: List[ZoneReading],
    qc_results: Dict[str, Any],
    stats_results: Dict[str, Any],
    correlation_results: Dict[str, Any],
    regression_results: Dict[str, Any],
    effect_size_results: Dict[str, Any],
    forecast_results: Dict[str, Any],
    intervention_results: Dict[str, Any],
    output_path: str = "docs/research/analysis-report.md",
    student_data_available: bool = False,
) -> str:
    """Generate a complete research analysis report.

    Returns the report content as a string and writes to output_path.
    """
    data_type = _determine_data_type(data)
    label = _data_type_label(data_type)
    warning = _data_type_warning(data_type)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append(f"# Research Analysis Report")
    lines.append(f"")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Data type:** {label}")
    lines.append(f"")
    lines.append(f"> {warning}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 1. Dataset description
    lines.append(f"## 1. Dataset Description")
    lines.append(f"")
    n_readings = len(data)
    zone_ids = sorted(set(r.zone_id for r in data))
    n_zones = len(zone_ids)
    n_days = len(set(r.timestamp.date() for r in data))
    provenances = set(r.provenance.value for r in data)
    lines.append(f"- **Total readings:** {n_readings}")
    lines.append(f"- **Zones:** {n_zones} ({', '.join(zone_ids)})")
    lines.append(f"- **Days:** {n_days}")
    lines.append(f"- **Provenance:** {', '.join(provenances)}")
    lines.append(f"")

    # 2. Variables
    lines.append(f"## 2. Variables")
    lines.append(f"")
    lines.append(f"### Environmental (measured/imported)")
    lines.append(f"- `air_temperature` (°C)")
    lines.append(f"- `humidity` (%)")
    lines.append(f"- `wind_speed` (m/s)")
    lines.append(f"- `canopy_pct` (%)")
    lines.append(f"- `shade_pct` (%)")
    lines.append(f"- `surface_type` (categorical)")
    lines.append(f"- `student_count` (count)")
    lines.append(f"- `exposure_hours` (hours/day)")
    lines.append(f"")
    if student_data_available:
        lines.append(f"### Student-level (synthetic)")
        lines.append(f"- `thermal_sensation` (ordinal -3 to +3)")
        lines.append(f"- `thermal_comfort` (ordinal 1–5)")
        lines.append(f"- `cognitive_score` (0–20)")
        lines.append(f"- `reaction_time_ms` (ms)")
        lines.append(f"- `activity_before`, `clothing`, `hydration` (categorical)")
        lines.append(f"")

    # 3. Methods
    lines.append(f"## 3. Methods")
    lines.append(f"")
    lines.append(f"### Statistical analysis")
    lines.append(f"- Descriptive statistics (mean, std, min, max per zone)")
    lines.append(f"- Zone comparison (hot vs cool): Cohen's d effect size")
    lines.append(f"- Correlation: Pearson and Spearman (canopy, surface, temperature)")
    lines.append(f"- Regression: OLS (temperature ~ canopy_pct)")
    lines.append(f"- Forecast validation: holdout MAE/RMSE per horizon")
    lines.append(f"- Intervention simulation: baseline vs +20% canopy scenario")
    lines.append(f"")
    lines.append(f"### Assumptions")
    lines.append(f"- All weights and coefficients are illustrative heuristics, NOT empirically calibrated")
    lines.append(f"- Intervention effects are scenario projections, NOT measured outcomes")
    lines.append(f"- No causal claims — all associations are exploratory")
    lines.append(f"")

    # 4. Quality control
    lines.append(f"## 4. Quality Control")
    lines.append(f"")
    lines.append(f"- **Total rows:** {qc_results.get('total_rows', 'N/A')}")
    lines.append(f"- **Missing values:** {qc_results.get('missing_values', {})}")
    lines.append(f"- **Duplicate timestamps:** {len(qc_results.get('duplicate_timestamps', []))}")
    lines.append(f"- **Invalid ranges:** {qc_results.get('invalid_ranges', {})}")
    lines.append(f"- **Missing zones:** {qc_results.get('missing_zones', [])}")
    lines.append(f"- **Temporal gaps:** {len(qc_results.get('temporal_gaps', []))}")
    lines.append(f"- **Overall pass:** {qc_results.get('overall_pass', 'N/A')}")
    lines.append(f"")

    # 5. Descriptive statistics
    lines.append(f"## 5. Descriptive Statistics")
    lines.append(f"")
    lines.append(f"| Zone | Mean (°C) | Std | Min | Max | N |")
    lines.append(f"|------|-----------|-----|-----|-----|---|")
    for zone_id, stats in stats_results.items():
        lines.append(
            f"| {zone_id} | {stats['mean']} | {stats['std']} | {stats['min']} | {stats['max']} | {stats['count']} |"
        )
    lines.append(f"")

    # 6. Zone comparison
    lines.append(f"## 6. Zone Comparison (Hot vs Cool)")
    lines.append(f"")
    zc = qc_results.get("zone_comparison", stats_results.get("zone_comparison", {}))
    if effect_size_results:
        hot_vs_cool = effect_size_results.get("hot_vs_cool", {})
        lines.append(f"- **Hot zones mean:** {hot_vs_cool.get('hot_mean', 'N/A')}°C (n={hot_vs_cool.get('hot_n', 'N/A')})")
        lines.append(f"- **Cool zones mean:** {hot_vs_cool.get('cool_mean', 'N/A')}°C (n={hot_vs_cool.get('cool_n', 'N/A')})")
        lines.append(f"- **Difference:** {hot_vs_cool.get('hot_mean', 0) - hot_vs_cool.get('cool_mean', 0):.2f}°C")
        lines.append(f"- **Cohen's d:** {hot_vs_cool.get('cohens_d', 'N/A')}")
    lines.append(f"")

    # 7. Correlation
    lines.append(f"## 7. Correlation Analysis")
    lines.append(f"")
    if correlation_results:
        pearson = correlation_results.get("pearson", {})
        spearman = correlation_results.get("spearman", {})
        lines.append(f"| Variable | Pearson r | Spearman ρ |")
        lines.append(f"|----------|-----------|------------|")
        lines.append(f"| Canopy–Temperature | {pearson.get('canopy_temperature', 'N/A')} | {spearman.get('canopy_temperature', 'N/A')} |")
        lines.append(f"| Surface–Temperature | {pearson.get('surface_temperature', 'N/A')} | {spearman.get('surface_temperature', 'N/A')} |")
        lines.append(f"- **N:** {correlation_results.get('n', 'N/A')}")
    lines.append(f"")

    # 8. Regression
    lines.append(f"## 8. Regression Analysis")
    lines.append(f"")
    if regression_results:
        lines.append(f"- **Model:** temperature ~ canopy_pct")
        lines.append(f"- **Slope:** {regression_results.get('slope', 'N/A')} °C per % canopy")
        lines.append(f"- **Intercept:** {regression_results.get('intercept', 'N/A')}")
        lines.append(f"- **R²:** {regression_results.get('r_squared', 'N/A')}")
        lines.append(f"- **N:** {regression_results.get('n', 'N/A')}")
        lines.append(f"- **Interpretation:** {regression_results.get('interpretation', 'N/A')}")
    lines.append(f"")

    # 9. Forecast validation
    lines.append(f"## 9. Forecast Validation")
    lines.append(f"")
    if forecast_results and forecast_results.get("horizons"):
        lines.append(f"| Horizon | MAE | RMSE | Samples |")
        lines.append(f"|---------|-----|------|---------|")
        for h in forecast_results["horizons"]:
            lines.append(f"| {h['horizon_hours']}h | {h['mae']} | {h['rmse']} | {h['n_samples']} |")
        lines.append(f"- **Average MAE:** {forecast_results.get('avg_mae', 'N/A')}")
        lines.append(f"- **Average RMSE:** {forecast_results.get('avg_rmse', 'N/A')}")
    else:
        lines.append(f"No forecast evaluation results available.")
    lines.append(f"")

    # 10. Intervention comparison
    lines.append(f"## 10. Intervention Comparison")
    lines.append(f"")
    if intervention_results and intervention_results.get("interventions"):
        lines.append(f"| Zone | Baseline | Simulated | Change (%) |")
        lines.append(f"|------|----------|-----------|------------|")
        for iv in intervention_results["interventions"]:
            lines.append(
                f"| {iv['zone_name']} | {iv['baseline_risk']} | {iv['simulated_risk']} | {iv['relative_change_pct']:+.1f}% |"
            )
        lines.append(f"- **Average change:** {intervention_results.get('avg_relative_change_pct', 'N/A')}%")
    lines.append(f"")

    # 11. Limitations
    lines.append(f"## 11. Limitations")
    lines.append(f"")
    lines.append(f"1. All weights and coefficients are illustrative heuristics, not empirically calibrated")
    lines.append(f"2. Intervention effects are scenario projections, not measured outcomes")
    lines.append(f"3. No causal claims — all associations are exploratory")
    lines.append(f"4. Forecast is a baseline — not validated against held-out field data")
    lines.append(f"5. Single-sensor spatial comparison: zones measured sequentially, not simultaneously")
    lines.append(f"6. Surface factors are categorical, not fixed temperature corrections")
    if data_type == "synthetic":
        lines.append(f"7. **ALL RESULTS ARE SYNTHETIC** — generated for pipeline demonstration, not empirical findings")
    lines.append(f"")

    # 12. What must be rerun
    lines.append(f"## 12. What Must Be Rerun After Real Data Collection")
    lines.append(f"")
    lines.append(f"After collecting real measured data, the following must be rerun:")
    lines.append(f"")
    lines.append(f"1. **Quality control** on real measurements")
    lines.append(f"2. **Descriptive statistics** on real measurements")
    lines.append(f"3. **Zone comparison** with real temperature data")
    lines.append(f"4. **Correlation analysis** with real variables")
    lines.append(f"5. **Regression analysis** with real data")
    lines.append(f"6. **Forecast validation** against real measurements")
    lines.append(f"7. **Effect sizes** from real data")
    lines.append(f"8. **Figures** regenerated from real data")
    lines.append(f"9. **This report** regenerated with real data")
    lines.append(f"")
    lines.append(f"Command: `python scripts/run_analysis.py --input data/real_measurements.csv`")
    lines.append(f"")

    # Footer
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Report generated by School Heat Intelligence Research Pipeline.*")
    lines.append(f"*{warning}*")

    report_content = "\n".join(lines)

    # Write to file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report_content, encoding="utf-8")
    print(f"Report generated -> {output}")

    return report_content
