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
