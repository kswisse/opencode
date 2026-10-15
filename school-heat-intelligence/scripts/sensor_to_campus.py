"""Convert raw DHT22 serial logs to campus CSV rows (measured provenance).

Usage:
    python scripts/sensor_to_campus.py data/sensor_log.csv data/campus_measured.csv

Input (raw):  timestamp,node_id,temp_c,humidity
Output: campus-format CSV with provenance=measured. Edit ZONES below so each
node_id maps to its install location. Wind/canopy/shade/surface are
site constants you fill in once per zone; exposure_hours counts school hours.
"""
import csv
import sys

# ponytail: edit per deployment; unknown nodes fall back to generic outdoor values
ZONES = {
    "san_truong": dict(zone_id="zone_01", zone_name="san_truong",
                       lat=10.76, lon=106.68, wind_speed=1.5,
                       canopy_pct=5.0, shade_pct=10.0, surface_type="asphalt",
                       student_count=80, exposure_hours=1.0),
    "lop_12a1": dict(zone_id="zone_02", zone_name="lop_12a1",
                     lat=10.76, lon=106.68, wind_speed=0.5,
                     canopy_pct=0.0, shade_pct=80.0, surface_type="concrete",
                     student_count=40, exposure_hours=5.0),
}
DEFAULT_ZONE = dict(wind_speed=1.0, canopy_pct=10.0, shade_pct=20.0,
                    surface_type="concrete", student_count=0, exposure_hours=0.0)

HEADER = ("timestamp,zone_id,zone_name,lat,lon,air_temperature,humidity,"
          "wind_speed,ndvi,canopy_pct,shade_pct,surface_type,"
          "student_count,exposure_hours,provenance")


def convert(src: str, dst: str) -> int:
    n = 0
    with open(src, newline="") as fin, open(dst, "w", newline="") as fout:
        fout.write(HEADER + "\n")
        for row in csv.DictReader(fin):
            node = row["node_id"]
            z = dict(DEFAULT_ZONE)
            z.update(ZONES.get(node, {}))
            zid = z.get("zone_id", node)
            zname = z.get("zone_name", node)
            fout.write(",".join([
                row["timestamp"], zid, zname, str(z["lat"]), str(z["lon"]),
                row["temp_c"], row["humidity"], str(z["wind_speed"]), "",
                str(z["canopy_pct"]), str(z["shade_pct"]), z["surface_type"],
                str(z["student_count"]), str(z["exposure_hours"]), "measured",
            ]) + "\n")
            n += 1
    return n


def demo() -> None:
    n = convert("data/sensor_template.csv", "data/campus_measured_demo.csv")
    assert n == 4, n
    print(f"demo OK: {n} rows -> data/campus_measured_demo.csv")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
    else:
        print(f"wrote {convert(sys.argv[1], sys.argv[2])} rows to {sys.argv[2]}")
