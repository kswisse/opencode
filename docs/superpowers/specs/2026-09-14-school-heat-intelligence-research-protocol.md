# Research Protocol v1: School Heat Intelligence — Real-World Measurement Study

**Version:** 1.0  
**Date:** 14 September 2026  
**Status:** Approved — Ready for pilot  
**Scope:** Field measurement protocol for Vietnamese urban school campus heat study

---

## 1. Research Objectives

### Primary Objective
Measure spatial and temporal variation in outdoor thermal conditions across campus zones at a Vietnamese urban school, and quantify student heat exposure during typical school hours.

### Secondary Objectives
1. Characterize the relationship between surface type, canopy cover, and microclimate temperature.
2. Measure the difference in thermal conditions between sun-exposed and shaded zones.
3. Document student thermal sensation and perceived comfort across zones.
4. Provide a measured dataset that can replace the synthetic demo data in SYS (School Heat Intelligence).
5. Validate whether the SYS Composite Heat Risk Score ranking aligns with observed thermal conditions.

### Hypotheses (Exploratory)
- H1: Zones with higher canopy cover have lower air temperature than zones with low canopy cover.
- H2: Concrete/asphalt surfaces are associated with higher thermal stress than grass surfaces.
- H3: Students report higher thermal discomfort in hot-exposed zones than in shaded zones.

> **Note:** These are exploratory hypotheses for a pilot study. The study is not powered for confirmatory testing.

---

## 2. Sampling Strategy for Campus Zones

### Zone Identification
1. Walk the campus with a school map.
2. Identify **4–6 distinct outdoor zones** that differ in surface type and/or canopy cover.
3. For each zone, record:
   - Descriptive name (e.g., "Main Playground", "Courtyard Near Canteen")
   - Approximate GPS coordinates (use phone GPS)
   - Surface type: `asphalt`, `concrete`, `grass`, `permeable`
   - Canopy cover: estimate percentage of zone shaded by trees at solar noon
   - Shade cover: estimate percentage of zone with any shade (buildings + trees)
   - Approximate area (m²)

### Zone Selection Criteria
- Must be outdoors (not covered by a permanent roof).
- Must be accessible to students during break time.
- Should span at least 2 different surface types.
- Should include at least one zone with tree canopy and one without.

### Deliverable
A zone map (hand-drawn or photo with annotations) listing zone_id, zone_name, lat, lon, surface_type, canopy_pct, shade_pct for each zone. This becomes the reference for all subsequent measurements.

---

## 3. Sensor Placement Protocol

### 3.1 Variables to Measure

| Variable | Unit | Method | Priority |
|----------|------|--------|----------|
| Air temperature (Ta) | °C | Digital thermometer / weather station | Required |
| Relative humidity (RH) | % | Hygrometer / weather station | Required |
| Wind speed | m/s | Anemometer (if available) or qualitative | Recommended |
| Surface temperature (Ts) | °C | IR thermometer (if available) | Optional |
| Solar radiation | W/m² | Phone light meter app (if available) | Optional |

### 3.2 Sensor Specifications (Minimum Viable)

**Required equipment:**
- 1 digital temperature/humidity sensor with display (e.g., household weather station, ±0.5°C accuracy minimum)
- 1 stopwatch or phone timer
- Notebook and pen
- Phone with camera and GPS

**Nice-to-have:**
- Handheld anemometer
- IR thermometer (non-contact)
- UV index meter

### 3.3 Sensor Height
- **Air temperature and humidity:** Place sensor at **1.1 meters above ground** (approximately chest height for a Vietnamese secondary school student).
- Use a tripod, clamp, or tape the sensor to a pole at the correct height.
- If no tripod is available, a student holds the sensor at chest height with arm extended, standing still, for the duration of the reading.

