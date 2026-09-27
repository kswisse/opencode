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
