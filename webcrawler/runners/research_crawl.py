# runners/research_crawl.py
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

# Allow direct script execution (`python runners/research_crawl.py`): sys.path[0]
# is the runners/ dir in that mode, so put the project root on sys.path first.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.extract import content_hash, extract
from core.fetch import Fetcher
from core.robots import RateLimiter, RobotsCache
from core.sources.news import DEFAULT_FEEDS, discover
from core.store import save_markdown, save_raw
from core.url_db import UrlDb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def load_seeds(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]


def crawl(db: UrlDb, fetcher: Fetcher, feeds: list[str], topic: str,
          limit: int, data_dir: Path, feed_text=None) -> dict:
    stats = {"discovered": 0, "fetched": 0, "saved": 0, "dup": 0, "failed": 0,
             "blocked": 0, "feed_errors": 0}
    candidates = []
    for feed in feeds:
        # A single dead feed must not abort the whole run: skip it and continue.
        try:
            items = discover(feed, limit=limit, fetch_text=feed_text)
        except Exception:
            stats["feed_errors"] += 1
            continue
        for item in items:
            stats["discovered"] += 1
            db.mark_discovered(item.url, item.source, urlparse(item.url).netloc)
            candidates.append(item)

    for item in candidates:
        if stats["saved"] >= limit:
            break
        if not db.is_fetchable(item.url):
            continue
        result = fetcher.fetch(item.url)
        if not result.ok:
            if result.via == "robots":
                db.mark(item.url, "blocked")
                stats["blocked"] += 1
            else:
                retry = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
                db.mark(item.url, "failed", next_retry=retry)
                stats["failed"] += 1
            continue
        doc = extract(result.html, item.url, item.source)
        if doc is None:
            db.mark(item.url, "fetched", content_hash=None)
            stats["failed"] += 1
            continue
        doc_hash = content_hash(doc.text)
        if db.has_content(doc_hash):
            db.mark(item.url, "fetched", content_hash=doc_hash)
            stats["dup"] += 1
            continue
        save_raw(data_dir, item.url, result.html)
        save_markdown(data_dir, doc, topic)
        db.mark(item.url, "fetched", content_hash=doc_hash)
        stats["saved"] += 1
        stats["fetched"] += 1
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl research corpus from RSS seeds")
    parser.add_argument("--topic", required=True, help="topic folder name for output md")
    parser.add_argument("--limit", type=int, default=50, help="max articles to save")
    parser.add_argument("--seeds", help="file with feed URLs, one per line (default: built-in feeds)")
    args = parser.parse_args()

    feeds = load_seeds(Path(args.seeds)) if args.seeds else list(DEFAULT_FEEDS)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = UrlDb(DATA_DIR / "url_db.sqlite")
    fetcher = Fetcher(robots=RobotsCache(), limiter=RateLimiter(min_delay=2.0))
    started = datetime.now(timezone.utc).isoformat()
    stats = crawl(db, fetcher, feeds, args.topic, args.limit, DATA_DIR)
    db.add_run("research_crawl", started, json.dumps(stats))
    db.close()
    print(f"done: {stats}")


if __name__ == "__main__":
    main()
