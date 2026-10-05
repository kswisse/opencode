# Synthetic Analysis Report — School Heat Intelligence

> **KẾT QUẢ DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THỰC NGHIỆM**
>
> All results presented in this report are based on synthetically generated data
> for research protocol demonstration. Coefficients, weights, and heuristics are
> illustrative parameters, NOT empirically calibrated findings.

---

## 1. Dataset Description

| Property | Value |
|----------|-------|
| Data type | Synthetic environmental + student-level |
| Zones | 5 (Playground, Garden, Courtyard, Sports Field, Canteen) |
| Duration | 10 days |
| Sampling | Hourly, 07:00–16:00 (10 hours/day) |
| Total readings | 500 (10 days × 10 hours × 5 zones) |
| Students | 30 (anonymous IDs S01–S30) |
| Student sessions | 180 (30 students × 2 zones × 3 days) |
| Reproducibility | `random.seed(42)` |
| Provenance | All records marked `provenance: synthetic` |

### 1.1 Zone Characteristics

| Zone | Name | Surface | Canopy (%) | Shade (%) |
|------|------|---------|------------|-----------|
| zone_01 | Main Playground | asphalt | 10 | 15 |
| zone_02 | School Garden | grass | 60 | 70 |
| zone_03 | Courtyard | concrete | 25 | 40 |
| zone_04 | Sports Field | grass | 5 | 10 |
| zone_05 | Canteen Area | concrete | 45 | 55 |

## 2. Variables Measured

### Environmental Variables
- `air_temperature` (°C) — hourly air temperature
- `humidity` (%) — relative humidity
- `wind_speed` (m/s) — wind speed at zone level
- `canopy_pct` (%) — tree canopy cover percentage
- `shade_pct` (%) — shade cover percentage
- `surface_type` — asphalt, concrete, or grass
- `student_count` — number of students in zone
- `exposure_hours` — daily exposure hours per zone

### Student-Level Variables
- `thermal_sensation` (ordinal, -3 to +3) — self-reported thermal feeling
- `thermal_comfort` (ordinal, 1–5) — self-reported comfort level
- `cognitive_score` (0–20) — cognitive test performance
- `reaction_time_ms` (400–800ms) — simple reaction time
- `activity_before` — sitting/walking/running
- `clothing` — short_sleeves/long_sleeves
- `hydration` — yes/no

## 3. Methods

### 3.1 Synthetic Data Generation

- **Diurnal pattern**: Temperature follows a realistic daily cycle: ~28°C at 07:00, peaking ~36°C at 13:00–14:00, declining to ~32°C at 16:00
- **Surface effects** (illustrative heuristics): asphalt +2.0°C, concrete baseline, grass -0.75°C
- **Canopy effects** (illustrative heuristic): ~0.3°C cooling per 10% canopy cover
- **Humidity**: inversely correlated with temperature (50–90% range)
- **Weather variability**: day-to-day temperature offsets ±1–3°C
- **Student presence**: zero outside recess periods, 20–80 during recess/lunch

### 3.2 Statistical Methods

- **Descriptive statistics**: mean, standard deviation, min, max per zone
- **Effect sizes**: Cohen's d for hot vs. cool zones, asphalt vs. grass
- **Correlation analysis**: Pearson and Spearman correlations (canopy↔temperature, surface↔temperature)
- **Linear regression**: temperature ~ canopy_pct (OLS)
- **Forecast validation**: 24-hour holdout MAE/RMSE
- **Intervention simulation**: +20% canopy cover scenario

### 3.3 Risk Scoring

The composite heat risk score uses the Rothfusz heat index (Steadman 1979) with the following illustrative heuristic weights:

```
risk_score = (0.5 × HI_norm + 0.2 × RH_norm + 0.15 × WS_norm + 0.15 × SF_norm) × 100
```

**These weights are NOT empirically calibrated.**

## 4. Assumptions

1. All temperature adjustments (surface, canopy) are illustrative heuristics, not empirical cooling coefficients
2. Risk score weights are arbitrary heuristic parameters for MVP demonstration
3. Student cognitive performance relationships are deliberately weak (R² ~0.05–0.10) to simulate realistic noise
4. No causal claims — all correlations are observational on synthetic data
5. Intervention projections are scenario outputs, not measured outcomes
6. Zone coordinates are illustrative (not real campus coordinates)

## 5. Synthetic Results

### 5.1 Descriptive Statistics

See `data/research_outputs/summary_stats.csv`

### 5.2 Zone Comparison

Hot zones (Playground, Sports Field) vs. Cool zones (Garden, Canteen):
- Mean temperature difference: ~2–4°C
- Effect size (Cohen's d): medium to large

### 5.3 Correlation Analysis

- Canopy cover ↔ Temperature: negative correlation (r ≈ -0.4 to -0.6)
- Surface type ↔ Temperature: asphalt warmer than grass

### 5.4 Regression

Temperature ~ Canopy: slope ≈ -0.03 to -0.04 °C per % canopy

### 5.5 Figures

All figures saved to `data/research_outputs/fig/`:
- `fig_campus_heatmap.png` — zone temperatures
- `fig_canopy_vs_temp.png` — canopy vs temperature scatter
- `fig_diurnal_pattern.png` — temperature over time
- `fig_forecast_vs_observed.png` — forecast validation
- `fig_exposure_ranking.png` — exposure scores
- `fig_intervention_comparison.png` — before/after intervention

## 6. Limitations

1. **All data is synthetic** — no real sensor measurements or student assessments
2. **No empirical calibration** — all weights and coefficients are illustrative heuristics
3. **No field validation** — relationships have not been verified against real-world measurements
4. **Small sample** — 500 readings over 10 days; real study would need multi-season data
5. **No confounders modeled** — real heat exposure depends on many unmodeled factors
6. **Cognitive effects** are deliberately weak and noisy — this is realistic but means no significant effect is expected
7. **Intervention projections** are heuristic, not physics-based temperature models

## 7. What Must Be Rerun After Real Data Collection

After collecting real field data, the following must be **completely rerun**:

1. **Environmental data loader** — replace synthetic CSV with real sensor data
2. **Risk score calibration** — empirically calibrate heat index weights using measured thermal stress indicators
3. **Statistical analysis** — rerun all descriptive statistics, correlations, regressions on real data
4. **Forecast validation** — retrain and evaluate forecast models on real time series
5. **Intervention comparison** — validate intervention effects with before/after field measurements
6. **QC pipeline** — rerun QC on real data (different expected ranges may apply)
7. **All figures and tables** — regenerate from real data
8. **Student-level analysis** — rerun with real thermal comfort and cognitive test data

**Do NOT present synthetic results as empirical findings.**

---

*Report generated by the School Heat Intelligence synthetic research pipeline.*
*All weights and coefficients are illustrative heuristics, NOT empirically calibrated.*
