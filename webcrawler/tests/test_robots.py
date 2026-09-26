# tests/test_robots.py
from core.robots import RobotsCache, RateLimiter

ROBOTS_TXT = "User-agent: *\nDisallow: /private/\nAllow: /public/\n"

def test_can_fetch_allows_public_and_blocks_disallowed():
    cache = RobotsCache(fetch_text=lambda url: ROBOTS_TXT)
    assert cache.can_fetch("https://a.com/public/article") is True
    assert cache.can_fetch("https://a.com/private/secret") is False

def test_robots_fetch_error_fails_open():
    def boom(url):
        raise RuntimeError("network down")
    cache = RobotsCache(fetch_text=boom)
    assert cache.can_fetch("https://a.com/anything") is True

def test_robots_fetched_once_per_domain():
    calls = []
    def fetch(url):
        calls.append(url)
        return ROBOTS_TXT
    cache = RobotsCache(fetch_text=fetch)
    cache.can_fetch("https://a.com/1")
    cache.can_fetch("https://a.com/2")
    assert len(calls) == 1

def test_rate_limiter_enforces_min_delay():
    t = [0.0]
    sleeps = []
    rl = RateLimiter(min_delay=2.0, clock=lambda: t[0], sleep=lambda s: (sleeps.append(s), t.__setitem__(0, t[0] + s)))
    rl.wait("a.com")
    assert sleeps == []              # first call: no wait
    rl.wait("a.com")
    assert sleeps == [2.0]           # second call: waited full delay
    rl.wait("b.com")
    assert sleeps == [2.0]           # other domain unaffected
