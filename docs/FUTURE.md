# Future — Deferred Features Outside V1

**Version:** V1 Freeze 2026-08-26  
**Rule:** *If it is on this list, a PR adding it in V1 must be rejected.* Deferred items require a V2 proposal with dependency and rationale before implementation.

---

## How to Read This List

| Field | Meaning |
|-------|---------|
| **Feature** | Deferred capability |
| **Why deferred** | Evidence, scope, or risk reason |
| **Dependency** | What must happen first |
| **Why not in V1** | Cost/complexity vs. value at V1 stage |
| **V2 trigger** | Signal that it becomes worth building |

---

## 1. Full Crawler & Deep Web Traversal

- **Feature:** Recursive site-wide crawl, frontier queue, politeness scheduler, sitemap parsing, JS-rendered traversal.
- **Why deferred:** V1 spec explicitly out-of-scope; frontier + crawl is a separate system, not a search-augmentation.
- **Dependency:** Dedicated crawl infra (frontier DB, scheduler, Bloom filter), Playwright fleet, budgeting separate from retrieval budget.
- **Why not in V1:** Discovery via search APIs + bounded fetch of top-K results suffices for V1's 33-item MVP; crawler would explode cost and scope without eval impact.
- **V2 trigger:** Benchmarks show recall bottleneck is *not* query expansion but missing deep pages not surfaced by search (measure via recall gap).

---

## 2. Login / CAPTCHA / Anti-Bot Bypass

- **Deferred:** Any automated bypass of authentication, paywalls, CAPTCHAs, bot-detection, or private endpoints.
- **Why deferred:** Legal/ethical hard gate, explicitly out-of-scope in spec and SOURCE_MODEL.md.
- **Dependency:** Legal review + explicit allowlist + per-source terms.
- **Why not:** Violates tier/source contracts and risks project viability.
- **Trigger:** Never for bypass; for *licensed* access, add `snapshot` source after contract.

---

## 3. Unauthorized / Private Social Extraction

- **Deferred:** Private Facebook, Instagram, TikTok, LinkedIn, Snapchat, private messages, closed groups, authenticated X feeds, or any scrape requiring login impersonation.
- **Why deferred:** Out-of-scope, legal blocklist in `configs/sources` validator.
- **Dependency:** Official public APIs only (already in `reddit_public`, `x_public_search`).
- **Trigger:** Partnership/license that provides a compliant `snapshot` or `api` source — then it appears as a registry entry, not a bypass.

---

## 4. Full FB / LI / TikTok / IG Scraping (Public but Complex)

- **Deferred:** Full-scale public social scraping at firehose volume, sentiment pipelines, trend detection across social.
- **Why deferred:** Volume, rate limits, moderation, and identity resolution at social scale are a separate product; V1 social is bounded (top-K public posts per query).
- **Dependency:** Social normalization pipeline, author dedup, virality scoring.
- **Trigger:** Category E (market/competition) benchmarks show missing social signal that moves pricing/positioning conclusions.

---

## 5. Proprietary Databases Without License

- **Deferred:** Crunchbase Pro, PitchBook, Factiva, LexisNexis, etc. beyond publicly licensed snapshot or free tier.
- **Why deferred:** License dependency; existing V1 uses `snapshot` access_method only if snapshot exists and is licensed.
- **Dependency:** Commercial license + ETL connector + snapshot refresh cadence.
- **Trigger:** Funding/market benchmarks (B/E) show systematic gaps for private companies that public filings can't fill, and license ROI is justified via eval delta.

---

## 6. Trading Execution & Financial Actions

- **Deferred:** Any ordering, trading, portfolio action, or execution on behalf of user.
- **Why deferred:** Out-of-scope explicitly; risk surface (regulatory, financial loss) unrelated to research engine.
- **Dependency:** Broker integration, compliance, user authorization framework.
- **Trigger:** Separate product decision; not derived from research engine evals.

---

## 7. Custom LLM / Embedding Training / Fine-Tuning

- **Deferred:** Training or fine-tuning own LLM or embedding model; custom model hosting.
- **Why deferred:** LLM-agnostic abstraction is the V1 strategy; LiteLLM + off-the-shelf embeddings (`text-embedding-3-small` at 1536) suffice. Training adds cost and locks in model.
- **Dependency:** Training data pipeline, eval for fine-tune, model registry, GPU fleet.
- **Trigger:** Evals show systematic failure mode that prompt engineering + deterministic scoring cannot fix and that a small fine-tune provably improves (measure via ablated eval).

---

## 8. Neo4j (Graph DB)

