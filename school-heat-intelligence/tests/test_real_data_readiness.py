"""Real-data readiness test.

Creates a small fixture representing measured data with MEASURED provenance
and verifies that the full pipeline (CSV → loader → QC → analysis → outputs)
works end-to-end.

DO NOT treat fixture results as scientific findings.
"""
import csv
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from heat_intelligence.data.loader import load_data
from heat_intelligence.config import load_config
from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading
from heat_intelligence.research.quality_control import run_qc, export_qc_report
from heat_intelligence.research.statistics import (
    descriptive_stats, zone_comparison, correlation_analysis,
    regression_analysis, effect_sizes, forecast_validation,
    intervention_comparison,
)
from heat_intelligence.research.report_generator import generate_report


def _create_measured_fixture(tmp_path: str) -> str:
    """Create a small CSV fixture with MEASURED provenance."""
    csv_path = Path(tmp_path) / "measured_fixture.csv"
    rows = []
    base = datetime(2026, 10, 15, 7, 0, 0)

    zones = [
        ("zone_01", "Playground", 10.7626, 106.6822, "asphalt", 10.0, 15.0),
        ("zone_02", "Garden", 10.7627, 106.6824, "grass", 60.0, 70.0),
        ("zone_03", "Courtyard", 10.7625, 106.6821, "concrete", 25.0, 40.0),
    ]

    for day in range(3):
        for hour_offset, (zid, zname, lat, lon, surf, canopy, shade) in enumerate(zones):
            ts = base + timedelta(days=day, hours=7 + hour_offset * 2)
            # Realistic temperatures: asphalt hot, grass cool, concrete mid
            temp = 30.0 + hour_offset * 2.0
            if surf == "asphalt":
                temp += 2.0
            elif surf == "grass":
                temp -= 1.5

            rows.append({
                "timestamp": ts.isoformat(),
                "zone_id": zid,
                "zone_name": zname,
                "lat": lat,
                "lon": lon,
                "air_temperature": round(temp, 1),
                "humidity": round(70.0 - hour_offset * 3.0, 1),
                "wind_speed": round(1.5 + hour_offset * 0.3, 2),
                "ndvi": "",
                "canopy_pct": canopy,
                "shade_pct": shade,
                "surface_type": surf,
                "student_count": 30 if hour_offset == 1 else 0,
                "exposure_hours": 1.0,
                "provenance": "measured",
            })

    fieldnames = [
        "timestamp", "zone_id", "zone_name", "lat", "lon",
        "air_temperature", "humidity", "wind_speed", "ndvi",
        "canopy_pct", "shade_pct", "surface_type",
        "student_count", "exposure_hours", "provenance",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return str(csv_path)


class TestRealDataReadiness:
    """Test that the full pipeline works with MEASURED provenance data."""

    def test_full_pipeline_with_measured_data(self, tmp_path):
        """CSV → loader → QC → analysis → outputs with MEASURED provenance."""
        # 1. Create fixture
        csv_path = _create_measured_fixture(str(tmp_path))

        # 2. Load data
        data = load_data(csv_path)
        assert len(data) == 9  # 3 zones × 3 time points

        # 3. Verify provenance is MEASURED
        for r in data:
            assert r.provenance == ProvenanceFlag.MEASURED

        # 4. Run QC
        expected_zones = ["zone_01", "zone_02", "zone_03"]
        qc_report = run_qc(data, expected_zones)
        assert qc_report.total_rows == 9
        assert len(qc_report.missing_zones) == 0

        # 5. Export QC report
        qc_path = str(tmp_path / "qc_report.json")
        export_qc_report(qc_report, qc_path)
        assert Path(qc_path).exists()

        # 6. Run statistics
        desc = descriptive_stats(data)
        assert len(desc) == 3
        for zone_id in expected_zones:
            assert zone_id in desc

        zc = zone_comparison(data)
        assert "hot_mean" in zc
        assert "cool_mean" in zc

        corr = correlation_analysis(data)
        assert "pearson" in corr
        assert "spearman" in corr

        reg = regression_analysis(data)
        assert "slope" in reg
        assert "r_squared" in reg

        es = effect_sizes(data)
        assert "hot_vs_cool" in es
        assert "asphalt_vs_grass" in es

        # 7. Generate report
        report_path = str(tmp_path / "analysis-report.md")
        config = load_config()
        report = generate_report(
            data=data,
            qc_results={
                "total_rows": qc_report.total_rows,
                "missing_values": qc_report.missing_values,
                "duplicate_timestamps": qc_report.duplicate_timestamps,
                "invalid_ranges": qc_report.invalid_ranges,
                "missing_zones": qc_report.missing_zones,
                "temporal_gaps": qc_report.temporal_gaps,
                "overall_pass": qc_report.overall_pass,
                "zone_comparison": zc,
            },
            stats_results=desc,
            correlation_results=corr,
            regression_results=reg,
            effect_size_results=es,
            forecast_results={},
            intervention_results={},
            output_path=report_path,
        )
        assert Path(report_path).exists()
        assert "MEASURED" in report or "THỰC TẾ" in report

    def test_provenance_preserved_through_pipeline(self, tmp_path):
        """Verify provenance is not lost during loading and analysis."""
        csv_path = _create_measured_fixture(str(tmp_path))
        data = load_data(csv_path)

        # All data should be MEASURED
        provenances = set(r.provenance for r in data)
        assert provenances == {ProvenanceFlag.MEASURED}

        # Statistics should work with MEASURED data
        desc = descriptive_stats(data)
        assert len(desc) > 0

        # Report should identify data as measured
        report_path = str(tmp_path / "report.md")
        report = generate_report(
            data=data,
            qc_results={"total_rows": 9, "missing_values": {}, "duplicate_timestamps": [],
                        "invalid_ranges": {}, "missing_zones": [], "temporal_gaps": [],
                        "overall_pass": True},
            stats_results=desc,
            correlation_results={},
            regression_results={},
            effect_size_results={},
            forecast_results={},
            intervention_results={},
            output_path=report_path,
        )
        assert "MEASURED" in report or "THỰC TẾ" in report

    def test_synthetic_vs_measured_report_labeling(self, tmp_path):
        """Verify that synthetic data gets SYNTHETIC label in report."""
        from heat_intelligence.research.synthetic_generator import generate_synthetic_environmental

        # Generate a small synthetic dataset
        env_data = generate_synthetic_environmental(seed=42)

        desc = descriptive_stats(env_data)
        report_path = str(tmp_path / "synthetic_report.md")
        report = generate_report(
            data=env_data,
            qc_results={"total_rows": len(env_data), "missing_values": {},
                        "duplicate_timestamps": [], "invalid_ranges": {},
                        "missing_zones": [], "temporal_gaps": [],
                        "overall_pass": True},
            stats_results=desc,
            correlation_results={},
            regression_results={},
            effect_size_results={},
            forecast_results={},
            intervention_results={},
            output_path=report_path,
        )
        assert "SYNTHETIC" in report or "MÔ PHỎNG" in report
