# Webcrawler Topic-Crawl Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a topic-driven crawl pipeline (`prompt → ddgs seeds → fetch → BM25 → Gemini → markdown + FTS5`) plus an opencode agent + skill that orchestrates it.

**Architecture:** Extend the existing `webcrawler/` library with 3 new modules (`core/sources/serp.py`, `core/score.py`, `runners/topic_crawl.py`) and FTS5 functions appended to `core/store.py`. A thin agent (`agent/web-crawler.md`) and skill (`.opencode/skills/webcrawler/SKILL.md`) only invoke the CLI and read its manifest — all logic lives in `webcrawler/`.

**Tech Stack:** Python 3.12, httpx, trafilatura, rank-bm25, ddgs (DuckDuckGo, keyless), Gemini REST (free-tier `GEMINI_API_KEY`, no SDK), SQLite FTS5, pytest.

**Spec:** `docs/superpowers/specs/2026-09-29-webcrawler-topic-crawl-agent-design.md`

## Global Constraints

- All commands run with working directory `C:\Opencode\webcrawler` (tests: `python -m pytest tests -v`).
- Reuse existing `core/` modules (`fetch`, `extract`, `robots`, `store`, `url_db`) — do not rewrite them; `store.py` and `requirements.txt` are the only existing files modified.
- Hard cap `--max 500` (scope A). Polite crawling: robots.txt + per-domain rate limit already enforced by `core.fetch.Fetcher`.
- 100% free: no paid API. Gemini only via env `GEMINI_API_KEY` (free tier); every Gemini failure must fall back to BM25 — a run must never fail because of Gemini.
- Gemini calls go through REST with `httpx` (already a dependency) — no new SDK packages.
- New dependencies allowed: `ddgs`, `rank-bm25` only.
- Commit after every task.

---

### Task 1: Seed discovery — `core/sources/serp.py`

**Files:**
- Create: `webcrawler/core/sources/serp.py`
- Test: `webcrawler/tests/test_serp.py`
- Modify: `webcrawler/requirements.txt`

**Interfaces:**
- Consumes: `core.sources.DiscoveredURL` (dataclass: `url: str`, `source: str`, `discovered_at: str`).
- Produces: `discover(query: str, limit: int = 50, lang: str = "en", search=None) -> list[DiscoveredURL]` where `search` is an optional callable `(query: str, lang: str = "en") -> list[dict]` returning raw result dicts with an `"href"` key. Default uses `ddgs`. Caps at 3 URLs per domain, skips non-http(s) URLs.

- [ ] **Step 1: Write the failing tests**

Create `webcrawler/tests/test_serp.py`:

```python
# tests/test_serp.py
from core.sources.serp import discover, MAX_PER_DOMAIN


def _results(n=10):
    return [{"href": f"https://site{i}.example.com/p{i}"} for i in range(n)]


def test_discover_injected_search_respects_limit():
    items = discover("q", limit=5, search=lambda q, lang="en": _results(10))
    assert len(items) == 5
    assert all(i.source == "serp" for i in items)


def test_discover_caps_per_domain():
    dup = [{"href": "https://same.com/a"} for _ in range(10)]
    items = discover("q", search=lambda q, lang="en": dup)
    assert len(items) == MAX_PER_DOMAIN


def test_discover_skips_non_http():
    mixed = [
        {"href": "ftp://x.com/f"},
        {"href": "javascript:void(0)"},
        {"href": "https://ok.com/a"},
    ]
    items = discover("q", search=lambda q, lang="en": mixed)
    assert [i.url for i in items] == ["https://ok.com/a"]


def test_discover_missing_href_ignored():
    items = discover("q", search=lambda q, lang="en": [{"href": ""}, {"title": "x"}])
    assert items == []


def test_discover_domain_cap_is_case_insensitive():
    dup = [
        {"href": "https://Same.com/a"},
        {"href": "https://SAME.com/b"},
        {"href": "https://same.com/c"},
        {"href": "https://same.com/d"},
    ]
    items = discover("q", search=lambda q, lang="en": dup)
    # without lowercasing the netloc, each casing would count separately -> 4
    assert len(items) == MAX_PER_DOMAIN
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_serp.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.sources.serp'`

- [ ] **Step 3: Add dependencies**

Append to `webcrawler/requirements.txt`:

```
ddgs>=9.0
rank-bm25>=0.2.2
```

Install: `python -m pip install -r requirements.txt`
Expected: installs `ddgs` and `rank-bm25` without errors.

- [ ] **Step 4: Write minimal implementation**

Create `webcrawler/core/sources/serp.py`:

```python
# core/sources/serp.py
from urllib.parse import urlparse

from core.sources import DiscoveredURL

MAX_PER_DOMAIN = 3
_SCHEMES = ("http", "https")


def _default_search(query: str, lang: str = "en") -> list[dict]:
    from ddgs import DDGS
    region = "vi-vn" if lang == "vi" else "us-en"
    with DDGS() as ddgs:
        return list(ddgs.text(query, region=region, max_results=50))


def discover(query: str, limit: int = 50, lang: str = "en", search=None) -> list[DiscoveredURL]:
    search = search or _default_search
    raw = search(query, lang)
    seen: dict[str, int] = {}
    out: list[DiscoveredURL] = []
    for item in raw:
        if len(out) >= limit:
            break
        url = (item or {}).get("href") or ""
        if not url.startswith(_SCHEMES):
            continue
        domain = urlparse(url).netloc.lower()
        if seen.get(domain, 0) >= MAX_PER_DOMAIN:
            continue
        seen[domain] = seen.get(domain, 0) + 1
        out.append(DiscoveredURL(url=url, source="serp"))
    return out
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/test_serp.py -v`
Expected: 5 passed

