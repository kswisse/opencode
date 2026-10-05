### Task 2: url_db â€” shared URL registry (TDD)

**Files:**
- Create: `webcrawler/core/url_db.py`
- Test: `webcrawler/tests/test_url_db.py`

**Interfaces:**
- Consumes: nothing.
- Produces (Task 6/8 rely on these exact names):
  - `UrlDb(path: str | Path)` with methods:
    - `is_fetchable(url: str, now: str | None = None) -> bool`
    - `mark_discovered(url: str, source: str, domain: str) -> None`
    - `mark(url: str, status: str, content_hash: str | None = None, next_retry: str | None = None) -> None`
    - `has_content(content_hash: str) -> bool`
    - `add_run(runner: str, started_at: str, stats_json: str) -> None`
    - `close() -> None`
  - status values: `'fetched' | 'failed' | 'blocked'`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_url_db.py
from core.url_db import UrlDb

def make_db(tmp_path):
    return UrlDb(tmp_path / "url_db.sqlite")

def test_new_url_not_fetchable_before_mark_then_fetchable(tmp_path):
    db = make_db(tmp_path)
    assert db.is_fetchable("https://a.com/1") is True
    db.mark_discovered("https://a.com/1", "news", "a.com")
    assert db.is_fetchable("https://a.com/1") is True
    db.mark("https://a.com/1", "fetched")
    assert db.is_fetchable("https://a.com/1") is False
    db.close()

def test_failed_url_blocked_until_next_retry(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/2", "news", "a.com")
    db.mark("https://a.com/2", "failed", next_retry="2026-09-27T00:00:00+00:00")
    assert db.is_fetchable("https://a.com/2", now="2026-09-26T00:00:00+00:00") is False
    assert db.is_fetchable("https://a.com/2", now="2026-09-27T01:00:00+00:00") is True
    db.close()

def test_blocked_never_fetchable(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/3", "news", "a.com")
    db.mark("https://a.com/3", "blocked")
    assert db.is_fetchable("https://a.com/3", now="2099-01-01T00:00:00+00:00") is False
    db.close()

def test_content_hash_dedup(tmp_path):
    db = make_db(tmp_path)
    assert db.has_content("abc123") is False
    db.mark_discovered("https://a.com/4", "news", "a.com")
    db.mark("https://a.com/4", "fetched", content_hash="abc123")
    assert db.has_content("abc123") is True
    db.close()

def test_double_discover_keeps_single_row(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/5", "news", "a.com")
    db.mark_discovered("https://a.com/5", "serp", "a.com")
    cur = db.conn.execute("SELECT COUNT(*) FROM urls WHERE url=?", ("https://a.com/5",))
    assert cur.fetchone()[0] == 1
    db.close()
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_url_db.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.url_db'`.

- [ ] **Step 3: Implement core/url_db.py**

```python
# core/url_db.py
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS urls (
  url TEXT PRIMARY KEY,
  source TEXT,
  status TEXT DEFAULT 'pending',
  content_hash TEXT,
  first_seen TEXT,
  last_crawled TEXT,
  next_retry TEXT,
  domain TEXT
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  runner TEXT,
  started_at TEXT,
  finished_at TEXT,
  stats_json TEXT
);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class UrlDb:
    def __init__(self, path):
        self.conn = sqlite3.connect(str(path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    def is_fetchable(self, url: str, now: str | None = None) -> bool:
        now = now or _utcnow()
        row = self.conn.execute(
            "SELECT status, next_retry FROM urls WHERE url=?", (url,)
        ).fetchone()
        if row is None:
            return True
        status, next_retry = row
        if status == "fetched":
            return False
        if status == "blocked":
            return False
        if status == "failed" and next_retry and next_retry > now:
            return False
        return True

    def mark_discovered(self, url: str, source: str, domain: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO urls (url, source, first_seen, domain) VALUES (?, ?, ?, ?)",
            (url, source, _utcnow(), domain),
        )
        self.conn.commit()

    def mark(self, url: str, status: str, content_hash: str | None = None,
             next_retry: str | None = None) -> None:
        now = _utcnow()
        self.conn.execute(
            "UPDATE urls SET status=?, content_hash=?, "
            "last_crawled=CASE WHEN ?='fetched' THEN ? ELSE last_crawled END, "
            "next_retry=? WHERE url=?",
            (status, content_hash, status, now, next_retry, url),
        )
        self.conn.commit()

    def has_content(self, content_hash: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM urls WHERE content_hash=? AND status='fetched' LIMIT 1",
            (content_hash,),
        ).fetchone()
        return row is not None

    def add_run(self, runner: str, started_at: str, stats_json: str) -> None:
        self.conn.execute(
            "INSERT INTO runs (runner, started_at, finished_at, stats_json) VALUES (?, ?, ?, ?)",
            (runner, started_at, _utcnow(), stats_json),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_url_db.py -q`
Expected: `5 passed`.

- [ ] **Step 5: Commit**

```powershell
git add webcrawler/core/url_db.py webcrawler/tests/test_url_db.py
git commit -m "feat(webcrawler): url_db shared registry with dedup + retry states"
```

---


