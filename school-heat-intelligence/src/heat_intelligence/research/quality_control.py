"""Research data quality control module.

Reports data quality issues including missing values, duplicates,
out-of-range values, missing zones, and temporal gaps.
"""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Tuple

from heat_intelligence.models.schemas import ZoneReading


@dataclass
class QCReport:
    """Quality control report for a set of ZoneReading records."""
    total_rows: int
    missing_values: Dict[str, int] = field(default_factory=dict)
    duplicate_timestamps: List[Tuple[str, str]] = field(default_factory=list)
    invalid_ranges: Dict[str, int] = field(default_factory=dict)
    missing_zones: List[str] = field(default_factory=list)
    temporal_gaps: List[str] = field(default_factory=list)
    overall_pass: bool = True


def run_qc(readings: List[ZoneReading], expected_zones: List[str]) -> QCReport:
    """Run quality control checks on a list of ZoneReading records.

    Checks:
    - Missing values (None/empty in required fields)
    - Duplicate (timestamp, zone_id) pairs
    - Out-of-range values (temperature 15–50°C, humidity 0–100%, wind 0–50 m/s)
    - All expected zones present
    - Temporal gaps > 1 hour within each zone
    """
    report = QCReport(total_rows=len(readings))

    # Check for missing values
    required_fields = [
        "timestamp", "zone_id", "zone_name", "air_temperature",
        "humidity", "wind_speed", "canopy_pct", "shade_pct",
        "surface_type", "student_count", "exposure_hours",
    ]

    for r in readings:
        d = r.model_dump()
        for field_name in required_fields:
            val = d.get(field_name)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                report.missing_values[field_name] = report.missing_values.get(field_name, 0) + 1

    # Check for duplicate (timestamp, zone_id) pairs
    seen = {}
    for r in readings:
        key = (r.timestamp.isoformat(), r.zone_id)
        if key in seen:
            report.duplicate_timestamps.append(key)
        seen[key] = True

    # Check for out-of-range values
    for r in readings:
        if not (15.0 <= r.air_temperature <= 50.0):
            report.invalid_ranges["air_temperature"] = report.invalid_ranges.get("air_temperature", 0) + 1
        if not (0.0 <= r.humidity <= 100.0):
            report.invalid_ranges["humidity"] = report.invalid_ranges.get("humidity", 0) + 1
        if not (0.0 <= r.wind_speed <= 50.0):
            report.invalid_ranges["wind_speed"] = report.invalid_ranges.get("wind_speed", 0) + 1

    # Check for missing zones
    found_zones = set(r.zone_id for r in readings)
    report.missing_zones = [z for z in expected_zones if z not in found_zones]

    # Check for temporal gaps > 1 hour within each zone
    zone_readings: Dict[str, List[ZoneReading]] = {}
    for r in readings:
        zone_readings.setdefault(r.zone_id, []).append(r)

    for zone_id, zone_list in zone_readings.items():
        sorted_list = sorted(zone_list, key=lambda x: x.timestamp)
        for i in range(1, len(sorted_list)):
            gap = (sorted_list[i].timestamp - sorted_list[i - 1].timestamp).total_seconds() / 3600.0
            if gap > 1.0:
                report.temporal_gaps.append(
                    f"{zone_id}: gap of {gap:.1f}h between "
                    f"{sorted_list[i - 1].timestamp.isoformat()} and "
                    f"{sorted_list[i].timestamp.isoformat()}"
                )

    # Overall pass
    report.overall_pass = (
        len(report.missing_values) == 0
        and len(report.duplicate_timestamps) == 0
        and len(report.invalid_ranges) == 0
        and len(report.missing_zones) == 0
        and len(report.temporal_gaps) == 0
    )

    return report


def export_qc_report(report: QCReport, output_path: str = "data/research_qc_report.json") -> None:
    """Export QC report to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert tuples to lists for JSON serialization
    data = asdict(report)
    data["duplicate_timestamps"] = [list(pair) for pair in data["duplicate_timestamps"]]

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"QC report exported -> {path}")
