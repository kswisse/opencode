# tests/test_extract.py
from pathlib import Path
from core.extract import extract, content_hash

FIXTURE = Path(__file__).parent / "fixtures" / "sample_page.html"

def test_extract_returns_content():
    html = FIXTURE.read_text(encoding="utf-8")
    doc = extract(html, "https://a.com/article", "news")
    assert doc is not None
    assert doc.url == "https://a.com/article"
    assert doc.source == "news"
    assert "web crawlers" in doc.text.lower()
    assert doc.title  # non-empty

def test_extract_returns_none_for_empty_page():
    html = "<html><body><div></div></body></html>"
    assert extract(html, "https://a.com/empty", "news") is None

def test_content_hash_is_whitespace_and_case_insensitive():
    assert content_hash("Hello   World\n") == content_hash("hello world")
    assert content_hash("a") != content_hash("b")