- [ ] **Step 6: Run full suite to confirm no regressions**

Run: `python -m pytest tests -v`
Expected: all existing tests + new 5 pass

- [ ] **Step 7: Commit**

```bash
git add webcrawler/core/sources/serp.py webcrawler/tests/test_serp.py webcrawler/requirements.txt
git commit -m "feat(webcrawler): ddgs seed discovery with per-domain cap"
```

---

### Task 2: BM25 pre-filter — `core/score.py` (part 1)

**Files:**
- Create: `webcrawler/core/score.py`
- Test: `webcrawler/tests/test_score.py`

**Interfaces:**
- Consumes: `core.sources.ExtractedContent` (fields: `url`, `source`, `title`, `text`, `published`, `author`, `fetched_at`).
- Produces:
  - `tokenize(text: str) -> list[str]` — lowercase `\w+` tokens (Unicode, works for Vietnamese).
  - `bm25_filter(docs: list[ExtractedContent], topic: str, keep_ratio: float = 0.4, min_keep: int = 20) -> list[tuple[ExtractedContent, float]]` — sorted by score descending. Keep rule: all docs when `len <= 50`, otherwise `max(int(len * keep_ratio), min_keep)`.

- [ ] **Step 1: Write the failing tests**

Create `webcrawler/tests/test_score.py`:

```python
# tests/test_score.py
from core.sources import ExtractedContent
from core.score import bm25_filter, tokenize


def _doc(url: str, title: str, text: str) -> ExtractedContent:
    return ExtractedContent(url=url, source="seeds", title=title, text=text)


def test_tokenize_lowercases_and_splits():
    assert tokenize("RAG Architecture 2026") == ["rag", "architecture", "2026"]


def test_tokenize_keeps_vietnamese_words():
    tokens = tokenize("kiến trúc RAG")
    assert "rag" in tokens
    assert any(t.startswith("ki") for t in tokens)


def test_bm25_empty_input():
    assert bm25_filter([], "topic") == []


def test_bm25_orders_relevant_docs_first():
    docs = [
        _doc("https://x/cooking", "Pasta", "tomato sauce recipe for pasta dinner"),
        _doc("https://x/rag1", "RAG systems", "retrieval augmented generation rag llm architecture"),
        _doc("https://x/garden", "Tomatoes", "how to grow tomatoes in a small garden"),
        _doc("https://x/rag2", "RAG pipeline", "rag retrieval with vector databases and llm"),
    ]
    kept = bm25_filter(docs, "rag retrieval llm")
    assert len(kept) == 4  # <= 50 docs: keep all, but order matters
    top_urls = [d.url for d, _ in kept[:2]]
    assert top_urls == ["https://x/rag1", "https://x/rag2"]


def test_bm25_applies_ratio_above_50_docs():
    docs = [_doc(f"https://x/{i}", f"T{i}", "unrelated filler text about weather") for i in range(100)]
    docs[50] = _doc("https://x/hit", "Hit", "quantum entanglement experiment results")
    kept = bm25_filter(docs, "quantum entanglement")
    assert len(kept) == 40
    assert kept[0][0].url == "https://x/hit"


def test_bm25_single_doc_returns_it():
    d = _doc("https://x/one", "One", "only page")
    assert bm25_filter([d], "anything") == [(d, 1.0)]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_score.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.score'`

- [ ] **Step 3: Write minimal implementation**

Create `webcrawler/core/score.py`:

```python
# core/score.py
import json
import os
import re

from core.sources import ExtractedContent

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_RATIO_THRESHOLD = 50  # below this, keep everything


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def bm25_filter(docs: list[ExtractedContent], topic: str,
                keep_ratio: float = 0.4, min_keep: int = 20
                ) -> list[tuple[ExtractedContent, float]]:
    if not docs:
        return []
    if len(docs) <= 2:
        return [(d, 1.0) for d in docs]
    from rank_bm25 import BM25Okapi
    corpus = [tokenize(f"{d.title} {d.text[:600]}") for d in docs]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(tokenize(topic))
    keep = (len(docs) if len(docs) <= _RATIO_THRESHOLD
            else max(int(len(docs) * keep_ratio), min_keep))
    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
    return ranked[:keep]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_score.py -v`
Expected: all tests pass

- [ ] **Step 5: Run full suite**

Run: `python -m pytest tests -v`
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add webcrawler/core/score.py webcrawler/tests/test_score.py
git commit -m "feat(webcrawler): BM25 pre-filter with fixed keep rule"
```

---

### Task 3: Gemini final scorer + `rank()` — `core/score.py` (part 2)

**Files:**
- Modify: `webcrawler/core/score.py` (append)
- Modify: `webcrawler/tests/test_score.py` (append)

**Interfaces:**
- Consumes: `bm25_filter`, `ExtractedContent` from Task 2; env `GEMINI_API_KEY`.
- Produces (appended to `core/score.py`):
  - `gemini_score(topic: str, docs: list[ExtractedContent], api_key: str, transport=None) -> dict[str, tuple[float, str]]` — maps `url -> (score 0..1, reason)`. `transport` is callable `(url: str, payload: dict, api_key: str) -> str` returning raw response text; default does `httpx.post` to Gemini REST. Batches of 10.
  - `rank(docs: list[ExtractedContent], topic: str, min_score: float = 0.6, use_gemini: bool = True, api_key: str | None = None, transport=None) -> tuple[list[tuple[ExtractedContent, float, str]], dict]` — returns `(kept, meta)`; `kept` items are `(doc, score, reason)` sorted desc by score; `meta = {"gemini_used": bool, "bm25_candidates": int, "errors": list[str]}`. On Gemini exception OR `use_gemini=False` OR no `api_key`: return **all** BM25 candidates with min-max-normalized scores and reason `"bm25-fallback"`, `gemini_used=False`, error recorded in `meta["errors"]` (only for actual exceptions).

- [ ] **Step 1: Write the failing tests**

Append to `webcrawler/tests/test_score.py`:

```python
import json

