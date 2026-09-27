from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DiscoveredURL:
    url: str
    source: str
    discovered_at: str = field(default_factory=_utcnow)


@dataclass
class ExtractedContent:
    url: str
    source: str
    title: str
    text: str
    published: str | None = None
    author: str | None = None
    fetched_at: str = field(default_factory=_utcnow)
