# Source Model — Registry, Tiers, and Access

**Version:** V1 Freeze 2026-08-26  
**Packages:** `packages/sources` (registry), `packages/search`/`social`/`crawling` (connectors)  
**Config:** `configs/sources/*.yaml` (+ `configs/regions/*.json`)  
**DB Cache:** `sources` table (mirrors YAML, queryable)  
**Principle:** *Tier affects weight, not censorship. Discovery ≠ Verification ≠ Context — different sources for different purposes.*

---

## 1. Source Registry Schema

### 1.1 YAML Source Definition (Source of Truth)

Each source is a YAML file under `configs/sources/` (or one `sources.yaml` with list). Schema enforced by `pydantic` at startup — invalid YAML fails boot with diagnostic.

```yaml
# configs/sources/sec_edgar.yaml
id: sec_edgar
display_name: "SEC EDGAR (US filings)"
tier: 1
authority_score: 0.98          # 0–1, human-curated, informs verification weighting
coverage:                     # regions / industries / entity types where source is authoritative
  regions: [us]
  industries: [all]
  entity_types: [company, funding_round, investor]
access_method: api            # api | rss | scrape | playwright | snapshot
search_url: "https://efts.sec.gov/LATEST/search?q={query}&dateRange=custom&startdt={start}&enddt={end}"
fetch_url_template: "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}"
rate_limit_per_min: 10        # token bucket
timeout_ms: 30000
max_results: 20
robots_respected: true
requires_key: false           # true → env var SEC_API_KEY
is_active: true
health_url: "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent"
description: "Primary source for US public company filings. Tier 1 for funding, identity, risks."
license_note: "Public domain. Respect rate limits."
tags: [official, primary, filings, us]

---
# configs/sources/tavily.yaml
id: tavily
display_name: "Tavily Search"
tier: 2
authority_score: 0.72
coverage: { regions: [us, eu, global], languages: [en] }
access_method: api
search_url: "https://api.tavily.com/search"
requires_key: true
env_key: TAVILY_API_KEY
rate_limit_per_min: 60
timeout_ms: 15000
max_results: 20
robots_respected: true
is_active: true
tags: [search, aggregator, web]

---
# configs/sources/reddit_public.yaml
id: reddit_public
display_name: "Reddit (public)"
tier: 4
authority_score: 0.35
coverage: { regions: [us, eu, global], languages: [en] }
access_method: api
search_url: "https://oauth.reddit.com/search.json?q={query}&sort=relevance&t={time_range}&limit={max_results}"
requires_key: true
env_key: REDDIT_CLIENT_ID
rate_limit_per_min: 30
timeout_ms: 15000
max_results: 20
robots_respected: true
is_active: true
tags: [social, ugc, sentiment]
access_scope: "public_search_and_comments_only"  # hard guardrail — no private scrape
```

**Full schema (Pydantic):**

```python
class SourceTier(int): 1 | 2 | 3 | 4 | 5

class Coverage(BaseModel):
    regions: list[str] = Field(default=["global"])   # us, eu, vn, ru, cn, latam, ...
    languages: list[str] = Field(default=["en"])
    industries: list[str] = Field(default=["all"])
    entity_types: list[str] = Field(default=["all"])

class SourceDef(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")        # registry key
    display_name: str
    tier: SourceTier
    authority_score: float = Field(ge=0, le=1)
    coverage: Coverage
    access_method: Literal["api","rss","scrape","playwright","snapshot"]
    search_url: str | None = None
    fetch_url_template: str | None = None
    rate_limit_per_min: int | None = None
    timeout_ms: int = 30000
    max_results: int = 20
    robots_respected: bool = True
    requires_key: bool = False
    env_key: str | None = None                      # e.g., TAVILY_API_KEY
    is_active: bool = True
    health_url: str | None = None
    health_status: Literal["unknown","healthy","degraded","down"] = "unknown"
    description: str = ""
    license_note: str = ""
    tags: list[str] = Field(default_factory=list)
    access_scope: str | None = None                 # for social: guardrail notes
```

### 1.2 DB Cache (`sources` table)

