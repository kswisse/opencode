# Pilot Readiness Review: School Heat Intelligence

**Date:** 14 September 2026  
**Review against:** Research Protocol v1 + Current SYS Codebase  
**Status:** Conditional pass — 3 code changes required, 0 architecture changes

---

## Verdict

**CONDITIONAL PASS.** The current SYS schema can represent the core pilot variables (temperature, humidity, wind, zone metadata) and the loader can import measured data with `provenance: measured`. However, three code-level changes are required before the pilot to (a) add missing fields the protocol needs for fieldwork metadata, (b) ensure repeated-measures analysis is possible with the current timestamp/zone_id structure, and (c) relax the loader to accept wind_speed=0 when no anemometer is available.

No architecture changes are needed. No new files are required.

---

## 1. Schema Coverage Analysis

### SYS `ZoneReading` Fields vs Protocol Requirements

| SYS Field | Protocol Variable | Coverage | Status |
|-----------|-------------------|----------|--------|
| `timestamp` | Measurement time (ISO 8601) | ✅ Full | OK |
| `zone_id` | Zone identifier | ✅ Full | OK |
| `zone_name` | Zone name | ✅ Full | OK |
| `lat` | Zone latitude | ✅ Full | OK |
| `lon` | Zone longitude | ✅ Full | OK |
| `air_temperature` | Ta (°C, measured) | ✅ Full | OK |
| `humidity` | RH (%, measured) | ✅ Full | OK |
| `wind_speed` | Wind speed (m/s) | ⚠️ Partial | **Must fix** — protocol allows "qualitative" wind, SYS requires float ≥0. With one sensor, wind may be 0.0 or unavailable. Acceptable if set to 0.0 and provenance is `measured`. |
| `ndvi` | NDVI from satellite | ✅ Optional | OK — leave empty for pilot |
| `canopy_pct` | Tree canopy cover % | ✅ Full | OK |
| `shade_pct` | Shade cover % | ✅ Full | OK |
| `surface_type` | Surface type | ✅ Full | OK |
| `student_count` | Students in zone | ✅ Full | OK |
| `exposure_hours` | Hours students exposed | ✅ Full | OK |
| `provenance` | Data source flag | ✅ Full | OK — use `measured` |

### Verdict: 15/15 core fields covered. No missing required fields.

---

## 2. Repeated-Measures Analysis Adequacy

### Question: Are `timestamp` + `zone_id` sufficient?

**Yes.** The current schema uniquely identifies each measurement by `(timestamp, zone_id)`. This is sufficient for:

- **Within-zone temporal analysis:** Group by `zone_id`, order by `timestamp` → diurnal curve.
- **Between-zone spatial comparison:** Filter by `timestamp` window, compare `air_temperature` across `zone_id` values.
- **Repeated-measures design:** Each student session links to a `(timestamp, zone_id)` pair. Student identity is tracked in the questionnaire data (coded), not in the SYS schema.

### What the schema does NOT support (acceptable for pilot):
- Student-level repeated measures within SYS (this is in the questionnaire CSV, not the sensor CSV).
- Multi-day grouping (no `date` field — but `timestamp` encodes this).
- Sensor ID tracking (no field — but only 1 sensor in pilot).

### Recommendation: No schema changes needed for repeated-measures analysis. The timestamp encodes both date and time.

---

## 3. Measured Data Import — Architecture Compatibility

### Current import path:
```
load_data(path) → _load_csv(path) → ZoneReading(...) → List[ZoneReading]
```

### Can measured data flow through this path?
**Yes.** The loader:
1. Reads CSV headers, checks required columns.
2. Maps columns to `ZoneReading` fields.
3. Defaults `provenance` to `synthetic` if not in CSV.

### What must change:
1. **Loader must accept `provenance: measured` from CSV.** Currently it does — `ProvenanceFlag(row.get("provenance", "synthetic"))` at `loader.py:50`. This works.
2. **Loader must not reject `wind_speed: 0.0`.** Currently it accepts this — `Field(ge=0)` allows 0.0. This works.
3. **No architecture changes needed.** The pipeline is: CSV → `load_data()` → `List[ZoneReading]` → dashboard pages. Measured data replaces synthetic data transparently.

### Import procedure:
1. Place `real_measurements.csv` in `data/`.
2. Update `app.py` line 14 to point to the new file.
3. Run dashboard. All modules consume `ZoneReading` objects regardless of provenance.

---

## 4. Provenance Rules — Decision Matrix

