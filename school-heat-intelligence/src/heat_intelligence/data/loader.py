"""CSV/JSON data loader with validation."""
import csv
import json
from pathlib import Path
from typing import List

from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading

REQUIRED_COLUMNS = {
    "timestamp", "zone_id", "zone_name", "lat", "lon",
    "air_temperature", "humidity", "wind_speed",
    "canopy_pct", "shade_pct", "surface_type",
    "student_count", "exposure_hours",
}


def load_data(path: str) -> List[ZoneReading]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    if file_path.suffix == ".csv":
        return _load_csv(file_path)
    elif file_path.suffix == ".json":
        return _load_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def _load_csv(file_path: Path) -> List[ZoneReading]:
    readings = []
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row")
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        for row in reader:
            reading = ZoneReading(
                timestamp=row["timestamp"], zone_id=row["zone_id"],
                zone_name=row["zone_name"], lat=float(row["lat"]),
                lon=float(row["lon"]), air_temperature=float(row["air_temperature"]),
                humidity=float(row["humidity"]), wind_speed=float(row["wind_speed"]),
                ndvi=float(row["ndvi"]) if row.get("ndvi") else None,
                canopy_pct=float(row["canopy_pct"]),
                shade_pct=float(row["shade_pct"]),
                surface_type=row["surface_type"],
                student_count=int(row["student_count"]),
                exposure_hours=float(row["exposure_hours"]),
                provenance=ProvenanceFlag(row.get("provenance", "synthetic")),
            )
            readings.append(reading)
    return readings


def _load_json(file_path: Path) -> List[ZoneReading]:
    with open(file_path, "r") as f:
        data = json.load(f)
    return [ZoneReading(**item) for item in data]