On API/worker startup, loader reads all `configs/sources/*.yaml`, validates, and upserts into `sources` table (see DATA_MODEL.md). DB is **queryable cache**, not authoring surface.

```python
class SourceRegistry:
    def load(self) -> list[SourceDef]: ...         # from YAML
    def all(self) -> list[Source]: ...             # from DB
    def get(self, id: str) -> Source | None: ...
    def active(self) -> list[Source]: ...          # is_active=true
    def by_tier(self, tiers: list[int]) -> list[Source]: ...
    def by_region(self, region: str) -> list[Source]: ...
    def health_check_all(self) -> dict[str, bool]: ...
```

- **Hot reload:** Not in V1 — registry reload requires restart (or `POST /admin/sources/reload` with API key in post-V1). V1 simplicity.
- **Versioning:** `config_hash = sha256(sorted YAML contents)` stored in `research_jobs.config_hash` at job creation for reproducibility; also logged.

### 1.3 `configs/regions/` and `configs/languages/`

```json
// configs/regions/us.json
{
  "code": "us",
  "name": "United States",
  "languages": ["en"],
  "search_domains": ["site:.com", "site:.us"],
  "preferred_sources": ["sec_edgar","tavily","brave","reddit_public"],
  "time_zone": "America/New_York"
}
// configs/regions/vn.json
{
  "code": "vn",
  "name": "Vietnam",
  "languages": ["vi","en"],
  "search_domains": ["site:.vn","site:.com.vn"],
  "preferred_sources": ["tavily","brave","vietstock_snapshot"],
  "time_zone": "Asia/Ho_Chi_Minh"
}
```

Planner picks `preferred_sources` per region to avoid querying irrelevant sources. Language configs hold transliteration rules (e.g., `configs/languages/vi.json` with diacritics folding for alias matching).

---

## 2. Tier Definitions (1–5, Configurable)

Tiers are **curated, versioned, explainable** — not LLM-guessed at query time. Tier affects verification weighting and ranking, not filtering (all tiers discoverable, but lower tiers need more corroboration).

| Tier | Label | Definition | Examples | Verification Weight | Discovery Priority |
|------|-------|------------|----------|----------------------|--------------------|
| **1** | **Primary / Official** | First-party issuance: filings, registries, official company domain, authoritative DB with license. Self-attestation or regulatory. | SEC EDGAR, company `.com` official site (careers/about), national company registry, USPTO, FDA, Crunchbase-licensed snapshot (if licensed), official press releases on verified domain, `site:company.com` | **1.0×** — single tier-1 evidence can push `supported`; two tier-1 → `verified` | High for `verification`/`gap_fill` on identity/funding/risks |
| **2** | **Major Reputable Secondary** | Established press/agency with editorial, large regional/national coverage, known fact-checking process. | Reuters, AP, Bloomberg, WSJ, FT, NYT, major regional dailies (e.g., Tuổi Trẻ for VN, Kommersant for RU), GDELT-indexed news API | **0.85×** — two tier-2 strong sources → `verified` if no contradicting |
| **3** | **Trade / Regional / Specialized** | Industry trade publications, sector analysts, smaller regional outlets, academic pre-prints. | TechCrunch (for funding, but tier 3 for claims), The Verge, regional business journals, arXiv | **0.60×** — needs 2–3 to corroborate |
| **4** | **Community / UGC / Blogs** | User-generated, social, personal blogs, forums, community wikis. Useful for sentiment, context, unconfirmed signals. | Reddit public, X public, Medium personal, StackOverflow, personal blogs | **0.30×** — counts as context, never alone for `verified`; contributes to market/competition signals |
| **5** | **Unverified / Aggregated / Low-signal** | Aggregators with no original reporting, SEO farms, content farms, unverified syndication. | Random aggregators, low-authority scraper mirrors, AI-generated filler sites | **0.10×** — tracked for coverage diversity but penalized in scoring; staleness + contradiction penalty applied |

**Configurability:**