from core.score import gemini_score, rank


def _gemini_response(entries):
    inner = json.dumps(entries)
    envelope = {"candidates": [{"content": {"parts": [{"text": inner}]}}]}
    return json.dumps(envelope)


def _fake_transport_factory(entries):
    def transport(url, payload, api_key):
        assert api_key == "test-key"
        assert "contents" in payload
        return _gemini_response(entries)
    return transport


def test_gemini_score_parses_batch_response():
    docs = [
        _doc("https://a.com/1", "T1", "body one"),
        _doc("https://a.com/2", "T2", "body two"),
    ]
    transport = _fake_transport_factory([
        {"url": "https://a.com/1", "score": 0.9, "reason": "on topic"},
        {"url": "https://a.com/2", "score": 0.2, "reason": "tangential"},
    ])
    out = gemini_score("my topic", docs, "test-key", transport=transport)
    assert out["https://a.com/1"] == (0.9, "on topic")
    assert out["https://a.com/2"] == (0.2, "tangential")


def test_gemini_score_clamps_values():
    docs = [_doc("https://a.com/1", "T1", "body")]
    transport = _fake_transport_factory([{"url": "https://a.com/1", "score": 7}])
    out = gemini_score("t", docs, "k", transport=transport)
    assert out["https://a.com/1"][0] == 1.0


def test_gemini_score_handles_markdown_fences():
    docs = [_doc("https://a.com/1", "T1", "body")]
    def transport(url, payload, api_key):
        inner = json.dumps([{"url": "https://a.com/1", "score": 0.5, "reason": "ok"}])
        return f"Here you go:\n```json\n{inner}\n```"
    out = gemini_score("t", docs, "k", transport=transport)
    assert out["https://a.com/1"] == (0.5, "ok")


def test_rank_uses_gemini_and_filters_by_min_score():
    docs = [
        _doc("https://a.com/1", "T1", "retrieval augmented generation everything"),
        _doc("https://a.com/2", "T2", "basketball scores today"),
    ]
    transport = _fake_transport_factory([
        {"url": "https://a.com/1", "score": 0.95, "reason": "core"},
        {"url": "https://a.com/2", "score": 0.1, "reason": "off"},
    ])
    kept, meta = rank(docs, "rag", min_score=0.6, api_key="test-key", transport=transport)
    assert meta["gemini_used"] is True
    assert len(kept) == 1
    assert kept[0][0].url == "https://a.com/1"
    assert kept[0][1] == 0.95


def test_rank_falls_back_to_bm25_when_gemini_raises():
    docs = [_doc(f"https://a.com/{i}", f"T{i}", "rag retrieval llm page") for i in range(3)]
    def broken(url, payload, api_key):
        raise RuntimeError("429 quota")
    kept, meta = rank(docs, "rag", api_key="test-key", transport=broken)
    assert meta["gemini_used"] is False
    assert meta["errors"] and "429" in meta["errors"][0]
    assert len(kept) == 3  # fallback keeps ALL bm25 candidates
    assert all(reason == "bm25-fallback" for _, _, reason in kept)


def test_rank_without_gemini_flag_returns_fallback_without_errors():
    docs = [_doc(f"https://a.com/{i}", f"T{i}", "rag page") for i in range(3)]
    kept, meta = rank(docs, "rag", use_gemini=False, api_key=None)
    assert meta["gemini_used"] is False
    assert meta["errors"] == []
    assert len(kept) == 3


def test_rank_empty_docs():
    kept, meta = rank([], "topic")
    assert kept == []
    assert meta["bm25_candidates"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_score.py -v`
Expected: new tests FAIL — `ImportError: cannot import name 'gemini_score'`

- [ ] **Step 3: Implement Gemini scorer + rank**

Append to `webcrawler/core/score.py`:

```python
_API_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent")
_BATCH = 10


def _default_transport(url: str, payload: dict, api_key: str) -> str:
    import httpx
    resp = httpx.post(url, params={"key": api_key}, json=payload, timeout=60.0)
    resp.raise_for_status()
    return resp.text


def _response_text(raw: str) -> str:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(data, dict):
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            return raw
    return raw


def _extract_json(text: str) -> list[dict]:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"no JSON array in response: {text[:200]}")
    return json.loads(text[start:end + 1])


def _build_prompt(topic: str, batch: list[ExtractedContent]) -> dict:
    entries = [
        {"url": d.url, "title": d.title, "snippet": d.text[:500]}
        for d in batch
    ]
    instructions = (
        "You rate web pages for relevance to a topic. Reply with ONLY a JSON array, "
        'no prose, entries like {"url": "...", "score": 0.0, "reason": "short sentence"}. '
        "score ranges from 0.0 (irrelevant) to 1.0 (exactly about the topic)."
    )
    user = f"Topic: {topic}\nPages:\n{json.dumps(entries, ensure_ascii=False)}"
    return {"contents": [{"parts": [{"text": instructions + "\n\n" + user}]}]}


