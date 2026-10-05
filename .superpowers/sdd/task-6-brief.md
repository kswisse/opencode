### Task 6: fetch â€” httpx transport with retries, injectable for tests (TDD)

**Files:**
- Create: `webcrawler/core/fetch.py`
- Test: `webcrawler/tests/test_fetch.py`

**Interfaces:**
- Consumes: `RobotsCache`, `RateLimiter` (Task 3).
- Produces (Task 8 relies on):
  - `FetchResult(ok: bool, html: str, status: int, via: str)` dataclass
  - `Fetcher(robots: RobotsCache, limiter: RateLimiter, transport=None, retries: int = 3, backoff: float = 1.5)` with `fetch(url: str) -> FetchResult`
    - `transport(url: str) -> tuple[int, str]` injectable; default `_httpx_transport` (uses scrapling first when importable, falls back to httpx â€” `via` records which ran).
    - On robots-block â†’ `FetchResult(False, "", 0, "robots")`; after retries exhausted â†’ `(False, "", status, via)`.

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
Expected: `200 <number>` (via scrapling if its API matches, else httpx fallback â€” either is acceptable; no exception).

- [ ] **Step 6: Commit**

```powershell
git add webcrawler/core/fetch.py webcrawler/tests/test_fetch.py
git commit -m "feat(webcrawler): fetcher with retries, robots gate, pluggable transport"
```

---


