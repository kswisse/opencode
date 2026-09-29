# tests/test_store.py
from core.sources import ExtractedContent
from core.store import save_raw, save_markdown

def make_doc():
    return ExtractedContent(
        url="https://blog.example.com/posts/1",
        source="news",
        title="Hello World!",
        text="Body paragraph one.\n\nBody paragraph two.",
        published="2026-09-01",
        author="Jane",
    )

def test_save_raw_creates_domain_folder(tmp_path):
    path = save_raw(tmp_path, "https://blog.example.com/posts/1", "<html>x</html>")
    assert path.exists()
    assert path.parent.name == "blog.example.com"
    assert path.read_text(encoding="utf-8") == "<html>x</html>"

def test_save_markdown_writes_frontmatter_and_body(tmp_path):
    path = save_markdown(tmp_path, make_doc(), "RAG architecture")
    assert path.exists()
    assert path.parent.name == "rag-architecture"
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---")
    assert "title: Hello World!" in content
    assert "url: https://blog.example.com/posts/1" in content
    assert "source: news" in content
    assert "Body paragraph one." in content

def test_save_markdown_filename_is_slug(tmp_path):
    path = save_markdown(tmp_path, make_doc(), "RAG architecture")
    assert path.name == "hello-world.md"

def test_save_raw_neutralizes_path_traversal(tmp_path):
    path = save_raw(tmp_path, "https://..\\../evil", "<html>x</html>")
    resolved = path.resolve()
    assert resolved.is_relative_to(tmp_path.resolve())
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "<html>x</html>"

def test_save_markdown_escapes_yaml_title(tmp_path):
    doc = make_doc()
    doc.title = 'Hello: World "quoted"\nline2'
    path = save_markdown(tmp_path, doc, "RAG architecture")
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")
    fences = [i for i, line in enumerate(lines) if line == "---"]
    assert fences[0] == 0
    assert len(fences) == 2
    title_line = next(line for line in lines if line.startswith("title:"))
    assert title_line.startswith('title: "')
    assert title_line.endswith('"')
    assert 'Hello: World \\"quoted\\"\\nline2' in title_line

def test_save_markdown_writes_topic_frontmatter(tmp_path):
    path = save_markdown(tmp_path, make_doc(), "RAG architecture")
    lines = path.read_text(encoding="utf-8").split("\n")
    fences = [i for i, line in enumerate(lines) if line == "---"]
    frontmatter = lines[1:fences[1]]
    assert frontmatter[0] == "topic: RAG architecture"

def test_save_markdown_quotes_yaml_trigger_titles(tmp_path):
    for title in ("Issue #42", "#1 reason", "- dashed"):
        doc = make_doc()
        doc.title = title
        path = save_markdown(tmp_path, doc, "RAG architecture")
        lines = path.read_text(encoding="utf-8").split("\n")
        title_line = next(line for line in lines if line.startswith("title:"))
        assert title_line.startswith('title: "'), title

def test_save_markdown_same_title_distinct_urls_writes_both(tmp_path):
    first = make_doc()
    second = make_doc()
    second.url = "https://blog.example.com/posts/2"
    path1 = save_markdown(tmp_path, first, "RAG architecture")
    first_content = path1.read_text(encoding="utf-8")
    path2 = save_markdown(tmp_path, second, "RAG architecture")
    assert path1 != path2
    assert path1.exists()
    assert path2.exists()
    assert path2.name.startswith("hello-world-")
    assert path1.read_text(encoding="utf-8") == first_content
    assert "url: https://blog.example.com/posts/2" in path2.read_text(encoding="utf-8")
