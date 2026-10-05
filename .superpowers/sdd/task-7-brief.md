### Task 7: news connector â€” RSS discover (TDD)

**Files:**
- Create: `webcrawler/core/sources/news.py`
- Test: `webcrawler/tests/test_news.py`
- Fixture: `webcrawler/tests/fixtures/sample_feed.xml`

**Interfaces:**
- Consumes: `DiscoveredURL` (Task 4).
- Produces (Task 8 relies on):
  - `parse_feed(xml_text: str, source: str = "news") -> list[DiscoveredURL]` â€” pure, testable.
  - `discover(feed_url: str, limit: int = 50, fetch_text=None) -> list[DiscoveredURL]` â€” fetches feed (injectable), calls `parse_feed`, truncates to `limit`.
  - module constant `DEFAULT_FEEDS: list[str]` â€” public RSS feeds usable as seeds.

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


