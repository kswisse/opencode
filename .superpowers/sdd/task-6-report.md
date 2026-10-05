# Task 6 Report: Fetcher (TDD)

## What I implemented

- `webcrawler/tests/test_fetch.py` — 5 tests transcribed verbatim from brief Step 1 (success path, retry-then-succeed, retries-exhausted, robots short-circuit, non-2xx failure keeps status).
- `webcrawler/core/fetch.py` — transcribed verbatim from brief Step 3:
  - `FetchResult(ok, html, status, via)` dataclass
  - `Fetcher(robots, limiter, transport=None, retries=3, backoff=1.5)` with `fetch(url) -> FetchResult`
  - `default_transport` (scrapling-first when importable, httpx fallback), `_httpx_transport`, `_scrapling_transport`
  - robots gate returns `FetchResult(False, "", 0, "robots")` before any transport call
  - per-attempt `limiter.wait(domain)` (domain = `httpx.URL(url).host`), exponential-ish backoff `backoff * (attempt + 1)` between attempts
  - success = `200 <= status < 300` **and** non-empty html; otherwise returns `(False, "", last_status, via)` after `retries` attempts

No other modules touched (robots/extract/store/url_db contract notes respected: `can_fetch`, `wait(domain)` used as-is).

## TDD Evidence

**RED** — `python -m pytest tests/test_fetch.py -q` (run from `C:\Opencode\webcrawler`):

```
=================================== ERRORS ====================================
____________________ ERROR collecting tests/test_fetch.py _____________________
ImportError while importing test module 'C:\Opencode\webcrawler\tests\test_fetch.py'.
...
tests\test_fetch.py:2: in <module>
    from core.fetch import Fetcher, FetchResult
E   ModuleNotFoundError: No module named 'core.fetch'
=========================== short test summary info ===========================
ERROR tests/test_fetch.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.66s
```

Expected failure exactly as brief Step 2 predicted (`ModuleNotFoundError: No module named 'core.fetch'`) — tests written first, implementation did not exist yet.

**GREEN** — after creating `core/fetch.py`, same command:

```
.....                                                                    [100%]
5 passed in 0.54s
```

Matches brief Step 4 prediction: `5 passed`.

## Step 5 smoke test (real transport)

`python -c "from core.fetch import default_transport; s,h=default_transport('https://example.com/'); print(s, len(h))"`

```
200 559
```

No exception; scrapling not installed → httpx fallback path (acceptable per brief). Tests themselves never touch the network (transport fully injected).

## Files changed

- `webcrawler/core/fetch.py` (new, +72)
- `webcrawler/tests/test_fetch.py` (new, +44)

## Full suite

`python -m pytest -q` → **23 passed in 1.71s** (actual: 18 pre-existing + 5 new = 23; matches expectation).

## Commit

- `7eeeec8` `feat(webcrawler): fetcher with retries, robots gate, pluggable transport` — staged only `webcrawler/core/fetch.py` + `webcrawler/tests/test_fetch.py`, message exactly as brief Step 6 (Step 5 in task instructions). Working tree for `webcrawler/` clean after commit.

## Self-review findings

1. **Interface mismatch vs. my task-prompt context (BRIEF WINS):** the orchestrator's context paragraph described `Fetcher(robots, limiter, timeout=10.0)` with `.fetch(url, source)` that also does `save_raw`/`extract`/url_db-marking. The brief (my stated requirements, verbatim) specifies `transport/retries/backoff` and `fetch(url)` only — and Task 8's brief (`task-8-brief.md`) constructs `Fetcher(..., transport=transport, backoff=0.0)` and calls `fetcher.fetch(item.url)`, with the runner doing extract/save/mark itself. I followed the brief verbatim; the two are consistent with each other.
2. `via` semantics: injected transport → `"transport"`, default transport → `"scrapling"` (no exception), exception → `"error"`, robots → `"robots"`. Task 8's runner only branches on `via == "robots"`, so this is safe.
3. Non-2xx-but-2xx-like edge: html required in addition to status for success (e.g. a 200 with empty body retries, then fails with status 200) — brief behavior, tests cover empty body on 500/404 paths.
4. Backoff sleeps `backoff*(attempt+1)` between attempts; all tests pass `backoff=0.0` so no test sleeps.
5. `retries=0` would return `FetchResult(False, "", 0, "transport")` — not tested, not required by brief; harmless default never used.

## Concerns

- None blocking. Optional note for Task 8: if `runners/research_crawl.py` ever passes `transport=None` in unit tests it would hit the real network — Task 8's brief already injects `transport`, so fine.
