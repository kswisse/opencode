# StockScope — Masterplan v2 (Research-First Revision)

> Research & Hypothesis-Validation Engine for Investment Signal Discovery

**Version:** 2.0  
**Date:** 2026-09-19  
**Status:** Research Design  
**Baseline:** `2026-09-19-stockscope-masterplan.md` (v1)

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Audit of v1](#2-audit-of-v1)
3. [Design Principles](#3-design-principles)
4. [Revised System Architecture](#4-revised-system-architecture)
5. [Point-in-Time Data Model](#5-point-in-time-data-model)
6. [Raw Features vs Research Signals](#6-raw-features-vs-research-signals)
7. [Hypothesis Engine](#7-hypothesis-engine)
8. [Backtesting Engine](#8-backtesting-engine)
9. [Research Gate](#9-research-gate)
10. [Semantic Insider Analysis](#10-semantic-insider-analysis)
11. [AI Role Definition](#11-ai-role-definition)
12. [Research Ledger](#12-research-ledger)
13. [Valuation Engine](#13-valuation-engine)
14. [Thesis + Thesis Breaker Framework](#14-thesis--thesis-breaker-framework)
15. [Data Source Hierarchy](#15-data-source-hierarchy)
16. [Revised Database Schema](#16-revised-database-schema)
17. [Revised Sprint Plan](#17-revised-sprint-plan)
18. [Cost Analysis (Honest)](#18-cost-analysis-honest)
19. [What NOT to Build Yet](#19-what-not-to-build-yet)
20. [Changes from v1 → v2](#20-changes-from-v1--v2)

---

## 1. Executive Summary

### Original Objective (v1)

> Build an AI stock analysis dashboard that scores stocks 0-100 across 5 layers and gives a BUY/SELL verdict.

### Revised Objective (v2)

> Build a research & hypothesis-validation engine that discovers potentially mispriced investment signals, formulates explicit hypotheses, tests them against historical data, quantifies whether they contain predictive or economically useful information, performs valuation and risk analysis, and only then generates an evidence-backed investment research conclusion.

### Core Questions StockScope Must Answer

1. What potentially mispriced / underappreciated phenomenon was discovered?
2. Why might the market be misunderstanding it?
3. What observable variables represent this phenomenon?
4. Can the hypothesis be tested historically?
5. Does the signal survive realistic transaction costs and timing?
6. Is the result statistically and economically meaningful?
7. What alternative explanations exist?
8. What evidence would falsify the thesis?
9. What is the fair-value range?
10. What is the downside under adverse scenarios?

### What Changes

| Aspect | v1 | v2 |
|--------|----|----|
| **Primary output** | Score 0-100 + verdict | Research report with evidence chain |
| **Data model** | Snapshot-based | Point-in-time with availability tracking |
| **Analysis** | Weighted scoring | Hypothesis → backtest → validation |
| **AI role** | Source of truth | Hypothesis generation + evidence synthesis |
| **Backtesting** | Not included | Core system component |
| **Valuation** | Not included | DCF + scenario analysis |
| **Insider analysis** | Binary BUY/SELL | Semantic transaction classification |
| **Infrastructure** | PostgreSQL + Redis + Qdrant + n8n | PostgreSQL + Parquet (MVP) |
| **Markets** | Global (US, VN, CN, EU, JP, crypto) | US equities only (MVP) |
| **Dashboard** | 7 pages, full polish | Research report viewer (minimal) |

---

## 2. Audit of v1

### 2.1 Methodological Weaknesses

| # | Weakness | Impact | Severity |
|---|----------|--------|----------|
| 1 | **0-100 scoring assumes predictive validity** | Arbitrary weights create false confidence. No empirical evidence that RSI 25% + MACD 25% + BB 20% + MA 20% + Volume 10% predicts returns. | CRITICAL |
| 2 | **No look-ahead bias prevention** | Backtesting or analysis could use future data (e.g., using revised earnings data at the time of original filing). | CRITICAL |
| 3 | **No transaction cost modeling** | A signal that works before costs may be unprofitable after spreads, slippage, and commissions. | CRITICAL |
| 4 | **AI as source of truth** | v1 asks AI to produce "Confidence: 78%" — this is manufactured precision. AI cannot assign statistical confidence to claims. | HIGH |
| 5 | **No distinction between correlation and causation** | High insider buying + price increase ≠ insider buying causes price increase. | HIGH |
| 6 | **No historical testing framework** | Signals are assumed valid without empirical validation. | HIGH |
| 7 | **Binary insider analysis** | All Form 4 transactions treated as equivalent (open-market purchase ≠ tax-related sale ≠ option exercise). | MEDIUM |
| 8 | **No survivorship bias handling** | Delisted stocks, ticker changes, M&A not accounted for. | MEDIUM |
| 9 | **No data freshness tracking** | No distinction between event_date, announcement_date, and available_at. | MEDIUM |
| 10 | **Arbitrary alert thresholds** | "RSI > 70" is conventional but not empirically validated for each stock/sector. | LOW |

### 2.2 Architecture Over-Engineering

| # | Over-Engineering | Why It's Premature |
|---|------------------|--------------------|
| 1 | **Redis cache layer** | Not needed until data volume requires it. PostgreSQL + Parquet sufficient for MVP. |
| 2 | **Qdrant vector search** | Useful for semantic news search, but not critical for research engine MVP. |
| 3 | **n8n workflow automation** | Complex orchestration tool not needed when Python scripts suffice. |
| 4 | **4 notification channels** | Telegram bot is enough for MVP. Discord, email, Slack are features, not architecture. |
| 5 | **7 dashboard pages** | Research report viewer is the only UI needed until research engine is validated. |
| 6 | **Real-time WebSocket** | Research is not a real-time activity. Batch processing is appropriate. |
| 7 | **Multiple MCP servers** | market-data-mcp + dbhub are sufficient. Adding more increases complexity without clear benefit. |
| 8 | **Global market support** | US equities have the strongest data infrastructure. Supporting 6 markets simultaneously dilutes quality. |

### 2.3 Missing Capabilities

| # | Missing | Why It Matters |
|---|---------|----------------|
| 1 | **Point-in-time data model** | Without this, backtesting results are unreliable. |
| 2 | **Hypothesis engine** | System can only analyze user-supplied tickers, not discover opportunities. |
| 3 | **Backtesting engine** | No way to validate whether signals actually work. |
| 4 | **Research ledger** | No traceability from claims to evidence. |
| 5 | **Valuation framework** | No intrinsic value estimation, only relative ratios. |
| 6 | **Thesis breaker framework** | No systematic way to identify what would invalidate a thesis. |
| 7 | **Transaction cost modeling** | No way to assess real-world profitability. |
| 8 | **Robustness testing** | No sensitivity analysis, walk-forward validation, or subperiod analysis. |

---

## 3. Design Principles

### 3.1 Primary Design Principle

StockScope is a:

> **Research & hypothesis-validation engine**

NOT a:

> Multi-factor stock scoring dashboard

### 3.2 Core Principles

1. **Evidence before conclusion.** Every claim must trace to a source. AI summarizes evidence; AI does not manufacture confidence.

2. **Assume nothing works until tested.** No signal becomes production without passing the Research Gate.

3. **Point-in-time integrity.** Every observation must know when it occurred, when it was announced, and when it became available.

4. **Transaction costs are real.** Every signal must survive realistic cost assumptions.

5. **Failed hypotheses are valuable.** Store rejected hypotheses as research artifacts.

6. **Simplicity first.** PostgreSQL + Parquet + Python. Add infrastructure only when a concrete requirement justifies it.

7. **US equities first.** Build adapter interfaces for future markets, but focus depth on one market.

8. **AI is a tool, not an oracle.** AI generates hypotheses, extracts documents, synthesizes evidence. AI does not invent data, citations, or confidence.

---

## 4. Revised System Architecture

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RESEARCH WORKBENCH                          │
│                  (Streamlit — minimal UI)                        │
│  Hypotheses │ Backtests │ Research Reports │ Watchlist          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                     RESEARCH ENGINE                              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Hypothesis  │  │  Backtest    │  │  Valuation   │          │
│  │  Generator   │  │  Engine      │  │  Engine      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│  ┌──────▼─────────────────▼──────────────────▼───────┐          │
│  │              Evidence Ledger                       │          │
│  │  (every claim → source → calculation → confidence) │          │
│  └──────────────────────┬────────────────────────────┘          │
│                         │                                        │
│  ┌──────────────────────▼────────────────────────────┐          │
│  │           Research Gate Validator                  │          │
│  │  (economically explainable? out-of-sample? robust?)│          │
│  └──────────────────────┬────────────────────────────┘          │
└─────────────────────────┼───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     DATA LAYER                                   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL   │  │  Parquet     │  │  File Store  │          │
│  │  (structured) │  │  (time-series│  │  (filings,   │          │
│  │               │  │   + features)│  │   documents) │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                  │                   │
│  ┌──────▼─────────────────▼──────────────────▼───────┐          │
│  │           Market Data Adapters                     │          │
│  │  yfinance │ EdgarTools │ fredapi │ finews          │          │
│  └───────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow: Research Pipeline

```
Market Universe (S&P 500, NASDAQ, ...)
      │
      ▼
┌─────────────────────┐
│  Anomaly / Pattern  │  ← Screen for unusual patterns
│  Detection          │     (margin changes, insider clusters,
│                     │      earnings revisions, valuation gaps)
└──────────┬──────────┘
           │ Candidates
           ▼
┌─────────────────────┐
│  Hypothesis         │  ← Formulate explicit testable hypothesis
│  Generation         │     "If X, then Y should happen within Z days"
└──────────┬──────────┘
           │ Hypotheses
           ▼
┌─────────────────────┐
│  Signal Definition  │  ← Precise mathematical definition
│                     │     observation_date, available_at, horizon
└──────────┬──────────┘
           │ Signals
           ▼
┌─────────────────────┐
│  Historical Test    │  ← Backtest on 5-10 years of data
│                     │     walk-forward, train/test split
└──────────┬──────────┘
           │ Raw results
           ▼
┌─────────────────────┐
│  Robustness Test    │  ← Sensitivity, subperiod, transaction costs
│                     │
└──────────┬──────────┘
           │ Validated signals
           ▼
┌─────────────────────┐
│  Economic           │  ← Why might this work? What's the mechanism?
│  Interpretation     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Company-Level      │  ← Apply validated signal to specific company
│  Research           │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Valuation          │  ← DCF, reverse DCF, sector multiples
│                     │     bear/base/bull scenarios
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Thesis +           │  ← What's the thesis? What breaks it?
│  Thesis Breakers    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Research Report    │  ← Evidence-backed conclusion
│                     │     with full traceability
└─────────────────────┘
```

---

## 5. Point-in-Time Data Model

### 5.1 Timestamp Requirements

Every observation must track:

| Timestamp | Definition | Example |
|-----------|------------|---------|
| `event_date` | When the event occurred | Q3 earnings for period ending Sep 30 |
| `announcement_date` | When the company disclosed it | Nov 2, 2023 (8-K filing) |
| `available_at` | When data was retrievable by our system | Nov 2, 2023 16:35 UTC |
| `effective_date` | When the data takes effect | Nov 2, 2023 (for price data) |
| `retrieved_at` | When we actually fetched it | Nov 2, 2023 17:00 UTC |
| `source` | Data provider | yfinance, EdgarTools, SEC EDGAR |
| `source_url` | Direct link to source | https://sec.gov/... |
| `document_id` | Filing/document identifier | CIK 0001318605-23-000012 |
| `data_revision` | If data was later revised | Original: $1.23 EPS → Restated: $1.18 EPS |

### 5.2 Bias Prevention

| Bias | How It Occurs | Prevention |
|------|---------------|------------|
| **Look-ahead bias** | Using data that wasn't available at the decision point | `available_at` must be ≤ signal observation time |
| **Survivorship bias** | Only testing stocks that still exist | Include delisted stocks, M&A targets, bankruptcies |
| **Stale fundamentals** | Using latest financials when older data was current | Point-in-time financials table with revision tracking |
| **Revised macro data** | GDP/employment data revised after initial release | Track `data_revision` for all macro series |
| **Corporate actions** | Splits, dividends, spin-offs distort price data | Adjusted prices + corporate actions table |
| **Ticker changes** | Company changes ticker (e.g., FB → META) | Ticker history table with valid_from/valid_to |
| **Delisted securities** | Stocks removed from exchanges | Delisted universe table with delist_date, reason |
| **Filing delays** | Companies file late | Track announcement_date vs expected_date |

### 5.3 Universe Management

```sql
-- Track all securities including delisted
CREATE TABLE securities_universe (
    ticker VARCHAR(10),
    name VARCHAR(255),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    first_listed DATE,
    delisted_date DATE,          -- NULL if still active
    delist_reason VARCHAR(100),  -- bankruptcy, merger, acquisition, etc.
    ticker_changes JSONB,        -- [{old_ticker, new_ticker, date}]
    is_active BOOLEAN GENERATED ALWAYS AS (delisted_date IS NULL) STORED,
    PRIMARY KEY (ticker, first_listed)
);
```

---

## 6. Raw Features vs Research Signals

### 6.1 Separation of Concerns

| Layer | Definition | Example |
|-------|------------|---------|
| **Raw Features** | Observable data points, no assumed predictive meaning | revenue_growth = 23%, RSI = 65, insider_buy_value = $2.3M |
| **Research Signals** | Hypothesized predictive relationship, requires validation | "Insider cluster buying > $1M in 30 days predicts +5% excess return over 60 days" |
| **Research Conclusion** | Validated finding with evidence chain | "Signal X works: Sharpe 1.2, after-cost Sharpe 0.9, survives walk-forward" |

### 6.2 Raw Features (No Predictive Assumption)

**Fundamental Features:**
- revenue_growth_yoy, revenue_growth_qoq
- gross_margin, operating_margin, net_margin
- fcf_margin, fcf_yield
- debt_equity, current_ratio, interest_coverage
- roe, roa, roic
- inventory_growth vs revenue_growth divergence
- capex_intensity, capex_growth
- earnings_revisions (up/down count and magnitude)
- guidance_changes
- segment_revenue_mix

**Technical Features:**
- momentum_1m, momentum_3m, momentum_6m, momentum_12m
- volatility_20d, volatility_60d
- rsi_14, macd_signal, bollinger_position
- volume_ratio (current vs 20d avg)
- bid_ask_spread
- short_interest_ratio

**Sentiment Features:**
- news_sentiment_score (FinBERT)
- social_mention_volume
- analyst_rating_changes
- insider_transaction_value

**Insider Features (Semantic):**
- open_market_purchase_value
- open_market_sale_value
- option_exercise_value
- grant_value
- tax_sale_value
- distinct_insiders_buying
- distinct_insiders_selling
- insider_concentration (top N holders %)

**Macro Features:**
- fed_funds_rate, rate_change
- yield_curve_slope (10y-2y)
- vix_level, vix_change
- unemployment_rate, unemployment_change
- pmi, pmi_change
- inflation_rate

### 6.3 Research Signal Definition

A signal MUST have:

```yaml
signal:
  id: "insider_cluster_buying_30d"
  name: "Insider Cluster Buying (30-day window)"
  hypothesis: |
    Clustered open-market purchases by multiple insiders
    indicate management confidence that is not yet priced in.
  mathematical_definition: |
    signal = 1 if:
      - transaction_type = 'open_market_purchase'
      - within 30 calendar days
      - distinct_insiders >= 3
      - total_value >= $1,000,000
    else 0
  observation_date: transaction_date
  available_at: filing_date + 1 day  # SEC filing delay
  expected_horizon: 60 trading_days
  universe: "US equities, market_cap > $1B"
  benchmark: "Russell 3000"
  transaction_costs:
    spread: 10 bps
    slippage: 5 bps
    commission: $0  # commission-free brokers
  hypothesis_id: "HYP-2026-001"
```

---

## 7. Hypothesis Engine

### 7.1 Hypothesis Classes

| Class | Example | Data Sources |
|-------|---------|--------------|
| **Earnings revision** | Analyst upgrades predict +3% over 30d | earnings_revisions |
| **Inventory divergence** | Inventory growth > 2x revenue growth → margin pressure | financials |
| **Margin inflection** | Operating margin improving for 3 consecutive quarters | financials |
| **Capex cycle** | Capex spike precedes revenue growth 4-8 quarters later | financials |
| **Insider cluster** | 3+ insiders buying within 30 days | Form 4 |
| **Valuation dislocation** | Price/FCF < sector median + improving fundamentals | prices + financials |
| **Sentiment shift** | News sentiment shift > 20 points in 7 days | news |
| **Volume-price divergence** | Price rising on declining volume → potential reversal | prices |
| **Guidance change** | Company raises guidance > 10% → re-rating | 8-K, earnings |
| **Footnote changes** | Significant changes in risk factors or accounting policies | 10-K, 10-Q |

### 7.2 Hypothesis Lifecycle

```
DISCOVERY
  │  Anomaly detected via screening
  │  OR manual hypothesis entry
  │  OR AI-generated hypothesis
  ▼
FORMULATION
  │  Explicit IF-THEN statement
  │  Precise variable definitions
  │  Time horizon specified
  ▼
DEFINITION
  │  Mathematical signal construction
  │  Observation date vs available date
  │  Universe and benchmark specified
  ▼
HISTORICAL TEST
  │  Backtest on 5-10 years
  │  Walk-forward validation
  │  Transaction cost deduction
  ▼
ROBUSTNESS
  │  Parameter sensitivity
  │  Subperiod analysis
  │  Sector breakdown
  │  Market regime analysis
  ▼
INTERPRETATION
  │  Economic mechanism identified
  │  Alternative explanations considered
  │  Thesis breakers defined
  ▼
RESEARCH GATE
  │  Pass → Production signal
  │  Fail → Store as rejected hypothesis
  ▼
REPORT
    Evidence-backed research report
    with full traceability
```

### 7.3 Hypothesis Database

```sql
CREATE TABLE hypotheses (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    hypothesis_class VARCHAR(100),
    mathematical_definition TEXT NOT NULL,
    observation_variable VARCHAR(100),
    expected_horizon_days INT,
    universe VARCHAR(100),
    benchmark VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft',  -- draft, testing, validated, rejected, archived
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    author VARCHAR(100) DEFAULT 'system'
);

CREATE TABLE hypothesis_variables (
    id UUID PRIMARY KEY,
    hypothesis_id UUID REFERENCES hypotheses(id),
    variable_name VARCHAR(100),
    source_table VARCHAR(100),
    source_column VARCHAR(100),
    transformation TEXT,  -- SQL or Python expression
    is_derived BOOLEAN DEFAULT FALSE,
    derivation_logic TEXT
);
```

---

## 8. Backtesting Engine

### 8.1 Required Metrics

| Category | Metric | Definition |
|----------|--------|------------|
| **Returns** | CAGR | Compound annual growth rate |
| | Total Return | Buy-and-hold total return |
| | Annualized Return | Geometric mean of annual returns |
| **Risk** | Annualized Volatility | Std dev of returns × √252 |
| | Maximum Drawdown | Largest peak-to-trough decline |
| | Downside Volatility | Std dev of negative returns only |
| **Risk-Adjusted** | Sharpe Ratio | (Return - Rf) / Volatility |
| | Sortino Ratio | (Return - Rf) / Downside Volatility |
| | Calmar Ratio | CAGR / Max Drawdown |
| **Trading** | Win Rate | % of trades with positive return |
| | Hit Rate by Horizon | % of signals with positive return at each horizon |
| | Average Win / Average Loss | Ratio of average winning trade to average losing trade |
| | Turnover | Annual portfolio turnover |
| | Average Excess Return | Mean return minus benchmark return |
| | Factor-Adjusted Return | Return after controlling for market, size, value, momentum factors |
| **Costs** | Pre-Cost Sharpe | Sharpe before transaction costs |
| | Post-Cost Sharpe | Sharpe after transaction costs |
| | Cost Drag | Difference between pre-cost and post-cost returns |

### 8.2 Testing Methodology

#### Walk-Forward Validation

```
Full Dataset: 2014-01-01 to 2026-09-01

Iteration 1:
  Train: 2014-01-01 to 2019-01-01 (5 years)
  Test:  2019-01-01 to 2020-01-01 (1 year)

Iteration 2:
  Train: 2014-01-01 to 2020-01-01 (6 years)
  Test:  2020-01-01 to 2021-01-01 (1 year)

... continue rolling forward ...

Iteration N:
  Train: 2014-01-01 to 2025-01-01 (11 years)
  Test:  2025-01-01 to 2026-09-01 (1.7 years)

Final Result: Concatenated out-of-sample returns
```

#### Transaction Cost Assumptions

| Component | Conservative | Aggressive | Notes |
|-----------|-------------|------------|-------|
| Spread | 10 bps | 5 bps | Large-cap US equities |
| Slippage | 10 bps | 5 bps | Market order assumption |
| Commission | $0 | $0 | Commission-free brokers |
| Market Impact | 5 bps | 0 bps | For positions < 1% of ADV |
| **Total per trade** | **25 bps** | **10 bps** | Round-trip = 2× |

#### Robustness Tests

| Test | Purpose |
|------|---------|
| **Parameter sensitivity** | Vary signal thresholds ±20%, check if results hold |
| **Subperiod analysis** | Test on 2014-2017, 2017-2020, 2020-2023, 2023-2026 separately |
| **Sector breakdown** | Does signal work in all sectors or only specific ones? |
| **Market regime** | Bull market vs bear market vs sideways vs high-vol vs low-vol |
| **Size quintile** | Does signal work in large-cap, mid-cap, small-cap separately? |
| **Out-of-sample** | Hold out last 2 years, never use in training |
| **Bootstrap** | Random resampling to estimate confidence intervals |
| **Minimum trades** | Require > 100 trades for statistical significance |

### 8.3 Backtesting Database

```sql
CREATE TABLE backtest_runs (
    id UUID PRIMARY KEY,
    hypothesis_id UUID REFERENCES hypotheses(id),
    signal_definition JSONB NOT NULL,
    run_config JSONB NOT NULL,  -- train/test dates, costs, universe
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE backtest_results (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES backtest_runs(id),
    metric_name VARCHAR(100),
    metric_value DECIMAL(15,6),
    benchmark_value DECIMAL(15,6),
    period_start DATE,
    period_end DATE,
    subset VARCHAR(100),  -- 'full', 'train', 'test', 'sector_tech', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE backtest_trades (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES backtest_runs(id),
    ticker VARCHAR(10),
    entry_date DATE,
    exit_date DATE,
    entry_price DECIMAL(10,2),
    exit_price DECIMAL(10,2),
    return_pct DECIMAL(8,4),
    excess_return_pct DECIMAL(8,4),
    holding_period_days INT,
    signal_strength DECIMAL(5,2),
    sector VARCHAR(100),
    market_cap_bucket VARCHAR(20)
);
```

---

## 9. Research Gate

### 9.1 Gate Definition

A signal CANNOT become a production signal simply because historical performance looks good.

```
Signal discovered
    │
    ├─→ Economically explainable? ──── NO ──→ REJECT (store as rejected)
    │
    ├─→ No obvious data leakage? ──── NO ──→ REJECT
    │
    ├─→ Survives out-of-sample test? ── NO ──→ REJECT
    │
    ├─→ Robust to reasonable parameter changes? ── NO ──→ REJECT
    │
    ├─→ Survives transaction-cost assumptions? ── NO ──→ REJECT
    │
    ├─→ Not driven by tiny number of observations? ── NO ──→ REJECT
    │
    ├─→ Independently reproducible? ── NO ──→ REJECT
    │
    ├─→ Documented limitations? ── NO ──→ REJECT
    │
    └─→ ALL PASS ──→ PRODUCTION SIGNAL
                    (with full documentation)
```

### 9.2 Gate Criteria Detail

| # | Criterion | Test | Threshold |
|---|-----------|------|-----------|
| 1 | **Economically explainable** | Can we articulate WHY this might work? | Must have a plausible mechanism |
| 2 | **No data leakage** | Point-in-time check | available_at ≤ observation_date for all data |
| 3 | **Out-of-sample test** | Walk-forward or holdout | Post-cost Sharpe > 0.5 in out-of-sample period |
| 4 | **Parameter robustness** | Vary thresholds ±20% | Sharpe degrades < 30% |
| 5 | **Transaction costs** | Apply conservative cost assumptions | Post-cost return > benchmark return |
| 6 | **Observation count** | Minimum number of independent observations | > 100 trades OR > 5 years of data |
| 7 | **Reproducibility** | Re-run on different time period or data source | Results directionally consistent |
| 8 | **Documented limitations** | Explicit list of known weaknesses | At least 3 limitations documented |

### 9.3 Rejected Hypotheses

Rejected hypotheses ARE valuable research artifacts. Store:

```sql
CREATE TABLE rejected_hypotheses (
    id UUID PRIMARY KEY,
    hypothesis_id UUID REFERENCES hypotheses(id),
    rejection_reason TEXT NOT NULL,
    gate_criterion_failed VARCHAR(100),
    evidence JSONB,  -- detailed test results
    rejected_at TIMESTAMP DEFAULT NOW(),
    reviewer VARCHAR(100) DEFAULT 'system',
    notes TEXT
);
```

**Rationale:** Knowing what DOESN'T work prevents wasted effort and informs future research.

---

## 10. Semantic Insider Analysis

### 10.1 Transaction Type Classification

Do NOT treat all Form 4 activity as equivalent.

| Code | Type | Predictive Value | Treatment |
|------|------|-----------------|-----------|
| **P** | Open-market purchase | HIGH | Strongest signal — insider using own money |
| **S** | Open-market sale | MEDIUM | Context-dependent (diversification vs conviction loss) |
| **A** | Grant/award | LOW | Compensation, not conviction signal |
| **M** | Option exercise | LOW-MEDIUM | Tax implications obscure intent |
| **G** | Gift | NONE | Not a market signal |
| **T** | Tax-related sale | NONE | Required by law, not discretionary |
| **W** | Will/inheritance | NONE | Estate planning |
| **C** | Conversion | LOW | Usually automatic |
| **Other** | Other coded | VARIES | Examine case-by-case |

### 10.2 Insider Signal Metrics

For open-market purchases only (Code P):

| Metric | Definition |
|--------|------------|
| `dollar_value` | Total $ value of purchases |
| `shares_acquired` | Total shares purchased |
| `distinct_insiders` | Number of different insiders |
| `transaction_count` | Number of separate transactions |
| `clustering_window` | Days between first and last purchase in cluster |
| `insider_roles` | List of roles (CEO, CFO, Director, etc.) |
| `ceo_cfo_involved` | Boolean: is C-suite participating? |
| `percentage_of_holdings` | % of insider's total holdings purchased (if available) |
| `historical_pattern` | Is this insider a repeat buyer? What's their track record? |
| `filing_delay` | Days between transaction and filing |

### 10.3 Insider Scoring (Empirical)

Instead of arbitrary weights, measure:

```sql
-- For each insider cluster, compute historical base rate
WITH insider_clusters AS (
    SELECT
        ticker,
        DATE_TRUNC('month', transaction_date) AS cluster_month,
        COUNT(DISTINCT insider) AS distinct_insiders,
        SUM(CASE WHEN code = 'P' THEN value ELSE 0 END) AS purchase_value,
        SUM(CASE WHEN code IN ('S','M','G') THEN value ELSE 0 END) AS sale_value
    FROM insider_trades
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY ticker, cluster_month
    HAVING COUNT(DISTINCT insider) >= 3
)
SELECT
    ic.ticker,
    ic.distinct_insiders,
    ic.purchase_value,
    -- What happened to stock price in next 60 days?
    AVG(dp.close / dp.open - 1) AS avg_forward_return_60d
FROM insider_clusters ic
JOIN daily_prices dp ON ic.ticker = dp.ticker
    AND dp.date BETWEEN ic.cluster_month + 1 AND ic.cluster_month + 61
GROUP BY ic.ticker, ic.distinct_insiders, ic.purchase_value;
```

---

## 11. AI Role Definition

### 11.1 AI May

| Task | How |
|------|-----|
| **Hypothesis generation** | Analyze market patterns, suggest testable hypotheses |
| **Document extraction** | Parse SEC filings, extract key metrics from 10-K/10-Q |
| **Evidence synthesis** | Summarize multiple sources into coherent narrative |
| **Contradiction detection** | Identify conflicting claims across sources |
| **Qualitative interpretation** | Explain what financial ratios mean in context |
| **Scenario construction** | Build bull/base/bear cases for valuation |
| **Research report drafting** | Generate draft report with evidence citations |
| **Anomaly flagging** | Identify unusual patterns for human review |

### 11.2 AI Must NOT

| Prohibition | Reason |
|-------------|--------|
| **Invent data** | AI hallucination creates false evidence |
| **Invent citations** | Fake sources undermine research integrity |
| **Override deterministic calculations** | Backtest results are mathematical facts |
| **Change historical data** | Data integrity is non-negotiable |
| **Assign arbitrary confidence** | "78% confidence" is manufactured precision |
| **Convert weak evidence to strong conclusion** | AI must not overstate uncertain findings |
| **Make final investment decisions** | AI recommends; human decides |

### 11.3 AI Prompt Template (Revised)

```
You are a research assistant, NOT a decision-maker.

CONTEXT:
You are analyzing {ticker} based on the following EVIDENCE.

DO NOT invent data or citations. Only reference provided evidence.

EVIDENCE PROVIDED:
{evidence_chain}

TASK:
1. Summarize the key findings from the evidence
2. Identify any contradictions in the evidence
3. List alternative explanations for the observed patterns
4. Draft a preliminary research conclusion
5. Explicitly state what evidence is MISSING

CONSTRAINTS:
- Every factual claim must reference a source from the evidence chain
- Use hedging language for uncertain conclusions ("the data suggests..." not "the data proves...")
- If evidence is insufficient, say so explicitly
- Do not assign numerical confidence percentages
- Flag any claims you cannot verify from provided evidence
```

---

## 12. Research Ledger

### 12.1 Claim Structure

Every important claim in a research report must be traceable:

```yaml
claim:
  id: "CLM-2026-00123"
  claim: "Tesla's operating margin declined from 17.2% to 9.2% over 4 quarters"
  source: "SEC EDGAR"
  source_type: "filing"
  publication_date: "2026-01-31"
  available_at: "2026-01-31T16:35:00Z"
  document_id: "000-320523-26-000012"
  location: "10-K, Item 8, Financial Statements, Income Statement"
  raw_evidence: "Operating income: Q1 2025 $2.5B, Q4 2025 $1.4B"
  calculation: "Operating margin = Operating income / Revenue"
  derived_value: "9.2% (Q4 2025)"
  confidence: "high"  # high/medium/low based on source reliability
  contradicting_evidence: null
```

### 12.2 Evidence Chain Visualization

```
CLAIM: "Tesla's gross margin is declining"
  │
  ├── SOURCE 1: 10-Q filing (Q3 2025)
  │   └── Gross margin: 18.7% (page 45)
  │
  ├── SOURCE 2: 10-Q filing (Q4 2025)
  │   └── Gross margin: 16.3% (page 42)
  │
  ├── SOURCE 3: Earnings call transcript
  │   └── CEO: "margin headwinds from pricing competition"
  │
  └── CALCULATION: 18.7% → 16.3% = -2.4pp decline
      └── CONFIDENCE: HIGH (primary sources, direct calculation)
```

### 12.3 Ledger Database

```sql
CREATE TABLE research_claims (
    id UUID PRIMARY KEY,
    report_id UUID,
    claim_text TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    source_type VARCHAR(50),  -- filing, transcript, news, calculation
    publication_date DATE,
    available_at TIMESTAMP,
    document_id VARCHAR(255),
    location TEXT,  -- page number, section, line
    raw_evidence TEXT,
    calculation TEXT,
    derived_value TEXT,
    confidence VARCHAR(10),  -- high, medium, low
    contradicting_evidence JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 12.4 User Query Interface

Eventually, the UI must support:

> "Show me why StockScope believes Tesla's margin is declining."

This traces back to:
1. The claim
2. The source document
3. The specific location in the document
4. The calculation performed
5. Any contradicting evidence

---

## 13. Valuation Engine

### 13.1 Valuation Methods

| Method | When to Use | Output |
|--------|-------------|--------|
| **DCF** | Cash-flow-generative businesses | Intrinsic value per share |
| **Reverse DCF** | Any stock — "what growth is implied?" | Implied growth rate |
| **P/E relative** | When comparing to peers | Relative value vs sector |
| **EV/EBITDA** | Capital-structure-neutral comparison | Enterprise value range |
| **EV/Sales** | Pre-profit or cyclical businesses | Revenue-based valuation |
| **FCF Yield** | Income-focused analysis | Yield vs risk-free rate |
| **Sector-specific** | Banks (P/B), REITs (FFO/AFFO), etc. | Sector-appropriate metric |

### 13.2 DCF Model

```
Inputs:
  ├── Revenue growth (forecast 5 years)
  ├── Operating margin (forecast)
  ├── Tax rate
  ├── Capex as % of revenue
  ├── Working capital change
  ├── WACC (weighted average cost of capital)
  └── Terminal growth rate

Outputs:
  ├── Fair value per share (base case)
  ├── Bear case value (-20% revenue, -5pp margin)
  ├── Bull case value (+20% revenue, +5pp margin)
  ├── Key assumptions (sensitivity table)
  ├── Implied growth rate at current price
  └── Margin of safety (current price vs fair value)
```

### 13.3 Valuation Database

```sql
CREATE TABLE valuations (
    id UUID PRIMARY KEY,
    ticker VARCHAR(10),
    method VARCHAR(50),
    valuation_date DATE,
    inputs JSONB,  -- all assumptions
    bear_value DECIMAL(10,2),
    base_value DECIMAL(10,2),
    bull_value DECIMAL(10,2),
    current_price DECIMAL(10,2),
    margin_of_safety DECIMAL(5,2),  -- (fair_value - current_price) / fair_value
    sensitivity JSONB,  -- sensitivity table
    key_drivers JSONB,  -- which assumptions move value most
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 13.4 Reverse DCF

Given current price, compute what the market is implying:

```
Current price: $245
Reverse DCF result:
  → Market implies 25% revenue CAGR for next 5 years
  → Market implies operating margin stabilizes at 15%
  → Market implies terminal growth of 3%

Question: Is 25% CAGR achievable given:
  - Industry growth rate: 12%
  - Market share trajectory: stable
  - Competitive dynamics: intensifying
```

---

## 14. Thesis + Thesis Breaker Framework

### 14.1 Required Report Sections

Every company research report MUST contain:

#### Thesis
> Why the opportunity exists.

Example: "Tesla is trading at a discount to its autonomous driving optionality because the market is valuing it as a car company."

#### Market Misunderstanding
> What the market may be underestimating or misunderstanding.

Example: "The market is discounting Tesla's FSD progress, treating it as a speculative feature rather than a potential revenue stream."

#### Catalyst
> What could cause repricing.

Example: "Regulatory approval for L4 autonomous driving, or FSD subscription revenue exceeding $1B annualized."

#### Valuation
> What the business may be worth under multiple scenarios.

```
Current price: $245
Bear case: $160 (autonomous driving fails, auto margins compress)
Base case: $280 (current trajectory continues)
Bull case: $400 (autonomous driving + robotaxi deployment)
```

#### Risks
> What could go wrong.

- Competition from Waymo, Cruise, Chinese AV companies
- Regulatory delays or prohibition
- Technology delays (full self-driving remains unsolved)
- Margin compression from pricing competition

#### Thesis Breakers
> Specific observable conditions that would invalidate the thesis.

```yaml
thesis_breakers:
  - condition: "Gross margin remains below 15% for two consecutive quarters"
    monitoring_variables: [gross_margin, asp, utilization]
    action: "REVIEW thesis — pricing power may be permanently impaired"

  - condition: "FSD subscription revenue fails to reach $100M annualized by Q4 2026"
    monitoring_variables: [fsd_subscriptions, fsd_revenue, take_rate]
    action: "REDUCE position — autonomous optionality thesis weakening"

  - condition: "Insider selling exceeds $500M in any 90-day window"
    monitoring_variables: [insider_sales, insider_holdings_pct]
    action: "EXIT — management does not believe in the thesis"
```

### 14.2 Thesis Breaker Monitoring

```sql
CREATE TABLE thesis_breakers (
    id UUID PRIMARY KEY,
    thesis_id UUID,
    condition_description TEXT NOT NULL,
    monitoring_variables JSONB NOT NULL,
    threshold_value DECIMAL(10,2),
    threshold_operator VARCHAR(10),  -- above, below, equals
    lookback_periods INT,
    action VARCHAR(50),  -- review, reduce, exit
    is_triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 15. Data Source Hierarchy

### 15.1 Tier System

| Tier | Source Type | Examples | Override Rule |
|------|-------------|----------|---------------|
| **Tier 1** | Official, primary sources | SEC EDGAR, company investor relations, official exchanges, central banks, government agencies, official regulatory databases | Tier 1 ALWAYS overrides lower tiers |
| **Tier 2** | High-quality providers | Bloomberg, Reuters, established financial data providers, reputable news sources | Can override Tier 3 |
| **Tier 3** | Aggregators, social, secondary | Reddit, StockTwits, social media, secondary summaries, blog posts | NEVER overrides Tier 1 |

### 15.2 Source Priority Rules

```
IF Tier 1 and Tier 2 conflict:
  → Use Tier 1
  → Flag discrepancy in research ledger
  → Investigate why they differ

IF Tier 2 and Tier 3 conflict:
  → Use Tier 2
  → Note Tier 3 as "market sentiment" only

IF Tier 1 and Tier 3 conflict:
  → Use Tier 1
  → Tier 3 is informational only (what people believe, not what is true)
```

### 15.3 Timestamp Requirements

ALL sources must have:
- `publication_date` — when the source published
- `available_at` — when we could have accessed it
- `source_url` — direct link for verification
- `retrieved_at` — when we actually fetched it

### 15.4 MVP Data Sources (US Equities Only)

| Category | Source | Tier | API Key |
|----------|--------|------|---------|
| **Price data** | yfinance | Tier 2 | No |
| **SEC filings** | EdgarTools (EDGAR) | Tier 1 | No (SEC rate limit: 10 req/sec) |
| **Financial statements** | yfinance + EdgarTools | Tier 1+2 | No |
| **Insider trades** | EdgarTools (Form 4) | Tier 1 | No |
| **Macro data** | fredapi (FRED) | Tier 1 | Free key required |
| **News** | finews (RSS) | Tier 2 | No |
| **Sentiment** | FinBERT (local) | N/A | No |
| **Analyst ratings** | yfinance | Tier 2 | No |

---

## 16. Revised Database Schema

### 16.1 Core Tables

```sql
-- ============================================
-- UNIVERSE
-- ============================================

CREATE TABLE securities_universe (
    ticker VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    first_listed DATE,
    delisted_date DATE,
    delist_reason VARCHAR(100),
    ticker_history JSONB,  -- [{old_ticker, new_ticker, date}]
    is_active BOOLEAN GENERATED ALWAYS AS (delisted_date IS NULL) STORED,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- POINT-IN-TIME PRICES
-- ============================================

CREATE TABLE daily_prices (
    ticker VARCHAR(10) REFERENCES securities_universe(ticker),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    adj_close DECIMAL(10,2),
    volume BIGINT,
    source VARCHAR(50) DEFAULT 'yfinance',
    retrieved_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (ticker, date)
);

-- ============================================
-- POINT-IN-TIME FINANCIALS
-- ============================================

CREATE TABLE financials (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES securities_universe(ticker),
    period_end DATE NOT NULL,
    filing_date DATE NOT NULL,           -- when filed with SEC
    available_at TIMESTAMP NOT NULL,     -- when we fetched it
    revenue DECIMAL(15,2),
    cost_of_revenue DECIMAL(15,2),
    gross_profit DECIMAL(15,2),
    operating_income DECIMAL(15,2),
    net_income DECIMAL(15,2),
    eps_diluted DECIMAL(10,2),
    total_assets DECIMAL(15,2),
    total_liabilities DECIMAL(15,2),
    shareholders_equity DECIMAL(15,2),
    cash_and_equivalents DECIMAL(15,2),
    total_debt DECIMAL(15,2),
    operating_cash_flow DECIMAL(15,2),
    free_cash_flow DECIMAL(15,2),
    capex DECIMAL(15,2),
    shares_outstanding BIGINT,
    -- Derived ratios (computed, not stored raw)
    pe_ratio DECIMAL(10,2),
    pb_ratio DECIMAL(10,2),
    ps_ratio DECIMAL(10,2),
    debt_equity DECIMAL(10,2),
    current_ratio DECIMAL(10,2),
    roe DECIMAL(10,4),
    roa DECIMAL(10,4),
    gross_margin DECIMAL(10,4),
    operating_margin DECIMAL(10,4),
    net_margin DECIMAL(10,4),
    fcf_margin DECIMAL(10,4),
    source VARCHAR(50),
    data_revision INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, period_end, data_revision)
);

-- ============================================
-- POINT-IN-TIME INSIDER TRADES (SEMANTIC)
-- ============================================

CREATE TABLE insider_trades (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES securities_universe(ticker),
    insider_name VARCHAR(255),
    insider_role VARCHAR(100),
    transaction_date DATE NOT NULL,
    filing_date DATE NOT NULL,
    available_at TIMESTAMP NOT NULL,
    code VARCHAR(5) NOT NULL,  -- P, S, A, M, G, T, W, C
    transaction_type VARCHAR(50),  -- open_market_purchase, grant, option_exercise, etc.
    shares DECIMAL(12,2),
    price_per_share DECIMAL(10,2),
    total_value DECIMAL(15,2),
    shares_owned_after DECIMAL(12,2),
    ownership_pct DECIMAL(8,4),
    is_direct BOOLEAN,
    is_10b51_plan BOOLEAN,
    source VARCHAR(50) DEFAULT 'SEC_EDGAR',
    document_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_insider_ticker_date ON insider_trades(ticker, transaction_date);
CREATE INDEX idx_insider_code ON insider_trades(code);
CREATE INDEX idx_insider_available ON insider_trades(available_at);

-- ============================================
-- NEWS & SENTIMENT
-- ============================================

CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10),
    source VARCHAR(100),
    title TEXT,
    summary TEXT,
    url TEXT,
    sentiment_score DECIMAL(5,4),  -- -1 to 1
    sentiment_model VARCHAR(50),  -- finbert, vader
    published_at TIMESTAMP,
    available_at TIMESTAMP,
    retrieved_at TIMESTAMP DEFAULT NOW(),
    document_id VARCHAR(255),
    source_tier INT DEFAULT 2  -- 1, 2, or 3
);

-- ============================================
-- MACRO DATA (POINT-IN-TIME)
-- ============================================

CREATE TABLE macro_observations (
    id SERIAL PRIMARY KEY,
    series_id VARCHAR(50),  -- FRED series ID
    observation_date DATE,
    value DECIMAL(15,4),
    revision_number INT DEFAULT 0,
    vintage_date DATE,  -- which vintage of the data
    available_at TIMESTAMP,
    source VARCHAR(50) DEFAULT 'FRED',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- HYPOTHESES
-- ============================================

CREATE TABLE hypotheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    hypothesis_class VARCHAR(100),
    mathematical_definition TEXT NOT NULL,
    observation_variable VARCHAR(100),
    expected_horizon_days INT,
    universe VARCHAR(100) DEFAULT 'US equities',
    benchmark VARCHAR(100) DEFAULT 'Russell 3000',
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- BACKTEST RESULTS
-- ============================================

CREATE TABLE backtest_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    signal_definition JSONB NOT NULL,
    run_config JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE backtest_metrics (
    id SERIAL PRIMARY KEY,
    run_id UUID REFERENCES backtest_runs(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6),
    benchmark_value DECIMAL(15,6),
    period VARCHAR(50),  -- 'full', 'train', 'test', 'oos'
    subset VARCHAR(100),  -- 'all', 'sector_tech', 'cap_large', etc.
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE backtest_trades (
    id SERIAL PRIMARY KEY,
    run_id UUID REFERENCES backtest_runs(id),
    ticker VARCHAR(10),
    entry_date DATE,
    exit_date DATE,
    entry_price DECIMAL(10,2),
    exit_price DECIMAL(10,2),
    return_pct DECIMAL(8,4),
    excess_return_pct DECIMAL(8,4),
    holding_days INT,
    sector VARCHAR(100),
    market_cap_bucket VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- RESEARCH LEDGER
-- ============================================

CREATE TABLE research_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID,
    claim_text TEXT NOT NULL,
    source VARCHAR(255) NOT NULL,
    source_type VARCHAR(50),
    source_tier INT,
    publication_date DATE,
    available_at TIMESTAMP,
    document_id VARCHAR(255),
    location TEXT,
    raw_evidence TEXT,
    calculation TEXT,
    derived_value TEXT,
    confidence VARCHAR(10),
    contradicting_evidence JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- REJECTED HYPOTHESES
-- ============================================

CREATE TABLE rejected_hypotheses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hypothesis_id UUID REFERENCES hypotheses(id),
    rejection_reason TEXT NOT NULL,
    gate_criterion VARCHAR(100),
    test_results JSONB,
    rejected_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- ============================================
-- VALUATIONS
-- ============================================

CREATE TABLE valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10),
    method VARCHAR(50),
    valuation_date DATE,
    inputs JSONB,
    bear_value DECIMAL(10,2),
    base_value DECIMAL(10,2),
    bull_value DECIMAL(10,2),
    current_price DECIMAL(10,2),
    margin_of_safety DECIMAL(5,4),
    sensitivity JSONB,
    key_drivers JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- THESIS BREAKERS
-- ============================================

CREATE TABLE theses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10),
    thesis_text TEXT NOT NULL,
    market_misunderstanding TEXT,
    catalyst TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE thesis_breakers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thesis_id UUID REFERENCES theses(id),
    condition_description TEXT NOT NULL,
    monitoring_variables JSONB NOT NULL,
    threshold_value DECIMAL(10,2),
    threshold_operator VARCHAR(10),
    action VARCHAR(50),
    is_triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- RESEARCH REPORTS
-- ============================================

CREATE TABLE research_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10),
    title VARCHAR(255),
    thesis_id UUID REFERENCES theses(id),
    hypothesis_ids UUID[],
    valuation_id UUID,
    status VARCHAR(20) DEFAULT 'draft',
    report_text TEXT,
    executive_summary TEXT,
    key_risks TEXT,
    thesis_breakers JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 16.2 Parquet Files (Time-Series Data)

For backtesting performance, store large time-series in Parquet:

```
data/
├── prices/
│   └── {ticker}/
│       └── daily.parquet    # date, open, high, low, close, volume
├── financials/
│   └── {ticker}/
│       └── quarterly.parquet
├── insider/
│   └── {ticker}/
│       └── form4.parquet
├── features/
│   └── {ticker}/
│       └── computed.parquet  # all derived features
└── universe/
    └── active.parquet
    └── delisted.parquet
```

---

## 17. Revised Sprint Plan

### Sprint 0 (Week 0): Research Methodology & Infrastructure

**Goal:** Establish research framework, schema, and benchmark design

**Deliverables:**
- [ ] Research methodology document (this document)
- [ ] PostgreSQL schema created (all tables)
- [ ] Parquet directory structure established
- [ ] Benchmark universe defined (S&P 500 or Russell 3000)
- [ ] Benchmark returns computed and stored
- [ ] Transaction cost assumptions documented
- [ ] Point-in-time data model validated

**Review Gate:** Schema complete, benchmark data loaded, methodology documented

---

### Sprint 1 (Week 1-2): Point-in-Time Data Foundation

**Goal:** Working data pipeline with full point-in-time integrity

**Deliverables:**
- [ ] yfinance adapter (prices, financials, company info)
- [ ] EdgarTools adapter (SEC filings, Form 4 insider trades)
- [ ] fredapi adapter (macro data)
- [ ] finews adapter (news aggregation)
- [ ] Point-in-time timestamps on ALL data
- [ ] Securities universe table (active + delisted)
- [ ] Ticker change tracking
- [ ] Data freshness monitoring
- [ ] Basic data quality checks

**Acceptance Criteria:**
- [ ] Can fetch 10 years of daily prices for any S&P 500 stock
- [ ] Financial statements have filing_date AND available_at
- [ ] Insider trades have transaction_date AND filing_date
- [ ] Delisted stocks are included in universe
- [ ] No future data leaks in historical fetches
- [ ] All data retrievable via Python API

**Review Gate:** Demo fetching TSLA data with full point-in-time metadata

---

### Sprint 2 (Week 3-4): Hypothesis Engine & Backtesting

**Goal:** Can define, test, and validate hypotheses

**Deliverables:**
- [ ] Feature computation engine (raw features → computed features)
- [ ] Hypothesis definition system (YAML → executable)
- [ ] Backtesting engine (walk-forward, train/test split)
- [ ] Transaction cost modeling
- [ ] All backtest metrics implemented
- [ ] Robustness tests (parameter sensitivity, subperiod, sector)
- [ ] Research Gate validator
- [ ] Rejected hypotheses storage

**Acceptance Criteria:**
- [ ] Can define a hypothesis in YAML and run backtest
- [ ] Backtest returns all required metrics (Sharpe, Sortino, drawdown, etc.)
- [ ] Walk-forward validation works (5 iterations minimum)
- [ ] Transaction costs are deducted and reported
- [ ] Parameter sensitivity test runs automatically
- [ ] Research Gate can approve/reject a hypothesis
- [ ] Rejected hypotheses are stored with reasons

**Review Gate:** Demo: define "insider cluster buying" hypothesis → backtest → full results → Research Gate decision

---

### Sprint 3 (Week 5-6): Valuation, Evidence Ledger & Reports

**Goal:** Can value companies and produce evidence-backed research reports

**Deliverables:**
- [ ] DCF model implementation
- [ ] Reverse DCF implementation
- [ ] Relative valuation (P/E, EV/EBITDA, sector multiples)
- [ ] Scenario analysis (bear/base/bull)
- [ ] Sensitivity analysis
- [ ] Evidence ledger (claim → source → calculation)
- [ ] AI-assisted report drafting (with strict constraints)
- [ ] Thesis + thesis breaker framework
- [ ] Thesis breaker monitoring system

**Acceptance Criteria:**
- [ ] DCF produces bear/base/bull values with documented assumptions
- [ ] Reverse DCF shows implied growth at current price
- [ ] Every claim in research report traces to a source
- [ ] AI-generated reports do not invent data or citations
- [ ] Thesis breakers are defined and monitorable
- [ ] Research report is complete with all required sections

**Review Gate:** Demo: full research report for TSLA with evidence chain, valuation, thesis breakers

---

### Sprint 4 (Week 7-8): Dashboard, Monitoring & Polish

**Goal:** Usable research workbench

**Deliverables:**
- [ ] Streamlit dashboard (minimal, research-focused)
- [ ] Hypothesis browser (view, create, test)
- [ ] Backtest results viewer
- [ ] Research report viewer
- [ ] Watchlist with thesis breaker monitoring
- [ ] Telegram alerts for thesis breaker triggers
- [ ] Data quality dashboard
- [ ] Documentation (README, setup guide)
- [ ] Performance optimization

**Acceptance Criteria:**
- [ ] Dashboard loads and shows research workflow
- [ ] Can browse hypotheses and their test results
- [ ] Can view research reports with evidence chain
- [ ] Can create watchlist and monitor thesis breakers
- [ ] Telegram alert fires when thesis breaker triggered
- [ ] Dashboard loads in < 3 seconds
- [ ] README complete with setup instructions

**Review Gate:** Full system demo — discover hypothesis → backtest → valuation → research report → monitor

---

## 18. Cost Analysis (Honest)

### 18.1 API Costs

| Service | Free Tier | Rate Limits | Paid Tier | Notes |
|---------|-----------|-------------|-----------|-------|
| yfinance | Unlimited | No official limit (may get throttled) | N/A | No API key needed |
| EdgarTools (SEC EDGAR) | Unlimited | 10 requests/sec | N/A | Must respect rate limit |
| fredapi (FRED) | Unlimited | 120 requests/min | N/A | Free API key required |
| Gemini API | 1M tokens/day | 15 RPM | $0.075/1K input tokens | Free tier sufficient for MVP |
| Ollama | Unlimited | Hardware limited | N/A | Needs 8GB+ RAM for 7B model |
| Telegram Bot | Unlimited | 30 msgs/sec | N/A | Free bot API |
| finews (RSS) | Unlimited | Varies by source | N/A | No key needed |

### 18.2 Infrastructure Costs

| Component | Cost | Notes |
|-----------|------|-------|
| PostgreSQL | $0 | Self-hosted Docker |
| Parquet files | $0 | Local filesystem |
| Python + libraries | $0 | Open source |
| Streamlit | $0 | Open source |
| Docker Desktop | $0 | Personal use |
| **Total infrastructure** | **$0** | Self-hosted |

### 18.3 Hidden Costs

| Cost | Estimate | Notes |
|------|----------|-------|
| **Electricity** | ~$5-15/month | Running Ollama + PostgreSQL + Docker |
| **Internet** | Already paid | Data fetching requires connectivity |
| **Storage** | ~50GB for 10 years of data | Local disk |
| **Time** | Significant | Research is labor-intensive |
| **Opportunity cost** | Value of time spent | Could be spent on other activities |

### 18.4 Honest Assessment

```
STATED COST: $0

ACTUAL COST:
  - API fees: $0 (free tiers sufficient for MVP)
  - Infrastructure: $0 (self-hosted)
  - Electricity: ~$5-15/month
  - Time: Significant (research + development + maintenance)
  
CAVEATS:
  - Free tier limits may be hit with heavy usage
  - Gemini free tier may change or be discontinued
  - yfinance may throttle aggressive scraping
  - SEC EDGAR has strict rate limits
  - Ollama quality depends on local hardware
```

---

## 19. What NOT to Build Yet

| Feature | Why Not Now | When to Add |
|---------|-------------|-------------|
| **Multi-market support (VN, CN, EU, JP)** | Dilutes depth. US equities have best data infrastructure. | After US market research engine is validated |
| **Redis cache** | Not needed until data volume or access patterns require it. PostgreSQL sufficient. | When query latency becomes a problem |
| **Qdrant vector search** | Useful for semantic news search, but not critical for research engine. | When news search becomes a bottleneck |
| **n8n workflow automation** | Complex orchestration. Python scripts + APScheduler sufficient. | When workflow complexity exceeds what Python can handle |
| **Multiple notification channels** | Telegram is sufficient. Discord/email/Slack are features, not architecture. | When user feedback requests them |
| **7 dashboard pages** | Research report viewer is the only critical UI. Others are features. | After research engine is validated |
| **Real-time WebSocket** | Research is not real-time. Batch processing is appropriate. | If monitoring requires faster-than-5-min updates |
| **Crypto support** | Different asset class, different data model, different analysis. | As a separate research domain |
| **React frontend** | Streamlit is sufficient for MVP. React is premature optimization. | When Streamlit limitations block needed features |
| **Multiple MCP servers** | market-data-mcp + dbhub sufficient. | When specific MCP capability is needed |
| **Screener** | Not needed until research engine can discover opportunities. | After hypothesis engine works |

---

## 20. Changes from v1 → v2

### 20.1 Conceptual Changes

| Aspect | v1 (Original) | v2 (Revised) | Rationale |
|--------|---------------|--------------|-----------|
| **Primary purpose** | Score stocks 0-100 | Discover and validate hypotheses | Scores assume predictive validity without evidence |
| **Output format** | BUY/SELL verdict + confidence | Research report with evidence chain | AI cannot assign confidence; evidence must be traceable |
| **Data model** | Snapshot-based | Point-in-time with availability tracking | Backtesting requires preventing look-ahead bias |
| **Analysis approach** | Weighted scoring (arbitrary weights) | Hypothesis → backtest → validate | No evidence that weighted scoring predicts returns |
| **AI role** | Source of truth, assigns confidence | Hypothesis generation + evidence synthesis | AI should not manufacture precision |
| **Backtesting** | Not included | Core system component | No way to validate signals without historical testing |
| **Valuation** | Not included | DCF + scenario analysis | Essential for determining fair value |
| **Insider analysis** | Binary BUY/SELL | Semantic transaction classification | Not all Form 4 activity is equivalent |

### 20.2 Architecture Changes

| Component | v1 | v2 | Rationale |
|-----------|----|----|-----------|
| **Storage** | PostgreSQL + Redis + Qdrant | PostgreSQL + Parquet | Simplify. Redis/Qdrant not needed for MVP |
| **Infrastructure** | Docker Compose (4 services) | PostgreSQL Docker (1 service) | Optimize for research throughput, not component count |
| **Markets** | Global (US, VN, CN, EU, JP, crypto) | US equities only | Depth over breadth. US has best data infrastructure |
| **Dashboard** | 7 pages, full polish | Research workbench (minimal) | Research engine first, UI second |
| **Scheduling** | APScheduler + n8n | APScheduler only | n8n is overkill for MVP |
| **MCP servers** | 3 (market-data, dbhub, brave-search) | 0 (direct API calls) | Simplify. MCP adds complexity without clear benefit for research |
| **Alerts** | Price, technical, sentiment, insider, AI | Thesis breaker triggers only | Focus on what matters for research |

### 20.3 Sprint Changes

| Sprint | v1 | v2 | Rationale |
|--------|----|----|-----------|
| **Sprint 0** | N/A | Research methodology & schema | Must establish framework before building |
| **Sprint 1** | Data Foundation | Point-in-Time Data Foundation | Added point-in-time requirements |
| **Sprint 2** | Analysis Engine | Hypothesis Engine & Backtesting | Replaced scoring with validation |
| **Sprint 3** | Dashboard & Alerts | Valuation, Evidence Ledger & Reports | Added valuation + evidence chain |
| **Sprint 4** | Enhancement & Polish | Dashboard, Monitoring & Polish | Dashboard comes after research engine |

### 20.4 Database Changes

| Table | v1 | v2 | Change |
|-------|----|----|--------|
| `stocks` | Basic info | `securities_universe` | Added delisting, ticker changes |
| `daily_prices` | Basic OHLCV | Added `available_at`, `source` | Point-in-time tracking |
| `financials` | Basic ratios | Added `filing_date`, `available_at`, `data_revision` | Point-in-time + revision tracking |
| `insider_trades` | Binary BUY/SELL | Added `code`, `transaction_type`, semantic classification | Not all transactions are equivalent |
| `news_articles` | Basic | Added `available_at`, `source_tier` | Point-in-time + source hierarchy |
| `analysis_results` | 0-100 scores | REMOVED | Replaced by backtest + research reports |
| `alerts` | Multiple alert types | REMOVED | Replaced by thesis breaker monitoring |
| `hypotheses` | N/A | NEW | Hypothesis definition and lifecycle |
| `backtest_runs` | N/A | NEW | Backtest execution tracking |
| `backtest_metrics` | N/A | NEW | Backtest results |
| `backtest_trades` | N/A | NEW | Individual trade analysis |
| `research_claims` | N/A | NEW | Evidence ledger |
| `rejected_hypotheses` | N/A | NEW | Failed hypothesis storage |
| `valuations` | N/A | NEW | DCF, relative valuation |
| `theses` | N/A | NEW | Investment thesis |
| `thesis_breakers` | N/A | NEW | Thesis invalidation monitoring |
| `research_reports` | N/A | NEW | Final research output |
| `macro_observations` | N/A | NEW | Point-in-time macro data |

### 20.5 What's Removed from v1

| Removed | Why |
|---------|-----|
| **5-Layer Scoring (0-100)** | Arbitrary weights with no empirical validation |
| **BUY/SELL/HOLD verdict** | AI cannot assign confidence; replaced by evidence-backed report |
| **Redis cache** | Premature optimization for MVP |
| **Qdrant vector search** | Not critical for research engine |
| **n8n workflow** | Overkill for MVP |
| **7 dashboard pages** | Replaced by minimal research workbench |
| **Multiple notification channels** | Telegram sufficient for MVP |
| **Global market support** | US equities only for depth |
| **Real-time WebSocket** | Research is batch, not real-time |
| **MCP servers** | Direct API calls simpler for MVP |
| **Screener** | Premature until research engine works |
| **Competitor comparison** | Feature, not architecture |

---

## Appendix A: Research Methodology References

- Harvey, Campbell R., et al. "…and the Cross-Section of Expected Returns." (2016) — multiple testing problem
- McLean, R. David, and Jeffrey Pontiff. "Does Academic Research Destroy Stock Return Predictability?" (2016)
- Hou, Kewei, Xue, Chen, and Lu Zhang. "Replicating Anomalies." (2020) — many anomalies fail to replicate
- Harvey, Campbell R. "Presidential Address: The Scientific Outlook in Financial Economics." (2017)
- Jensen, Michael C., and Kevin J. Murphy. "Performance Pay and Top-Management Incentives." (1990) — insider incentives

## Appendix B: Transaction Cost Sensitivity Template

```yaml
transaction_cost_scenarios:
  optimistic:
    spread_bps: 5
    slippage_bps: 0
    commission: 0
    market_impact_bps: 0
    label: "Commission-free, tight spread"
  
  realistic:
    spread_bps: 10
    slippage_bps: 5
    commission: 0
    market_impact_bps: 5
    label: "Typical retail execution"
  
  conservative:
    spread_bps: 15
    slippage_bps: 10
    commission: 0
    market_impact_bps: 10
    label: "Worst-case retail execution"
  
  institutional:
    spread_bps: 10
    slippage_bps: 15
    commission: 0
    market_impact_bps: 25
    label: "Large position, institutional"
```

---

*Document generated: 2026-09-19*  
*Baseline: v1 (2026-09-19-stockscope-masterplan.md)*  
*Status: Research Design — DO NOT IMPLEMENT until approved*  
*Author: StockScope Team*
