# Task 2 Report: BM25 pre-filter — core/score.py (part 1)

**Status:** DONE
**Commit:** `06ac4e9` feat(webcrawler): BM25 pre-filter with fixed keep rule

## What I implemented

- `webcrawler/tests/test_score.py` — the 6 tests from the plan's Task 2 brief, verbatim (verified programmatically: test file matches the plan's code fence byte-for-byte).
- `webcrawler/core/score.py` — `tokenize()` (lowercase Unicode `\w+` tokens) and `bm25_filter(docs, topic, keep_ratio=0.4, min_keep=20)` with the fixed keep rule (all docs when `len <= 50`, else `max(int(len * keep_ratio), min_keep)`), sorted by BM25 score descending. No Gemini code, no `rank()` — Task 3's scope only.

## Brief discrepancy (important)

`C:\Opencode\.superpowers\sdd\task-2-brief.md` does **not** contain this task's brief — it holds Phase 1's stale `url_db` Task 2 content (and HEAD's version holds an unrelated "Shared Models Package" brief). The authoritative Task 2 brief — matching my dispatch exactly (files, interfaces, keep rule, test code, commit message) — was taken from `git show HEAD:docs/superpowers/plans/2026-09-29-webcrawler-topic-crawl-agent.md`, section `### Task 2: BM25 pre-filter — core/score.py (part 1)`.

## TDD evidence

**RED** — `python -m pytest tests/test_score.py -v` (workdir `C:\Opencode\webcrawler`):

```
tests\test_score.py:3: in <module>
    from core.score import bm25_filter, tokenize
E   ModuleNotFoundError: No module named 'core.score'
============================== 1 error in 0.69s ===============================
```

**Implementation applied, first GREEN attempt FAILED** one mandated assertion:

```
test_bm25_orders_relevant_docs_first — AssertionError:
  At index 0 diff: 'https://x/cooking' != 'https://x/rag1'
1 failed, 5 passed
```

**Root cause (diagnosed, not papered over):** in the 4-doc test corpus the query terms `rag/retrieval/llm` appear in exactly 2 of 4 docs, so `rank_bm25`'s Okapi idf = `log(2.5) − log(2.5)` = **exactly 0**. `BM25Okapi._calc_idf` only floors *negative* idf to `epsilon·avg_idf`; zero stays zero → all four scores are 0 → stable sort preserves input order (cooking first).

**Fix — implementation, not assertions:** `BM25Okapi` → `BM25L` in `core/score.py`. BM25L's idf is `log(N+1) − log(df+0.5)`, strictly positive for all `df ≤ N`, so document frequency always discriminates. Single-class swap; keep rule, scoring formula, and every test assertion untouched.

**GREEN** — `python -m pytest tests/test_score.py -v`:

```
tests/test_score.py::test_tokenize_lowercases_and_splits PASSED
tests/test_score.py::test_tokenize_keeps_vietnamese_words PASSED
tests/test_score.py::test_bm25_empty_input PASSED
tests/test_score.py::test_bm25_orders_relevant_docs_first PASSED
tests/test_score.py::test_bm25_applies_ratio_above_50_docs PASSED
tests/test_score.py::test_bm25_single_doc_returns_it PASSED
============================== 6 passed in 0.49s ==============================
```

**Full suite** — `python -m pytest -v` (workdir `C:\Opencode\webcrawler`): **33 passed** + 2 collection errors (`tests/test_extract.py`, `tests/test_research_crawl.py`) that are **pre-existing**: identical failure occurred at baseline (before any of my files existed), caused by the OS Application Control policy blocking `lxml\sax.cp312-win_amd64.pyd` (trafilatura → justext → `lxml.sax` import chain). `import lxml.etree` works; only `lxml.sax` is blocked. Not caused by this change; no test I added or own is affected. Excluding those two environmentally-blocked modules: `33 passed in 0.91s`.

## Files changed

Exactly the two allowed files, committed alone:

```
06ac4e9 feat(webcrawler): BM25 pre-filter with fixed keep rule
 webcrawler/core/score.py       | 30 ++++++++++++++++++++++++++++
 webcrawler/tests/test_score.py | 47 ++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 77 insertions(+)
```

Verified `git show --stat HEAD` shows only these two paths; no `git add -A`. Pre-existing dirty state (`webcrawler/core/sources/serp.py` deleted, `webcrawler/tests/test_serp.py` deleted, `webcrawler/requirements.txt` modified, plus unrelated `.superpowers/sdd/*` and other-project files) was left unstaged and untouched.

## Self-review findings

- **Test fidelity:** programmatic byte-comparison against the plan's fenced test block → `TEST VERBATIM MATCH`.
- **Impl deviation from plan:** exactly one intentional delta — `BM25Okapi` → `BM25L` (2 lines), plus keeping the plan's `import json` / `import os` header. `json` is required by Task 3's append (`json.loads` in `_response_text`, no import of its own in the appended block), so removing it would break Task 3; `os` is plan-verbatim (unused now, used by runners elsewhere in the plan).
- **Interface conformance:** signatures, defaults, keep rule, empty-input behavior, and `<= 2 docs → [(d, 1.0)]` shortcut all match the brief exactly.
- **Scope:** no Gemini, no `rank()` — Task 3 can append cleanly to this file.
- **Commit hygiene:** message is the plan's mandated `feat(webcrawler): BM25 pre-filter with fixed keep rule`.

## Concerns

1. **Stale brief file:** `.superpowers/sdd/task-2-brief.md` holds the wrong task's content (Phase 1 url_db). Orchestrator should refresh it for subsequent tasks or the next subagents will read the wrong requirements.
2. **Plan's implementation fails its own mandated test:** the plan specifies `BM25Okapi`, which cannot pass `test_bm25_orders_relevant_docs_first` (zero-idf tie documented above). I fixed by swapping to `BM25L` per dispatch instructions ("fix the implementation first"); assertions were not weakened. Task 3+ implementers reading the plan will hit the same trap — the committed `core/score.py` (BM25L) is the correct base.
3. **Pre-existing worktree damage (not mine):** `webcrawler/core/sources/serp.py` and `webcrawler/tests/test_serp.py` are deleted in the worktree (uncommitted; both exist at HEAD), and `webcrawler/requirements.txt` has `ddgs>=9.0` / `rank-bm25>=0.2.2` stripped. Serp tests therefore do not run in the full suite. Left untouched per file-scope rules; someone should restore or intentionally discard these before the next commit.
4. **Environment:** Application Control policy blocks `lxml.sax`, so `test_extract.py` / `test_research_crawl.py` cannot be collected on this machine (pre-existing, Phase 1 tests were green under a permissive policy).