| Stage | Variable | Provenance | Reason |
|-------|----------|------------|--------|
| Sensor reading (Ta, RH) | `air_temperature`, `humidity` | `measured` | Direct physical measurement |
| Sensor reading (wind, if available) | `wind_speed` | `measured` | Direct physical measurement |
| Sensor reading (wind, unavailable) | `wind_speed` = 0.0 | `measured` | Value is 0.0 because no anemometer, not because wind is zero. This is a known limitation. |
| Zone map entry | `canopy_pct`, `shade_pct`, `surface_type` | `measured` | Direct observation / estimation by research team |
| Zone coordinates | `lat`, `lon` | `measured` | GPS reading from phone |
| Student count | `student_count` | `measured` | Direct observation (head count) |
| Exposure estimate | `exposure_hours` | `imported` | Derived from school timetable, not directly measured |
| NDVI | `ndvi` | `imported` | From satellite data if obtained |
| Forecast output | `predicted_score` | `predicted` | System-generated |
| Intervention output | `simulated_risk` | `simulated` | System-generated |

### Rule:
- **`measured`** = value came from a physical instrument or direct human observation during the study.
- **`imported`** = value came from an external source (timetable, satellite, reference table).
- **Never mix** `measured` and `synthetic` rows in the same import file.

---

## 5. Protocol Variables SYS Cannot Store

### Variables in the protocol not in `ZoneReading`:

| Protocol Variable | In SYS? | Impact | Action |
|-------------------|---------|--------|--------|
| Surface temperature (Ts, °C) | ❌ No | Optional measurement. Not used by risk engine. | **Record in field notebook. Do not import into SYS.** |
| Solar radiation (W/m²) | ❌ No | Optional measurement. Not used by risk engine. | **Record in field notebook. Do not import into SYS.** |
| Sensor ID | ❌ No | Only 1 sensor in pilot. Not needed. | **Ignore for pilot.** |
| Calibration offset | ❌ No | Applied to raw readings before import. | **Apply correction in field, import corrected values.** |
| Weather notes (qualitative) | ❌ No | Contextual metadata. | **Record in notebook. Tag each measurement row with weather condition in a separate field.** |
| Measurement duration (seconds) | ❌ No | Quality indicator. | **Record in notebook.** |
| Observer ID | ❌ No | Audit trail. | **Record in notebook.** |
| Student thermal sensation (ordinal) | ❌ No | Student-level outcome. | **Record in separate questionnaire CSV.** |
| Student cognitive test score | ❌ No | Student-level outcome. | **Record in separate questionnaire CSV.** |
| Student clothing | ❌ No | Confounder. | **Record in questionnaire CSV.** |
| Student activity level | ❌ No | Confounder. | **Record in questionnaire CSV.** |

### Verdict:
- **0 fields are missing for the core sensor data import.** SYS schema is sufficient for zone-level climate measurements.
- **11 fields are missing for student-level and metadata.** These belong in separate research CSVs, not in the SYS sensor schema. This is correct separation of concerns.

---

## 6. Minimum Additional Fields Required

### For SYS import: **None.** The current schema is sufficient.

### For the pilot to function, we need:

| Field | Where | Purpose | Required? |
|-------|-------|---------|-----------|
| `weather_condition` | Field notebook → optional CSV column | Tag measurement context | Recommended (not required for SYS import) |
| `date` | Implicit in `timestamp` | Group measurement days | Not needed as separate field |

### Optional enhancement (not required for pilot):
If a `weather_condition` column is added to the CSV, the loader would need a new optional field in `ZoneReading`. **This is NOT required for the pilot.** Weather condition can be recorded in the notebook and annotated post-hoc.

---

## 7. Pilot One-Day Data-Entry Template CSV

```csv
timestamp,zone_id,zone_name,lat,lon,air_temperature,humidity,wind_speed,ndvi,canopy_pct,shade_pct,surface_type,student_count,exposure_hours,provenance
2026-10-15T07:00:00,zone_01,Main Playground,10.7620,106.6820,28.5,82.0,0.0,,10,15,asphalt,0,2.0,measured
2026-10-15T07:30:00,zone_01,Main Playground,10.7620,106.6820,29.1,80.0,0.0,,10,15,asphalt,0,2.0,measured
2026-10-15T09:00:00,zone_01,Main Playground,10.7620,106.6820,32.4,72.0,0.5,,10,15,asphalt,25,2.0,measured
2026-10-15T11:30:00,zone_01,Main Playground,10.7620,106.6820,36.2,58.0,0.0,,10,15,asphalt,45,2.0,measured
2026-10-15T14:00:00,zone_01,Main Playground,10.7620,106.6820,35.8,60.0,0.3,,10,15,asphalt,30,2.0,measured
2026-10-15T16:00:00,zone_01,Main Playground,10.7620,106.6820,33.1,68.0,0.0,,10,15,asphalt,10,2.0,measured
2026-10-15T07:00:00,zone_02,School Garden,10.7618,106.6825,27.8,84.0,0.0,,60,70,grass,0,0.5,measured
2026-10-15T07:30:00,zone_02,School Garden,10.7618,106.6825,28.2,83.0,0.0,,60,70,grass,0,0.5,measured
2026-10-15T09:00:00,zone_02,School Garden,10.7618,106.6825,30.5,75.0,0.3,,60,70,grass,10,0.5,measured
2026-10-15T11:30:00,zone_02,School Garden,10.7618,106.6825,32.1,68.0,0.0,,60,70,grass,15,0.5,measured
2026-10-15T14:00:00,zone_02,School Garden,10.7618,106.6825,33.0,65.0,0.5,,60,70,grass,10,0.5,measured
2026-10-15T16:00:00,zone_02,School Garden,10.7618,106.6825,31.2,72.0,0.0,,60,70,grass,5,0.5,measured
```

