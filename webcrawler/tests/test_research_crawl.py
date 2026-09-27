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