def gemini_score(topic: str, docs: list[ExtractedContent], api_key: str,
                 transport=None) -> dict[str, tuple[float, str]]:
    transport = transport or _default_transport
    out: dict[str, tuple[float, str]] = {}
    for i in range(0, len(docs), _BATCH):
        batch = docs[i:i + _BATCH]
        raw = transport(_API_URL, _build_prompt(topic, batch), api_key)
        for row in _extract_json(_response_text(raw)):
            url = row.get("url")
            if not url:
                continue
            try:
                score = float(row.get("score", 0.0))
            except (TypeError, ValueError):
                score = 0.0
            score = max(0.0, min(1.0, score))
            out[url] = (score, str(row.get("reason", "")))
    return out


def rank(docs: list[ExtractedContent], topic: str, min_score: float = 0.6,
         use_gemini: bool = True, api_key: str | None = None,
         transport=None) -> tuple[list[tuple[ExtractedContent, float, str]], dict]:
    candidates = bm25_filter(docs, topic)
    meta: dict = {"gemini_used": False, "bm25_candidates": len(candidates),
                  "errors": []}
    if not candidates:
        return [], meta

    scores: dict[str, tuple[float, str]] | None = None
    if use_gemini and api_key:
        try:
            scores = gemini_score(topic, [d for d, _ in candidates], api_key,
                                  transport=transport)
            meta["gemini_used"] = True
        except Exception as exc:
            meta["errors"].append(f"gemini: {exc}")

    if scores is None:
        raw = [s for _, s in candidates]
        lo, hi = min(raw), max(raw)
        span = (hi - lo) or 1.0
        fallback = [
            (d, round((s - lo) / span, 3), "bm25-fallback")
            for d, s in candidates
        ]
        return fallback, meta

    ranked = []
    for d, _ in candidates:
        if d.url in scores:
            score, reason = scores[d.url]
        else:
            score, reason = 0.0, "gemini-missing"
        if score >= min_score:
            ranked.append((d, score, reason))
    ranked.sort(key=lambda row: row[1], reverse=True)
    return ranked, meta
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_score.py -v`
Expected: all pass (Task 2 + Task 3 tests)

- [ ] **Step 5: Run full suite**

Run: `python -m pytest tests -v`
Expected: all pass

- [ ] **Step 6: Commit**

```bash
git add webcrawler/core/score.py webcrawler/tests/test_score.py
git commit -m "feat(webcrawler): Gemini batch scorer with BM25 fallback rank()"
```

---

### Task 4: FTS5 index functions — append to `core/store.py`

**Files:**
- Modify: `webcrawler/core/store.py` (append; add `import sqlite3` at top)
- Test: `webcrawler/tests/test_store_fts.py`

**Interfaces:**
- Consumes: nothing new.
- Produces (appended to `core/store.py`):
  - `init_index(db_path: Path) -> None` — creates FTS5 table `docs(title, body, url UNINDEXED, topic UNINDEXED, score UNINDEXED, fetched_at UNINDEXED, reason UNINDEXED)` (idempotent).
  - `index_documents(db_path: Path, topic: str, rows: list[dict]) -> None` — bulk insert; each row = `{"title", "body", "url", "score", "reason", "fetched_at"}`.
  - `search_index(db_path: Path, query: str, topic: str | None = None, limit: int = 20) -> list[dict]` — returns `{"title", "url", "topic", "score", "reason"}` ordered by relevance. Query tokens are quoted and joined with `AND`; empty/sanitized-to-empty query returns `[]`.

- [ ] **Step 1: Write the failing tests**

Create `webcrawler/tests/test_store_fts.py`:

```python
# tests/test_store_fts.py
from pathlib import Path

from core.store import index_documents, init_index, search_index


def _row(i):
    return {
        "title": f"Article {i}",
        "body": "retrieval augmented generation with vector databases" if i == 1
                else "cooking pasta with tomato sauce",
        "url": f"https://x.com/{i}",
        "score": 0.9 if i == 1 else 0.2,
        "reason": "on topic" if i == 1 else "off topic",
        "fetched_at": "2026-09-29T00:00:00+00:00",
    }


def test_init_index_idempotent(tmp_path):
    db = tmp_path / "index.db"
    init_index(db)
    init_index(db)  # second call must not raise
    assert db.exists()


def test_index_and_search(tmp_path):
    db = tmp_path / "index.db"
    init_index(db)
    index_documents(db, "rag", [_row(1), _row(2)])
    hits = search_index(db, "retrieval generation")
    assert hits
    assert hits[0]["url"] == "https://x.com/1"
    assert hits[0]["topic"] == "rag"


def test_search_filters_by_topic(tmp_path):
    db = tmp_path / "index.db"
    index_documents(db, "rag", [_row(1)])
    index_documents(db, "cooking", [_row(2)])
    hits = search_index(db, "pasta", topic="cooking")
    assert [h["url"] for h in hits] == ["https://x.com/2"]
    assert search_index(db, "pasta", topic="rag") == []


def test_search_returns_empty_on_blank_query(tmp_path):
    db = tmp_path / "index.db"
    init_index(db)
    assert search_index(db, "   ") == []
    assert search_index(db, '""') == []


