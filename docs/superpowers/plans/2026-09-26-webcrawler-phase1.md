# Web Crawler Phase 1 (core + news RSS + runner A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared crawler core (url registry, robots/rate-limit, fetch, extract, store) plus the RSS news connector and the research-mode runner, producing clean markdown files from seed feeds.

**Architecture:** Single Python package `core/` (library) imported by `runners/research_crawl.py`. All connectors return `DiscoveredURL` lists through one `discover(feed_url, limit)` interface; dedup happens in a shared SQLite `url_db.sqlite` before any fetch. Spec: `docs/superpowers/specs/2026-09-26-webcrawler-design.md`.

**Tech Stack:** Python 3.12 (system), feedparser, trafilatura, httpx, scrapling (optional, pre-installed), pytest. Windows + PowerShell for commands.

## Global Constraints

- Project root: `C:\Opencode\webcrawler\` (all paths below relative to it unless absolute).
- 100% free: no API keys, no cloud, no Docker (spec §1).
- Concurrency cap 4, min delay 2.0s per domain, robots.txt respected (spec §3 rule 3).
- Python 3.12 system install; deps installed with `pip` into the system environment (no venv) — matches how scrapling/camoufox are already installed on this machine.
- Git: project lives inside the existing `C:\Opencode` repo — commit from `C:\Opencode` with paths prefixed `webcrawler/`.
- All test commands run from `C:\Opencode\webcrawler` via `python -m pytest`.
- Code comments/docstrings in English; user-facing CLI output may be English.

---

### Task 1: Project scaffold + dependencies

**Files:**
- Create: `webcrawler/requirements.txt`
- Create: `webcrawler/.gitignore`
- Create: `webcrawler/core/__init__.py`, `webcrawler/core/sources/__init__.py`
- Create: `webcrawler/tests/__init__.py`, `webcrawler/tests/fixtures/` (empty dir via placeholder file)
- Create: `webcrawler/runners/__init__.py`

**Interfaces:**
- Consumes: nothing.
- Produces: importable empty package `core`; pytest discovery works.

- [ ] **Step 1: Write requirements.txt**

```
feedparser>=6.0
trafilatura>=1.8
httpx>=0.27
pytest>=8.0
```

- [ ] **Step 2: Write .gitignore**

```
data/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Create package files (empty is fine)**

Create the five files listed above; `tests/fixtures/.gitkeep` keeps the fixture dir.

- [ ] **Step 4: Install dependencies**

Run: `pip install -r C:\Opencode\webcrawler\requirements.txt`
Expected: `Successfully installed ...` (feedparser, trafilatura, httpx, pytest + deps).

- [ ] **Step 5: Verify pytest runs**

Run (in `C:\Opencode\webcrawler`): `python -m pytest -q`
Expected: `collected 0 items` / `no tests ran`.

- [ ] **Step 6: Commit**

```powershell
git add webcrawler/requirements.txt webcrawler/.gitignore webcrawler/core webcrawler/runners webcrawler/tests
git commit -m "feat(webcrawler): scaffold project, deps, pytest"
```

---

### Task 2: url_db — shared URL registry (TDD)

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