- `tier` and `authority_score` live in YAML and are **versioned in git**; PR to change tier requires rationale in `description` + review.
- Scoring reads `sources.tier` + `authority_score` at job start (snapshot) — mid-job tier changes don't affect running jobs (config_hash frozen).
- Per-category tier overrides allowed: e.g., `TechCrunch` is tier 3 globally but tier 2 for `funding` dimension if `coverage.industries` includes `tech` and `tags` includes `funding_authoritative`. Overridden via `tier_overrides: {funding: 2}` in YAML (optional).

**Why 5 tiers not 3:** Spec calls tiers 1-5 configurable. Granularity separates "major press" (2) from "trade" (3) from "UGC" (4) — scoring needs distinct weights to avoid over-trusting trade press as Reuters-equivalent.

---

## 3. Authority, Coverage, Access Method (Deep Dive)

### 3.1 Authority

- `authority_score` (0–1) is **human-curated** at source registration, informed by factual accuracy history, editorial process, citation practices, and domain expertise.
- Not set by LLM at query time (LLM can *suggest* but human reviews). Rationale logged in `description` + git blame.
- Verification weighting: `effective_weight = authority_score * tier_weight` (tier_weight from table). Example: SEC `tier 1, 0.98 → 0.98`, Reuters `tier 2, 0.90 → 0.765`, Reddit `tier 4, 0.35 → 0.105`.
- Authority decay: if a tier 2 source shows systemic bias on a dimension (measured via eval benchmarks), its `authority_score` can be lowered per `metadata.authority_history`.

### 3.2 Coverage

`coverage` declares where a source is authoritative — used by planner to avoid wasteful shards.

```yaml
coverage:
  regions: [us, eu]        # empty or [global] → all regions
  languages: [en, de]
  industries: [tech, finance]
  entity_types: [company, person]
```

- Planner filters: shard `region=vn` → only sources covering `vn` or `global`.
- Gap detector biases: `funding` gap → prefers sources covering `entity_types: [company]` + `tier 1-2`.
- Eval metric: `source_diversity` measures distinct `coverage` buckets hit per job.

### 3.3 `access_method`

| Method | When Used | Tech | V1 Allowed |
|--------|-----------|------|------------|
| `api` | Structured search APIs | `httpx` + key, paginated | ✅ all tiers |
| `rss` | News/RSS feeds | `httpx` + `feedparser`-like | ✅ news tier 2-3 |
| `scrape` | Public HTML fetch | `httpx` + `trafilatura`/`BS4`, respects `robots.txt` | ✅ limited — only public pages, no bypass |
| `playwright` | JS-heavy pages where `trafilatura` fails | `playwright` headless (fallback, not default) | ✅ limited — only when `scrape` fails + `robots.txt` allows |
| `snapshot` | Licensed/cached snapshots (e.g., Crunchbase snapshot if licensed) | local file or snapshot API | ✅ only if license present; else stubbed/mock in tests |

**Hard rules (anti-scope):**

- If `robots.txt` disallows, method downgrades: `scrape→skip`, `playwright→skip`. Never bypass.
- `login` / `captcha` / `anti-bot` bypass → **never**; shard marked `failed` with `error="access_method_not_allowed"`.
- Private social (`facebook_private`, `instagram_private`, `linkedin_private`, `tiktok_private`) — **not in registry in V1**; any PR adding them is rejected per review gate.
- Access method health is tracked per `sources.health_status` via periodic `health_check`.

---

## 4. Discovery vs Verification vs Context Separation

Sources are not monolithically "trusted" — their role depends on **purpose** (from planner shards / gap queries).

### 4.1 Purposes (Column `research_queries.purpose`, `gap_queries.purpose`)

| Purpose | Description | Preferred Tiers | Example Query | Weight in Verification |
|---------|-------------|-----------------|---------------|------------------------|
| `discovery` | Maximize relevant coverage — broad funnel | All tiers, breadth-first | "Acme AI Berlin startup" | Used as candidate evidence, but verification still needs tier-weighted corroboration |
| `verification` | Confirm or disconfirm a specific claim | Tier 1–2 only | "Acme AI seed round $3M SEC filing" | Higher weight; prefer primary |
| `context` | Surrounding signals: market, competition, sentiment | Tier 3–4 + social | "AI startups Berlin funding trends 2023" | Context only — populates coverage dims `market`, `customers`, `competition`, not direct claim verification |
| `gap_fill` | Fill missing coverage dimension (deep research) | Tier 1–2 for identity/funding/risks; 2–3 for product/tech | "Acme AI founders LinkedIn official" | Gap-specific tier bias |
| `recursive` | Follow-up from prior evidence (cited source) | Tier of cited source + verification bias | "Source cited in Acme filing" | Inherits cited source's tier |

