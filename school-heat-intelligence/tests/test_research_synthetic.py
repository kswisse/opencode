"""Tests for synthetic data generators."""
import csv
import pytest
from pathlib import Path

from heat_intelligence.research.synthetic_generator import (
    generate_synthetic_environmental, ZONES, HOURS, NUM_DAYS,
)
from heat_intelligence.research.synthetic_students import (
    generate_synthetic_students, STUDENT_IDS, HOT_ZONES, COOL_ZONES,
)
from heat_intelligence.models.schemas import ProvenanceFlag


class TestSyntheticGenerator:
    def test_generates_correct_count(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        expected = NUM_DAYS * len(HOURS) * len(ZONES)
        assert len(readings) == expected

    def test_all_zones_present(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        zone_ids = set(r.zone_id for r in readings)
        assert zone_ids == set(ZONES.keys())

    def test_all_hours_present(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        hours = set(r.timestamp.hour for r in readings)
        assert hours == set(HOURS)

    def test_provenance_synthetic(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        for r in readings:
            assert r.provenance == ProvenanceFlag.SYNTHETIC

    def test_temperature_in_reasonable_range(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        for r in readings:
            assert 15.0 <= r.air_temperature <= 50.0, f"Temp {r.air_temperature} out of range"

    def test_humidity_in_range(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        for r in readings:
            assert 0.0 <= r.humidity <= 100.0

    def test_wind_speed_non_negative(self):
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        for r in readings:
            assert r.wind_speed >= 0.0

    def test_reproducibility(self):
        r1 = generate_synthetic_environmental(seed=42, output_csv="data/test_env1.csv")
        r2 = generate_synthetic_environmental(seed=42, output_csv="data/test_env2.csv")
        temps1 = [r.air_temperature for r in r1]
        temps2 = [r.air_temperature for r in r2]
        assert temps1 == temps2

    def test_csv_export(self):
        generate_synthetic_environmental(seed=42, output_csv="data/test_env_csv.csv")
        assert Path("data/test_env_csv.csv").exists()
        with open("data/test_env_csv.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == NUM_DAYS * len(HOURS) * len(ZONES)

    def test_diurnal_pattern(self):
        """Temperature should peak around 13:00-14:00."""
        readings = generate_synthetic_environmental(seed=42, output_csv="data/test_env.csv")
        # Get zone_01 readings
        z1 = [r for r in readings if r.zone_id == "zone_01"]
        temps_by_hour = {}
        for r in z1:
            h = r.timestamp.hour
            temps_by_hour.setdefault(h, []).append(r.air_temperature)
        avg_by_hour = {h: sum(t) / len(t) for h, t in temps_by_hour.items()}
        # Peak should be around 13-14
        peak_hour = max(avg_by_hour, key=avg_by_hour.get)
        assert peak_hour in (13, 14)


class TestSyntheticStudents:
    def test_generates_correct_count(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        # 30 students × 2 zones × 3 days
        assert len(records) == 180

    def test_all_student_ids(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        ids = set(r["student_id"] for r in records)
        assert ids == set(STUDENT_IDS)

    def test_all_days(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        days = set(r["day"] for r in records)
        assert days == {1, 2, 3}

    def test_zones_are_hot_or_cool(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        for r in records:
            assert r["zone_id"] in HOT_ZONES + COOL_ZONES

    def test_thermal_sensation_in_range(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        for r in records:
            assert -3 <= r["thermal_sensation"] <= 3

    def test_thermal_comfort_in_range(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        for r in records:
            assert 1 <= r["thermal_comfort"] <= 5

    def test_cognitive_score_in_range(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        for r in records:
            assert 0 <= r["cognitive_score"] <= 20

    def test_reaction_time_in_range(self):
        records = generate_synthetic_students(seed=42, output_csv="data/test_students.csv")
        for r in records:
            assert 400 <= r["reaction_time_ms"] <= 800

    def test_csv_export(self):
        generate_synthetic_students(seed=42, output_csv="data/test_students_csv.csv")
        assert Path("data/test_students_csv.csv").exists()
        with open("data/test_students_csv.csv") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 180

    def test_reproducibility(self):
        r1 = generate_synthetic_students(seed=42, output_csv="data/test_stud1.csv")
        r2 = generate_synthetic_students(seed=42, output_csv="data/test_stud2.csv")
        temps1 = [r["air_temperature"] for r in r1]
        temps2 = [r["air_temperature"] for r in r2]
        assert temps1 == temps2
