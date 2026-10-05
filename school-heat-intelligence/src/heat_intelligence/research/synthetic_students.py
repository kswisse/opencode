"""Synthetic student dataset generator for research demonstration.

Generates student-level data with thermal comfort, cognitive performance,
and activity measurements across multiple zones and days. Designed to
produce detectable but not forced relationships between environment and outcomes.

WARNING: This is synthetic demo data. All relationships are illustrative
heuristics, NOT empirically calibrated.
"""
import csv
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from heat_intelligence.research.synthetic_generator import ZONES, _diurnal_temperature, _surface_effect, _canopy_effect

# Hot zones (asphalt, low canopy) and cool zones (grass, high canopy)
HOT_ZONES = ["zone_01", "zone_04"]
COOL_ZONES = ["zone_02", "zone_05"]
ZONE_PAIRS = [(hot, cool) for hot in HOT_ZONES for cool in COOL_ZONES]

STUDENT_IDS = [f"S{i:02d}" for i in range(1, 31)]
ACTIVITIES = ["sitting", "walking", "running"]
CLOTHING_OPTIONS = ["short_sleeves", "long_sleeves"]
BASE_DATE = datetime(2026, 10, 5, 0, 0, 0)
RECESS_HOURS = [9, 10, 11, 12, 13, 14]


def _get_temperature_for_session(zone_id: str, day: int, hour: int, seed_extra: int = 0) -> float:
    """Get temperature for a session, with noise for measurement uncertainty."""
    zone = ZONES[zone_id]
    day_offset = random.uniform(-3.0, 3.0)
    base_temp = _diurnal_temperature(hour) + day_offset
    base_temp += _surface_effect(zone["surface_type"])
    base_temp += _canopy_effect(zone["canopy_pct"])
    base_temp += random.uniform(-0.5, 0.5)
    return round(base_temp, 1)


def _thermal_sensation(temp: float) -> int:
    """Thermal sensation correlated with temperature (ordinal -3 to +3)."""
    # -3: cold, -2: cool, -1: slightly cool, 0: neutral, +1: slightly warm, +2: warm, +3: hot
    if temp < 26:
        base = -2
    elif temp < 28:
        base = -1
    elif temp < 30:
        base = 0
    elif temp < 32:
        base = 1
    elif temp < 34:
        base = 2
    else:
        base = 3
    noise = random.choice([-1, 0, 0, 0, 1])
    return max(-3, min(3, base + noise))


def _thermal_comfort(sensation: int) -> int:
    """Thermal comfort correlated with thermal sensation (1–5)."""
    # 1: very comfortable, 2: comfortable, 3: neutral, 4: uncomfortable, 5: very uncomfortable
    comfort_map = {3: 5, 2: 4, 1: 3, 0: 2, -1: 2, -2: 3, -3: 4}
    base = comfort_map.get(sensation, 3)
    noise = random.choice([-1, 0, 0, 1])
    return max(1, min(5, base + noise))


def _cognitive_score(temp: float) -> int:
    """Cognitive score 0–20 with weak negative correlation to temperature."""
    # Weak relationship: R² ~0.05–0.10
    base = 18.0 - (temp - 28.0) * 0.15  # Very weak effect
    noise = random.gauss(0, 3.0)  # Substantial noise
    return max(0, min(20, round(base + noise)))


def _reaction_time_ms(temp: float) -> int:
    """Reaction time 400–800ms with weak positive correlation to temperature."""
    base = 500.0 + (temp - 28.0) * 8.0  # Weak effect
    noise = random.gauss(0, 80.0)
    return max(400, min(800, round(base + noise)))


def generate_synthetic_students(
    seed: int = 42,
    output_csv: str = "data/research_synthetic_students.csv",
) -> List[Dict]:
    """Generate synthetic student-level data for 30 students, 3 days, 2 zones each."""
    random.seed(seed)

    records: List[Dict] = []
    # Assign 2 zones to each student (1 hot, 1 cool)
    student_zone_assignments: List[Tuple[str, str, str]] = []
    for i, sid in enumerate(STUDENT_IDS):
        hot_zone = HOT_ZONES[i % len(HOT_ZONES)]
        cool_zone = COOL_ZONES[i % len(COOL_ZONES)]
        student_zone_assignments.append((sid, hot_zone, cool_zone))

    for day in range(1, 4):
        # Each day: different weather variation
        day_offset = random.uniform(-2.0, 2.0)

        for sid, hot_zone, cool_zone in student_zone_assignments:
            for zone_id in [hot_zone, cool_zone]:
                # Pick a random recess hour
                hour = random.choice(RECESS_HOURS)
                zone = ZONES[zone_id]

                temp = _get_temperature_for_session(zone_id, day, hour)

                # Risk score placeholder (will be computed from environment)
                # For now, simple proxy based on temperature
                risk_score = round(min(100.0, max(0.0, (temp - 20.0) * 3.5)), 1)

                sensation = _thermal_sensation(temp)
                comfort = _thermal_comfort(sensation)
                cognitive = _cognitive_score(temp)
                reaction = _reaction_time_ms(temp)
                activity = random.choice(ACTIVITIES)
                clothing = random.choice(CLOTHING_OPTIONS)
                hydration = random.choice(["yes", "no"])

                timestamp = BASE_DATE + timedelta(days=day - 1, hours=hour)

                records.append({
                    "student_id": sid,
                    "zone_id": zone_id,
                    "zone_name": zone["name"],
                    "day": day,
                    "timestamp": timestamp.isoformat(),
                    "air_temperature": temp,
                    "risk_score": risk_score,
                    "thermal_sensation": sensation,
                    "thermal_comfort": comfort,
                    "cognitive_score": cognitive,
                    "reaction_time_ms": reaction,
                    "activity_before": activity,
                    "clothing": clothing,
                    "hydration": hydration,
                })

    # Export to CSV
    fieldnames = [
        "student_id", "zone_id", "zone_name", "day", "timestamp",
        "air_temperature", "risk_score", "thermal_sensation",
        "thermal_comfort", "cognitive_score", "reaction_time_ms",
        "activity_before", "clothing", "hydration",
    ]

    output_path = __import__("pathlib").Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)

    print(f"Generated {len(records)} synthetic student session records -> {output_path}")
    return records


if __name__ == "__main__":
    generate_synthetic_students()
