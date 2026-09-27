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
