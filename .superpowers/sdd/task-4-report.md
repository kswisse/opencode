# Task 4 Report: extract — HTML to content + content hash (TDD)

## What I implemented

- `webcrawler/tests/fixtures/sample_page.html` — brief Step 1 fixture verbatim.
- `webcrawler/tests/test_extract.py` — 3 failing tests verbatim (brief Step 2).
- `webcrawler/core/sources/__init__.py` — populated (was empty from Task 1) with `DiscoveredURL` and `ExtractedContent` dataclasses, verbatim brief Step 4.
- `webcrawler/core/extract.py` — `content_hash(text)` (sha256 of whitespace-collapsed, lowercased text) and `extract(html, url, source) -> ExtractedContent | None` wrapping trafilatura, verbatim brief Step 4.

Interface note: the task-context prose says `extract(html, url) -> dict | None` with a `links` key, but the brief's code (which the task declares gospel: "COMPLETE test code and implementation code to use verbatim") specifies `extract(html, url, source) -> ExtractedContent | None` with no `links`. I followed the brief exactly. Task 6/7 must import the 3-arg form.

## TDD Evidence

### RED

Command (from `C:\Opencode\webcrawler`):

```
python -m pytest tests/test_extract.py -q
```

Output:

```
=================================== ERRORS ====================================
___________________________ ERROR collecting tests/test_extract.py ___________________________
ImportError while importing test module 'C:\Opencode\webcrawler\tests\test_extract.py'.
...
tests\test_extract.py:3: in <module>
    from core.extract import extract, content_hash
E   ModuleNotFoundError: No module named 'core.extract'
=========================== short test summary info ===========================
ERROR tests/test_extract.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.36s
```

Why expected: brief Step 3 predicts exactly `ModuleNotFoundError: No module named 'core.extract'` — `core/extract.py` did not exist yet. Failure confirmed.

### GREEN

Command (from `C:\Opencode\webcrawler`), after implementing brief Step 4:

```
python -m pytest tests/test_extract.py -q
```

Output:

```
...                                                                      [100%]
3 passed in 1.72s
```

Matches brief Step 5 prediction: `3 passed`.

## Full-suite result

```
python -m pytest -q   # from C:\Opencode\webcrawler
.............                                                            [100%]
13 passed in 1.83s
```

**ACTUAL: 13 passed** (10 pre-existing + 3 new task-4 tests) — exactly the expected 10 + 3.

## Files changed

- `webcrawler/tests/fixtures/sample_page.html` (new)
- `webcrawler/tests/test_extract.py` (new)
- `webcrawler/core/sources/__init__.py` (modified — dataclasses added)
- `webcrawler/core/extract.py` (new)

## Commit

- `6eeb361` `feat(webcrawler): extract via trafilatura + content hash` on `feature/webcrawler-phase1`, staged from `C:\Opencode` with only the 4 `webcrawler/` paths (verified: `4 files changed, 95 insertions(+)`).

## Self-review findings

- Code transcribed verbatim from brief Steps 1/2/4; no deviations, comments in English.
- RED failure mode matches brief prediction exactly; GREEN count matches (3 passed).
- Full suite green at 13; no regressions in `test_url_db.py` / `test_robots.py`.
- Only the 4 intended `webcrawler/` paths staged; the repo's large unrelated dirty working tree (`.opencode/`, `ai-workforce-platform/`, etc.) was left untouched.

## Concerns

- **Brief vs. task-prose interface mismatch** (`dict` + `links` vs. `ExtractedContent` + `source` arg): brief wins per instructions, but Tasks 6/7 briefs must be checked for consistency before they import this function.
- `trafilatura.extract` output for a given page can vary across trafilatura versions (metadata fields like `date`/`author` may be None); tests don't pin the version — acceptable for Phase 1 since tests only assert url/source/text/title.
- Working tree contains many unrelated uncommitted changes; any future commit must keep staging scoped to `webcrawler/` paths.
