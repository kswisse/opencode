#!/usr/bin/env python3
"""Reproducibility script — generates all synthetic research data, runs QC,
statistical analysis, and produces all outputs.

Usage: python scripts/generate_all.py
"""
import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))


def main():
    print("=" * 60)
    print("School Heat Intelligence — Synthetic Research Pipeline")
    print("=" * 60)

    # 1. Generate synthetic environmental data
    print("\n[1/6] Generating synthetic environmental data...")
    from heat_intelligence.research.synthetic_generator import generate_synthetic_environmental
    env_data = generate_synthetic_environmental(
        seed=42,
        output_csv="data/research_synthetic_environmental.csv",
    )

    # 2. Generate synthetic student data
    print("\n[2/6] Generating synthetic student data...")
    from heat_intelligence.research.synthetic_students import generate_synthetic_students
    student_data = generate_synthetic_students(
        seed=42,
        output_csv="data/research_synthetic_students.csv",
    )

    # 3. Run QC
    print("\n[3/6] Running quality control...")
    from heat_intelligence.research.quality_control import run_qc, export_qc_report
    expected_zones = ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05"]
    qc_report = run_qc(env_data, expected_zones)
    export_qc_report(qc_report, "data/research_qc_report.json")

    # 4. Run statistical analysis
    print("\n[4/6] Running statistical analysis...")
    from heat_intelligence.research.statistics import (
        descriptive_stats, zone_comparison, correlation_analysis,
        regression_analysis, effect_sizes,
    )

    desc = descriptive_stats(env_data)
    print(f"  Descriptive stats: {len(desc)} zones analyzed")

    zc = zone_comparison(env_data)
    print(f"  Zone comparison: hot={zc['hot_mean']:.1f}°C, cool={zc['cool_mean']:.1f}°C, d={zc['cohens_d']:.3f}")

    corr = correlation_analysis(env_data)
    print(f"  Correlation: canopy-temp r={corr['pearson']['canopy_temperature']:.3f}")

    reg = regression_analysis(env_data)
    print(f"  Regression: slope={reg['slope']:.4f}, R²={reg['r_squared']:.4f}")

    es = effect_sizes(env_data)
    print(f"  Effect sizes: hot_vs_cool d={es['hot_vs_cool']['cohens_d']:.3f}")

    # 5. Generate all outputs
    print("\n[5/6] Generating outputs (tables + figures)...")
    from heat_intelligence.research.outputs import (
        generate_summary_stats, generate_correlation_matrix,
        generate_effect_sizes, generate_risk_by_zone,
        generate_exposure_ranking, generate_forecast_validation,
        generate_intervention_comparison, generate_figures,
    )
    from heat_intelligence.config import load_config

    config = load_config()

    generate_summary_stats(env_data)
    generate_correlation_matrix(env_data)
    generate_effect_sizes(env_data)
    generate_risk_by_zone(env_data, config)
    generate_exposure_ranking(env_data, config)

    # Forecast validation
    from heat_intelligence.forecast.predictor import evaluate_forecast
    zone_ids = list(set(r.zone_id for r in env_data))
    eval_results = []
    if zone_ids:
        eval_results = evaluate_forecast(env_data, config, zone_ids[0], holdout_hours=24)
    generate_forecast_validation(eval_results)

    # Intervention comparison
    from heat_intelligence.risk.engine import compute_risk_score
    from heat_intelligence.intervention.simulator import simulate_intervention
    zone_latest = {}
    for r in env_data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    interventions = []
    for zone_id, r in zone_latest.items():
        rs = compute_risk_score(r, config)
        scenario = {"canopy_pct": min(100.0, r.canopy_pct + 20.0)}
        iv = simulate_intervention(r, rs, scenario, config)
        interventions.append(iv)
    generate_intervention_comparison(interventions)

    # Generate figures
    generate_figures(env_data, config)

    # 6. Print summary
    print("\n[6/6] Summary")
    print("=" * 60)
    print(f"  Environmental readings: {len(env_data)}")
    print(f"  Student sessions:       {len(student_data)}")
    print(f"  QC overall pass:        {qc_report.overall_pass}")
    print(f"  Zones analyzed:         {len(desc)}")
    print(f"  Hot vs Cool diff:       {zc['difference']:.2f}°C (d={zc['cohens_d']:.3f})")
    print(f"  Canopy-Temp r:          {corr['pearson']['canopy_temperature']:.3f}")
    print(f"  Regression R2:          {reg['r_squared']:.4f}")
    print()
    print("  Generated files:")
    print("    data/research_synthetic_environmental.csv")
    print("    data/research_synthetic_students.csv")
    print("    data/research_qc_report.json")
    print("    data/research_outputs/summary_stats.csv")
    print("    data/research_outputs/correlation_matrix.csv")
    print("    data/research_outputs/effect_sizes.csv")
    print("    data/research_outputs/risk_by_zone.csv")
    print("    data/research_outputs/exposure_ranking.csv")
    print("    data/research_outputs/forecast_validation.csv")
    print("    data/research_outputs/intervention_comparison.csv")
    print("    data/research_outputs/fig/*.png")
    print()
    print("  WARNING: All results are SYNTHETIC - not empirical findings.")
    print("=" * 60)


if __name__ == "__main__":
    main()
