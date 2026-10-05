"""Research outputs generator — tables and figures.

Generates CSV tables and PNG figures for the research analysis.
All figures include the Vietnamese synthetic data warning annotation.
"""
import csv
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from heat_intelligence.models.schemas import InterventionResult, ZoneReading

SYNTHETIC_WARNING = "DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THỰC NGHIỆM"
MEASURED_WARNING = "DỮ LIỆU THỰC TẾ — CHƯA ĐƯỢC XÁC NHẬN BẰNG THỰC NGHIỆM"
DEFAULT_WARNING = SYNTHETIC_WARNING


def _get_warning_label(data: List[ZoneReading]) -> str:
    """Determine the appropriate warning label from data provenance."""
    if not data:
        return DEFAULT_WARNING
    provenances = set(r.provenance for r in data)
    from heat_intelligence.models.schemas import ProvenanceFlag
    if provenances == {ProvenanceFlag.MEASURED}:
        return MEASURED_WARNING
    if provenances == {ProvenanceFlag.SYNTHETIC}:
        return SYNTHETIC_WARNING
    return "DỮ LIỆU KẾT HỢP — CẦN XÁC NHẬN NGUỒN"

# Zone color map
ZONE_COLORS = {
    "zone_01": "#e74c3c",
    "zone_02": "#2ecc71",
    "zone_03": "#f39c12",
    "zone_04": "#3498db",
    "zone_05": "#9b59b6",
}

ZONE_LABELS = {
    "zone_01": "Playground",
    "zone_02": "Garden",
    "zone_03": "Courtyard",
    "zone_04": "Sports Field",
    "zone_05": "Canteen",
}


def _ensure_dirs(output_dir: str = "data/research_outputs"):
    """Create output directories."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, "fig").mkdir(parents=True, exist_ok=True)


def _save_csv(rows: List[Dict], fieldnames: List[str], filepath: str):
    """Save list of dicts as CSV."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_summary_stats(data: List[ZoneReading], output_dir: str = "data/research_outputs"):
    """Export descriptive statistics per zone as CSV."""
    from heat_intelligence.research.statistics import descriptive_stats
    stats = descriptive_stats(data)

    rows = []
    for zone_id, s in stats.items():
        rows.append({
            "zone_id": zone_id,
            "zone_name": ZONE_LABELS.get(zone_id, zone_id),
            "mean": s["mean"],
            "std": s["std"],
            "min": s["min"],
            "max": s["max"],
            "count": s["count"],
        })

    _save_csv(rows, ["zone_id", "zone_name", "mean", "std", "min", "max", "count"],
              f"{output_dir}/summary_stats.csv")
    print(f"  -> {output_dir}/summary_stats.csv")
    return rows


def generate_correlation_matrix(data: List[ZoneReading], output_dir: str = "data/research_outputs"):
    """Export correlation matrix as CSV."""
    from heat_intelligence.research.statistics import correlation_analysis
    corr = correlation_analysis(data)

    fieldnames = ["variable", "pearson", "spearman"]
    rows = [
        {"variable": "canopy_pct", "pearson": corr["pearson"]["canopy_temperature"],
         "spearman": corr["spearman"]["canopy_temperature"]},
        {"variable": "surface_type", "pearson": corr["pearson"]["surface_temperature"],
         "spearman": corr["spearman"]["surface_temperature"]},
    ]

    _save_csv(rows, fieldnames, f"{output_dir}/correlation_matrix.csv")
    print(f"  -> {output_dir}/correlation_matrix.csv")
    return rows


def generate_effect_sizes(data: List[ZoneReading], output_dir: str = "data/research_outputs"):
    """Export effect sizes as CSV."""
    from heat_intelligence.research.statistics import effect_sizes
    es = effect_sizes(data)

    rows = []
    for comparison, vals in es.items():
        rows.append({
            "comparison": comparison,
            "cohens_d": vals["cohens_d"],
            "group1_mean": vals.get("hot_mean") or vals.get("asphalt_mean", 0),
            "group2_mean": vals.get("cool_mean") or vals.get("grass_mean", 0),
            "group1_n": vals.get("hot_n") or vals.get("asphalt_n", 0),
            "group2_n": vals.get("cool_n") or vals.get("grass_n", 0),
        })

    _save_csv(rows, ["comparison", "cohens_d", "group1_mean", "group2_mean", "group1_n", "group2_n"],
              f"{output_dir}/effect_sizes.csv")
    print(f"  -> {output_dir}/effect_sizes.csv")
    return rows


