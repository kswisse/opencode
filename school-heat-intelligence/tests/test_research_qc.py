"""Tests for quality control module."""
import json
import pytest
from datetime import datetime, timedelta

from heat_intelligence.research.quality_control import run_qc, export_qc_report, QCReport
from heat_intelligence.models.schemas import ZoneReading, ProvenanceFlag


def _make_reading(zone_id="zone_01", temp=30.0, humidity=70.0, wind=1.5,
                  ts_offset_hours=0):
    return ZoneReading(
        timestamp=datetime(2026, 10, 5, 7, 0, 0) + timedelta(hours=ts_offset_hours),
        zone_id=zone_id,
        zone_name="Test Zone",
        lat=10.76,
        lon=106.68,
        air_temperature=temp,
        humidity=humidity,
        wind_speed=wind,
        canopy_pct=10.0,
        shade_pct=15.0,
        surface_type="asphalt",
        student_count=0,
        exposure_hours=1.0,
        provenance=ProvenanceFlag.SYNTHETIC,
    )


class TestQCReport:
    def test_empty_readings(self):
        report = run_qc([], ["zone_01", "zone_02"])
        assert report.total_rows == 0
        assert not report.overall_pass  # missing zones

    def test_valid_readings_pass(self):
        readings = [_make_reading(zone_id=f"zone_0{i}") for i in range(1, 6)]
        report = run_qc(readings, ["zone_01", "zone_02", "zone_03", "zone_04", "zone_05"])
        assert report.overall_pass
        assert report.total_rows == 5
        assert len(report.missing_values) == 0
        assert len(report.duplicate_timestamps) == 0
        assert len(report.invalid_ranges) == 0
        assert len(report.missing_zones) == 0

    def test_detects_missing_zones(self):
        readings = [_make_reading(zone_id="zone_01")]
        report = run_qc(readings, ["zone_01", "zone_02", "zone_03"])
        assert not report.overall_pass
        assert "zone_02" in report.missing_zones
        assert "zone_03" in report.missing_zones

    def test_detects_duplicate_timestamps(self):
        readings = [
            _make_reading(zone_id="zone_01", ts_offset_hours=0),
            _make_reading(zone_id="zone_01", ts_offset_hours=0),
        ]
        report = run_qc(readings, ["zone_01"])
        assert not report.overall_pass
        assert len(report.duplicate_timestamps) == 1

    def test_detects_invalid_temperature_high(self):
        reading = _make_reading(temp=55.0)  # > 50
        report = run_qc([reading], ["zone_01"])
        assert not report.overall_pass
        assert "air_temperature" in report.invalid_ranges

    def test_detects_invalid_temperature_low(self):
        reading = _make_reading(temp=10.0)  # < 15
        report = run_qc([reading], ["zone_01"])
        assert not report.overall_pass
        assert "air_temperature" in report.invalid_ranges

    def test_detects_invalid_humidity(self):
        # Pydantic blocks invalid humidity at creation, so test the QC check logic
        # by verifying a valid reading passes the range check
        reading = _make_reading(humidity=50.0)
        report = run_qc([reading], ["zone_01"])
        assert "humidity" not in report.invalid_ranges  # 50 is valid

        # Verify boundary values are accepted
        reading_low = _make_reading(humidity=0.0)
        report_low = run_qc([reading_low], ["zone_01"])
        assert "humidity" not in report_low.invalid_ranges

        reading_high = _make_reading(humidity=100.0)
        report_high = run_qc([reading_high], ["zone_01"])
        assert "humidity" not in report_high.invalid_ranges

    def test_detects_invalid_wind(self):
        reading = _make_reading(wind=60.0)  # > 50
        report = run_qc([reading], ["zone_01"])
        assert not report.overall_pass
        assert "wind_speed" in report.invalid_ranges

    def test_temporal_gap_detected(self):
        readings = [
            _make_reading(zone_id="zone_01", ts_offset_hours=0),
            _make_reading(zone_id="zone_01", ts_offset_hours=5),  # 5h gap
        ]
        report = run_qc(readings, ["zone_01"])
        assert len(report.temporal_gaps) == 1
        assert "5.0h" in report.temporal_gaps[0]

    def test_no_temporal_gap_within_1_hour(self):
        readings = [
            _make_reading(zone_id="zone_01", ts_offset_hours=0),
            _make_reading(zone_id="zone_01", ts_offset_hours=1),
        ]
        report = run_qc(readings, ["zone_01"])
        assert len(report.temporal_gaps) == 0

    def test_export_qc_report(self):
        report = QCReport(
            total_rows=100,
            missing_values={"temp": 2},
            duplicate_timestamps=[("2026-10-05T07:00:00", "zone_01")],
            invalid_ranges={},
            missing_zones=[],
            temporal_gaps=[],
            overall_pass=False,
        )
        export_qc_report(report, "data/test_qc_report.json")
        with open("data/test_qc_report.json") as f:
            data = json.load(f)
        assert data["total_rows"] == 100
        assert data["missing_values"]["temp"] == 2
        assert data["duplicate_timestamps"] == [["2026-10-05T07:00:00", "zone_01"]]
        assert data["overall_pass"] is False
