### Task 4: extract â€” HTML to content + content hash (TDD)

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
    - `content_hash(text: str) -> str` â€” sha256 of whitespace-collapsed, lowercased text
    - `extract(html: str, url: str, source: str) -> ExtractedContent | None` â€” None when trafilatura finds no text.

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