def test_search_quotes_do_not_break_match(tmp_path):
    db = tmp_path / "index.db"
    index_documents(db, "rag", [_row(1)])
    hits = search_index(db, 'retrieval "generation"')
    assert hits
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_store_fts.py -v`
Expected: FAIL — `ImportError: cannot import name 'init_index'`

- [ ] **Step 3: Implement FTS functions**

In `webcrawler/core/store.py`: add `import sqlite3` to the imports at the top, then append at the end of the file:

```python
def init_index(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5("
            "title, body, url UNINDEXED, topic UNINDEXED, score UNINDEXED, "
            "fetched_at UNINDEXED, reason UNINDEXED)"
        )
        conn.commit()
    finally:
        conn.close()


def index_documents(db_path: Path, topic: str, rows: list[dict]) -> None:
    init_index(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executemany(
            "INSERT INTO docs (title, body, url, topic, score, fetched_at, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (r["title"], r["body"], r["url"], topic, r["score"],
                 r["fetched_at"], r.get("reason", ""))
                for r in rows
            ],
        )
        conn.commit()
    finally:
        conn.close()


def search_index(db_path: Path, query: str, topic: str | None = None,
                 limit: int = 20) -> list[dict]:
    init_index(db_path)
    tokens = re.findall(r"\w+", query)
    if not tokens:
        return []
    match = " AND ".join(f'"{t}"' for t in tokens)
    conn = sqlite3.connect(str(db_path))
    try:
        sql = "SELECT title, url, topic, score, reason FROM docs WHERE docs MATCH ?"
        params: list = [match]
        if topic:
            sql += " AND topic=?"
            params.append(topic)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [
            {"title": r[0], "url": r[1], "topic": r[2], "score": r[3], "reason": r[4]}
            for r in rows
        ]
    finally:
        conn.close()
```

(`re` is already imported in `store.py`.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_store_fts.py -v`
Expected: 5 passed

- [ ] **Step 5: Run full suite**

Run: `python -m pytest tests -v`
Expected: all pass (including old `test_store.py` — `save_markdown` untouched)

- [ ] **Step 6: Commit**

```bash
git add webcrawler/core/store.py webcrawler/tests/test_store_fts.py
git commit -m "feat(webcrawler): FTS5 index + search functions in store"
```

---

### Task 5: CLI runner — `runners/topic_crawl.py`

**Files:**
- Create: `webcrawler/runners/topic_crawl.py`
- Test: `webcrawler/tests/test_topic_crawl.py`

**Interfaces:**
- Consumes (exact signatures from earlier tasks): `serp.discover(query, limit, lang, search)`, `score.rank(docs, topic, min_score, use_gemini, api_key, transport)`, `store.save_raw/save_markdown/slugify/init_index/index_documents`, `core.fetch.Fetcher(robots, limiter).fetch(url) -> FetchResult(ok, html, status, via)`, `core.extract.extract(html, url, source) -> ExtractedContent | None`, `core.extract.content_hash(text)`, `UrlDb(path).mark_discovered/mark/is_fetchable/has_content/add_run`.
- Produces: CLI `python runners/topic_crawl.py --topic "..." [--max 300] [--lang en|vi] [--min-score 0.6] [--no-gemini] [--seeds FILE] [--data-dir PATH]` printing manifest JSON to stdout. Checkpoint file `data/md/<slug>/.checkpoint.jsonl` (JSONL of `ExtractedContent.__dict__`), removed after successful run. Outputs: `data/md/<slug>/*.md`, `data/md/<slug>/manifest.json`, `data/index.db`, `data/url_db.sqlite`.

- [ ] **Step 1: Write the failing tests**

Create `webcrawler/tests/test_topic_crawl.py`:

