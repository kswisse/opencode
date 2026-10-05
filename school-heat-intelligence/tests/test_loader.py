"""Tests for data loader."""
import json
import pytest
import tempfile
from pathlib import Path
from heat_intelligence.data.loader import load_data
from heat_intelligence.models.schemas import ProvenanceFlag


class TestLoader:
    @pytest.fixture
    def csv_file(self, tmp_path):
        csv_content = (
            "timestamp,zone_id,zone_name,lat,lon,air_temperature,humidity,wind_speed,"
            "canopy_pct,shade_pct,surface_type,student_count,exposure_hours,provenance\n"
            "2026-07-01T12:00:00,z1,School A,10.0,106.0,35.0,70.0,2.0,"
            "10.0,15.0,asphalt,50,4.0,synthetic\n"
            "2026-07-01T13:00:00,z1,School A,10.0,106.0,36.0,65.0,1.5,"
            "10.0,15.0,asphalt,50,4.0,synthetic\n"
        )
        path = tmp_path / "test_data.csv"
        path.write_text(csv_content)
        return str(path)

    @pytest.fixture
    def json_file(self, tmp_path):
        data = [
            {
                "timestamp": "2026-07-01T12:00:00",
                "zone_id": "z1",
                "zone_name": "School A",
                "lat": 10.0,
                "lon": 106.0,
                "air_temperature": 35.0,
                "humidity": 70.0,
                "wind_speed": 2.0,
                "canopy_pct": 10.0,
                "shade_pct": 15.0,
                "surface_type": "asphalt",
                "student_count": 50,
                "exposure_hours": 4.0,
                "provenance": "synthetic",
            }
        ]
        path = tmp_path / "test_data.json"
        path.write_text(json.dumps(data))
        return str(path)

    def test_load_csv(self, csv_file):
        readings = load_data(csv_file)
        assert len(readings) == 2
        assert readings[0].zone_id == "z1"
        assert readings[0].air_temperature == 35.0

    def test_load_json(self, json_file):
        readings = load_data(json_file)
        assert len(readings) == 1
        assert readings[0].zone_name == "School A"

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            load_data("/nonexistent/data.csv")

    def test_unsupported_format(self, tmp_path):
        path = tmp_path / "data.txt"
        path.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_data(str(path))

    def test_missing_required_column_csv(self, tmp_path):
        csv_content = "timestamp,zone_id,lat,lon\n2026-07-01T12:00:00,z1,10.0,106.0\n"
        path = tmp_path / "bad.csv"
        path.write_text(csv_content)
        with pytest.raises((KeyError, ValueError)):
            load_data(str(path))

    def test_csv_default_provenance(self, tmp_path):
        csv_content = (
            "timestamp,zone_id,zone_name,lat,lon,air_temperature,humidity,wind_speed,"
            "canopy_pct,shade_pct,surface_type,student_count,exposure_hours\n"
            "2026-07-01T12:00:00,z1,School A,10.0,106.0,35.0,70.0,2.0,"
            "10.0,15.0,asphalt,50,4.0\n"
        )
        path = tmp_path / "no_prov.csv"
        path.write_text(csv_content)
        readings = load_data(str(path))
        assert readings[0].provenance == ProvenanceFlag.SYNTHETIC
