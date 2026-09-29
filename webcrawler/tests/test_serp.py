# tests/test_serp.py
from core.sources.serp import discover, MAX_PER_DOMAIN


def _results(n=10):
    return [{"href": f"https://site{i}.example.com/p{i}"} for i in range(n)]


def test_discover_injected_search_respects_limit():
    items = discover("q", limit=5, search=lambda q, lang="en": _results(10))
    assert len(items) == 5
    assert all(i.source == "serp" for i in items)


def test_discover_caps_per_domain():
    dup = [{"href": "https://same.com/a"} for _ in range(10)]
    items = discover("q", search=lambda q, lang="en": dup)
    assert len(items) == MAX_PER_DOMAIN


def test_discover_skips_non_http():
    mixed = [
        {"href": "ftp://x.com/f"},
        {"href": "javascript:void(0)"},
        {"href": "https://ok.com/a"},
    ]
    items = discover("q", search=lambda q, lang="en": mixed)
    assert [i.url for i in items] == ["https://ok.com/a"]


def test_discover_missing_href_ignored():
    items = discover("q", search=lambda q, lang="en": [{"href": ""}, {"title": "x"}])
    assert items == []


def test_discover_domain_cap_is_case_insensitive():
    dup = [
        {"href": "https://Same.com/a"},
        {"href": "https://SAME.com/b"},
        {"href": "https://same.com/c"},
        {"href": "https://same.com/d"},
    ]
    items = discover("q", search=lambda q, lang="en": dup)
    # without lowercasing the netloc, each casing would count separately -> 4
    assert len(items) == MAX_PER_DOMAIN