```python
# tests/test_topic_crawl.py
import json
from pathlib import Path

from core.fetch import FetchResult
from core.sources import DiscoveredURL
from core.store import search_index, slugify
from core.url_db import UrlDb
from runners.topic_crawl import build_seeds, crawl_candidates, load_checkpoint, save_outputs


RAG_HTML = (
    "<!doctype html><html><head><title>RAG architecture guide</title></head>"
    "<body><article><h1>RAG architecture guide</h1><p>"
    + "Retrieval augmented generation combines a retriever with an LLM. " * 20
    + "</p></article></body></html>"
)


class FakeFetcher:
    def __init__(self, pages):
        self.pages = pages

    def fetch(self, url):
        html = self.pages.get(url)
        if html:
            return FetchResult(True, html, 200, "fake")
        return FetchResult(False, "", 0, "error")


def _stats():
    return {"discovered": 0, "fetched": 0, "skipped": 0, "failed": 0,
            "blocked": 0, "dup": 0, "written_md": 0}


def test_build_seeds_from_file(tmp_path):
    seeds = tmp_path / "seeds.txt"
    seeds.write_text("# comment\nhttps://a.com/x\n\nhttps://b.com/y\n", encoding="utf-8")
    out = build_seeds("ignored", "en", 10, seeds)
    assert [u.url for u in out] == ["https://a.com/x", "https://b.com/y"]
    assert all(u.source == "seeds" for u in out)


def test_build_seeds_uses_search():
    fake = lambda q, lang="en": [{"href": "https://found.com/p"}]
    out = build_seeds("topic", "en", 10, None, search=fake)
    assert [u.url for u in out] == ["https://found.com/p"]


def test_crawl_checkpoint_and_resume(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = UrlDb(data_dir / "url_db.sqlite")
    ckpt = data_dir / "md" / "t" / ".checkpoint.jsonl"
    seeds = [DiscoveredURL(url="https://a.example/rag", source="seeds"),
             DiscoveredURL(url="https://a.example/dead", source="seeds")]
    fetcher = FakeFetcher({"https://a.example/rag": RAG_HTML})
    stats = _stats()
    crawl_candidates(db, fetcher, data_dir, ckpt, seeds, max_fetch=10, stats=stats)
    assert stats["fetched"] == 1
    assert stats["failed"] == 1
    docs = load_checkpoint(ckpt)
    assert len(docs) == 1
    assert "Retrieval augmented" in docs[0].text
    # resume: already-fetched URL must be skipped next run
    stats2 = _stats()
    crawl_candidates(db, fetcher, data_dir, ckpt, seeds, max_fetch=10, stats=stats2)
    assert stats2["skipped"] == 1  # a.example/rag is 'fetched'
    assert len(load_checkpoint(ckpt)) == 1  # not duplicated
    db.close()


def test_max_fetch_cap(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    db = UrlDb(data_dir / "url_db.sqlite")
    ckpt = data_dir / "md" / "t" / ".checkpoint.jsonl"
    seeds = [DiscoveredURL(url=f"https://a.example/{i}", source="seeds") for i in range(5)]
    fetcher = FakeFetcher({f"https://a.example/{i}": RAG_HTML for i in range(5)})
    stats = _stats()
    crawl_candidates(db, fetcher, data_dir, ckpt, seeds, max_fetch=2, stats=stats)
    assert stats["fetched"] == 2
    db.close()


def test_save_outputs_writes_md_manifest_and_index(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    from core.score import rank
    from core.sources import ExtractedContent
    docs = [ExtractedContent(url="https://a.example/1", source="seeds",
                             title="RAG guide", text="retrieval augmented generation " * 30)]
    kept, meta = rank(docs, "rag", use_gemini=False)
    stats = _stats()
    stats["discovered"] = 1
    stats["fetched"] = 1
    manifest = save_outputs(data_dir, "test topic", kept, meta, stats)
    slug = slugify("test topic")
    assert (data_dir / "md" / slug / "manifest.json").exists()
    assert list((data_dir / "md" / slug).glob("*.md"))
    assert manifest["kept"] == 1
    assert manifest["gemini_used"] is False
    hits = search_index(data_dir / "index.db", "retrieval generation")
    assert hits and hits[0]["topic"] == "test topic"


def test_save_outputs_warns_when_nothing_kept(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    meta = {"gemini_used": False, "bm25_candidates": 0, "errors": []}
    manifest = save_outputs(data_dir, "empty topic", [], meta, _stats())
    assert manifest["warnings"]
    assert (data_dir / "md" / "empty-topic" / "manifest.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_topic_crawl.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'runners.topic_crawl'`

- [ ] **Step 3: Implement the runner**

Create `webcrawler/runners/topic_crawl.py`:

