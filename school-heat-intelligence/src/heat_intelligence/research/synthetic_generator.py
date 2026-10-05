"""Synthetic environmental data generator for research demonstration.

Generates realistic synthetic environmental data with diurnal temperature patterns,
surface/canopy effects, and weather variability. All data is synthetic and clearly
marked as such.

WARNING: This is synthetic demo data for research protocol demonstration.
Coefficients and heuristics are illustrative, NOT empirically calibrated.
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from heat_intelligence.models.schemas import ProvenanceFlag, ZoneReading

# Zone definitions
ZONES = {
    "zone_01": {
        "name": "Main Playground",
        "lat": 10.762622,
        "lon": 106.682228,
        "surface_type": "asphalt",
        "canopy_pct": 10.0,
        "shade_pct": 15.0,
        "exposure_hours": 2.0,
        "recess_times": [(0, 7), (0, 8), (0, 12), (0, 13)],
    },
    "zone_02": {
        "name": "School Garden",
        "lat": 10.762650,
        "lon": 106.682350,
        "surface_type": "grass",
        "canopy_pct": 60.0,
        "shade_pct": 70.0,
        "exposure_hours": 0.5,
        "recess_times": [(0, 12), (0, 13)],
    },
    "zone_03": {
        "name": "Courtyard",
        "lat": 10.762580,
        "lon": 106.682150,
        "surface_type": "concrete",
        "canopy_pct": 25.0,
        "shade_pct": 40.0,
        "exposure_hours": 1.0,
        "recess_times": [(0, 10), (0, 11), (0, 12), (0, 13)],
    },
    "zone_04": {
        "name": "Sports Field",
        "lat": 10.762700,
        "lon": 106.682400,
        "surface_type": "grass",
        "canopy_pct": 5.0,
        "shade_pct": 10.0,
        "exposure_hours": 1.5,
        "recess_times": [(0, 8), (0, 9), (0, 15), (0, 16)],
    },
    "zone_05": {
        "name": "Canteen Area",
        "lat": 10.762550,
        "lon": 106.682300,
        "surface_type": "concrete",
        "canopy_pct": 45.0,
        "shade_pct": 55.0,
        "exposure_hours": 1.0,
        "recess_times": [(0, 11), (0, 12), (0, 13)],
    },
}

HOURS = list(range(7, 17))  # 07:00–16:00
NUM_DAYS = 10
UTC7 = timedelta(hours=7)


def _diurnal_temperature(hour: int) -> float:
    """Base temperature from diurnal pattern. Peaks at 13:00-14:00."""
    # Morning 28°C, peak ~36°C at 13:00, decline to ~32°C at 16:00
    if hour <= 10:
        base = 28.0 + (hour - 7) * (8.0 / 6.0)
    elif hour <= 14:
        base = 32.0 + (hour - 10) * (4.0 / 4.0)
    else:
        base = 36.0 - (hour - 14) * (4.0 / 2.0)
    return base


def _surface_effect(surface_type: str) -> float:
    """Surface type effect on temperature (illustrative heuristic)."""
    effects = {
        "asphalt": 2.0,  # asphalt: +1.5–2.5°C
        "concrete": 0.0,  # concrete: baseline
        "grass": -0.75,   # grass: -0.5–1.0°C
    }
    return effects.get(surface_type, 0.0)


def _canopy_effect(canopy_pct: float) -> float:
    """Canopy cooling effect (illustrative heuristic: ~0.3°C per 10% canopy)."""
    return -(canopy_pct / 10.0) * 0.3


def _humidity(hour: int, temp: float) -> float:
    """Humidity inversely correlated with temperature."""
    base_humidity = 85.0 - (temp - 28.0) * 1.5
    noise = random.uniform(-3.0, 3.0)
    return max(50.0, min(90.0, base_humidity + noise))


def _wind_speed(surface_type: str) -> float:
    """Random wind speed, slightly higher in open areas."""
    if surface_type in ("grass", "permeable"):
        return round(random.uniform(0.5, 3.0), 2)
    return round(random.uniform(0.0, 2.5), 2)


def _student_count(zone_id: str, hour: int) -> int:
    """Student count: 0 outside recess, 20–80 during recess/lunch."""
    zone = ZONES[zone_id]
    is_recess = False
    for h_start, h_end in zone["recess_times"]:
        if h_start <= hour <= h_end:
            is_recess = True
            break

    if not is_recess:
        return 0
    return random.randint(20, 80)


def generate_synthetic_environmental(
    seed: int = 42,
    output_csv: str = "data/research_synthetic_environmental.csv",
) -> List[ZoneReading]:
    """Generate synthetic environmental data for 5 zones over 10 days.

    Returns list of ZoneReading and optionally exports to CSV.
    """
    random.seed(seed)
    readings: List[ZoneReading] = []

    # Day-to-day weather variation
    day_offsets = [random.uniform(-3.0, 3.0) for _ in range(NUM_DAYS)]

    # Base date (Oct 2026)
    base_date = datetime(2026, 10, 5, 0, 0, 0)

    for day_idx in range(NUM_DAYS):
        day_offset = day_offsets[day_idx]
        for hour in HOURS:
            base_temp = _diurnal_temperature(hour) + day_offset
            for zone_id, zone in ZONES.items():
                temp = base_temp
                temp += _surface_effect(zone["surface_type"])
                temp += _canopy_effect(zone["canopy_pct"])
                # Add small random noise
                temp += random.uniform(-0.3, 0.3)
                temp = round(temp, 1)

                humidity = round(_humidity(hour, temp), 1)
                wind = _wind_speed(zone["surface_type"])
                student_count = _student_count(zone_id, hour)

                timestamp = base_date + timedelta(days=day_idx, hours=hour)

                reading = ZoneReading(
                    timestamp=timestamp,
                    zone_id=zone_id,
                    zone_name=zone["name"],
                    lat=zone["lat"],
                    lon=zone["lon"],
                    air_temperature=temp,
                    humidity=humidity,
                    wind_speed=wind,
                    ndvi=None,
                    canopy_pct=zone["canopy_pct"],
                    shade_pct=zone["shade_pct"],
                    surface_type=zone["surface_type"],
                    student_count=student_count,
                    exposure_hours=zone["exposure_hours"],
                    provenance=ProvenanceFlag.SYNTHETIC,
                )
                readings.append(reading)

    # Export to CSV
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp", "zone_id", "zone_name", "lat", "lon",
        "air_temperature", "humidity", "wind_speed", "ndvi",
        "canopy_pct", "shade_pct", "surface_type",
        "student_count", "exposure_hours", "provenance",
    ]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in readings:
            writer.writerow({
                "timestamp": r.timestamp.isoformat(),
                "zone_id": r.zone_id,
                "zone_name": r.zone_name,
                "lat": r.lat,
                "lon": r.lon,
                "air_temperature": r.air_temperature,
                "humidity": r.humidity,
                "wind_speed": r.wind_speed,
                "ndvi": r.ndvi if r.ndvi is not None else "",
                "canopy_pct": r.canopy_pct,
                "shade_pct": r.shade_pct,
                "surface_type": r.surface_type,
                "student_count": r.student_count,
                "exposure_hours": r.exposure_hours,
                "provenance": r.provenance.value,
            })

    print(f"Generated {len(readings)} synthetic environmental readings -> {output_path}")
    return readings


if __name__ == "__main__":
    generate_synthetic_environmental()
