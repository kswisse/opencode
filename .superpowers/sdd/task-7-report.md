# Task 7 Report: news RSS connector (TDD)

## Status: DONE

## What was implemented

`webcrawler/core/sources/news.py` (code verbatim from brief Step 4):

- `DEFAULT_FEEDS: list[str]` — 4 public HTTPS RSS seeds (hnrss, BBC, Guardian, Ars Technica).
- `parse_feed(xml_text: str, source: str = "news") -> list[DiscoveredURL]` — pure: `feedparser.parse`, keeps entries with a `link`, wraps each as `DiscoveredURL(url, source)`; no network.
- `discover(feed_url: str, limit: int = 50, fetch_text=None) -> list[DiscoveredURL]` — injectable fetch (default: `httpx.get` with 15 s timeout, redirects, `webcrawler/0.1` UA, `raise_for_status`), pipes through `parse_feed`, truncates to `limit`. `discover` is public for Task 8's runner.

Supporting files (verbatim brief Steps 1–2):
- `tests/fixtures/sample_feed.xml` — 3-item RSS 2.0 fixture (first/second/third article links).
- `tests/test_news.py` — 4 tests: parse returns 3 discovered URLs with `source == "news"`; all items present (limiting is discover's job); discover uses injected fetcher + applies limit; `DEFAULT_FEEDS` non-empty and all `https://`.

Tests never touch the network: `parse_feed` reads a local fixture string; `discover` is called with a `fake_fetch` that asserts the URL and returns the fixture text.

## TDD Evidence

**RED** — command from `C:\Opencode\webcrawler`:

```
python -m pytest tests/test_news.py -q
```

Output:

```
=================================== ERRORS ====================================
_____________________ ERROR collecting tests/test_news.py _____________________
ImportError while importing test module 'C:\Opencode\webcrawler\tests\test_news.py'.
...
tests\test_news.py:3: in <module>
    from core.sources.news import parse_feed, discover, DEFAULT_FEEDS
E   ModuleNotFoundError: No module named 'core.sources.news'
=========================== short test summary info ===========================
ERROR tests/test_news.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.63s
```

Expected failure exactly as brief Step 3 predicted (`ModuleNotFoundError: No module named 'core.sources.news'`) — module did not exist yet.

**GREEN** — after writing `core/sources/news.py`:

```
python -m pytest tests/test_news.py -q
....                                                                         [100%]
4 passed in 0.69s
```

Matches brief Step 5's predicted `4 passed`.

**Full suite** (`python -m pytest -q`, from `C:\Opencode\webcrawler`):

```
...........................                                              [100%]
27 passed in 1.87s
```

ACTUAL: **27 passed** (23 pre-existing + 4 new task-7 tests), 0 failed.

**Smoke test** (brief Step 6, real feed, manual — not part of the suite):

```
python -c "from core.sources.news import discover; r=discover('https://hnrss.org/newest', limit=3); print(len(r), r[0].url)"
3 https://alphapublish.com/
```

Returned 3 items with a real URL as predicted.

## Files changed

- Created `webcrawler/core/sources/news.py` (32 lines)
- Created `webcrawler/tests/test_news.py` (28 lines)
- Created `webcrawler/tests/fixtures/sample_feed.xml` (24 lines)

## Commit

From `C:\Opencode`, staging only those 3 `webcrawler/` paths:

```
fcf49d0 feat(webcrawler): news RSS connector with injectable fetch
 3 files changed, 84 insertions(+)
```

## Self-review findings

- Code and tests transcribed verbatim from the brief; only the two brief-provided header comments, English throughout.
- `discover`'s `if fetch_text is None: def fetch_text(...)` shadowing works: the parameter initializes the local, and the `def` only rebinds when no fetcher was injected (proven by the injected-fetch test passing).
- `parse_feed` skips entries without a `link` instead of emitting empty URLs; `source` defaults to `"news"` as the interface requires.
- Limit applied only in `discover` (`items[:limit]`), matching the test named `..._limit_is_discover_concern`.
- `git status -- webcrawler/` clean after commit; commit contains exactly the 3 intended files (other dirty paths in the repo left untouched).
- Dependency check: `feedparser 6.0.14` and `httpx 0.28.1` present in system Python 3.12, both already in `requirements.txt` — no venv, no new installs.

## Concerns

- None blocking. Note: `.superpowers/sdd/task-7-report.md` previously held a stale report from an unrelated project (claim extraction); this file overwrites it as instructed by the task.
- The default (non-injected) `discover` path performs real HTTP; tests never exercise it, so the suite stays offline. Robot/politeness gating is Task 8's runner concern, not this connector's.