```python
# runners/topic_crawl.py
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.extract import content_hash, extract
from core.fetch import Fetcher
from core.robots import RateLimiter, RobotsCache
from core.score import rank
from core.sources import DiscoveredURL, ExtractedContent
from core.sources.serp import discover as serp_discover
from core.store import (index_documents, init_index, save_markdown, save_raw,
                        slugify)
from core.url_db import UrlDb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MAX_HARD_CAP = 500


def build_seeds(topic: str, lang: str, limit: int, seeds_file: Path | None,
                search=None) -> list[DiscoveredURL]:
    if seeds_file is not None:
        lines = seeds_file.read_text(encoding="utf-8").splitlines()
        urls = [ln.strip() for ln in lines
                if ln.strip() and not ln.startswith("#")]
        return [DiscoveredURL(url=u, source="seeds") for u in urls[:limit]]
    return serp_discover(topic, limit=limit, lang=lang, search=search)


def crawl_candidates(db, fetcher, data_dir: Path, ckpt: Path,
                     seeds: list[DiscoveredURL], max_fetch: int,
                     stats: dict) -> dict:
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    for item in seeds:
        if stats["fetched"] >= max_fetch:
            break
        db.mark_discovered(item.url, item.source, urlparse(item.url).netloc)
        if not db.is_fetchable(item.url):
            stats["skipped"] += 1
            continue
        result = fetcher.fetch(item.url)
        if not result.ok:
            if result.via == "robots":
                db.mark(item.url, "blocked")
                stats["blocked"] += 1
            else:
                db.mark(item.url, "failed")
                stats["failed"] += 1
            continue
        doc = extract(result.html, item.url, item.source)
        if doc is None:
            db.mark(item.url, "failed")
            stats["failed"] += 1
            continue
        c_hash = content_hash(doc.text)
        if db.has_content(c_hash):
            db.mark(item.url, "fetched", c_hash)
            stats["dup"] += 1
            continue
        save_raw(data_dir, item.url, result.html)
        with ckpt.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(doc.__dict__, ensure_ascii=False) + "\n")
        db.mark(item.url, "fetched", c_hash)
        stats["fetched"] += 1
    return stats


def load_checkpoint(ckpt: Path) -> list[ExtractedContent]:
    if not ckpt.exists():
        return []
    docs = []
    for line in ckpt.read_text(encoding="utf-8").splitlines():
        if line.strip():
            docs.append(ExtractedContent(**json.loads(line)))
    return docs


def save_outputs(data_dir: Path, topic: str,
                 kept: list[tuple[ExtractedContent, float, str]],
                 meta: dict, stats: dict) -> dict:
    slug = slugify(topic, "general")
    out_dir = data_dir / "md" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for doc, score, reason in kept:
        save_markdown(data_dir, doc, topic)
        stats["written_md"] += 1
        rows.append({
            "title": doc.title or doc.url,
            "url": doc.url,
            "body": doc.text,
            "score": round(score, 3),
            "reason": reason,
            "fetched_at": doc.fetched_at,
        })
    index_db = data_dir / "index.db"
    init_index(index_db)
    if rows:
        index_documents(index_db, topic, rows)

    warnings = []
    if meta["bm25_candidates"] == 0:
        warnings.append("no pages extracted — check seeds/network")
    elif not kept:
        warnings.append(
            f"0 pages >= min-score after ranking — topic may be too narrow; "
            f"retry with lower --min-score"
        )
    if meta["errors"]:
        warnings.append("gemini failed, BM25 fallback used: "
                        + "; ".join(meta["errors"]))

    manifest = {
        "topic": topic,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "discovered": stats["discovered"],
        "fetched": stats["fetched"],
        "kept": len(kept),
        "skipped": stats["skipped"],
        "gemini_used": meta["gemini_used"],
        "errors": meta["errors"],
        "warnings": warnings,
        "stats": stats,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Topic-driven crawl (scope A)")
    p.add_argument("--topic", required=True, help="topic / research prompt")
    p.add_argument("--max", type=int, default=300, dest="max_pages")
    p.add_argument("--lang", default="en", choices=["en", "vi"])
    p.add_argument("--min-score", type=float, default=0.6)
    p.add_argument("--no-gemini", action="store_true",
                   help="skip Gemini, keep BM25-only ranking")
    p.add_argument("--seeds", type=Path, default=None,
                   help="file with one seed URL per line (bypasses ddgs)")
    p.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = p.parse_args(argv)

    max_pages = min(args.max_pages, MAX_HARD_CAP)
    data_dir = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.topic, "general")
    ckpt = data_dir / "md" / slug / ".checkpoint.jsonl"

    stats = {"discovered": 0, "fetched": 0, "skipped": 0, "failed": 0,
             "blocked": 0, "dup": 0, "written_md": 0}
    started = datetime.now(timezone.utc).isoformat()

    seeds = build_seeds(args.topic, args.lang, max_pages * 2, args.seeds)
    stats["discovered"] = len(seeds)

    db = UrlDb(data_dir / "url_db.sqlite")
    fetcher = Fetcher(RobotsCache(), RateLimiter(min_delay=2.0))
    try:
        crawl_candidates(db, fetcher, data_dir, ckpt, seeds, max_pages, stats)
        docs = load_checkpoint(ckpt)
        api_key = None if args.no_gemini else os.environ.get("GEMINI_API_KEY")
        kept, meta = rank(docs, args.topic, min_score=args.min_score,
                          use_gemini=not args.no_gemini, api_key=api_key)
        manifest = save_outputs(data_dir, args.topic, kept, meta, stats)
        db.add_run("topic_crawl", started, json.dumps(manifest, ensure_ascii=False))
        if ckpt.exists():
            ckpt.unlink()
    finally:
        db.close()

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_topic_crawl.py -v`
Expected: 6 passed

- [ ] **Step 5: Run full suite**

Run: `python -m pytest tests -v`
Expected: all pass

- [ ] **Step 6: CLI smoke (offline, seeds file, no network fetch to ddgs)**

Run:
```powershell
Set-Content -Path "$env:TEMP\smoke_seeds.txt" -Value "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"
python runners/topic_crawl.py --topic "RAG architecture" --max 3 --no-gemini --seeds "$env:TEMP\smoke_seeds.txt" --data-dir "$env:TEMP\wc_smoke"
```
Expected: prints manifest JSON; `kept >= 1` OR `warnings` mentions the reason; files exist under `$env:TEMP\wc_smoke\md\rag-architecture\`.

- [ ] **Step 7: Commit**

```bash
git add webcrawler/runners/topic_crawl.py webcrawler/tests/test_topic_crawl.py
git commit -m "feat(webcrawler): topic_crawl CLI with checkpoint resume + manifest"
```

---

### Task 6: Agent + skill layer

**Files:**
- Create: `agent/web-crawler.md`
- Create: `.opencode/skills/webcrawler/SKILL.md`

**Interfaces:**
- Consumes: CLI from Task 5 (`python runners/topic_crawl.py ...`), `core.store.search_index`.
- Produces: an opencode subagent named `Web Crawler` (frontmatter pattern copied from `agent/trend-researcher.md`: `name`, `description`, `mode: subagent`, `color`) and a skill routing crawl requests to the CLI.

- [ ] **Step 1: Create the agent**

Create `agent/web-crawler.md`:

```markdown
---
name: Web Crawler
description: >-
  Crawls 50-500 quality pages on a topic from a prompt. Runs the webcrawler
  topic_crawl pipeline (ddgs seeds -> fetch -> BM25 -> Gemini -> markdown +
  FTS5 index), reads the manifest, and reports kept pages with scores.
  Triggers: crawl this topic, crawl chủ đề, thu thập trang về, find pages about.
mode: subagent
color: '#2ECC71'
---

# Web Crawler Agent

## Identity
You operate the topic-crawl pipeline in `C:\Opencode\webcrawler`. You never
write your own fetching/scraping code — you only invoke the CLI, monitor it,
and report results.

## Workflow
1. Run the crawler from `C:\Opencode\webcrawler`:
   ```powershell
   python runners/topic_crawl.py --topic "<user topic>" --max 300
   ```
   Flags: `--lang vi|en`, `--min-score 0.6`, `--no-gemini` (offline/BM25-only),
   `--seeds file.txt` (skip search), hard cap `--max 500`.
