# StockScope - Masterplan

> AI-Powered Stock Analysis System | 100% Free | Self-Hosted

**Version:** 1.0  
**Date:** 2026-09-19  
**Status:** Planning  

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [System Architecture](#system-architecture)
4. [5-Layer Analysis Engine](#5-layer-analysis-engine)
5. [Data Layer Design](#data-layer-design)
6. [Alert System](#alert-system)
7. [Dashboard Pages](#dashboard-pages)
8. [Implementation Plan](#implementation-plan)
9. [AI Prompt Template](#ai-prompt-template)
10. [File Structure](#file-structure)
11. [Cost Analysis](#cost-analysis)
12. [Risk Assessment](#risk-assessment)
13. [Success Metrics](#success-metrics)

---

## Project Overview

StockScope is a self-hosted, 100% free web-based stock analysis system that:

- Accepts any stock ticker (US, crypto, VN, global)
- Crawls all available data: prices, financials, SEC filings, news, social media, insider trading
- Runs 5-layer AI analysis (technical, fundamental, sentiment, insider, AI synthesis)
- Provides verdict: **STRONG BUY / BUY / HOLD / SELL / STRONG SELL** with confidence
- Auto-monitors and alerts via Telegram/Discord

### Key Differentiators

| Feature | StockScope | Commercial Tools |
|---------|------------|------------------|
| Cost | $0 | $29-$299/month |
| Data Sources | Unlimited (self-hosted) | Limited by plan |
| AI Models | Local + Cloud fallback | Proprietary black box |
| Customization | Full control | Restricted |
| Privacy | Self-hosted, no data sharing | Third-party servers |

---

## Tech Stack

All components are free and open-source.

### Data Providers

| Library | Stars | Purpose | API Key |
|---------|-------|---------|---------|
| yfinance | 24.9k | Price data, financials, company info | No |
| AKShare | 21.8k | Chinese/VN market data | No |
| EdgarTools | 2.6k | SEC filings, insider trades (Form 4) | No |
| fredapi | 1.6k | Federal Reserve economic data | No |

### News & Sentiment

| Library | Stars | Purpose |
|---------|-------|---------|
| finews | - | Financial news aggregation |
| sentiment-scanner | - | News sentiment scoring |
| FinBERT | - | Financial sentiment analysis (NLP) |
| VADER | - | Social media sentiment |

### AI & Analysis

| Library | Stars | Purpose |
|---------|-------|---------|
| Ollama | 180k | Local LLM inference (free, private) |
| Gemini API | - | Cloud LLM (free tier: 1M tokens/day) |
| TA-Lib | 9.7k | Technical indicators (RSI, MACD, Bollinger) |
| pandas-ta | - | Additional technical analysis |

### Storage

| Technology | Stars | Purpose |
|------------|-------|---------|
| PostgreSQL | - | Structured data (stocks, financials, alerts) |
| Qdrant | 34.4k | Vector search (news embeddings, sentiment) |
| Redis | - | Cache layer, rate limiting, sessions |

### Infrastructure

| Component | Stars | Purpose |
|-----------|-------|---------|
| FastAPI | - | Backend REST API |
| Streamlit | 45.7k | Dashboard (MVP) → React (v2) |
| APScheduler | - | Periodic task scheduling |
| n8n | 203k | Workflow automation |
| Docker | - | Container orchestration |

### MCP Servers

| Server | Stars | Purpose |
|--------|-------|---------|
| market-data-mcp | - | Market data access (no API key) |
| dbhub | 3.4k | Database MCP interface |
| brave-search-mcp | 1.4k | Web search for news/social |

### Alerts

| Channel | Purpose |
|---------|---------|
| Telegram Bot | Real-time push notifications |
| Discord Webhook | Team/group alerts |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT DASHBOARD                         │
│  📊 Overview │ 🔍 Stock Analysis │ 📰 News │ ⚠️ Alerts │ ⚙️ Settings │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API
┌───────────────────────────▼─────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│  /api/analyze/{ticker}    → Phân tích 1 cổ phiếu                │
│  /api/portfolio           → Quản lý danh mục                    │
│  /api/news/{ticker}       → Tin tức liên quan                   │
│  /api/alerts              → CRUD cảnh báo                        │
│  /api/dashboard           → Tổng hợp cho dashboard              │
│  /ws/live                 → WebSocket realtime                   │
└───┬──────────┬──────────────┬──────────────┬────────────────────┘
    │          │              │              │
┌───▼───┐ ┌───▼────┐  ┌─────▼─────┐  ┌────▼────┐
│ Data  │ │Analysis│  │ Scheduler │  │ Alert   │
│ Fetcher│ │Engine │  │(APScheduler)│ │ Engine  │
└───┬───┘ └───┬────┘  └─────┬─────┘  └────┬────┘
    │         │             │              │
┌───▼─────────▼─────────────▼──────────────▼─────────────────────┐
│                      STORAGE LAYER                              │
│  PostgreSQL          Qdrant             Redis                    │
│  - Stock data        - News embeddings  - Cache API responses    │
│  - Financials        - Sentiment vectors - Session data         │
│  - User watchlist    - Analysis results  - Rate limiting        │
│  - Alert rules                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User → Dashboard → FastAPI → Data Fetcher → yfinance/EdgarTools
                                    ↓
                              Cache Check (Redis)
                                    ↓ (miss)
                              Fetch & Store
                                    ↓
                              Analysis Engine
                                    ↓
                              5-Layer Scoring
                                    ↓
                              AI Synthesis
                                    ↓
                              Store Results → Return to Dashboard
```

---

## 5-Layer Analysis Engine

Each layer produces a normalized score (0-100). The AI Synthesis layer combines all scores into a final verdict.

### Layer 1: Technical Analysis

**Source:** TA-Lib  
**Score:** 0-100 (weighted average of indicators)

| Indicator | Weight | Buy Signal | Sell Signal |
|-----------|--------|------------|-------------|
| RSI (14) | 25% | < 30 (oversold) | > 70 (overbought) |
| MACD | 25% | MACD > Signal | MACD < Signal |
| Bollinger Bands | 20% | Price < Lower Band | Price > Upper Band |
| Moving Averages | 20% | 50MA > 200MA (Golden Cross) | 50MA < 200MA (Death Cross) |
| Volume | 10% | Volume > 2x avg | Volume < 0.5x avg |

### Layer 2: Fundamental Analysis

**Source:** EdgarTools + yfinance  
**Score:** 0-100 (comparison to sector averages)

| Metric | Weight | Bullish | Bearish |
|--------|--------|---------|---------|
| P/E Ratio | 20% | < sector avg | > 2x sector avg |
| P/B Ratio | 15% | < 1.5 | > 3.0 |
| Revenue Growth | 20% | > 15% YoY | < 0% YoY |
| Debt/Equity | 15% | < 0.5 | > 2.0 |
| Free Cash Flow | 15% | Positive & growing | Negative |
| Dividend Yield | 15% | > 2% | 0% (for income stocks) |

### Layer 3: Sentiment Analysis

**Source:** FinBERT + VADER  
**Score:** 0-100 (weighted sentiment composite)

| Source | Weight | Data Points |
|--------|--------|-------------|
| News Headlines | 40% | Last 7 days, financial news |
| Reddit/StockTwits | 25% | r/wallstreetbets, r/stocks |
| Social Volume | 20% | Mention frequency vs baseline |
| Analyst Upgrades | 15% | Price target changes |

### Layer 4: Insider Trading

**Source:** EdgarTools (Form 4)  
**Score:** 0-100 (clustered activity scoring)

| Signal | Weight | Bullish | Bearish |
|--------|--------|---------|---------|
| Clustered Buying | 30% | > 3 insiders buying | > 3 insiders selling |
| CEO/CFO Trades | 30% | Purchase > $100K | Sale > $500K |
| Buy/Sell Ratio | 25% | > 2:1 buy:sell | < 1:2 buy:sell |
| Timing | 15% | Before earnings | After earnings |

### Layer 5: AI Synthesis

**Source:** Gemini API (primary) → Ollama (fallback)  
**Input:** All 4 layer scores + raw data  
**Output:** Final verdict with reasoning

---

## Data Layer Design

### PostgreSQL Schema

```sql
-- Core stock information
CREATE TABLE stocks (
    ticker VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Daily OHLCV price data
CREATE TABLE daily_prices (
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    adj_close DECIMAL(10,2),
    PRIMARY KEY (ticker, date)
);

-- Quarterly financial statements
CREATE TABLE financials (
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    period DATE,
    revenue DECIMAL(15,2),
    net_income DECIMAL(15,2),
    eps DECIMAL(10,2),
    pe_ratio DECIMAL(10,2),
    pb_ratio DECIMAL(10,2),
    debt_equity DECIMAL(10,2),
    free_cash_flow DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (ticker, period)
);

-- SEC Form 4 insider trades
CREATE TABLE insider_trades (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    date DATE,
    insider VARCHAR(255),
    role VARCHAR(100),
    action VARCHAR(20), -- BUY or SELL
    shares INTEGER,
    price DECIMAL(10,2),
    total_value DECIMAL(15,2),
    filing_date DATE
);

-- News articles with sentiment
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    source VARCHAR(100),
    title TEXT,
    summary TEXT,
    url TEXT,
    sentiment_score DECIMAL(5,2), -- -1 to 1
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analysis results history
CREATE TABLE analysis_results (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    date TIMESTAMP,
    technical_score DECIMAL(5,2),
    fundamental_score DECIMAL(5,2),
    sentiment_score DECIMAL(5,2),
    insider_score DECIMAL(5,2),
    ai_verdict VARCHAR(20), -- STRONG BUY, BUY, HOLD, SELL, STRONG SELL
    confidence DECIMAL(5,2),
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alert rules
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    condition VARCHAR(50), -- price_above, rsi_overbought, etc.
    threshold DECIMAL(10,2),
    channel VARCHAR(20), -- telegram, discord
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User watchlists
CREATE TABLE watchlists (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    ticker VARCHAR(10) REFERENCES stocks(ticker),
    added_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);
```

### Cache Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Stock price (intraday) | 5 min | Prices change frequently |
| Financial statements | 24h | Quarterly reports don't change |
| News articles | 1h | New articles published regularly |
| Insider trades | 24h | Form 4 filings are batch processed |
| Analysis results | 6h | Balances freshness vs compute cost |

### Redis Key Patterns

```
price:{ticker}              → Latest price data (5min TTL)
financials:{ticker}         → Financial statements (24h TTL)
news:{ticker}               → Recent news (1h TTL)
analysis:{ticker}:{date}    → Analysis results (6h TTL)
rate_limit:{ip}             → API rate limiting
session:{user_id}           → User session data
```

---

## Alert System

### Alert Types

| Category | Alert | Condition | Default Channel |
|----------|-------|-----------|-----------------|
| **Price** | Threshold Cross | Price crosses above/below value | Telegram |
| **Price** | Daily Change | > 5% change in 1 day | Telegram |
| **Price** | 52-Week High/Low | Price hits 52-week extreme | Telegram |
| **Technical** | RSI Extreme | RSI > 70 or RSI < 30 | Telegram |
| **Technical** | MACD Crossover | MACD crosses signal line | Discord |
| **Technical** | Bollinger Breakout | Price breaks Bollinger band | Discord |
| **Sentiment** | Sentiment Shift | Score changes > 20 points | Telegram |
| **Sentiment** | Volume Spike | Social mentions > 3x baseline | Discord |
| **Insider** | Clustered Buying | > 3 insiders buying | Telegram |
| **Insider** | Executive Trade | CEO/CFO purchase > $100K | Telegram |
| **AI** | Verdict Change | Verdict changes to STRONG BUY/SELL | Telegram |
| **AI** | High Confidence | AI confidence > 85% | Telegram |

### Alert Processing Flow

```
APScheduler (every 5 min)
    ↓
Fetch latest data for all watchlist stocks
    ↓
Evaluate alert conditions
    ↓
Triggered? → Send notification (Telegram/Discord)
    ↓
Update last_triggered timestamp
    ↓
Log to alerts_history table
```

---

## Dashboard Pages

### 1. Dashboard (Home)

```
┌─────────────────────────────────────────────────────┐
│  PORTFOLIO OVERVIEW                                 │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│  │Total │ │Day   │ │Top   │ │Alerts│ │Stocks│     │
│  │Value │ │Change│ │Gainer│ │Count │ │Count │     │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘     │
├─────────────────────────────────────────────────────┤
│  TOP MOVERS (Today)                                 │
│  ┌─────────────────────────────────────────────┐   │
│  │ TSLA  +5.2%  │ NVDA  +3.1% │ AAPL  -1.2%  │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  RECENT ALERTS                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ ⚠️ TSLA RSI crossed 70 - 2 min ago         │   │
│  │ ⚠️ NVDA insider buy $150K - 1 hour ago     │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 2. Stock Detail (Main Analysis Page)

```
┌─────────────────────────────────────────────────────┐
│  TSLA - Tesla, Inc.                    [⚡ Full Analysis]
├─────────────────────────────────────────────────────┤
│  Price: $245.30  │  Change: +3.2%  │  Volume: 85M  │
├──────────────────────┬──────────────────────────────┤
│  ANALYSIS SCORES     │  PRICE CHART                 │
│  ┌────────────────┐  │  ┌────────────────────────┐ │
│  │ Technical: 72  │  │  │  TradingView Widget    │ │
│  │ Fundamental: 65│  │  │  (interactive chart)   │ │
│  │ Sentiment: 58  │  │  │                        │ │
│  │ Insider: 45    │  │  └────────────────────────┘ │
│  │                │  │                              │
│  │ VERDICT: BUY   │  │                              │
│  │ Confidence: 78%│  │                              │
│  └────────────────┘  │                              │
├──────────────────────┴──────────────────────────────┤
│  AI ANALYSIS                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ Key Reasons:                                │   │
│  │ • Strong revenue growth (23% YoY)           │   │
│  │ • RSI indicates oversold conditions         │   │
│  │ • Insider buying cluster in last 30 days    │   │
│  │                                             │   │
│  │ Risk Factors:                               │   │
│  │ • High P/E ratio (45x) vs sector (25x)     │   │
│  │ • EV competition intensifying               │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  RESENT NEWS                                        │
│  • Tesla Q4 deliveries beat expectations (2h ago)   │
│  • New Gigafactory announced in Mexico (5h ago)     │
└─────────────────────────────────────────────────────┘
```

### 3. Watchlist

- Add/remove stocks with notes
- Quick view of scores and verdicts
- Sort by: score, price change, last analyzed
- Bulk actions: analyze all, export

### 4. News Feed

- Real-time filtered news by ticker or sector
- Sentiment coloring (green/red/neutral)
- Source filtering (SEC, news, social)
- Search by keyword

### 5. Alerts Management

- Create/edit/delete alert rules
- Alert history with timestamps
- Channel selection (Telegram/Discord)
- Enable/disable individual alerts

### 6. Screener

- Filter by: PE, RSI, sector, market cap, dividend yield
- Sort by any metric
- Save custom screener presets
- Export results to CSV

### 7. Settings

- API key management (Gemini, etc.)
- Notification channel configuration
- Theme (dark/light)
- Data refresh intervals
- User preferences

---

## Implementation Plan

### Sprint 1 (Week 1-2): Data Foundation

**Goal:** Working data pipeline that can fetch any stock data

**Deliverables:**
- FastAPI backend running
- PostgreSQL + Redis in Docker
- yfinance integration (price, financials, profile)
- EdgarTools integration (SEC filings, insider trades)
- Basic API endpoints working
- Data caching in Redis (5min TTL)

**Acceptance Criteria:**
- [ ] Docker compose starts PostgreSQL + Redis
- [ ] FastAPI app boots and serves `/api/health`
- [ ] `GET /api/stock/{ticker}` returns price + profile from yfinance
- [ ] `GET /api/stock/{ticker}/financials` returns financial statements
- [ ] `GET /api/stock/{ticker}/insider` returns Form 4 data
- [ ] Redis caching reduces repeat fetch time by >50%
- [ ] Error handling for invalid tickers

**Review Gate:** Demo fetching TSLA data - price, financials, SEC filings all returned correctly

---

### Sprint 2 (Week 3-4): Analysis Engine

**Goal:** Complete 5-layer analysis for any stock

**Deliverables:**
- TA-Lib technical analysis (RSI, MACD, Bollinger)
- FinBERT sentiment analysis on news
- Insider trading analysis (Form 4 parsing)
- AI synthesis (Gemini API + Ollama fallback)
- Analysis results stored in PostgreSQL

**Acceptance Criteria:**
- [ ] `GET /api/analyze/{ticker}` triggers full 5-layer analysis
- [ ] Technical score (0-100) returned with individual indicator values
- [ ] Fundamental score (0-100) returned with metric breakdown
- [ ] Sentiment score (0-100) returned with source breakdown
- [ ] Insider score (0-100) returned with trade summary
- [ ] AI verdict returned with confidence + reasoning
- [ ] Results persisted to PostgreSQL
- [ ] Gemini API call works; Ollama fallback works when Gemini unavailable
- [ ] Full analysis completes in < 30 seconds

**Review Gate:** Run full analysis on TSLA - all 5 scores + AI verdict displayed correctly

---

### Sprint 3 (Week 5-6): Dashboard & Alerts

**Goal:** Usable dashboard with alert system

**Deliverables:**
- Streamlit dashboard with all pages
- Stock detail page with charts (TradingView widget)
- Alert rules engine
- APScheduler running checks every 5 min
- Telegram bot sending alerts
- Watchlist CRUD

**Acceptance Criteria:**
- [ ] Dashboard loads and shows portfolio overview
- [ ] Stock search returns results and navigates to detail page
- [ ] Stock detail page shows all 5 analysis scores + AI verdict
- [ ] TradingView widget displays price chart
- [ ] User can create/edit/delete alert rules
- [ ] APScheduler triggers alert checks on schedule
- [ ] Telegram bot receives and displays alert messages
- [ ] Watchlist add/remove works
- [ ] Dashboard loads in < 3 seconds

**Review Gate:** User can search TSLA, see full analysis on dashboard, receive Telegram alert when RSI crosses 70

---

### Sprint 4 (Week 7-8): Enhancement & Polish

**Goal:** Production-ready system

**Deliverables:**
- Qdrant vector search for news
- Stock screener (filter by PE, RSI, sector...)
- Competitor comparison
- Error handling & loading states
- Mobile responsive design
- n8n workflow for daily reports
- Documentation

**Acceptance Criteria:**
- [ ] News semantic search works via Qdrant
- [ ] Screener filters stocks by multiple criteria
- [ ] Competitor comparison shows side-by-side metrics
- [ ] All error states handled gracefully (loading, empty, error)
- [ ] Dashboard responsive on mobile devices
- [ ] n8n sends daily portfolio summary
- [ ] README.md complete with setup instructions
- [ ] All 4 sprint review gates passing

**Review Gate:** Full system demo - search any stock, get analysis, receive alerts, use screener

---

## AI Prompt Template

```
You are a professional stock analyst. Analyze {ticker} based on:

TECHNICAL DATA:
- RSI: {rsi} | MACD: {macd} | Bollinger: {bollinger_position}
- 52-week range: {low_52w} - {high_52w}
- Volume: {volume} (avg: {avg_volume})

FUNDAMENTAL DATA:
- P/E: {pe} | P/B: {pb} | P/S: {ps}
- Revenue growth: {revenue_growth}%
- EPS: {eps} | Dividend: {dividend}%
- Debt/Equity: {debt_equity}

SENTIMENT:
- News sentiment: {news_sentiment}/100
- Social mentions: {social_mentions} (trend: {social_trend})

INSIDER ACTIVITY:
- Recent trades: {insider_summary}
- Buy/Sell ratio: {buy_sell_ratio}

Provide:
1. Verdict: STRONG BUY / BUY / HOLD / SELL / STRONG SELL
2. Confidence: 0-100%
3. Key reasons (3-5 bullets)
4. Risk factors
5. Target price suggestion (if applicable)
```

---

## File Structure

```
stockscope/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings & environment variables
│   ├── database/
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   └── connection.py    # Database connection pool
│   ├── services/
│   │   ├── data_fetcher.py  # yfinance, EdgarTools, AKShare
│   │   ├── technical.py     # TA-Lib analysis
│   │   ├── sentiment.py     # FinBERT sentiment analysis
│   │   ├── insider.py       # Insider trading analysis
│   │   ├── ai_analyzer.py   # Gemini/Ollama AI synthesis
│   │   └── alert_engine.py  # Alert processing & dispatch
│   ├── routers/
│   │   ├── stock.py         # /api/stock/* endpoints
│   │   ├── analysis.py      # /api/analyze/* endpoints
│   │   ├── alerts.py        # /api/alerts/* endpoints
│   │   └── watchlist.py     # /api/watchlist/* endpoints
│   └── requirements.txt
├── frontend/
│   ├── app.py               # Streamlit main app
│   ├── pages/
│   │   ├── dashboard.py     # Portfolio overview
│   │   ├── stock_detail.py  # Full stock analysis
│   │   ├── news.py          # News feed
│   │   ├── alerts.py        # Alert management
│   │   └── settings.py      # Configuration
│   └── components/
│       ├── charts.py        # Chart components
│       └── cards.py         # Metric cards
├── docker-compose.yml       # PostgreSQL, Redis, Qdrant
├── .env                     # API keys (gitignored)
├── .env.example             # Environment template
└── README.md
```

---

## Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| yfinance | Free | No API key required |
| AKShare | Free | No API key required |
| EdgarTools | Free | MIT license |
| fredapi | Free | Federal Reserve data |
| finews | Free | RSS-based news |
| Gemini API | Free | 1M tokens/day free tier |
| Ollama | Free | Local inference, needs RAM (8GB+ for 7B model) |
| PostgreSQL | Free | Self-hosted Docker |
| Qdrant | Free | Self-hosted Docker |
| Redis | Free | Self-hosted Docker |
| Streamlit | Free | Open source |
| APScheduler | Free | Python library |
| Telegram Bot | Free | Bot API, no cost |
| Discord Webhook | Free | Webhook URL |
| n8n | Free | Self-hosted, open source |
| **Total** | **$0** | **100% free stack** |

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| yfinance rate limit | Data gaps | Medium | Cache aggressively, fallback to AKShare |
| Gemini free tier limit | AI unavailable | Low | Ollama local fallback (always available) |
| Ollama needs GPU | Slow inference | Medium | Use smaller models (7B), CPU fallback |
| SEC rate limit | Filing delay | Low | Cache filings 24h, respect robots.txt |
| Data accuracy | Wrong analysis | Medium | Cross-validate multiple sources, flag anomalies |
| API breaking changes | Feature breakage | Low | Pin versions, test upgrades in dev |
| Docker resource usage | High RAM/CPU | Medium | Monitor, optimize container sizes |
| Streamlit limitations | UI constraints | Medium | Plan React migration in v2 |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analysis speed | < 30 seconds | Time from request to response |
| Score validity | 100% | All 5 layers return 0-100 |
| AI accuracy | > 70% | Verdict matches human judgment |
| Alert latency | < 5 minutes | Time from condition to notification |
| Dashboard load | < 3 seconds | Page load time |
| Cost | $0 | No paid APIs used |
| Uptime | > 99% | Self-hosted availability |
| Data coverage | > 95% | Successful fetches for valid tickers |

---

## Appendix

### A. Supported Markets

| Market | Coverage | Source |
|--------|----------|--------|
| US (NYSE, NASDAQ) | Full | yfinance, EdgarTools |
| Crypto (BTC, ETH...) | Prices + volume | yfinance |
| Vietnam (HOSE, HNX) | Full | AKShare |
| China (SSE, SZSE) | Full | AKShare |
| Europe (LSE, XETRA) | Prices + financials | yfinance |
| Japan (TSE) | Prices + financials | yfinance |

### B. Technical Indicators Reference

| Indicator | Formula | Buy Signal | Sell Signal |
|-----------|---------|------------|-------------|
| RSI (14) | 100 - (100 / (1 + RS)) | < 30 | > 70 |
| MACD | 12 EMA - 26 EMA | MACD > Signal | MACD < Signal |
| Bollinger | SMA ± 2σ | Price < Lower | Price > Upper |
| SMA 50/200 | Simple Moving Average | 50 > 200 | 50 < 200 |

### C. AI Model Selection

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| Gemini 2.0 Flash | Cloud | Fast | High | Primary (free tier) |
| Llama 3.1 8B | 4GB | Medium | Good | Local fallback |
| Mistral 7B | 4GB | Medium | Good | Alternative local |
| Phi-3 Mini | 2GB | Fast | Decent | Low-resource fallback |

---

*Document generated: 2026-09-19*  
*Last updated: 2026-09-19*  
*Author: StockScope Team*