### 3.4 Placement Rules
1. Place sensor in the **center of the zone** or in a representative location.
2. Avoid placing directly against a wall, metal surface, or inside a trash bin.
3. Avoid placing directly in a puddle or wet surface.
4. For shaded zones, place sensor **in the shade** (this is the zone's characteristic condition).
5. For sun-exposed zones, place sensor **in direct sunlight** (this is the zone's characteristic condition).
6. Keep the sensor at least 2 meters away from the person recording data (to avoid body heat interference).
7. Do not breathe on or touch the sensor element.

### 3.5 Sampling Interval
- **Primary measurements:** Every **30 minutes** during school hours (07:00–16:00).
- **Peak measurement:** Additional reading at **11:30–12:30** (solar noon window).
- Each reading takes approximately 2–3 minutes per zone.

### 3.6 Calibration / Check Procedure
1. **Before each measurement day:**
   - Place all sensors side by side in the same location for 10 minutes.
   - Record readings from all sensors.
   - If readings differ by >1°C or >5% RH, note the offset and apply corrections.
2. **Reference check:**
   - If a calibrated reference thermometer is available, compare each sensor against it.
   - Record the offset for each sensor.
3. **Documentation:**
   - Log all calibration checks in a notebook with date, time, sensor ID, reference value, and measured value.

---

## 4. Measurement Schedule

### 4.1 Times of Day
| Period | Time | Reason |
|--------|------|--------|
| Morning cool | 07:00–07:30 | Baseline before heat builds |
| Morning warm-up | 09:00–09:30 | Mid-morning transition |
| Midday peak | 11:30–12:30 | Maximum solar radiation |
| Afternoon | 14:00–14:30 | Post-peak sustained heat |
| Late afternoon | 16:00–16:30 | Cooling phase |

Each measurement window = 5 minutes per zone × 6 zones = 30 minutes total per window.

### 4.2 Number of Days
- **Minimum:** 3 measurement days (one per weather condition type).
- **Target:** 5 measurement days spread across 2–3 weeks.
- **Required conditions to capture:**
  - 1 hot, sunny day (clear sky, T_max > 33°C)
  - 1 warm, partly cloudy day (T_max 30–33°C)
  - 1 overcast or rainy day (T_max < 30°C or rain)

### 4.3 Weather-Condition Requirements
- **Must measure on hot days** — this is the core use case for the system.
- **Should also measure on cooler days** — to provide contrast and test system sensitivity.
- **Do NOT measure during active rainfall** — sensors may be damaged and readings are not representative of the system's use case (outdoor activity conditions).
- **Wind:** Record qualitative wind (calm / light / moderate) if no anemometer is available.

### 4.4 Scheduling Constraints
- Measurements must not disrupt class time. Align measurement windows with recess, lunch, or PE periods.
- Student participants must not be pulled from class for more than 10 minutes at a time.
- Avoid exam periods and school holidays.

---

## 5. Ground-Truth Data Schema

The following schema is **directly compatible** with the existing SYS `ZoneReading` schema.

### CSV Column Definitions

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `timestamp` | ISO 8601 | Yes | `YYYY-MM-DDTHH:MM:SS` (local time, ICT/UTC+7) |
| `zone_id` | string | Yes | Zone identifier (e.g., `zone_01`) |
| `zone_name` | string | Yes | Human-readable zone name (e.g., `Main Playground`) |
| `lat` | float | Yes | Zone center latitude (decimal degrees) |
| `lon` | float | Yes | Zone center longitude (decimal degrees) |
| `air_temperature` | float | Yes | Air temperature in °C (measured, not derived) |
| `humidity` | float | Yes | Relative humidity in % (measured) |
| `wind_speed` | float | Yes | Wind speed in m/s. If unavailable, use `0.0` and set provenance to `synthetic` |
| `ndvi` | float | No | NDVI from satellite. If unavailable, leave empty |
| `canopy_pct` | float | Yes | Tree canopy cover % (estimated from zone map) |
| `shade_pct` | float | Yes | Total shade % (trees + buildings, estimated) |
| `surface_type` | string | Yes | One of: `asphalt`, `concrete`, `grass`, `permeable` |
| `student_count` | int | Yes | Number of students present in zone during measurement |
| `exposure_hours` | float | Yes | Estimated hours students spend in this zone per day |
| `provenance` | string | Yes | `measured` for all real data points |

### Example Row
```
2026-10-15T11:30:00,zone_01,Main Playground,10.762,106.682,36.2,58.0,0.5,,30,20,asphalt,45,2.0,measured
```

### Additional Metadata (Optional, Not in SYS Schema)
These fields are for the research log only and are not imported into SYS:

| Field | Description |
|-------|-------------|
| `sensor_id` | Identifier for the sensor used |
| `calibration_offset` | Offset applied from calibration check |
| `weather_notes` | Qualitative weather description |
| `measurement_duration` | Seconds the sensor was at the location |
| `observer_id` | Who took the reading |

---

## 6. Student Study Design

### 6.1 Recruitment
- **Population:** Students at the participating school, grades 7–10 (age ~12–16).
- **Sample:** 20–30 volunteers from one or two classes.
- **Inclusion criteria:** Able to attend outdoor recess/lunch periods. No medical condition that contraindicates heat exposure (e.g., asthma requiring indoor restriction — check with school nurse).
- **Exclusion criteria:** Absent on measurement day, refuses consent.

### 6.2 Study Structure: Within-Subject Repeated Measures
Each student serves as their own control, experiencing multiple zones on the same day.

```
Day structure (per student):
  Morning:  Baseline questionnaire → Cognitive test 1 → Assign to Zone A → 15 min → Thermal questionnaire → Cognitive test 2
  Midday:   Assign to Zone B → 15 min → Thermal questionnaire → Cognitive test 3
  Afternoon: Assign to Zone C → 15 min → Thermal questionnaire → Cognitive test 4
```

### 6.3 Hot vs Cool Zone Comparison
- **Hot zone:** Zone with lowest canopy cover, hardest surface (asphalt/concrete), highest measured temperature.
- **Cool zone:** Zone with highest canopy cover, softest surface (grass), lowest measured temperature.
- Each student visits **at least one hot zone and one cool zone** on the same day.
- Zone order is **counterbalanced** across students (see randomization below).

### 6.4 Randomization
1. After the first measurement day (or pilot), classify zones as "hot" or "cool" based on measured temperatures.
2. Create a **crossover schedule:** Half the students visit Hot→Cool first, the other half Cool→Hot first.
3. Use a simple randomization method: write zone order assignments on slips of paper, have students draw randomly.
4. If more than 2 zones are studied, use a **Latin square** design to balance order effects.

### 6.5 Cognitive Tests
- **Tool:** A simple 5-minute paper test appropriate for the students' age.
- **Suggested tests:**
  - Digit symbol substitution test (DSST) — measures processing speed
  - Or a simple arithmetic test (20 problems, timed)
- **Administration:** Same test form each time (or parallel forms if available).
- **Record:** Number correct, number attempted.

### 6.6 Thermal Sensation / Comfort Questionnaire
Administer immediately after each 15-minute zone exposure.

**Thermal Sensation (adapted from ASHRAE 7-point scale):**
> "How do you feel right now?"  
> ☐ -3 Very cold  
> ☐ -2 Cold  
> ☐ -1 Slightly cold  
> ☐ 0 Neutral  
> ☐ +1 Slightly warm  
> ☐ +2 Warm  
> ☐ +3 Very warm / Hot

**Thermal Comfort:**
> "How comfortable do you feel right now?"  
> ☐ 1 Very comfortable  
> ☐ 2 Comfortable  
> ☐ 3 Slightly uncomfortable  
> ☐ 4 Uncomfortable  
> ☐ 5 Very uncomfortable

**Thermal Preference:**
> "Right now, I would prefer to be:"  
> ☐ Much cooler  
> ☐ Somewhat cooler  
> ☐ No change  
> ☐ Somewhat warmer  
> ☐ Much warmer

**Additional questions:**
- "Are you currently in the sun or shade?" (sun / shade / partly both)
- "How many minutes have you been outdoors today?" (estimated)

---

## 7. Confounders to Record

For each student measurement session, record:

| Confounder | How to Record | Why It Matters |
|------------|---------------|----------------|
| Time of day | Timestamp | Temperature varies diurnally |
| Weather condition | Sunny / Cloudy / Overcast / Rainy | Affects radiation load |
| Student activity level before measurement | Sitting / Walking / Running / Playing | Affects thermal perception |
| Clothing | Short sleeves / Long sleeves / Uniform type | Affects heat retention |
| Hydration status | Drank water in last 30 min? (Y/N) | Affects comfort |
| Recent physical activity | Moderate / Vigorous / None in last 15 min | Affects body heat production |
| Menstrual cycle phase (optional) | Self-reported if comfortable | May affect thermal perception |
| BMI (optional) | Height/weight if collected with consent | May affect thermal perception |

---

## 8. Student Exposure Measurement Method

### Definition
Student exposure = the amount of time students spend in thermally stressful conditions.

### Method
1. **Direct observation:** During recess/lunch, an observer records which zone each student group is in and for how long.
2. **Time-motion sampling:** Every 5 minutes, note which zone the student is in.
3. **Exposure hours calculation:**
   ```
   exposure_hours = Σ (minutes in zone_i) / 60
   ```
4. For the SYS schema, `exposure_hours` is the estimated daily hours a student spends in that zone (not per measurement session).

### Estimation Procedure
1. During recess (typically 30 min), observe a sample of students.
2. Record: total minutes spent in each zone.
3. Extrapolate to daily exposure: if recess is 30 min and lunch is 30 min, and a student spends 20 min of recess in the playground, daily exposure ≈ 20/60 × (recess + lunch) / recess_duration.

**Simplified approach for MVP:** Estimate exposure_hours per zone based on school schedule:
- If the playground is used for 2 hours/day → `exposure_hours = 2.0`
- If the courtyard is passed through for 0.5 hours/day → `exposure_hours = 0.5`

---

## 9. Safety, Consent, Privacy, and Stopping Criteria

### 9.1 Safety
- **Heat safety:** If any student shows signs of heat exhaustion (dizziness, nausea, excessive sweating, confusion), immediately move them to shade, provide water, and notify school staff.
- **Wet-bulb globe temperature (WBGT):** If available and WBGT > 32°C, suspend outdoor measurements and student activities.
- **Without WBGT:** If air temperature exceeds 40°C or a student reports feeling unwell, stop the session.
- **Water:** Ensure all participants have water bottles.
- **Sunscreen/hats:** Recommend students wear hats and sunscreen.

### 9.2 Consent
- **Parental/guardian consent:** Written consent form in Vietnamese, distributed at least 3 days before the study.
- **Student assent:** Verbal assent on the day, recorded by observer.
- **Consent form contents:** Purpose, procedures, risks, benefits, voluntary participation, right to withdraw, data usage, contact information.

### 9.3 Privacy
- Students are identified by **codes** (e.g., S01, S02), not names.
- The code-to-name mapping is stored separately in a locked notebook, accessible only to the research team.
- No photographs of students' faces.
- Data is stored on a password-protected device.
- No data is shared publicly with identifiable information.

### 9.4 Stopping Criteria
- **Safety stopping:** Any student shows heat-related illness → stop that student's session.
- **Data quality stopping:** If sensors malfunction or produce inconsistent readings → stop and recalibrate.
- **Ethical stopping:** If a student or parent withdraws consent → immediately stop and delete their data.
- **Study completion:** All planned measurement days are finished.

---

## 10. Sample-Size Strategy

### Approach
This is a **pilot study** — the goal is to collect enough data to:
1. Estimate the magnitude of temperature differences between zones.
2. Estimate the variability of student thermal responses.
3. Provide input for a future power analysis.

### What Is Needed for Power Analysis
To design a definitive study, we need from this pilot:

| Parameter | What to Estimate | How |
|-----------|-----------------|-----|
| Effect size (ΔT between zones) | Mean temperature difference between hottest and coolest zones | Pilot mean ± SD |
| Within-student variance | Variance of thermal sensation scores within the same student across sessions | Pilot variance |
| Between-student variance | Variance of thermal sensation scores between students | Pilot variance |
| Correlation between repeated measures | Intraclass correlation coefficient (ICC) for within-subject design | Pilot data |

### Pilot Sample Size Rationale
- **Zones:** 4–6 zones is sufficient to capture spatial variation on one campus.
- **Measurement days:** 3 days minimum (one per weather condition) provides initial data on day-to-day variability.
- **Students:** 20–30 students provides enough observations to estimate within-student variance (each student provides 2–4 observations across zones).
- **Total observations:** 4 zones × 5 time points × 3 days = 60 zone-time observations. With 20 students × 3 zones = 60 student-zone observations.

### Definitive Study Power Analysis
- Will be conducted after pilot data collection.
- Target: 80% power to detect a clinically meaningful difference in thermal sensation (e.g., 1 point on the 7-point scale) between hot and cool zones.
- Account for repeated measures design (within-subject correlation reduces required n).
- Use pilot estimates of ICC and effect size.

---

## 11. Primary Statistical Analysis Plan

### Primary Outcome
**Difference in air temperature between the hottest and coolest campus zones during peak hours (11:30–12:30).**

### Analysis
1. **Descriptive:** Mean, SD, min, max temperature per zone per time period.
2. **Visualization:** Heatmap of zone × time, bar chart of zone means with error bars.
3. **Comparison:** Paired t-test or Wilcoxon signed-rank test comparing temperatures between the hottest and coolest zones at each time point.
4. **Effect size:** Cohen's d for the temperature difference.

### Secondary Analyses
- Linear mixed-effects model: `temperature ~ zone + time_of_day + weather_condition + (1|day)`
- Correlation between canopy cover % and zone mean temperature.
- Correlation between surface type and zone mean temperature.

> **Note:** All analyses are exploratory. No multiple-comparison correction is applied in the pilot. Effect sizes and confidence intervals are reported.

---

## 12. Secondary / Exploratory Analyses

| Analysis | Method | Purpose |
|----------|--------|---------|
| Thermal sensation by zone | Ordinal logistic regression or Mann-Whitney U | Do students feel hotter in hot zones? |
| Cognitive performance by zone | Paired t-test on test scores | Does heat affect performance? |
| Thermal comfort by zone | Ordinal logistic regression or Mann-Whitney U | Is comfort lower in hot zones? |
| Diurnal pattern | Line plot of zone temperatures over time | When does heat peak? |
| Weather effect | Compare temperatures across measurement days | How much does weather matter? |
| Exposure estimate | Sum of student-hours × zone temperature | Total student heat exposure (degree-hours) |
| SYS validation | Rank zones by measured temperature, compare to SYS risk ranking | Does the system's ranking match reality? |

---

## 13. Data-Quality Checks and Exclusion Criteria

### Data-Quality Checks
1. **Range checks:** Air temperature must be 15–50°C. Humidity must be 0–100%. Flag values outside range.
2. **Consistency checks:** Temperature should not change by >5°C between consecutive readings at the same zone (unless weather changed dramatically).
3. **Completeness:** All required fields must be filled. If a field is missing, the row is excluded.
4. **Calibration:** If calibration check shows offset >1°C, apply correction before analysis.
5. **Duplicate check:** No two readings with the same timestamp and zone_id.

### Exclusion Criteria
- Row excluded if: missing required fields, temperature out of range, sensor known to be malfunctioning.
- Student excluded if: withdrew consent, incomplete questionnaire, absent for more than one session.
- Zone excluded if: fewer than 3 valid measurements across all days.

---

## 14. Mapping Between Measured Data and SYS Provenance Flags

| Source | SYS Provenance Flag | When to Use |
|--------|---------------------|-------------|
| Field measurement (sensor reading) | `measured` | All data points collected with physical sensors |
| School schedule estimate | `imported` | exposure_hours derived from timetable (not measured) |
| Satellite/NDVI data | `imported` | NDVI values from external source |
| Previously collected data | `measured` | If re-using data from an earlier measurement day |
| SYS model output | `predicted` | Forecast results generated by the system |
| SYS simulation output | `simulated` | Intervention scenario results |

### Rules
- Every row in the imported CSV must have `provenance: measured`.
- The system will automatically assign `provenance: predicted` to forecast outputs.
- The system will automatically assign `provenance: simulated` to intervention results.
- **Never mix** measured and synthetic data in the same import batch.

---

## 15. Exact Procedure for Importing Real Data into SYS

### Step 1: Prepare the CSV
1. Export or type the measurement data into a CSV file following the schema in Section 5.
2. Ensure all required columns are present.
3. Ensure timestamps are in ISO 8601 format: `YYYY-MM-DDTHH:MM:SS`.
4. Set `provenance` to `measured` for all rows.

### Step 2: Validate
1. Open the CSV in a spreadsheet or text editor.
2. Check that no columns are missing.
3. Check that numeric columns contain numbers (no stray text).
4. Check that zone_id values match the zone map.

### Step 3: Import
1. Place the CSV file at: `school-heat-intelligence/data/real_measurements.csv`
2. In the dashboard app, the data path in `app.py` can be updated to load the new file:
   ```python
   data_path = Path(__file__).parent.parent.parent.parent / "data" / "real_measurements.csv"
   ```
3. Alternatively, keep the existing path and replace the demo CSV content with real data.

### Step 4: Verify
1. Run the dashboard: `streamlit run src/heat_intelligence/dashboard/app.py`
2. Check that the Overview page shows the correct zones.
3. Check that Risk Analysis shows non-synthetic risk scores.
4. Check that the Methodology page shows `provenance: measured` in the data provenance badge.

### Step 5: Preserve the Demo
1. Before importing, rename the demo file: `demo_campus.csv` → `demo_campus_synthetic.csv`
2. Keep it in the data folder for reference and testing.

---

## 16. One-Day Pilot Protocol

### Purpose
Test the measurement procedure, timing, and logistics before the full study.

### Pilot Day Checklist
- [ ] Choose one measurement day (ideally warm/sunny).
- [ ] Select 3 zones (one hot, one cool, one intermediate).
- [ ] Prepare 1 temperature/humidity sensor.
- [ ] Prepare a notebook, pen, stopwatch, phone.
- [ ] Bring water bottles and first-aid kit.
- [ ] Conduct calibration check (sensor side-by-side for 10 min).

### Pilot Schedule (Example)
| Time | Activity | Duration |
|------|----------|----------|
| 07:00 | Calibration check. Record baseline readings. | 15 min |
| 07:15 | Measure all 3 zones (baseline). | 15 min |
| 07:30 | Check timing: is 15 min per zone realistic? | — |
| 09:00 | Measure all 3 zones (mid-morning). | 15 min |
| 11:30 | Measure all 3 zones (peak). | 15 min |
| 12:00 | Pilot student session: 2 students, 1 zone each, 15 min + questionnaire. | 45 min |
| 14:00 | Measure all 3 zones (afternoon). | 15 min |
| 16:00 | Measure all 3 zones (late afternoon). | 15 min |
| 16:30 | Debrief: What worked? What needs adjustment? | 30 min |

### Pilot Data to Record
- Total time per zone measurement.
- Any difficulties with sensor placement.
- Student reactions to the questionnaire.
- Whether the measurement windows fit within school schedules.
- Whether the zone map is accurate.

### Pilot Success Criteria
- All measurements completed within planned time windows.
- No sensor failures.
- Students understand and complete the questionnaire.
- Data can be entered into the CSV without issues.

---

## 17. Fieldwork Day Checklist

### Before the Day
- [ ] Consent forms distributed and collected.
- [ ] Sensors calibrated and checked.
- [ ] Zone map finalized and printed.
- [ ] Measurement schedule confirmed with school.
- [ ] Student participants briefed on procedure.
- [ ] Questionnaires printed (one per student per zone session).
- [ ] Cognitive tests printed.
- [ ] Notebook and pen ready.
- [ ] Phone charged (camera, GPS, timer).
- [ ] Water bottles for all participants.
- [ ] First-aid kit available.

### On the Day
- [ ] Arrive 30 minutes before first measurement.
- [ ] Conduct calibration check. Record in notebook.
- [ ] Set up measurement station for Zone 1.
- [ ] Begin measurements at scheduled times.
- [ ] After each reading: record timestamp, zone, temperature, humidity, wind, weather notes.
- [ ] For student sessions: distribute consent check, administer questionnaire, administer cognitive test, record responses.
- [ ] At end of day: check all data entries are complete, back up photos/notes.

### After the Day
- [ ] Enter data into CSV within 24 hours.
- [ ] Run range and consistency checks.
- [ ] Note any anomalies or issues in the research log.
- [ ] Store raw notebook pages in a safe location.
- [ ] Back up digital data to at least 2 locations.

---

## Appendix: Equipment List (Minimum Viable)

| Item | Quantity | Estimated Cost (VND) | Priority |
|------|----------|----------------------|----------|
| Digital T/RH sensor with display | 1–2 | 200,000–500,000 | Required |
| Notebook (A5) | 2 | 30,000 | Required |
| Pen (waterproof ink) | 3 | 15,000 | Required |
| Stopwatch (phone app) | 1 | Free | Required |
| Tape measure (for sensor height) | 1 | 30,000 | Required |
| String/tape (for marking height) | 1 roll | 10,000 | Required |
| Clipboard | 2 | 20,000 | Required |
| Printed questionnaires | 100 | 50,000 | Required |
| Printed cognitive tests | 50 | 25,000 | Required |
| Water bottles | 30 | 150,000 | Required |
| First-aid kit | 1 | 100,000 | Required |
| Handheld anemometer | 1 | 300,000–500,000 | Recommended |
| IR thermometer | 1 | 200,000–400,000 | Optional |
| UV index meter | 1 | 200,000 | Optional |
| **Total (minimum)** | | **~600,000–900,000** | |

---

*End of Research Protocol v1.*
