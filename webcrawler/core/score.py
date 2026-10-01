# core/score.py
import json
import os
import re

from core.sources import ExtractedContent

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_RATIO_THRESHOLD = 50  # below this, keep everything


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def bm25_filter(docs: list[ExtractedContent], topic: str,
                keep_ratio: float = 0.4, min_keep: int = 20
                ) -> list[tuple[ExtractedContent, float]]:
    if not docs:
        return []
    if len(docs) <= 2:
        return [(d, 1.0) for d in docs]
    from rank_bm25 import BM25L
    corpus = [tokenize(f"{d.title} {d.text[:600]}") for d in docs]
    bm25 = BM25L(corpus)
    scores = bm25.get_scores(tokenize(topic))
    keep = (len(docs) if len(docs) <= _RATIO_THRESHOLD
            else max(int(len(docs) * keep_ratio), min_keep))
    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
    return ranked[:keep]
