# Task 5 Report: store — raw + markdown output (TDD)

## What you implemented
Created `webcrawler/core/store.py` and `webcrawler/tests/test_store.py` verbatim from brief Step 1 / Step 3:

- `slugify(text, fallback)` — lowercases, replaces non-alphanumerics with `-`, strips edges, caps at 80 chars, falls back to `fallback`.
- `save_raw(data_dir, url, html) -> Path` — writes HTML to `data/raw/<domain>/<sha1(url)>.html` (port `:` → `_`, `mkdir(parents=True)`), returns path.
- `save_markdown(data_dir, doc: ExtractedContent, topic) -> Path` — writes `data/md/<slug(topic)>/<slug(title)>.md` with YAML frontmatter (`title`, `url`, `source`, `fetched_at`, optional `published`/`author`), body = `doc.text`, returns path.

Stdlib only: `hashlib`, `re`, `pathlib`, `urllib.parse`. English comments only (file headers).

## TDD Evidence

### RED (Step 1–2)
Command (from `C:\Opencode\webcrawler`):
```
python -m pytest tests/test_store.py -q
```
Output:
```
=================================== ERRORS ====================================
____________________ ERROR collecting tests/test_store.py _____________________
ImportError while importing test module '...\tests\test_store.py'.
tests\test_store.py:3: in <module>
    from core.store import save_raw, save_markdown
E   ModuleNotFoundError: No module named 'core.store'
=========================== short test summary info ===========================
ERROR tests/test_store.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.59s
```
Expected failure per brief Step 2: `ModuleNotFoundError: No module named 'core.store'` — exact match (module did not exist yet; tests written first).

### GREEN (Step 3–4)
After writing `core/store.py`:
```
python -m pytest tests/test_store.py -q
```
Output:
```
...                                                                      [100%]
3 passed in 0.51s
```
Matches brief's predicted `3 passed`.

### Full suite (Step 5 of task instructions)
```
python -m pytest -q
```
Output:
```
................                                                         [100%]
16 passed in 1.95s
```
**ACTUAL: 16 passed** (13 prior + 3 new task-5 tests), 0 failed.

## Files changed
- `webcrawler/tests/test_store.py` (new, 3 tests, verbatim from brief)
- `webcrawler/core/store.py` (new, verbatim from brief)

## Commit
From `C:\Opencode`, staged only the two `webcrawler/` paths (repo has unrelated dirt elsewhere; pathspec-limited commit used):
```
c17e2f6 feat(webcrawler): store raw html + frontmattered markdown
2 files changed, 78 insertions(+)
```

## Self-review findings
- Test and implementation code transcribed verbatim from the brief; no deviations.
- No third-party imports; Python 3.12 system interpreter; no venv.
- `slugify` fallback covers empty/whitespace titles; `save_raw` covers empty netloc (`"unknown"`); filename collisions overwrite deterministically (same URL → same sha1, idempotent).
- Frontmatter values are interpolated raw — titles containing `:` or newlines would produce invalid YAML. Acceptable for Phase 1 scope; brief dictates the format.
- Commit touched only the 2 intended files; no unrelated paths staged.

## Concerns
- **Interface mismatch with task prompt:** the task prompt describes a content-addressed `Store(root)` with `put(content_hash, text)` / `get(content_hash)` sharded by hash prefix, but the brief (declared authoritative requirements, "use verbatim") specifies `save_raw` / `save_markdown`. I implemented the brief. If Task 6/8 expect the `Store` API, the orchestrator should reconcile before those tasks run.
- `save_markdown` writes `data/md/<topic-slug>/…`, not content-addressed; raw HTML is sha1-of-URL, not hash-of-content. Matches brief, but does not satisfy "content-addressed" wording of the prompt.

## Fix Round 1

Two reviewed findings (F1 path traversal, F2 unescaped YAML frontmatter), approved by the human owner; fixed TDD-style (regression tests written first, watched fail, then fixed).

### What changed
- `webcrawler/core/store.py`
  - F1: new `_safe_domain(netloc)` helper used by `save_raw` � keeps `replace(":", "_")`, then falls back to `"unknown"` when the netloc is empty, all dots (`.`, `..`, `...`), or contains `/` or `\` (so `urlparse("https://..\\../evil").netloc == "..\\.."` can no longer escape `data/raw/`).
  - F2: new `_yaml_value(value)` helper used for every frontmatter field � double-quotes and escapes (`\` ? `\\`, `"` ? `\"`, newline ? `\n`) when the value contains `": "`, ends with `:`, contains `"` or a newline, or has edge whitespace; safe values (e.g. `https://blog.example.com/posts/1`) stay unquoted plain scalars so existing assertions still pass.
- `webcrawler/tests/test_store.py`: added 2 regression tests � `test_save_raw_neutralizes_path_traversal` (path resolves inside `tmp_path` via `is_relative_to`, file exists there) and `test_save_markdown_escapes_yaml_title` (title `Hello: World "quoted"\nline2` ? line 1 starts with `title: "`, escaped value present, exactly two `---` fence lines).
- `docs/superpowers/plans/2026-09-26-webcrawler-phase1.md`: Task 5 Step 3 sample code replaced with the fixed `_safe_domain` + `_yaml_value` versions; the 2 regression tests appended to Step 1's test block; Step 4 expected count updated `3 passed` ? `5 passed`.

### RED (before fix)
```
python -m pytest tests/test_store.py -q
2 failed, 3 passed in 0.56s
```
- `test_save_raw_neutralizes_path_traversal`: `assert resolved.is_relative_to(tmp_path)` ? False (file written outside `tmp_path`).
- `test_save_markdown_escapes_yaml_title`: `lines[1]` was `title: Hello: World "quoted"` (unquoted, split across lines).

### GREEN (after fix)
```
python -m pytest tests/test_store.py -q
.....                                                                      [100%]
5 passed in 0.51s
```

### Full suite
```
python -m pytest -q
..................                                                         [100%]
18 passed in 1.79s
```
