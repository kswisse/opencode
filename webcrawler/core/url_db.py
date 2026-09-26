# core/url_db.py
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS urls (
  url TEXT PRIMARY KEY,
  source TEXT,
  status TEXT DEFAULT 'pending',
  content_hash TEXT,
  first_seen TEXT,
  last_crawled TEXT,
  next_retry TEXT,
  domain TEXT
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  runner TEXT,
  started_at TEXT,
  finished_at TEXT,
  stats_json TEXT
);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class UrlDb:
    def __init__(self, path):
        self.conn = sqlite3.connect(str(path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)

    def is_fetchable(self, url: str, now: str | None = None) -> bool:
        now = now or _utcnow()
        row = self.conn.execute(
            "SELECT status, next_retry FROM urls WHERE url=?", (url,)
        ).fetchone()
        if row is None:
            return True
        status, next_retry = row
        if status == "fetched":
            return False
        if status == "blocked":
            return False
        if status == "failed" and next_retry and next_retry > now:
            return False
        return True

    def mark_discovered(self, url: str, source: str, domain: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO urls (url, source, first_seen, domain) VALUES (?, ?, ?, ?)",
            (url, source, _utcnow(), domain),
        )
        self.conn.commit()

    def mark(self, url: str, status: str, content_hash: str | None = None,
             next_retry: str | None = None) -> None:
        now = _utcnow()
        self.conn.execute(
            "UPDATE urls SET status=?, content_hash=COALESCE(?, content_hash), "
            "last_crawled=CASE WHEN ?='fetched' THEN ? ELSE last_crawled END, "
            "next_retry=? WHERE url=?",
            (status, content_hash, status, now, next_retry, url),
        )
        self.conn.commit()

    def has_content(self, content_hash: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM urls WHERE content_hash=? LIMIT 1",
            (content_hash,),
        ).fetchone()
        return row is not None

    def add_run(self, runner: str, started_at: str, stats_json: str) -> None:
        self.conn.execute(
            "INSERT INTO runs (runner, started_at, finished_at, stats_json) VALUES (?, ?, ?, ?)",
            (runner, started_at, _utcnow(), stats_json),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
