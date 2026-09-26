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