def generate_risk_by_zone(data: List[ZoneReading], config, output_dir: str = "data/research_outputs"):
    """Export risk scores by zone as CSV."""
    from heat_intelligence.risk.engine import compute_risk_score

    # Get latest reading per zone
    zone_latest = {}
    for r in data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    rows = []
    for zone_id, r in sorted(zone_latest.items()):
        rs = compute_risk_score(r, config)
        rows.append({
            "zone_id": zone_id,
            "zone_name": ZONE_LABELS.get(zone_id, zone_id),
            "risk_score": rs.score,
            "risk_label": rs.label,
            "temperature": r.air_temperature,
            "surface_type": r.surface_type,
            "canopy_pct": r.canopy_pct,
        })

    _save_csv(rows, ["zone_id", "zone_name", "risk_score", "risk_label", "temperature",
                      "surface_type", "canopy_pct"],
              f"{output_dir}/risk_by_zone.csv")
    print(f"  -> {output_dir}/risk_by_zone.csv")
    return rows


def generate_exposure_ranking(data: List[ZoneReading], config, output_dir: str = "data/research_outputs"):
    """Export exposure scores ranked as CSV."""
    from heat_intelligence.exposure.calculator import compute_exposure
    from heat_intelligence.risk.engine import compute_risk_score

    # Get latest reading per zone
    zone_latest = {}
    for r in data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    rows = []
    for zone_id, r in sorted(zone_latest.items()):
        rs = compute_risk_score(r, config)
        es = compute_exposure(rs, r, config)
        rows.append({
            "zone_id": zone_id,
            "zone_name": ZONE_LABELS.get(zone_id, zone_id),
            "exposure_score": es.score,
            "risk_score": es.risk_score,
            "student_count": es.student_count,
            "exposure_hours": es.exposure_hours,
        })

    rows.sort(key=lambda x: x["exposure_score"], reverse=True)
    for i, row in enumerate(rows):
        row["rank"] = i + 1

    _save_csv(rows, ["rank", "zone_id", "zone_name", "exposure_score", "risk_score",
                      "student_count", "exposure_hours"],
              f"{output_dir}/exposure_ranking.csv")
    print(f"  -> {output_dir}/exposure_ranking.csv")
    return rows


def generate_forecast_validation(eval_results: List, output_dir: str = "data/research_outputs"):
    """Export forecast validation MAE/RMSE as CSV."""
    from heat_intelligence.research.statistics import forecast_validation
    fv = forecast_validation(eval_results)

    rows = fv.get("horizons", [])
    if rows:
        _save_csv(rows, ["horizon_hours", "mae", "rmse", "n_samples"],
                  f"{output_dir}/forecast_validation.csv")
        print(f"  -> {output_dir}/forecast_validation.csv")
    return rows


def generate_intervention_comparison(interventions: List[InterventionResult],
                                     output_dir: str = "data/research_outputs"):
    """Export intervention comparison as CSV."""
    rows = []
    for iv in interventions:
        rows.append({
            "zone_id": iv.zone_id,
            "zone_name": iv.zone_name,
            "baseline_risk": iv.baseline_risk,
            "simulated_risk": iv.simulated_risk,
            "relative_change_pct": iv.relative_change_pct,
        })

    if rows:
        _save_csv(rows, ["zone_id", "zone_name", "baseline_risk", "simulated_risk",
                          "relative_change_pct"],
                  f"{output_dir}/intervention_comparison.csv")
        print(f"  -> {output_dir}/intervention_comparison.csv")
    return rows


def generate_figures(data: List[ZoneReading], config=None,
                     output_dir: str = "data/research_outputs"):
    """Generate all research figures."""
    fig_dir = Path(output_dir, "fig")
    fig_dir.mkdir(parents=True, exist_ok=True)

    warning = _get_warning_label(data)

    _fig_campus_heatmap(data, fig_dir, warning=warning)
    _fig_canopy_vs_temp(data, fig_dir, warning=warning)
    _fig_diurnal_pattern(data, fig_dir, warning=warning)

    if config:
        _fig_forecast_vs_observed(data, config, fig_dir, warning=warning)
        _fig_exposure_ranking(data, config, fig_dir, warning=warning)
        _fig_intervention_comparison(data, config, fig_dir, warning=warning)


