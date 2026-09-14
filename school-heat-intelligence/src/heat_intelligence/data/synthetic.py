"""Synthetic demo data generator for School Heat Intelligence."""
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import numpy as np

from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading

ZONES = [
    {"zone_id": "zone_01", "zone_name": "playground", "lat": 40.7128, "lon": -74.0060,
     "surface_type": "asphalt", "canopy_pct": 5, "shade_pct": 10, "base_temp_offset": 2.0},
    {"zone_id": "zone_02", "zone_name": "parking_lot", "lat": 40.7130, "lon": -74.0062,
     "surface_type": "asphalt", "canopy_pct": 0, "shade_pct": 0, "base_temp_offset": 3.5},
    {"zone_id": "zone_03", "zone_name": "courtyard", "lat": 40.7126, "lon": -74.0058,
     "surface_type": "concrete", "canopy_pct": 15, "shade_pct": 25, "base_temp_offset": 1.0},
    {"zone_id": "zone_04", "zone_name": "building_roof", "lat": 40.7129, "lon": -74.0059,
     "surface_type": "concrete", "canopy_pct": 0, "shade_pct": 0, "base_temp_offset": 4.0},
    {"zone_id": "zone_05", "zone_name": "sports_field", "lat": 40.7131, "lon": -74.0061,
     "surface_type": "grass", "canopy_pct": 0, "shade_pct": 5, "base_temp_offset": 0.5},
    {"zone_id": "zone_06", "zone_name": "library_exterior", "lat": 40.7127, "lon": -74.0057,
     "surface_type": "concrete", "canopy_pct": 20, "shade_pct": 35, "base_temp_offset": 0.8},
    {"zone_id": "zone_07", "zone_name": "cafeteria_patio", "lat": 40.7125, "lon": -74.0063,
     "surface_type": "concrete", "canopy_pct": 40, "shade_pct": 50, "base_temp_offset": 0.3},
    {"zone_id": "zone_08", "zone_name": "walkway", "lat": 40.7132, "lon": -74.0056,
     "surface_type": "asphalt", "canopy_pct": 10, "shade_pct": 15, "base_temp_offset": 1.5},
    {"zone_id": "zone_09", "zone_name": "garden", "lat": 40.7124, "lon": -74.0064,
     "surface_type": "grass", "canopy_pct": 60, "shade_pct": 70, "base_temp_offset": -0.5},
    {"zone_id": "zone_10", "zone_name": "gym_exterior", "lat": 40.7133, "lon": -74.0065,
     "surface_type": "concrete", "canopy_pct": 10, "shade_pct": 20, "base_temp_offset": 1.2},
    {"zone_id": "zone_11", "zone_name": "admin_building", "lat": 40.7123, "lon": -74.0055,
     "surface_type": "concrete", "canopy_pct": 25, "shade_pct": 30, "base_temp_offset": 0.6},
    {"zone_id": "zone_12", "zone_name": "entrance_plaza", "lat": 40.7134, "lon": -74.0066,
     "surface_type": "asphalt", "canopy_pct": 5, "shade_pct": 10, "base_temp_offset": 2.5},
]

STUDENT_SCHEDULE = {
    0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0,
    6: 0.1, 7: 0.3, 8: 0.8, 9: 1.0, 10: 1.0, 11: 0.9,
    12: 0.7, 13: 0.9, 14: 1.0, 15: 0.8, 16: 0.5, 17: 0.3,
    18: 0.1, 19: 0.0, 20: 0.0, 21: 0.0, 22: 0.0, 23: 0.0,
}

ZONE_CAPACITY = {
    "playground": 80, "parking_lot": 10, "courtyard": 45, "building_roof": 5,
    "sports_field": 120, "library_exterior": 30, "cafeteria_patio": 60,
    "walkway": 25, "garden": 15, "gym_exterior": 40, "admin_building": 20,
    "entrance_plaza": 35,
}


def _diurnal_temperature(hour: int, base: float, offset: float) -> float:
    diurnal = 5.0 * np.sin(2 * np.pi * (hour - 5) / 24)
    return base + diurnal + offset


def _diurnal_humidity(hour: int) -> float:
    return 65.0 - 25.0 * np.sin(2 * np.pi * (hour - 5) / 24)


def generate_demo_data(
    days: int = 14, base_temperature: float = 28.0,
    output_path: str = "data/demo_campus.csv",
) -> List[ZoneReading]:
    np.random.seed(42)
    readings: List[ZoneReading] = []
    start_date = datetime(2026, 7, 1, 0, 0, 0)

    for day in range(days):
        current_date = start_date + timedelta(days=day)
        for hour in range(24):
            timestamp = current_date.replace(hour=hour)
            schedule_factor = STUDENT_SCHEDULE[hour]

            for zone in ZONES:
                temp = _diurnal_temperature(hour, base_temperature, zone["base_temp_offset"])
                temp += np.random.normal(0, 0.5)
                humidity = _diurnal_humidity(hour) + np.random.normal(0, 3)
                humidity = max(20, min(100, humidity))
                wind_speed = max(0, 2.0 + np.random.normal(0, 1.0))
                student_count = int(ZONE_CAPACITY[zone["zone_name"]] * schedule_factor)
                student_count = max(0, student_count + int(np.random.normal(0, 2)))
                exposure_hours = 1.0 if schedule_factor > 0.1 else 0.0

                reading = ZoneReading(
                    timestamp=timestamp, zone_id=zone["zone_id"],
                    zone_name=zone["zone_name"], lat=zone["lat"], lon=zone["lon"],
                    air_temperature=round(temp, 1), humidity=round(humidity, 1),
                    wind_speed=round(wind_speed, 1),
                    ndvi=round(np.random.uniform(0.1, 0.8), 2),
                    canopy_pct=zone["canopy_pct"], shade_pct=zone["shade_pct"],
                    surface_type=zone["surface_type"], student_count=student_count,
                    exposure_hours=exposure_hours, provenance=ProvenanceFlag.SYNTHETIC,
                )
                readings.append(reading)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        headers = ["timestamp", "zone_id", "zone_name", "lat", "lon",
                    "air_temperature", "humidity", "wind_speed", "ndvi",
                    "canopy_pct", "shade_pct", "surface_type",
                    "student_count", "exposure_hours", "provenance"]
        writer.writerow(headers)
        for r in readings:
            writer.writerow([r.timestamp.isoformat(), r.zone_id, r.zone_name,
                r.lat, r.lon, r.air_temperature, r.humidity, r.wind_speed,
                r.ndvi, r.canopy_pct, r.shade_pct, r.surface_type,
                r.student_count, r.exposure_hours, r.provenance.value])
    print(f"Generated {len(readings)} readings -> {output_path}")
    return readings