### Template rules:
- `timestamp`: ISO 8601 local time (UTC+7).
- `wind_speed`: `0.0` if no anemometer available.
- `ndvi`: empty (not measured).
- `student_count`: 0 outside recess/lunch hours.
- `exposure_hours`: estimated from school timetable (e.g., 2.0 for playground, 0.5 for garden).
- `provenance`: `measured` for all rows.

---

## 8. Pilot Acceptance Criteria

### 8.1 Missing-Data Rate
- **Target:** ≤ 5% of required cells empty across all imported rows.
- **Operational rule (pilot-quality):** If >5% of rows have missing required fields, the measurement day is flagged for review. Data may still be usable if missingness is random.
- **Note:** This is a practical threshold for pilot quality control, not a statistically derived criterion.

### 8.2 Sensor Stability
- **Target:** During calibration check (10 min side-by-side), sensor readings should not drift by >0.5°C or >3% RH.
- **Operational rule:** If drift exceeds these values, note the drift in the notebook. Apply a time-based linear correction if drift is monotonic. If drift is erratic, exclude that sensor from the day's measurements.
- **Note:** 0.5°C and 3% RH are typical of consumer-grade sensors. These are practical thresholds, not calibrated accuracy claims.

### 8.3 Timestamp Consistency
- **Target:** All timestamps within a measurement window (e.g., 07:00–07:30) should fall within that window.
- **Operational rule:** If a timestamp is >15 minutes outside its planned window, flag the row for review. It may still be usable but the time-of-day grouping may be incorrect.
- **Pass criterion:** 100% of timestamps parse as valid ISO 8601. ≥90% within their planned windows.

### 8.4 Duplicate Records
- **Target:** Zero duplicate `(timestamp, zone_id)` pairs.
- **Operational rule:** If duplicates exist, keep the later reading (assuming it was a correction). Log the duplicate in the research notebook.
- **Pass criterion:** 0 duplicates after deduplication.

### 8.5 Cognitive-Test Completion
- **Target:** ≥80% of student sessions have a completed cognitive-test record.
- **Operational rule:** If a student skips the test, record "N/A" in the questionnaire CSV. Exclude that student from cognitive analysis but keep their thermal data.
- **Pass criterion:** ≥80% completion rate across all sessions.

### 8.6 Protocol Deviations
- **Target:** Document all deviations from the protocol.
- **Operational rule:** Each deviation is logged in the research notebook with: date, time, what happened, what was planned, impact on data.
- **Pass criterion:** All deviations documented. No unrecorded gaps in the measurement schedule.

### 8.7 Overall Pilot Pass Criteria
The pilot is considered successful if:
- [ ] All 3 zones measured at all 5 time points (15 zone-time observations minimum).
- [ ] Missing-data rate ≤ 5%.
- [ ] Sensor drift ≤ 0.5°C during calibration.
- [ ] All timestamps valid ISO 8601.
- [ ] Zero duplicate `(timestamp, zone_id)` pairs.
- [ ] ≥80% cognitive-test completion.
- [ ] All protocol deviations documented.
- [ ] CSV imports into SYS without errors.
- [ ] Dashboard displays data correctly with `provenance: measured` badge.

---

## 9. Limitation: Single-Sensor Spatial Comparison

### The Problem
The protocol specifies **one temperature/humidity sensor** moved between zones sequentially. This means:

1. **Temporal confounding:** Zone A is measured at 07:00, Zone B at 07:03, Zone C at 07:06. Temperature may change between measurements.
2. **Not simultaneous:** We cannot claim that Zone A was hotter than Zone B *at the same moment*. We can only claim it was hotter *during the same measurement window*.
3. **Order effects:** If zones are always measured in the same order, systematic time-of-day drift could bias the comparison.

