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


def _safe_domain(netloc: str) -> str:
    domain = netloc.replace(":", "_")
    if not domain or set(domain) <= {"."} or "/" in domain or "\\" in domain:
        return "unknown"
    return domain


def _yaml_value(value) -> str:
    text = "" if value is None else str(value)
    needs_quotes = (
        ": " in text
        or text.endswith(":")
        or '"' in text
        or "\n" in text
        or text != text.strip()
    )
    if needs_quotes:
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    return text


def save_raw(data_dir: Path, url: str, html: str) -> Path:
    domain = _safe_domain(urlparse(url).netloc)
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
        f"title: {_yaml_value(doc.title or doc.url)}",
        f"url: {_yaml_value(doc.url)}",
        f"source: {_yaml_value(doc.source)}",
        f"fetched_at: {_yaml_value(doc.fetched_at)}",
    ]
    if doc.published:
        lines.append(f"published: {_yaml_value(doc.published)}")
    if doc.author:
        lines.append(f"author: {_yaml_value(doc.author)}")
    lines += ["---", "", doc.text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
