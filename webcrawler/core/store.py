# core/store.py
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

from core.sources import ExtractedContent

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, fallback: str = "untitled") -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:80] or fallback


def save_raw(data_dir: Path, url: str, html: str) -> Path:
    domain = urlparse(url).netloc.replace(":", "_") or "unknown"
    folder = data_dir / "raw" / domain
    folder.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha1(url.encode("utf-8")).hexdigest() + ".html"
    path = folder / name
    path.write_text(html, encoding="utf-8")
    return path


def save_markdown(data_dir: Path, doc: ExtractedContent, topic: str) -> Path:
    folder = data_dir / "md" / slugify(topic, "general")
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (slugify(doc.title, hashlib.sha1(doc.url.encode()).hexdigest()[:12]) + ".md")
    lines = [
        "---",
        f"title: {doc.title or doc.url}",
        f"url: {doc.url}",
        f"source: {doc.source}",
        f"fetched_at: {doc.fetched_at}",
    ]
    if doc.published:
        lines.append(f"published: {doc.published}")
    if doc.author:
        lines.append(f"author: {doc.author}")
    lines += ["---", "", doc.text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