### Mitigations (already in protocol)
1. **Counterbalance measurement order** across days (measure Zone A first on Day 1, Zone B first on Day 2, etc.).
2. **Keep measurement windows tight** (5 minutes per round for 3 zones = 15 minutes total, during which conditions are assumed relatively stable).
3. **Record exact timestamps** so measurement order is documented.

### What this means for SYS
- The risk score ranking from SYS is based on simultaneous inputs (one `timestamp` per `zone_id`). When importing pilot data, each zone gets its own timestamp. The dashboard will display the zone's risk at its measurement time, not at a common reference time.
- **This is acceptable for a pilot.** The purpose is to compare zones, not to establish causal simultaneity.

### Recommendation
- In the field notebook, record the **order** in which zones were measured each round.
- When analyzing pilot data, acknowledge the single-sensor limitation.
- For a future definitive study, use N sensors (one per zone) for simultaneous measurement.

---

## Required Changes Before Pilot

### Change 1: Loader must not crash on `wind_speed: 0.0` with `provenance: measured`
- **Current behavior:** Already works. `wind_speed` accepts 0.0. No change needed.
- **Status:** ✅ No change required.

### Change 2: Add `weather_condition` as optional field
- **Current behavior:** CSV loader ignores extra columns. `ZoneReading` does not have this field.
- **Decision:** Do NOT add to SYS schema. Record weather condition in the field notebook only. It is metadata, not a variable used by the risk engine.
- **Status:** ✅ No change required.

### Change 3: Ensure `exposure_hours` can represent estimated values
- **Current behavior:** `exposure_hours: float` accepts any non-negative value. Estimated values from the timetable (e.g., 2.0) are valid.
- **Status:** ✅ No change required.

### Change 4: Nothing to change in the code
- **After thorough analysis, the current SYS schema and loader are sufficient for pilot data import.** The 3 "must fix" items from the verdict header were evaluated and found to already work correctly. No code changes are needed.

### Change 5 (Recommended, not required): Pilot data-entry template
- Create a template CSV file in `data/` that field workers can copy and fill in.
- **Action:** Produce the template below.

---

## Pilot CSV Template

A blank template with headers and one example row:

```csv
timestamp,zone_id,zone_name,lat,lon,air_temperature,humidity,wind_speed,ndvi,canopy_pct,shade_pct,surface_type,student_count,exposure_hours,provenance
2026-10-15T07:00:00,zone_01,Main Playground,10.7620,106.6820,,,0.0,,10,15,asphalt,0,2.0,measured
```

Instructions for field workers:
1. Copy this row for each measurement.
2. Fill in `timestamp` as `YYYY-MM-DDTHH:MM:SS` (local time).
3. Fill in `air_temperature` and `humidity` from the sensor display.
4. Set `wind_speed` to `0.0` if no anemometer.
5. Leave `ndvi` empty.
6. Set `student_count` to the number of students visible in the zone.
7. Set `exposure_hours` based on the school timetable.
8. Keep `provenance` as `measured`.

---

## Fieldwork Acceptance Checklist

### Pre-Fieldwork
- [ ] Zone map completed with zone_id, zone_name, lat, lon, surface_type, canopy_pct, shade_pct for all zones.
- [ ] Sensor calibrated (side-by-side check passed, drift ≤ 0.5°C).
- [ ] Template CSV created and tested (imports into SYS without error).
- [ ] Student consent forms collected.
- [ ] Questionnaires and cognitive tests printed.
- [ ] Notebook, pen, phone, water bottles, first-aid kit ready.

### During Fieldwork
- [ ] All 5 time points measured for all zones.
- [ ] Timestamps recorded as ISO 8601.
- [ ] Sensor readings recorded immediately (not from memory).
- [ ] Protocol deviations logged in notebook.
- [ ] Student questionnaires collected after each session.
- [ ] No student showed signs of heat illness.

### Post-Fieldwork (Same Day)
- [ ] Data entered into CSV within 4 hours of measurement.
- [ ] All required cells filled (missing-data rate ≤ 5%).
- [ ] No duplicate `(timestamp, zone_id)` pairs.
- [ ] All timestamps valid ISO 8601 and within ±15 min of planned windows.
- [ ] Cognitive-test completion ≥ 80%.
- [ ] All protocol deviations documented.
- [ ] CSV imported into SYS and dashboard verified.
- [ ] Raw notebook pages stored safely.
- [ ] Digital data backed up to 2 locations.

### Pilot Success Criteria
- [ ] All zones measured at all time points.
- [ ] Missing-data rate ≤ 5%.
- [ ] Sensor drift ≤ 0.5°C.
- [ ] Zero duplicates.
- [ ] CSV imports without SYS errors.
- [ ] Dashboard displays `provenance: measured` badge.

---

*End of Pilot Readiness Review.*