### 4.2 How Separation Flows Through Pipeline

```
Planner emits shards:  {discovery × 8, verification × 2, context × 2} per job
         │
Discovery Workers: execute discovery+context shards broadly (all tiers, budget-aware)
         │
Verification / Deep Research: verification/gap_fill shards target tier 1-2 via filtered connectors
         │
Evidence Engine: tags each evidence with purpose → verification engine weights by (tier × purpose)
         │  e.g., discovery-tier4 evidence = 0.3× weight even if snippet matches claim
         ▼
Assertion: "Funding $3M" supported by SEC filing (tier 1, verification) + Reddit (tier 4, discovery)
   → verification = SUPPORTED (not VERIFIED, because only 1 primary tier-1)
   → but add Reuters tier-2 verification hit → upgrades to VERIFIED
```

### 4.3 Config Example for Purpose Routing

```yaml
# configs/sources/tavily.yaml
purposes: [discovery, verification, context]  # can serve all
verification_boost: 0.0                       # no special boost

# configs/sources/sec_edgar.yaml
purposes: [verification, gap_fill]           # not used for broad discovery (too narrow)
verification_boost: 0.2                      # extra weight when used for verification

# configs/sources/reddit_public.yaml
purposes: [discovery, context]               # never verification
verification_boost: -0.5                     # penalized if mistakenly used for verification
```

If unspecified, default `purposes` = `[discovery, verification, context]`.

---

## 5. Registry Lifecycle & Governance

1. **Add source:** Create `configs/sources/<id>.yaml` + PR with description rationale + tier justification + license note + `requires_key` env doc. CI validates schema + checks `health_url` (if given) reachable.
2. **Tier change:** PR touching `tier` or `authority_score` requires review by 2nd maintainer + update `description` with "Tier rationale: ...".
3. **Deactivate:** Set `is_active: false` + remove from active list; DB row stays (historical jobs still reference it via `source_id` — never hard-delete).
4. **Health:** Nightly `health_check_all()` updates `last_health_check` + `health_status`; degraded sources are deprioritized (not failed) by DiscoveryOrchestrator.
5. **Audit:** All changes git-versioned; `config_hash` per job captures registry snapshot, so eval runs are reproducible even as registry evolves.

---

## 6. Relation to Other Models

- **Evidence (`evidence.source_id → sources.id`):** Each evidence span knows its tier/authority at scoring time (snapshot).
- **Claim sources (`claim_sources.source_id` + tier denormalized):** Fast scoring without join to documents.
- **Scores:** `factors.source_independence` penalizes multiple evidences from same `coverage` bucket (copy-paste across syndicates).
- **Reports:** Citation badge shows tier (e.g., `[1†]` for tier 1, `[4]` for tier 4) so reader sees primary vs UGC.

---

## 7. Anti-Scope Guards (Registry-Level)

CI check `scripts/validate_sources.py` (added Phase 1):

- Reject any YAML with `access_method` requiring undocumented bypass.
- Reject `id` matching private-social blocklist: `facebook_private`, `instagram_private`, `linkedin_private`, `tiktok_private`, `snapchat.*`.
- Reject `is_active=true` with `access_method=playwright` + `robots_respected=false`.
- Warn if `requires_key=true` but `env_key` missing from `.env.example`.

---

## 8. Open Questions

- **Snapshot sources:** If we license a Crunchbase-like snapshot, confirm schema for `snapshot` access_method (local Parquet or API) — deferred to phase where license exists.
- **Tier override granularity:** Confirm per-dimension override (`tier_overrides: {funding: 2}`) is needed in V1 or defer to post-V1 (current freeze: allow but not required).
