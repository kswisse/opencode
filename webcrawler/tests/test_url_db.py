# tests/test_url_db.py
from core.url_db import UrlDb

def make_db(tmp_path):
    return UrlDb(tmp_path / "url_db.sqlite")

def test_new_url_not_fetchable_before_mark_then_fetchable(tmp_path):
    db = make_db(tmp_path)
    assert db.is_fetchable("https://a.com/1") is True
    db.mark_discovered("https://a.com/1", "news", "a.com")
    assert db.is_fetchable("https://a.com/1") is True
    db.mark("https://a.com/1", "fetched")
    assert db.is_fetchable("https://a.com/1") is False
    db.close()

def test_failed_url_blocked_until_next_retry(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/2", "news", "a.com")
    db.mark("https://a.com/2", "failed", next_retry="2026-09-27T00:00:00+00:00")
    assert db.is_fetchable("https://a.com/2", now="2026-09-26T00:00:00+00:00") is False
    assert db.is_fetchable("https://a.com/2", now="2026-09-27T01:00:00+00:00") is True
    db.close()

def test_blocked_never_fetchable(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/3", "news", "a.com")
    db.mark("https://a.com/3", "blocked")
    assert db.is_fetchable("https://a.com/3", now="2099-01-01T00:00:00+00:00") is False
    db.close()

def test_content_hash_dedup(tmp_path):
    db = make_db(tmp_path)
    assert db.has_content("abc123") is False
    db.mark_discovered("https://a.com/4", "news", "a.com")
    db.mark("https://a.com/4", "fetched", content_hash="abc123")
    assert db.has_content("abc123") is True
    db.close()

def test_double_discover_keeps_single_row(tmp_path):
    db = make_db(tmp_path)
    db.mark_discovered("https://a.com/5", "news", "a.com")
    db.mark_discovered("https://a.com/5", "serp", "a.com")
    cur = db.conn.execute("SELECT COUNT(*) FROM urls WHERE url=?", ("https://a.com/5",))
    assert cur.fetchone()[0] == 1
    db.close()