def _fig_campus_heatmap(data: List[ZoneReading], fig_dir: Path, warning: str = DEFAULT_WARNING):
    """Scatter plot of zones colored by temperature."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get latest reading per zone
    zone_latest = {}
    for r in data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    for zone_id, r in zone_latest.items():
        color = ZONE_COLORS.get(zone_id, "#95a5a6")
        ax.scatter(r.lon, r.lat, c=color, s=200, zorder=5, edgecolors="black", linewidth=0.5)
        ax.annotate(f"{ZONE_LABELS.get(zone_id, zone_id)}\n{r.air_temperature}°C",
                    (r.lon, r.lat), textcoords="offset points", xytext=(10, 10),
                    fontsize=9, fontweight="bold")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Campus Zone Temperatures — Latest Reading\n" + warning,
                 fontsize=10)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_campus_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_dir}/fig_campus_heatmap.png")


def _fig_canopy_vs_temp(data: List[ZoneReading], fig_dir: Path, warning: str = DEFAULT_WARNING):
    """Scatter plot of canopy % vs temperature with trend line."""
    fig, ax = plt.subplots(figsize=(8, 5))

    canopy = np.array([r.canopy_pct for r in data])
    temp = np.array([r.air_temperature for r in data])

    # Color by surface type
    surface_colors = {"asphalt": "#e74c3c", "concrete": "#f39c12", "grass": "#2ecc71"}
    colors = [surface_colors.get(r.surface_type, "#95a5a6") for r in data]
    ax.scatter(canopy, temp, c=colors, alpha=0.3, s=20)

    # Trend line
    if len(canopy) > 1:
        x_mean = np.mean(canopy)
        y_mean = np.mean(temp)
        slope = np.sum((canopy - x_mean) * (temp - y_mean)) / np.sum((canopy - x_mean) ** 2)
        intercept = y_mean - slope * x_mean
        x_line = np.linspace(0, 100, 100)
        ax.plot(x_line, slope * x_line + intercept, "k--", linewidth=1.5, label="Trend")
        r2 = 1 - np.sum((temp - (slope * canopy + intercept)) ** 2) / np.sum((temp - y_mean) ** 2)
        ax.text(0.05, 0.95, f"R² = {r2:.3f}", transform=ax.transAxes, fontsize=10,
                verticalalignment="top")

    ax.set_xlabel("Canopy Cover (%)")
    ax.set_ylabel("Air Temperature (°C)")
    ax.set_title("Canopy Cover vs Temperature\n" + warning, fontsize=10)
    ax.legend()

    # Legend for surface types
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=s) for s, c in surface_colors.items()]
    ax.legend(handles=legend_elements, loc="upper right")

    fig.tight_layout()
    fig.savefig(fig_dir / "fig_canopy_vs_temp.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_dir}/fig_canopy_vs_temp.png")


def _fig_diurnal_pattern(data: List[ZoneReading], fig_dir: Path, warning: str = DEFAULT_WARNING):
    """Line plot of temperature over time by zone."""
    fig, ax = plt.subplots(figsize=(12, 5))

    # Group by zone and sort by timestamp
    zone_data = {}
    for r in data:
        zone_data.setdefault(r.zone_id, []).append(r)

    for zone_id, readings in zone_data.items():
        readings.sort(key=lambda x: x.timestamp)
        timestamps = [r.timestamp for r in readings]
        temps = [r.air_temperature for r in readings]
        color = ZONE_COLORS.get(zone_id, "#95a5a6")
        ax.plot(timestamps, temps, color=color, linewidth=0.8, alpha=0.8,
                label=ZONE_LABELS.get(zone_id, zone_id))

    ax.set_xlabel("Time")
    ax.set_ylabel("Air Temperature (°C)")
    ax.set_title("Diurnal Temperature Pattern by Zone\n" + warning, fontsize=10)
    ax.legend(loc="upper left", fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d %H:%M"))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_diurnal_pattern.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_dir}/fig_diurnal_pattern.png")


def _fig_forecast_vs_observed(data: List[ZoneReading], config, fig_dir: Path,
                              warning: str = DEFAULT_WARNING):
    """Forecast vs actual risk scores."""
    from heat_intelligence.forecast.predictor import evaluate_forecast

    fig, ax = plt.subplots(figsize=(8, 5))

    # Evaluate for first zone
    zone_ids = list(set(r.zone_id for r in data))
    if zone_ids:
        evaluations = evaluate_forecast(data, config, zone_ids[0], holdout_hours=24)
        if evaluations:
            horizons = [e.horizon_hours for e in evaluations]
            maes = [e.mae for e in evaluations]
            rmses = [e.rmse for e in evaluations]

            x = np.arange(len(horizons))
            width = 0.35
            ax.bar(x - width / 2, maes, width, label="MAE", color="#3498db")
            ax.bar(x + width / 2, rmses, width, label="RMSE", color="#e74c3c")
            ax.set_xlabel("Forecast Horizon (hours)")
            ax.set_ylabel("Error")
            ax.set_xticks(x)
            ax.set_xticklabels([f"{h}h" for h in horizons])
            ax.legend()
        else:
            ax.text(0.5, 0.5, "Insufficient data for forecast evaluation",
                    transform=ax.transAxes, ha="center", va="center")

    ax.set_title("Forecast Validation — MAE/RMSE by Horizon\n" + warning, fontsize=10)
    fig.tight_layout()
    fig.savefig(fig_dir / "fig_forecast_vs_observed.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_dir}/fig_forecast_vs_observed.png")


def _fig_exposure_ranking(data: List[ZoneReading], config, fig_dir: Path,
                         warning: str = DEFAULT_WARNING):
    """Bar chart of exposure scores."""
    from heat_intelligence.exposure.calculator import compute_exposure
    from heat_intelligence.risk.engine import compute_risk_score

    fig, ax = plt.subplots(figsize=(8, 5))

    # Get latest reading per zone
    zone_latest = {}
    for r in data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    zone_ids = sorted(zone_latest.keys())
    scores = []
    labels = []
    for zone_id in zone_ids:
        r = zone_latest[zone_id]
        rs = compute_risk_score(r, config)
        es = compute_exposure(rs, r, config)
        scores.append(es.score)
        labels.append(ZONE_LABELS.get(zone_id, zone_id))

    colors = [ZONE_COLORS.get(zid, "#95a5a6") for zid in zone_ids]
    bars = ax.barh(labels, scores, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Exposure Score")
    ax.set_title("Student Exposure Ranking by Zone\n" + warning, fontsize=10)

    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig_exposure_ranking.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_dir}/fig_exposure_ranking.png")


def _fig_intervention_comparison(data: List[ZoneReading], config, fig_dir: Path,
                                warning: str = DEFAULT_WARNING):
    """Before/after intervention bar chart."""
    from heat_intelligence.risk.engine import compute_risk_score
    from heat_intelligence.intervention.simulator import simulate_intervention

    fig, ax = plt.subplots(figsize=(10, 5))

    # Get latest reading per zone
    zone_latest = {}
    for r in data:
        if r.zone_id not in zone_latest or r.timestamp > zone_latest[r.zone_id].timestamp:
            zone_latest[r.zone_id] = r

    zone_ids = sorted(zone_latest.keys())
    baselines = []
    simulated = []
    labels = []
    for zone_id in zone_ids:
        r = zone_latest[zone_id]
        rs = compute_risk_score(r, config)
        # Simulate: increase canopy by 20%
        scenario = {"canopy_pct": min(100.0, r.canopy_pct + 20.0)}
        iv = simulate_intervention(r, rs, scenario, config)
        baselines.append(iv.baseline_risk)
        simulated.append(iv.simulated_risk)
        labels.append(ZONE_LABELS.get(zone_id, zone_id))

    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width / 2, baselines, width, label="Baseline", color="#e74c3c")
    ax.bar(x + width / 2, simulated, width, label="+20% Canopy", color="#2ecc71")
    ax.set_ylabel("Risk Score")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_title("Intervention Simulation: Baseline vs +20% Canopy\n" + warning,
                 fontsize=10)

    fig.tight_layout()
    fig.savefig(fig_dir / "fig_intervention_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {fig_dir}/fig_intervention_comparison.png")