- **Deferred:** Dedicated graph DB (Neo4j, Neptune) as primary store.
- **Why deferred:** Spec says prefer PostgreSQL unless insufficient; `graph_nodes/edges` + `source_lineages` + adjacency indexes satisfy V1 evidence graph queries. One fewer infra to operate.
- **Dependency:** Demonstration that PG graph queries (recursive CTEs, adjacency sweeps) exceed latency or correctness thresholds on real V1 workloads (measure p95 traversal on `contradictions` + `lineages`).
- **Trigger:** Graph traversal > 500ms p95 for report synthesis or lineage independence scoring.

---

## 9. Kafka / K8s / Microservice Explosion

- **Deferred:** Kafka, Kubernetes, service mesh, per-package microservices, event sourcing at scale.
- **Why deferred:** Explicit anti-scope. V1 is single `FastAPI + arq/Redis + Postgres` deploy, Docker Compose. Microservices add ops without throughput need.
- **Dependency:** Throughput requirement > 100 concurrent jobs or multi-region HA.
- **Trigger:** Scale eval shows queue backpressure at `arq` limits or deployment complexity forces isolation.

---

## 10. Mobile App

- **Deferred:** Native iOS/Android or mobile-specific apps.
- **Why deferred:** Out-of-scope for V1; minimal web UI suffices for eval and API consumers.
- **Dependency:** Mobile design, API auth, offline sync decisions.
- **Trigger:** User research shows mobile research consumption is primary channel.

---

## 11. RBAC & Billing

- **Deferred:** Role-based access control, multi-tenant isolation, billing/metering, invoices, plan limits.
- **Why deferred:** Out-of-scope in V1; single-tenant, API-key stub in V1. Billing would obscure eval-driven quality work.
- **Dependency:** Auth provider, tenant DB sharding, meter aggregation.
- **Trigger:** Multi-user pilot with external customers and clear pricing model.

---

## 12. Fancy Frontend / Graph Visualization

- **Deferred:** D3/graph viz, interactive evidence graphs, network diagrams, drag-and-drop report builder.
- **Why deferred:** Out-of-scope; minimal UI (form, progress, report, eval table) is the V1 spec. Graph viz adds frontend complexity for limited insight at V1 data scale.
- **Dependency:** Stable graph schema, UX research on what viz actually improves decision-making.
- **Trigger:** User studies show text+table report is insufficient for contested claims comprehension.

---

## 13. Additional Deferred (Not in Spec Anti-Scope but Explicitly Post-V1)

| Feature | Why Deferred |
|---------|--------------|
| **Real-time SSE/WebSocket for progress** | Polling every 2s suffices; SSE adds infra for V1. |
| **Embedding fine-tuning per industry** | Dimension frozen at 1536; tuning deferred until category E/F show embedding misses. |
| **Multi-tenant row-level security** | Single-tenant PG in V1; RLS added with RBAC. |
| **Vector DB separation (Qdrant/Weaviate)** | pgvector suffices; separate DB deferred until scale probe fails. |
| **Human-in-the-loop adjudication UI** | `needs_human` contradictions flagged in report but no adjudication workflow in V1. |
| **Scheduled re-research / watchlists** | One-shot jobs in V1; cron + diff reporting is V2. |
| **Export to PDF/Slides** | Markdown + JSON in V1; PDF deferred to reporting package extension. |
| **Opportunity-search module (scholarships/competitions)** | Explicitly deferred in prior spec; out of evidence engine scope. |

---

## 14. What Is NOT Deferred (Must Be in V1 — Common Temptations to Cut, but Spec Requires)

These are sometimes mistakenly deferred — they are **required in V1** per the 33-item list:

- Prompt parsing, planning, query expansion
- Multi-region & multi-language (shards + transliteration)
- Web + news + social discovery (bounded but present)
- Candidate extraction/dedup, entity resolution + aliases
- Deep research + gap detection + recursive loop
- Parallel workers (discovery/verification fan-out)
- Evidence/claim extraction/verification, contradiction detection
- Source quality classification (tiers) + confidence scoring + deterministic ranking
- Citation-backed reports
- Job persistence/history, budget controls/stopping criteria, source registry
- Eval benchmarks + basic API + minimal UI

Any proposal to defer these is a re-scope requiring spec amendment.

---

## 15. Process for Re-Introducing a Deferred Item

1. **V2 proposal** (one-page) with: problem → benchmark evidence of gap → dependency check → cost/latency estimate → eval threshold for success → rollback plan.
2. **Review** against `ARCHITECTURE.md` ADRs and `AGENT_CONTRACTS.md` — new agent? new table? new config? Justify boundary change.
3. **Migrations + tests** before code: DATA_MODEL.md amendment, AGENT_CONTRACTS update, eval category added.
4. **No silent re-introduction:** CI source validator blocks registry drift; review gate blocks agent proliferation without doc update.