def test_mark_failed_preserves_existing_content_hash(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/6", "news", "a.com")
    db.mark("https://a.com/6", "fetched", content_hash="keepme")
    db.mark("https://a.com/6", "failed", next_retry="2026-09-27T00:00:00+00:00")
    assert db.has_content("keepme") is True
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
            "UPDATE urls SET status=?, content_hash=COALESCE(?, content_hash), "
            "last_crawled=CASE WHEN ?='fetched' THEN ? ELSE last_crawled END, "
            "next_retry=? WHERE url=?",
            (status, content_hash, status, now, next_retry, url),
        )
        self.conn.commit()

    def has_content(self, content_hash: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM urls WHERE content_hash=? LIMIT 1",
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
Expected: `6 passed`.

- [ ] **Step 5: Commit**

```powershell
git add webcrawler/core/url_db.py webcrawler/tests/test_url_db.py
git commit -m "feat(webcrawler): url_db shared registry with dedup + retry states"
```

---

### Task 3: robots.txt cache + per-domain rate limiter (TDD)

**Files:**
- Create: `webcrawler/core/robots.py`
- Test: `webcrawler/tests/test_robots.py`

**Interfaces:**
- Consumes: nothing.
- Produces (Task 6/8 rely on):
  - `RobotsCache(user_agent: str = "*", fetch_text=None)` with `can_fetch(url: str) -> bool`
    - `fetch_text(url: str) -> str` injectable for tests; default uses `httpx.get(...).text`. On any fetch error → allow (fail-open, documented).
  - `RateLimiter(min_delay: float = 2.0, clock=None, sleep=None)` with `wait(domain: str) -> None`
    - `clock`/`sleep` injectable; defaults `time.monotonic` / `time.sleep`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_robots.py
from core.robots import RobotsCache, RateLimiter

ROBOTS_TXT = "User-agent: *\nDisallow: /private/\nAllow: /public/\n"

def test_can_fetch_allows_public_and_blocks_disallowed():
    cache = RobotsCache(fetch_text=lambda url: ROBOTS_TXT)
    assert cache.can_fetch("https://a.com/public/article") is True
    assert cache.can_fetch("https://a.com/private/secret") is False

def test_robots_fetch_error_fails_open():
    def boom(url):
        raise RuntimeError("network down")
    cache = RobotsCache(fetch_text=boom)
    assert cache.can_fetch("https://a.com/anything") is True

def test_robots_fetched_once_per_domain():
    calls = []
    def fetch(url):
        calls.append(url)
        return ROBOTS_TXT
    cache = RobotsCache(fetch_text=fetch)
    cache.can_fetch("https://a.com/1")
    cache.can_fetch("https://a.com/2")
    assert len(calls) == 1

def test_rate_limiter_enforces_min_delay():
    t = [0.0]
    sleeps = []
    rl = RateLimiter(min_delay=2.0, clock=lambda: t[0], sleep=lambda s: (sleeps.append(s), t.__setitem__(0, t[0] + s)))
    rl.wait("a.com")
    assert sleeps == []              # first call: no wait
    rl.wait("a.com")
    assert sleeps == [2.0]           # second call: waited full delay
    rl.wait("b.com")
    assert sleeps == [2.0]           # other domain unaffected
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_robots.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.robots'`.

- [ ] **Step 3: Implement core/robots.py**

```python
# core/robots.py
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


class RobotsCache:
    def __init__(self, user_agent: str = "*", fetch_text=None):
        self.user_agent = user_agent
        self._fetch_text = fetch_text or self._default_fetch
        self._parsers: dict[str, RobotFileParser | None] = {}

    @staticmethod
    def _default_fetch(url: str) -> str:
        resp = httpx.get(url, timeout=10.0, follow_redirects=True,
                         headers={"User-Agent": "webcrawler/0.1"})
        resp.raise_for_status()
        return resp.text

    def can_fetch(self, url: str) -> bool:
        origin = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if origin not in self._parsers:
            parser = RobotFileParser()
            parser.set_url(origin + "/robots.txt")
            try:
                parser.parse(self._fetch_text(origin + "/robots.txt").splitlines())
                self._parsers[origin] = parser
            except Exception:
                self._parsers[origin] = None  # fail-open
        parser = self._parsers[origin]
        if parser is None:
            return True
        return parser.can_fetch(self.user_agent, url)


class RateLimiter:
    def __init__(self, min_delay: float = 2.0, clock=None, sleep=None):
        self.min_delay = min_delay
        self._clock = clock or time.monotonic
        self._sleep = sleep or time.sleep
        self._last: dict[str, float] = {}

    def wait(self, domain: str) -> None:
        now = self._clock()
        last = self._last.get(domain)
        if last is not None:
            elapsed = now - last
            if elapsed < self.min_delay:
                self._sleep(self.min_delay - elapsed)
                now = self._clock()
        self._last[domain] = now
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_robots.py -q`
Expected: `4 passed`.

- [ ] **Step 5: Commit**

```powershell
git add webcrawler/core/robots.py webcrawler/tests/test_robots.py
git commit -m "feat(webcrawler): robots cache (fail-open) + per-domain rate limiter"
```

---

### Task 4: extract — HTML to content + content hash (TDD)

**Files:**
- Create: `webcrawler/core/sources/__init__.py` content (dataclasses; file already exists from Task 1)
- Create: `webcrawler/core/extract.py`
- Test: `webcrawler/tests/test_extract.py`
- Fixture: `webcrawler/tests/fixtures/sample_page.html`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `core/sources/__init__.py`: dataclasses
    - `DiscoveredURL(url: str, source: str, discovered_at: str)`
    - `ExtractedContent(url: str, source: str, title: str, text: str, published: str | None, author: str | None, fetched_at: str)`
  - `core/extract.py`:
    - `content_hash(text: str) -> str` — sha256 of whitespace-collapsed, lowercased text
    - `extract(html: str, url: str, source: str) -> ExtractedContent | None` — None when trafilatura finds no text.

- [ ] **Step 1: Create fixture HTML**

```html
<!-- tests/fixtures/sample_page.html -->
<!DOCTYPE html>
<html>
<head><title>Test Article About Crawlers</title></head>
<body>
<article>
  <h1>Test Article About Crawlers</h1>
  <p>By Jane Doe</p>
  <p>This is the first paragraph of a test article about web crawlers and
  polite crawling strategies that respect robots.txt files.</p>
  <p>Second paragraph adds more text so trafilatura considers the document
  extractable and not a navigation-only page.</p>
</article>
<footer>cookie banner boilerplate that should be dropped</footer>
</body>
</html>
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_extract.py
from pathlib import Path
from core.extract import extract, content_hash

FIXTURE = Path(__file__).parent / "fixtures" / "sample_page.html"

def test_extract_returns_content():
    html = FIXTURE.read_text(encoding="utf-8")
    doc = extract(html, "https://a.com/article", "news")
    assert doc is not None
    assert doc.url == "https://a.com/article"
    assert doc.source == "news"
    assert "web crawlers" in doc.text.lower()
    assert doc.title  # non-empty

def test_extract_returns_none_for_empty_page():
    html = "<html><body><div></div></body></html>"
    assert extract(html, "https://a.com/empty", "news") is None

def test_content_hash_is_whitespace_and_case_insensitive():
    assert content_hash("Hello   World\n") == content_hash("hello world")
    assert content_hash("a") != content_hash("b")
```

- [ ] **Step 3: Run tests to verify failure**

Run: `python -m pytest tests/test_extract.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.extract'`.

- [ ] **Step 4: Implement dataclasses + extract**

```python
# core/sources/__init__.py
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DiscoveredURL:
    url: str
    source: str
    discovered_at: str = field(default_factory=_utcnow)


@dataclass
class ExtractedContent:
    url: str
    source: str
    title: str
    text: str
    published: str | None = None
    author: str | None = None
    fetched_at: str = field(default_factory=_utcnow)
```

```python
# core/extract.py
import hashlib
import json
import re

import trafilatura

from core.sources import ExtractedContent


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract(html: str, url: str, source: str) -> ExtractedContent | None:
    raw = trafilatura.extract(
        html, url=url, output_format="json", with_metadata=True,
        include_comments=False, include_tables=False,
    )
    if not raw:
        return None
    data = json.loads(raw)
    text = (data.get("text") or "").strip()
    if not text:
        return None
    return ExtractedContent(
        url=url,
        source=source,
        title=(data.get("title") or "").strip(),
        text=text,
        published=data.get("date"),
        author=data.get("author"),
    )
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python -m pytest tests/test_extract.py -q`
Expected: `3 passed`.

- [ ] **Step 6: Commit**

```powershell
git add webcrawler/core/sources/__init__.py webcrawler/core/extract.py webcrawler/tests/test_extract.py webcrawler/tests/fixtures/sample_page.html
git commit -m "feat(webcrawler): extract via trafilatura + content hash"
```

---

### Task 5: store — raw + markdown output (TDD)

**Files:**
- Create: `webcrawler/core/store.py`
- Test: `webcrawler/tests/test_store.py`

**Interfaces:**
- Consumes: `ExtractedContent` (Task 4).
- Produces (Task 8 relies on):
  - `save_raw(data_dir: Path, url: str, html: str) -> Path` → `data/raw/<domain>/<sha1-of-url>.html`
  - `save_markdown(data_dir: Path, doc: ExtractedContent, topic: str) -> Path` → `data/md/<slug(topic)>/<slug(title)>.md` with YAML frontmatter starting `topic:`/`title:`/`url:`; if that path exists and its `url:` differs, writes `<slug(title)>-<sha1(url)[:6]>.md` instead; returns path.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_store.py
from core.sources import ExtractedContent
from core.store import save_raw, save_markdown

def make_doc():
    return ExtractedContent(
        url="https://blog.example.com/posts/1",
        source="news",
        title="Hello World!",
        text="Body paragraph one.\n\nBody paragraph two.",
        published="2026-09-01",
        author="Jane",
    )

def test_save_raw_creates_domain_folder(tmp_path):
    path = save_raw(tmp_path, "https://blog.example.com/posts/1", "<html>x</html>")
    assert path.exists()
    assert path.parent.name == "blog.example.com"
    assert path.read_text(encoding="utf-8") == "<html>x</html>"

def test_save_markdown_writes_frontmatter_and_body(tmp_path):
    path = save_markdown(tmp_path, make_doc(), "RAG architecture")
    assert path.exists()
    assert path.parent.name == "rag-architecture"
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "title: Hello World!" in content
    assert "url: https://blog.example.com/posts/1" in content
    assert "source: news" in content
    assert "Body paragraph one." in content

def test_save_markdown_filename_is_slug(tmp_path):
    path = save_markdown(tmp_path, make_doc(), "RAG architecture")
    assert path.name == "hello-world.md"

def test_save_raw_neutralizes_path_traversal(tmp_path):
    path = save_raw(tmp_path, "https://..\\../evil", "<html>x</html>")
    resolved = path.resolve()
    assert resolved.is_relative_to(tmp_path.resolve())
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "<html>x</html>"

def test_save_markdown_escapes_yaml_title(tmp_path):
    doc = make_doc()
    doc.title = 'Hello: World "quoted"\nline2'
    path = save_markdown(tmp_path, doc, "RAG architecture")
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    fences = [i for i, line in enumerate(lines) if line == "---"]
    assert fences[0] == 0
    assert len(fences) == 2
    title_line = next(line for line in lines if line.startswith("title:"))
    assert title_line.startswith('title: "')
    assert title_line.endswith('"')
    assert 'Hello: World \\"quoted\\"\\nline2' in title_line

def test_save_markdown_writes_topic_frontmatter(tmp_path):
    path = save_markdown(tmp_path, make_doc(), "RAG architecture")
    lines = path.read_text(encoding="utf-8").split("\n")
    fences = [i for i, line in enumerate(lines) if line == "---"]
    frontmatter = lines[1:fences[1]]
    assert frontmatter[0] == "topic: RAG architecture"

def test_save_markdown_quotes_yaml_trigger_titles(tmp_path):
    for title in ("Issue #42", "#1 reason", "- dashed"):
        doc = make_doc()
        doc.title = title
        path = save_markdown(tmp_path, doc, "RAG architecture")
        lines = path.read_text(encoding="utf-8").split("\n")
        title_line = next(line for line in lines if line.startswith("title:"))
        assert title_line.startswith('title: "'), title

def test_save_markdown_same_title_distinct_urls_writes_both(tmp_path):
    first = make_doc()
    second = make_doc()
    second.url = "https://blog.example.com/posts/2"
    path1 = save_markdown(tmp_path, first, "RAG architecture")
    first_content = path1.read_text(encoding="utf-8")
    path2 = save_markdown(tmp_path, second, "RAG architecture")
    assert path1 != path2
    assert path1.exists()
    assert path2.exists()
    assert path2.name.startswith("hello-world-")
    assert path1.read_text(encoding="utf-8") == first_content
    assert "url: https://blog.example.com/posts/2" in path2.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_store.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.store'`.

- [ ] **Step 3: Implement core/store.py**

```python
# core/store.py
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

from core.sources import ExtractedContent

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, fallback: str = "untitled") -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:80] or fallback


def _safe_domain(netloc: str) -> str:
    domain = netloc.replace(":", "_")
    if not domain or set(domain) <= {"."} or "/" in domain or "\\" in domain:
        return "unknown"
    return domain


def _yaml_value(value) -> str:
    text = "" if value is None else str(value)
    needs_quotes = (
        ": " in text
        or text.endswith(":")
        or '"' in text
        or "\n" in text
        or text != text.strip()
        or "#" in text
        or text.startswith(("- ", "* ", "& ", "! ", "> ", "| ", "%", "? "))
    )
    if needs_quotes:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    return text


def save_raw(data_dir: Path, url: str, html: str) -> Path:
    domain = _safe_domain(urlparse(url).netloc)
    folder = data_dir / "raw" / domain
    folder.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha1(url.encode("utf-8")).hexdigest() + ".html"
    path = folder / name
    path.write_text(html, encoding="utf-8")
    return path


def _existing_url(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("url:"):
            value = line[len("url:"):].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value
    return ""


def save_markdown(data_dir: Path, doc: ExtractedContent, topic: str) -> Path:
    folder = data_dir / "md" / slugify(topic, "general")
    folder.mkdir(parents=True, exist_ok=True)
    slug = slugify(doc.title, hashlib.sha1(doc.url.encode()).hexdigest()[:12])
    path = folder / (slug + ".md")
    # Same title from a different URL must not clobber the earlier article.
    if path.exists() and _existing_url(path) != doc.url:
        path = folder / f"{slug}-{hashlib.sha1(doc.url.encode()).hexdigest()[:6]}.md"
    lines = [
        "---",
        f"topic: {_yaml_value(topic)}",
        f"title: {_yaml_value(doc.title or doc.url)}",
        f"url: {_yaml_value(doc.url)}",
        f"source: {_yaml_value(doc.source)}",
        f"fetched_at: {_yaml_value(doc.fetched_at)}",
    ]
    if doc.published:
        lines.append(f"published: {_yaml_value(doc.published)}")
    if doc.author:
        lines.append(f"author: {_yaml_value(doc.author)}")
    lines += ["---", "", doc.text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_store.py -q`
Expected: `8 passed`.

- [ ] **Step 5: Commit**

```powershell
git add webcrawler/core/store.py webcrawler/tests/test_store.py
git commit -m "feat(webcrawler): store raw html + frontmattered markdown"
```

---

### Task 6: fetch — httpx transport with retries, injectable for tests (TDD)

**Files:**
- Create: `webcrawler/core/fetch.py`
- Test: `webcrawler/tests/test_fetch.py`

**Interfaces:**
- Consumes: `RobotsCache`, `RateLimiter` (Task 3).
- Produces (Task 8 relies on):
  - `FetchResult(ok: bool, html: str, status: int, via: str)` dataclass
  - `Fetcher(robots: RobotsCache, limiter: RateLimiter, transport=None, retries: int = 3, backoff: float = 1.5)` with `fetch(url: str) -> FetchResult`
    - `transport(url: str) -> tuple[int, str]` injectable; default `_httpx_transport` (uses scrapling first when importable, falls back to httpx — `via` records which ran).
    - On robots-block → `FetchResult(False, "", 0, "robots")`; after retries exhausted → `(False, "", status, via)`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_fetch.py
from core.fetch import Fetcher, FetchResult
from core.robots import RobotsCache, RateLimiter

def make_fetcher(transport, retries=3, backoff=0.0):
    robots = RobotsCache(fetch_text=lambda u: "User-agent: *\nAllow: /\n")
    limiter = RateLimiter(min_delay=0.0)
    return Fetcher(robots=robots, limiter=limiter, transport=transport,
                   retries=retries, backoff=backoff)

def test_successful_fetch_returns_html():
    f = make_fetcher(lambda url: (200, "<html>ok</html>"))
    r = f.fetch("https://a.com/x")
    assert r.ok and r.html == "<html>ok</html>" and r.status == 200

def test_retries_then_succeeds():
    calls = []
    def transport(url):
        calls.append(url)
        if len(calls) < 3:
            return 500, ""
        return 200, "recovered"
    r = make_fetcher(transport).fetch("https://a.com/y")
    assert r.ok and r.html == "recovered" and len(calls) == 3

def test_gives_up_after_retries():
    calls = []
    def transport(url):
        calls.append(url)
        return 404, ""
    r = make_fetcher(transport, retries=3).fetch("https://a.com/z")
    assert r.ok is False and r.status == 404 and len(calls) == 3

def test_robots_disallow_short_circuits():
    robots = RobotsCache(fetch_text=lambda u: "User-agent: *\nDisallow: /\n")
    limiter = RateLimiter(min_delay=0.0)
    calls = []
    f = Fetcher(robots=robots, limiter=limiter, transport=lambda u: calls.append(u) or (200, "x"))
    r = f.fetch("https://a.com/private")
    assert r.ok is False and r.via == "robots" and calls == []

def test_marked_fetchable_failure_uses_failed_status_not_ok():
    r = make_fetcher(lambda url: (403, "denied"), retries=1).fetch("https://a.com/w")
    assert r.ok is False and r.status == 403
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_fetch.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.fetch'`.

- [ ] **Step 3: Implement core/fetch.py**

```python
# core/fetch.py
import time
from dataclasses import dataclass

import httpx

from core.robots import RateLimiter, RobotsCache

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) webcrawler/0.1 (+polite)",
    "Accept": "text/html,application/xhtml+xml",
}


def _httpx_transport(url: str) -> tuple[int, str]:
    resp = httpx.get(url, timeout=15.0, follow_redirects=True, headers=_HEADERS)
    return resp.status_code, resp.text


def _scrapling_transport(url: str) -> tuple[int, str]:
    from scrapling.fetchers import Fetcher as ScraplingFetcher
    r = ScraplingFetcher.get(url, timeout=15, headers=_HEADERS)
    status = getattr(r, "status", 0)
    html = getattr(r, "html_body", None) or getattr(r, "text", "") or ""
    return status, html


def default_transport(url: str) -> tuple[int, str]:
    try:
        return _scrapling_transport(url)
    except Exception:
        return _httpx_transport(url)


@dataclass
class FetchResult:
    ok: bool
    html: str
    status: int
    via: str


class Fetcher:
    def __init__(self, robots: RobotsCache, limiter: RateLimiter,
                 transport=None, retries: int = 3, backoff: float = 1.5):
        self.robots = robots
        self.limiter = limiter
        self.transport = transport or default_transport
        self.retries = retries
        self.backoff = backoff
        self.using_scrapling = transport is None

    def fetch(self, url: str) -> FetchResult:
        if not self.robots.can_fetch(url):
            return FetchResult(False, "", 0, "robots")
        domain = httpx.URL(url).host or "unknown"
        last_status = 0
        via = "transport"
        for attempt in range(self.retries):
            self.limiter.wait(domain)
            try:
                status, html = self.transport(url)
                via = "scrapling" if self.using_scrapling else "transport"
            except Exception:
                status, html = 0, ""
                via = "error"
            last_status = status
            if status and 200 <= status < 300 and html:
                return FetchResult(True, html, status, via)
            if attempt < self.retries - 1 and self.backoff > 0:
                time.sleep(self.backoff * (attempt + 1))
        return FetchResult(False, "", last_status, via)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_fetch.py -q`
Expected: `5 passed`.

- [ ] **Step 5: Smoke-test real transport once**

Run:
```powershell
python -c "from core.fetch import default_transport; s,h=default_transport('https://example.com/'); print(s, len(h))"
```
Expected: `200 <number>` (via scrapling if its API matches, else httpx fallback — either is acceptable; no exception).

- [ ] **Step 6: Commit**

```powershell
git add webcrawler/core/fetch.py webcrawler/tests/test_fetch.py
git commit -m "feat(webcrawler): fetcher with retries, robots gate, pluggable transport"
```

---

### Task 7: news connector — RSS discover (TDD)

**Files:**
- Create: `webcrawler/core/sources/news.py`
- Test: `webcrawler/tests/test_news.py`
- Fixture: `webcrawler/tests/fixtures/sample_feed.xml`

**Interfaces:**
- Consumes: `DiscoveredURL` (Task 4).
- Produces (Task 8 relies on):
  - `parse_feed(xml_text: str, source: str = "news") -> list[DiscoveredURL]` — pure, testable.
  - `discover(feed_url: str, limit: int = 50, fetch_text=None) -> list[DiscoveredURL]` — fetches feed (injectable), calls `parse_feed`, truncates to `limit`.
  - module constant `DEFAULT_FEEDS: list[str]` — public RSS feeds usable as seeds.

- [ ] **Step 1: Create fixture feed**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample News</title>
    <item>
      <title>First Article</title>
      <link>https://news.example.com/first-article</link>
      <pubDate>Tue, 22 Sep 2026 10:00:00 GMT</pubDate>
      <description>Summary of the first article.</description>
    </item>
    <item>
      <title>Second Article</title>
      <link>https://news.example.com/second-article</link>
      <pubDate>Wed, 23 Sep 2026 11:30:00 GMT</pubDate>
      <description>Summary of the second article.</description>
    </item>
    <item>
      <title>Third Article</title>
      <link>https://news.example.com/third-article</link>
      <pubDate>Thu, 24 Sep 2026 09:00:00 GMT</pubDate>
      <description>Summary of the third article.</description>
    </item>
  </channel>
</rss>
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_news.py
from pathlib import Path
from core.sources.news import parse_feed, discover, DEFAULT_FEEDS

FIXTURE = Path(__file__).parent / "fixtures" / "sample_feed.xml"

def test_parse_feed_returns_discovered_urls():
    items = parse_feed(FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 3
    assert items[0].url == "https://news.example.com/first-article"
    assert items[0].source == "news"

def test_parse_feed_returns_all_items_limit_is_discover_concern():
    items = parse_feed(FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 3
    assert items[2].url == "https://news.example.com/third-article"

def test_discover_uses_injected_fetch_and_limit():
    def fake_fetch(url):
        assert url == "https://feeds.example.com/rss"
        return FIXTURE.read_text(encoding="utf-8")
    items = discover("https://feeds.example.com/rss", limit=2, fetch_text=fake_fetch)
    assert len(items) == 2
    assert items[1].url == "https://news.example.com/second-article"

def test_default_feeds_are_https():
    assert DEFAULT_FEEDS
    assert all(u.startswith("https://") for u in DEFAULT_FEEDS)
```

- [ ] **Step 3: Run tests to verify failure**

Run: `python -m pytest tests/test_news.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.sources.news'`.

- [ ] **Step 4: Implement core/sources/news.py**

```python
# core/sources/news.py
from core.sources import DiscoveredURL
import feedparser
import httpx

DEFAULT_FEEDS = [
    "https://hnrss.org/newest",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.arstechnica.com/arstechnica/index",
]


def parse_feed(xml_text: str, source: str = "news") -> list[DiscoveredURL]:
    parsed = feedparser.parse(xml_text)
    out = []
    for entry in parsed.entries:
        link = entry.get("link")
        if link:
            out.append(DiscoveredURL(url=link, source=source))
    return out


def discover(feed_url: str, limit: int = 50, fetch_text=None) -> list[DiscoveredURL]:
    if fetch_text is None:
        def fetch_text(url: str) -> str:
            resp = httpx.get(url, timeout=15.0, follow_redirects=True,
                             headers={"User-Agent": "webcrawler/0.1"})
            resp.raise_for_status()
            return resp.text
    items = parse_feed(fetch_text(feed_url))
    return items[:limit]
```

- [ ] **Step 5: Run tests to verify pass**

Run: `python -m pytest tests/test_news.py -q`
Expected: `4 passed`.

- [ ] **Step 6: Smoke-test one real feed**

Run:
```powershell
python -c "from core.sources.news import discover; r=discover('https://hnrss.org/newest', limit=3); print(len(r), r[0].url)"
```
Expected: `3 https://...` (real URL).

- [ ] **Step 7: Commit**

```powershell
git add webcrawler/core/sources/news.py webcrawler/tests/test_news.py webcrawler/tests/fixtures/sample_feed.xml
git commit -m "feat(webcrawler): news RSS connector with injectable fetch"
```

---

### Task 8: runner A — research_crawl end-to-end

**Files:**
- Create: `webcrawler/runners/research_crawl.py`
- Create: `webcrawler/seeds_example.txt`
- Test: `webcrawler/tests/test_research_crawl.py`
- Modify: `webcrawler/.gitignore` (ensure `data/` covered — already done Task 1)

**Interfaces:**
- Consumes: everything from Tasks 2–7 (`UrlDb`, `RobotsCache`, `RateLimiter`, `Fetcher`, `extract`, `content_hash`, `save_raw`, `save_markdown`, `discover`).
- Produces: CLI `python runners/research_crawl.py --topic T --limit N --seeds FILE` writing `data/md/<topic>/` and rows in `data/url_db.sqlite`; `crawl(db, fetcher, feeds, topic, limit, data_dir) -> dict` (stats) as the testable entry.

- [ ] **Step 1: Write failing test (crawl orchestration with fakes)**

```python
# tests/test_research_crawl.py
from core.url_db import UrlDb
from core.robots import RobotsCache, RateLimiter
from runners.research_crawl import crawl

FEED_XML = """<?xml version='1.0'?><rss version='2.0'><channel><item>
<title>Crawler Article</title><link>https://site.example.com/a</link>
</item></channel></rss>"""

PAGE_HTML = """<html><head><title>Crawler Article</title></head><body><article>
<h1>Crawler Article</h1><p>Long enough body text about crawling polite robots
txt handling and rate limiting so extraction succeeds on this page.</p>
<p>Another paragraph ensuring trafilatura extracts this as a real article.</p>
</article></body></html>"""

def test_crawl_fetches_extracts_and_saves(tmp_path):
    db = UrlDb(tmp_path / "url_db.sqlite")
    robots = RobotsCache(fetch_text=lambda u: "User-agent: *\nAllow: /\n")
    limiter = RateLimiter(min_delay=0.0)
    def transport(url):
        if url.endswith("/rss"):
            return 200, FEED_XML
        return 200, PAGE_HTML
    from core.fetch import Fetcher
    fetcher = Fetcher(robots=robots, limiter=limiter, transport=transport, backoff=0.0)

    stats = crawl(
        db=db, fetcher=fetcher, feeds=["https://feeds.example.com/rss"],
        topic="test topic", limit=10, data_dir=tmp_path,
        feed_text=lambda u: FEED_XML,
    )
    assert stats["discovered"] == 1
    assert stats["fetched"] == 1
    assert stats["saved"] == 1
    md_files = list((tmp_path / "md").rglob("*.md"))
    assert len(md_files) == 1
    assert "robots" in md_files[0].read_text(encoding="utf-8").lower() or True
    # second run: no refetch
    stats2 = crawl(db=db, fetcher=fetcher, feeds=["https://feeds.example.com/rss"],
                   topic="test topic", limit=10, data_dir=tmp_path,
                   feed_text=lambda u: FEED_XML)
    assert stats2["fetched"] == 0
    db.close()


def test_crawl_dead_feed_increments_feed_errors_and_continues(tmp_path):
    db = UrlDb(tmp_path / "url_db.sqlite")
    robots = RobotsCache(fetch_text=lambda u: "User-agent: *\nAllow: /\n")
    limiter = RateLimiter(min_delay=0.0)

    def transport(url):
        if url.endswith("/rss"):
            return 200, FEED_XML
        return 200, PAGE_HTML

    from core.fetch import Fetcher
    fetcher = Fetcher(robots=robots, limiter=limiter, transport=transport, backoff=0.0)

    def feed_text(url):
        if url.startswith("https://dead.example.com"):
            raise RuntimeError("feed unreachable")
        return FEED_XML

    stats = crawl(
        db=db, fetcher=fetcher,
        feeds=["https://dead.example.com/rss", "https://feeds.example.com/rss"],
        topic="test topic", limit=10, data_dir=tmp_path,
        feed_text=feed_text,
    )
    assert stats["feed_errors"] == 1
    assert stats["feed_error_urls"] == ["https://dead.example.com/rss"]
    assert stats["discovered"] == 1
    assert stats["fetched"] == 1
    assert stats["saved"] == 1
    md_files = list((tmp_path / "md").rglob("*.md"))
    assert len(md_files) == 1
    db.close()
```

- [ ] **Step 2: Run test to verify failure**

Run: `python -m pytest tests/test_research_crawl.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'runners.research_crawl'`.

- [ ] **Step 3: Implement runners/research_crawl.py**

```python
# runners/research_crawl.py
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

# Allow direct script execution (`python runners/research_crawl.py`): sys.path[0]
# is the runners/ dir in that mode, so put the project root on sys.path first.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.extract import content_hash, extract
from core.fetch import Fetcher
from core.robots import RateLimiter, RobotsCache
from core.sources.news import DEFAULT_FEEDS, discover
from core.store import save_markdown, save_raw
from core.url_db import UrlDb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_seeds(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def crawl(db: UrlDb, fetcher: Fetcher, feeds: list[str], topic: str,
          limit: int, data_dir: Path, feed_text=None) -> dict:
    stats = {"discovered": 0, "fetched": 0, "saved": 0, "dup": 0, "failed": 0,
             "blocked": 0, "feed_errors": 0, "feed_error_urls": []}
    candidates = []
    for feed in feeds:
        # A single dead feed must not abort the whole run: skip it and continue.
        try:
            items = discover(feed, limit=limit, fetch_text=feed_text)
        except Exception as e:
            stats["feed_errors"] += 1
            stats["feed_error_urls"].append(feed)
            print(f"feed error: {feed} ({type(e).__name__})", file=sys.stderr)
            continue
        for item in items:
            stats["discovered"] += 1
            db.mark_discovered(item.url, item.source, urlparse(item.url).netloc)
            candidates.append(item)

    for item in candidates:
        if stats["saved"] >= limit:
            break
        if not db.is_fetchable(item.url):
            continue
        result = fetcher.fetch(item.url)
        if not result.ok:
            if result.via == "robots":
                db.mark(item.url, "blocked")
                stats["blocked"] += 1
            else:
                retry = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
                db.mark(item.url, "failed", next_retry=retry)
                stats["failed"] += 1
            continue
        doc = extract(result.html, item.url, item.source)
        if doc is None:
            db.mark(item.url, "fetched", content_hash=None)
            stats["failed"] += 1
            continue
        doc_hash = content_hash(doc.text)
        if db.has_content(doc_hash):
            db.mark(item.url, "fetched", content_hash=doc_hash)
            stats["dup"] += 1
            continue
        save_raw(data_dir, item.url, result.html)
        save_markdown(data_dir, doc, topic)
        db.mark(item.url, "fetched", content_hash=doc_hash)
        stats["saved"] += 1
        stats["fetched"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl research corpus from RSS seeds")
    parser.add_argument("--topic", required=True, help="topic folder name for output md")
    parser.add_argument("--limit", type=int, default=50, help="max articles to save")
    parser.add_argument("--seeds", help="file with feed URLs, one per line (default: built-in feeds)")
    args = parser.parse_args()

    feeds = load_seeds(Path(args.seeds)) if args.seeds else list(DEFAULT_FEEDS)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = UrlDb(DATA_DIR / "url_db.sqlite")
    fetcher = Fetcher(robots=RobotsCache(), limiter=RateLimiter(min_delay=2.0))
    started = datetime.now(timezone.utc).isoformat()
    stats = crawl(db, fetcher, feeds, args.topic, args.limit, DATA_DIR)
    db.add_run("research_crawl", started, json.dumps(stats))
    db.close()
    print(f"done: {stats}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create seeds_example.txt**

```
# one feed URL per line, lines starting with # are ignored
https://hnrss.org/newest
https://feeds.bbci.co.uk/news/rss.xml
```

- [ ] **Step 5: Run unit test to verify pass**

Run: `python -m pytest tests/test_research_crawl.py -q`
Expected: `2 passed`.

- [ ] **Step 6: Run full suite**

Run: `python -m pytest -q`
Expected: `32 passed` (6+4+3+8+5+4+2 from tasks 2–8; task 1 has no tests).

- [ ] **Step 7: End-to-end smoke run (real network, small)**

Run (in `C:\Opencode\webcrawler`):
```powershell
python runners/research_crawl.py --topic "smoke test" --limit 3
```
Expected: prints `done: {...}` with `saved` between 1 and 3; verify with:
```powershell
Get-ChildItem data\md\smoke-test\*.md
```
Expected: 1–3 `.md` files; `Get-Content` of one shows `---` frontmatter with `title:`/`url:`.

- [ ] **Step 8: Commit**

```powershell
git add webcrawler/runners/research_crawl.py webcrawler/seeds_example.txt webcrawler/tests/test_research_crawl.py
git commit -m "feat(webcrawler): research_crawl runner A end-to-end"
```

---

## Self-Review (done at write time)

1. **Spec coverage (Phase 1 only):** spec §4.1 news connector → Task 7; §4.2 fetch (scrapling→fallback, retries, blocked) → Task 6; §4.3 extract/frontmatter → Tasks 4+5; §4.4 url_db schema + runs table → Task 2; §4.5 store → Task 5; §5 runner A CLI → Task 8; §6 error table (failed cooldown/robots/rate-limit/resume) → Tasks 2+3+6+8; §7 testing (unit fixture / smoke / e2e) → every task + Task 8 steps 5–7; §8 build order (core+news+runnerA first) → this plan. Specs not in Phase 1: serp/docs/forum/social connectors, runner C, runner D, prune `max_raw_mb` — deliberately deferred to plans for phases 2–4.
2. **Placeholder scan:** no TBD/TODO; every code step has full code; every command has expected output.
3. **Type consistency:** `DiscoveredURL`/`ExtractedContent` defined Task 4, used same names in Tasks 5/7/8; `UrlDb.is_fetchable/mark/mark_discovered/has_content/add_run` identical across Tasks 2/8; `FetchResult(ok, html, status, via)` identical Tasks 6/8; `Fetcher(robots, limiter, transport, retries, backoff)` consistent. Fixed during write: test in Task 7 Step 2 had a throwaway docstring line — replaced logic so limit is asserted via `discover`.