2. Read `data/md/<topic-slug>/manifest.json` after the run.
3. Report to the user: `kept / fetched / discovered`, `gemini_used`,
   every `warnings`/`errors` entry, and the top 10 kept pages
   (`data/md/<topic-slug>/*.md` frontmatter has `title`, `url`, `score`).
4. If the user wants to query results later, use FTS5:
   ```powershell
   python -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; from core.store import search_index; [print(r) for r in search_index(Path('data/index.db'), 'QUERY')]"
   ```

## Rules
- Respect the 500-page hard cap and robots.txt (enforced by the CLI — never bypass).
- If `manifest.warnings` says 0 pages kept, suggest lowering `--min-score`
  or broadening the topic — do not silently retry with the same arguments.
- If ddgs fails, ask the user for seed URLs and rerun with `--seeds`.
- Never fabricate results: everything you report must come from the manifest
  or the stored markdown files.
```

- [ ] **Step 2: Create the skill**

Create `.opencode/skills/webcrawler/SKILL.md`:

````markdown
---
name: webcrawler
description: >-
  Crawl a topic from a prompt into a local markdown + FTS5 corpus using the
  webcrawler topic_crawl pipeline. Use when the user says "crawl X", "crawl
  chủ đề X", "find/collect pages about X", "thu thập tài liệu về X", or wants
  to search an already-crawled corpus. Free: ddgs seeds, BM25+Gemini ranking,
  no paid API.
---

# Web Crawler Skill

## Run a crawl

Working directory must be `C:\Opencode\webcrawler` (use the `workdir` param).

```powershell
python runners/topic_crawl.py --topic "<topic>" --max 300
```

| Flag | Default | Meaning |
|---|---|---|
| `--max` | 300 | pages to fetch, hard cap 500 |
| `--lang` | en | `vi` for Vietnamese sources |
| `--min-score` | 0.6 | keep threshold (Gemini/BM25-normalized) |
| `--no-gemini` | off | BM25-only, fully offline ranking |
| `--seeds FILE` | — | one URL per line; bypasses ddgs search |
| `--data-dir PATH` | `data` | output root (tests use temp dirs) |

Output: `data/md/<slug>/*.md` (YAML frontmatter: title/url/score/reason),
`data/md/<slug>/manifest.json` (run report), `data/index.db` (FTS5),
`data/url_db.sqlite` (registry + resume state).

## After the crawl

- Always read `manifest.json` first — `kept`, `gemini_used`, `warnings`,
  `errors`. Surface `warnings` to the user verbatim.
- Resume: rerunning the same command skips already-fetched URLs
  (checkpoint + url_db state). A crashed run continues where it stopped.

## Search the corpus (FTS5)

```powershell
python -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; from core.store import search_index; [print(r) for r in search_index(Path('data/index.db'), 'your query', topic='optional-topic')]"
```

## Troubleshooting

- 0 kept → lower `--min-score` or broaden `--topic`; manifest has the reason.
- ddgs rate-limited → rerun with `--seeds seeds.txt`.
- Gemini 429 → automatic BM25 fallback (manifest: `gemini_used: false`);
  no action needed unless quality is too low.
````

- [ ] **Step 3: Verify frontmatter parses and files are in place**

Run:
```powershell
python -c "import pathlib; [print(p, len(p.read_text(encoding='utf-8').splitlines())) for p in [pathlib.Path(r'C:\Opencode\agent\web-crawler.md'), pathlib.Path(r'C:\Opencode\.opencode\skills\webcrawler\SKILL.md')]]"
```
Expected: both paths printed with nonzero line counts.

- [ ] **Step 4: Commit**

```bash
git add agent/web-crawler.md .opencode/skills/webcrawler/SKILL.md
git commit -m "feat(webcrawler): Web Crawler agent + skill"
```

---

### Task 7: End-to-end verification

**Files:** none (verification only; fix bugs found via small commits).

- [ ] **Step 1: Full test suite**

Run (workdir `C:\Opencode\webcrawler`): `python -m pytest tests -v`
Expected: all tests pass.

- [ ] **Step 2: Real network smoke — no Gemini**

Run:
```powershell
python runners/topic_crawl.py --topic "retrieval augmented generation" --max 5 --no-gemini
```
Expected: exits 0, prints manifest with `fetched >= 1`; markdown files in `data/md/retrieval-augmented-generation/`; `index.db` searchable.

- [ ] **Step 3: Real network smoke — with Gemini (optional if quota available)**

Run:
```powershell
$env:GEMINI_API_KEY  # verify it is set
python runners/topic_crawl.py --topic "retrieval augmented generation" --max 5 --min-score 0.5
```
Expected: manifest `gemini_used: true`, `kept >= 1`; if Gemini fails, manifest shows `gemini_used: false` + `errors` — acceptable (fallback path).

- [ ] **Step 4: FTS5 query against real output**

Run:
```powershell
python -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; from core.store import search_index; print(search_index(Path('data/index.db'), 'retrieval'))"
```
Expected: at least one dict with title/url/score.

- [ ] **Step 5: Resume behavior**

Rerun the Step 2 command unchanged.
Expected: manifest shows `skipped >= 1` (previously fetched URLs not refetched), `fetched` grows only with new URLs.

- [ ] **Step 6: Final commit (if any fixes were made)**

```bash
git add -A webcrawler
git commit -m "test(webcrawler): e2e smoke fixes for topic_crawl"
```
(Skip if there is nothing to commit.)
