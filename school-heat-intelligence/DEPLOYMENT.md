# Deployment Guide — School Heat Intelligence

## Deployment Readiness

**Status: PASS**

## Python Version

- **Required:** Python 3.11 or higher
- **Recommended:** Python 3.12 (Streamlit Community Cloud default)
- **Tested on:** Python 3.12.10

## Runtime Dependencies

All runtime dependencies are listed in `requirements.txt`:

```
streamlit>=1.30.0
pandas>=2.1.0
numpy>=1.26.0
pydantic>=2.5.0
folium>=0.15.0
streamlit-folium>=0.15.0
plotly>=5.18.0
pyyaml>=6.0
matplotlib>=3.7.0
```

## Streamlit Entry Point

```
src/heat_intelligence/dashboard/app.py
```

## Repository Structure (Deployment-Relevant)

```
school-heat-intelligence/
├── config.yaml                          # Runtime configuration (weights, thresholds)
├── data/
│   └── demo_campus.csv                  # Synthetic demo data (4032 readings)
├── src/
│   └── heat_intelligence/
│       ├── config.py                    # Config loader
│       ├── data/
│       │   └── loader.py                # CSV/JSON data loader
│       ├── models/
│       │   └── schemas.py               # Pydantic data models
│       ├── risk/
│       │   ├── engine.py                # Risk score computation
│       │   └── heat_index.py            # Rothfusz heat index
│       ├── hotspot/
│       │   └── detector.py              # Hotspot detection
│       ├── exposure/
│       │   └── calculator.py            # Student exposure scoring
│       ├── intervention/
│       │   └── simulator.py             # Intervention simulation
│       ├── priority/
│       │   └── engine.py                # Priority ranking
│       └── dashboard/
│           ├── app.py                   # ← Streamlit entry point
│           ├── components.py            # Reusable UI components
│           └── pages/
│               └── p1_overview.py       # Overview page (campus map, risk, hotspots)
├── requirements.txt                     # Runtime dependencies
├── pyproject.toml                       # Project metadata
└── run.sh                               # Local launch script
```

## Streamlit Community Cloud Setup Steps

### 1. Push to GitHub
Ensure the repository is on the `main` branch with all files committed:
```bash
git add .
git commit -m "Deployment-ready MVP"
git push origin main
```

### 2. Connect to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository and the `main` branch

### 3. Configure the App
- **Repository:** `your-username/school-heat-intelligence`
- **Branch:** `main`
- **Main file path:** `src/heat_intelligence/dashboard/app.py`
- **Python version:** 3.12

### 4. Deploy
Click "Deploy". Streamlit Community Cloud will:
1. Install dependencies from `requirements.txt`
2. Run `streamlit run src/heat_intelligence/dashboard/app.py`
3. Serve the app at a public URL

## Key Path Configuration

All paths in the app are relative to the repository root and resolve correctly on Linux/cloud:

- **Data path:** `data/demo_campus.csv` — resolved via `Path(__file__).parent.parent.parent.parent / "data" / "demo_campus.csv"` from `app.py`
- **Config path:** `config.yaml` — loaded via `load_config()` with default CWD-relative path

## Known Limitations

1. **Single-page MVP:** Only the Overview page is exposed. Backend modules are preserved for future development.
2. **Synthetic data only:** Demo data is synthetic, not real measurements.
3. **No authentication:** The app is publicly accessible once deployed.
4. **Folium maps:** May have limited interactivity on mobile devices.
5. **No persistent storage:** Data is loaded from the repository on each app start.

## Verification Checklist

- [x] `requirements.txt` includes all runtime dependencies
- [x] `streamlit-folium` added (was missing from pyproject.toml)
- [x] Unused `pydantic-settings` removed
- [x] Data path resolves on Linux (4 levels up from app.py)
- [x] Config path resolves from CWD (repo root)
- [x] `data/demo_campus.csv` committed
- [x] `config.yaml` committed
- [x] No secrets, API keys, or machine-specific paths
- [x] 119/119 tests passing
- [x] App imports verified (no import errors)

## Local Launch

```bash
streamlit run src/heat_intelligence/dashboard/app.py
```

Or use the shell script:
```bash
bash run.sh
```
