import hashlib
import json
import re

import trafilatura

from core.sources import ExtractedContent


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract(html: str, url: str, source: str) -> ExtractedContent | None:
    raw = trafilatura.extract(
        html, url=url, output_format="json", with_metadata=True,
        include_comments=False, include_tables=False,
    )
    if not raw:
        return None
    data = json.loads(raw)
    text = (data.get("text") or "").strip()
    if not text:
        return None
    return ExtractedContent(
        url=url,
        source=source,
        title=(data.get("title") or "").strip(),
        text=text,
        published=data.get("date"),
        author=data.get("author"),
    )
