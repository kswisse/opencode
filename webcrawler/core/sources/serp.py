# core/sources/serp.py
from urllib.parse import urlparse

from core.sources import DiscoveredURL

MAX_PER_DOMAIN = 3
_SCHEMES = ("http", "https")


def _default_search(query: str, lang: str = "en") -> list[dict]:
    from ddgs import DDGS
    region = "vi-vn" if lang == "vi" else "us-en"
    with DDGS() as ddgs:
        return list(ddgs.text(query, region=region, max_results=50))


def discover(query: str, limit: int = 50, lang: str = "en", search=None) -> list[DiscoveredURL]:
    search = search or _default_search
    raw = search(query, lang)
    seen: dict[str, int] = {}
    out: list[DiscoveredURL] = []
    for item in raw:
        if len(out) >= limit:
            break
        url = (item or {}).get("href") or ""
        if urlparse(url).scheme.lower() not in _SCHEMES:
            continue
        domain = urlparse(url).netloc.lower()
        if seen.get(domain, 0) >= MAX_PER_DOMAIN:
            continue
        seen[domain] = seen.get(domain, 0) + 1
        out.append(DiscoveredURL(url=url, source="serp"))
    return out
