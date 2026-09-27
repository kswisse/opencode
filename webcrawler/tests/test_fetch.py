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
