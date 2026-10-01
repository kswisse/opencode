# tests/test_score.py
from core.sources import ExtractedContent
from core.score import bm25_filter, tokenize


def _doc(url: str, title: str, text: str) -> ExtractedContent:
    return ExtractedContent(url=url, source="seeds", title=title, text=text)


def test_tokenize_lowercases_and_splits():
    assert tokenize("RAG Architecture 2026") == ["rag", "architecture", "2026"]


def test_tokenize_keeps_vietnamese_words():
    tokens = tokenize("kiến trúc RAG")
    assert "rag" in tokens
    assert any(t.startswith("ki") for t in tokens)


def test_bm25_empty_input():
    assert bm25_filter([], "topic") == []


def test_bm25_orders_relevant_docs_first():
    docs = [
        _doc("https://x/cooking", "Pasta", "tomato sauce recipe for pasta dinner"),
        _doc("https://x/rag1", "RAG systems", "retrieval augmented generation rag llm architecture"),
        _doc("https://x/garden", "Tomatoes", "how to grow tomatoes in a small garden"),
        _doc("https://x/rag2", "RAG pipeline", "rag retrieval with vector databases and llm"),
    ]
    kept = bm25_filter(docs, "rag retrieval llm")
    assert len(kept) == 4  # <= 50 docs: keep all, but order matters
    top_urls = [d.url for d, _ in kept[:2]]
    assert top_urls == ["https://x/rag1", "https://x/rag2"]


def test_bm25_applies_ratio_above_50_docs():
    docs = [_doc(f"https://x/{i}", f"T{i}", "unrelated filler text about weather") for i in range(100)]
    docs[50] = _doc("https://x/hit", "Hit", "quantum entanglement experiment results")
    kept = bm25_filter(docs, "quantum entanglement")
    assert len(kept) == 40
    assert kept[0][0].url == "https://x/hit"


def test_bm25_single_doc_returns_it():
    d = _doc("https://x/one", "One", "only page")
    assert bm25_filter([d], "anything") == [(d, 1.0)]
