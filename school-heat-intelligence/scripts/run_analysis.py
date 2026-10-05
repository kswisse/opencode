#!/usr/bin/env python3
"""Unified research analysis pipeline.

Accepts an input dataset (synthetic or real) and produces a complete
analysis: QC, statistics, figures, tables, and report.

Usage:
    python scripts/run_analysis.py --input data/research_synthetic_environmental.csv
    python scripts/run_analysis.py --input data/real_measurements.csv

The same pipeline works for both synthetic and real data.
Provenance is preserved from the input data, not inferred from filenames.
"""
import argparse
import json
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from heat_intelligence.data.loader import load_data
from heat_intelligence.config import load_config
from heat_intelligence.models.schemas import ProvenanceFlag
from heat_intelligence.research.quality_control import run_qc, export_qc_report
from heat_intelligence.research.statistics import (
    descriptive_stats, zone_comparison, correlation_analysis,
    regression_analysis, effect_sizes, forecast_validation,
    intervention_comparison,
)
from heat_intelligence.research.outputs import (
    generate_summary_stats, generate_correlation_matrix,
    generate_effect_sizes, generate_risk_by_zone,
    generate_exposure_ranking, generate_forecast_validation,
    generate_intervention_comparison, generate_figures,
)
from heat_intelligence.research.report_generator import generate_report


def _determine_provenance(data):
    """Determine the dominant provenance from the dataset."""
    if not data:
        return ProvenanceFlag.SYNTHETIC
    provenances = set(r.provenance for r in data)
    if provenances == {ProvenanceFlag.MEASURED}:
        return ProvenanceFlag.MEASURED
    return ProvenanceFlag.SYNTHETIC


def _get_output_dir(input_path: str) -> str:
    """Determine output directory based on input."""
    input_name = Path(input_path).stem
    if "synthetic" in input_name:
        return "data/research_outputs"
    return "data/real_outputs"


def main():
    parser = argparse.ArgumentParser(
        description="School Heat Intelligence — Unified Research Analysis Pipeline"
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to input CSV (synthetic or real measurements)"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory (default: auto-determined from input)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    args = parser.parse_args()

    input_path = args.input
    output_dir = args.output_dir or _get_output_dir(input_path)

    print("=" * 60)
    print("School Heat Intelligence — Research Analysis Pipeline")
    print("=" * 60)
    print(f"\nInput:  {input_path}")
    print(f"Output: {output_dir}/")

    # 1. Load data
    print("\n[1/7] Loading data...")
    data = load_data(input_path)
    provenance = _determine_provenance(data)
    print(f"  Loaded {len(data)} readings")
    print(f"  Provenance: {provenance.value}")

    # 2. Load config
    config = load_config()

    # 3. Quality control
    print("\n[2/7] Running quality control...")
    expected_zones = sorted(set(r.zone_id for r in data))
    qc_report = run_qc(data, expected_zones)
    qc_dict = {
        "total_rows": qc_report.total_rows,
        "missing_values": qc_report.missing_values,
        "duplicate_timestamps": qc_report.duplicate_timestamps,
        "invalid_ranges": qc_report.invalid_ranges,
        "missing_zones": qc_report.missing_zones,
        "temporal_gaps": qc_report.temporal_gaps,
        "overall_pass": qc_report.overall_pass,
    }
    export_qc_report(qc_report, f"{output_dir}/qc_report.json")
    print(f"  Overall pass: {qc_report.overall_pass}")

    # 4. Statistical analysis
    print("\n[3/7] Running statistical analysis...")
    desc_stats = descriptive_stats(data)
    zc = zone_comparison(data)
    corr = correlation_analysis(data)
    reg = regression_analysis(data)
    es = effect_sizes(data)

    print(f"  Zones: {len(desc_stats)}")
    print(f"  Hot vs Cool: {es['hot_vs_cool']['cohens_d']:.3f} Cohen's d")
    print(f"  Canopy-Temp r: {corr['pearson']['canopy_temperature']:.3f}")

    # 5. Forecast validation
    print("\n[4/7] Running forecast validation...")
    from heat_intelligence.forecast.predictor import evaluate_forecast
    zone_ids = list(set(r.zone_id for r in data))
    eval_results = []
    if zone_ids:
        eval_results = evaluate_forecast(data, config, zone_ids[0], holdout_hours=24)
    fv = forecast_validation(eval_results)
    print(f"  Avg MAE: {fv.get('avg_mae', 'N/A')}")

    # 6. Intervention comparison
    print("\n[5/7] Running intervention comparison...")
    from heat_intelligence.risk.engine import compute_risk_score
    from heat_intelligence.intervention.simulator import simulate_intervention
    zone_latest = {}
    for r in data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    interventions = []
    for zone_id, r in zone_latest.items():
        rs = compute_risk_score(r, config)
        scenario = {"canopy_pct": min(100.0, r.canopy_pct + 20.0)}
        iv = simulate_intervention(r, rs, scenario, config)
        interventions.append(iv)
    ic = intervention_comparison(interventions)
    print(f"  Avg change: {ic.get('avg_relative_change_pct', 'N/A')}%")

    # 7. Generate outputs
    print("\n[6/7] Generating outputs...")
    generate_summary_stats(data, output_dir)
    generate_correlation_matrix(data, output_dir)
    generate_effect_sizes(data, output_dir)
    generate_risk_by_zone(data, config, output_dir)
    generate_exposure_ranking(data, config, output_dir)
    generate_forecast_validation(eval_results, output_dir)
    generate_intervention_comparison(interventions, output_dir)
    generate_figures(data, config, output_dir)

    # 8. Generate report
    print("\n[7/7] Generating research report...")
    report_path = f"docs/research/analysis-report.md"
    generate_report(
        data=data,
        qc_results={**qc_dict, "zone_comparison": zc},
        stats_results=desc_stats,
        correlation_results=corr,
        regression_results=reg,
        effect_size_results=es,
        forecast_results=fv,
        intervention_results=ic,
        output_path=report_path,
    )

    # Summary
    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)
    print(f"  Data type: {provenance.value}")
    print(f"  Readings: {len(data)}")
    print(f"  Zones: {len(desc_stats)}")
    print(f"  QC pass: {qc_report.overall_pass}")
    print(f"  Hot-Cool diff: {es['hot_vs_cool']['hot_mean'] - es['hot_vs_cool']['cool_mean']:.2f}°C")
    print(f"  Canopy-Temp r: {corr['pearson']['canopy_temperature']:.3f}")
    print(f"  Regression R²: {reg['r_squared']:.4f}")
    print(f"\n  Outputs: {output_dir}/")
    print(f"  Report:  {report_path}")
    print()

    if provenance == ProvenanceFlag.SYNTHETIC:
        print("  WARNING: All results are SYNTHETIC — not empirical findings.")
    else:
        print("  NOTE: Results are from measured data — verify before drawing conclusions.")
    print("=" * 60)


if __name__ == "__main__":
    main()
