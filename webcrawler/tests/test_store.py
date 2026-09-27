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
    assert lines[1].startswith('title: "')
    assert lines[1].endswith('"')
    assert 'Hello: World \\"quoted\\"\\nline2' in lines[1]
