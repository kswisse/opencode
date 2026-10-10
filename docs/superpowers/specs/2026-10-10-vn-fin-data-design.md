# vn-fin-data — Vietnam Listed-Company Financial Dataset

**Date:** 2026-10-10
**Status:** Approved (design phase)
**Timeline:** 12 weeks, ~5–10h/week

## Goal

Ship one public, well-engineered dataset of Vietnamese listed-company financial
statements (HOSE/HNX/UPCoM, ~300–700 tickers, quarterly + annual), published on
Kaggle and GitHub, with clean methodology docs and a demo notebook.

This is a foundation project, not a revenue product. Success is:

1. A CI-green repo with crawler + transform + quality tests.
2. A public Kaggle dataset others can actually use.
3. A blog post (EN) that doubles as portfolio/marketing for later data products.

## Non-goals (explicit)

- No web app, no API server, no dashboard, no database server.
- No ML / credit scoring / predictions — data first, models later.
- No private-company registry data (dangkykinhdoanh) in this phase — deferred
  until pipeline + credibility exist.
- Storage = Parquet files + DuckDB CLI queries only.

## Data sources

Primary candidates (probe in week 1, pick based on what the probe finds):

- **CafeF** — free ticker pages with balance sheet / income / cash flow tables.
- **Vietstock Finance** — financials pages per ticker; also sells a paid
  DataFeed (out of scope, but their public pages are the fallback source).
- **HSX/HNX official disclosures** — backup if aggregators block scraping.

Probe decides. The chosen source must provide: full statement line items,
per-period values (quarter + year), at least ~5 years of history, and a stable
HTML/JSON structure.

### Access rules

- Respect `robots.txt` and rate-limit requests (concrete limit set after
  probe; default guess ≤1 request/sec per host).
- Crawler must be resumable and idempotent — reruns never double-store.
- Raw pages/JSON snapshots stored alongside parsed data for auditability.
- `docs/data-sources.md` records: source URLs, fetch dates, observed ToS
  constraints, and what is/isn't allowed for redistribution.
- **Known risk:** aggregator ToS may restrict commercial resale. Attribution
  + non-commercial license on v1; commercial licensing question is a later
  decision, documented in the README, not resolved now.

## Architecture

```
vn-fin-data/
├── pyproject.toml          # ruff, mypy, pytest, hypothesis (dev deps)
├── .github/workflows/ci.yml
├── docs/
│   ├── data-sources.md     # sources, ToS notes, probe findings
│   └── schema.md           # canonical field definitions
├── src/vnfindata/
│   ├── crawl/              # fetchers: raw -> data/raw/*.parquet + snapshots
│   ├── transform/          # normalize: raw -> canonical VAS schema
│   ├── ratios/             # derived indicators
│   └── cli.py              # duckdb-friendly entry: crawl / transform / ratios
├── tests/                  # fixture-driven parse tests + hypothesis quality tests
├── data/
│   ├── raw/                # immutable snapshots (gitignored if large)
│   └── clean/              # canonical parquet (published artifact)
└── notebooks/              # demo analysis (runs clean top-to-bottom)
```

Three stages, each independently runnable and testable:

1. **crawl** — fetch statements per ticker/period → raw Parquet + source
   snapshot. Rate-limited, resume-aware (skip already-fetched keys).
2. **transform** — map raw line items → canonical schema (VAS: balance sheet,
   income statement, cash flow). Unmapped items are flagged, not silently
   dropped; missing items are null with a `quality_flag`.
3. **ratios** — derive ~15 indicators from canonical data: ROE, ROA,
   debt/equity, current ratio, gross/net/operating margin, revenue & profit
   growth (YoY, QoQ), asset turnover, working-capital days, interest coverage,
   capex/revenue.

### Canonical schema (v1)

Long format: `ticker, fiscal_period (FY/Q1..Q4), period_end, statement,
item_code, value_vnd, unit, source, quality_flag`. One row per item per
period. Wide tables are a presentation concern — the notebook pivots as
needed.

Why long: statement formats differ across companies (banks/insurers vs
industrial), and long format survives missing items without schema churn.

## Quality testing

Hypothesis + example-based tests:

- Accounting identity: `assets ≈ liabilities + equity` within tolerance.
- Range checks: margins/ratios within sane bounds (flag, not fail, on
  outliers — real companies can be weird).
- Completeness: every ticker in the registry has ≥1 period; report coverage.
- Parse stability: fixture HTML/JSON → exact expected rows (regression guard
  when site markup changes).

Failures produce a quality report (`quality_report.md`), not a crash loop —
data collection must survive bad rows.

## Publish (weeks 10–12)

- **Kaggle:** dataset upload (parquet + README + schema doc), version-tagged.
- **GitHub:** repo public, CI badge, methodology README (sources, fetch
  dates, limitations, license, attribution).
- **Notebook:** one demo (e.g., sector-level margin trends 5 năm) that runs
  from the published data without crawling.
- **Blog (EN):** "How I built a Vietnam listed-company financial dataset" —
  published on GitHub Pages or dev.to.

## 12-week schedule

| Week | Deliverable |
|------|-------------|
| 1–2 | Source probe results in `docs/data-sources.md`; repo scaffold; CI green with empty-pipeline test |
| 3–6 | Crawler covers full ticker registry; resumable; fixture parse tests pass |
| 7–9 | Canonical transform + ratios; hypothesis quality tests pass; quality report generated |
| 10–11 | Kaggle upload; README + schema docs; demo notebook runs clean |
| 12 | Blog post published; final CI + full-rerun verification |

## Verification

- CI (ruff + mypy + pytest) green on every push.
- Phase gate: each phase ends with its tests passing locally.
- Final gate: full crawl from scratch (resume path exercised) + transform +
  ratios + notebook executed top-to-bottom on a fresh clone.

## Risks

| Risk | Mitigation |
|------|------------|
| Source blocks scraping / markup changes | Fixture regression tests; fallback source listed above; raw snapshots allow re-parse without re-fetch |
| ToS restricts redistribution | Non-commercial v1 license + attribution; revisit before any commercial use |
| Scope creep (API! dashboard! scoring!) | Non-goals section is binding; revisit only after v1 ships |
| Time overrun (exam weeks, 5–10h budget) | Weekly deliverables sized so any week can be skipped without breaking the pipeline |
