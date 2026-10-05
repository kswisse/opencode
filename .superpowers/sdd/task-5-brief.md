### Task 5: store â€” raw + markdown output (TDD)

**Files:**
- Create: `webcrawler/core/store.py`
- Test: `webcrawler/tests/test_store.py`

**Interfaces:**
- Consumes: `ExtractedContent` (Task 4).
- Produces (Task 8 relies on):
  - `save_raw(data_dir: Path, url: str, html: str) -> Path` â†’ `data/raw/<domain>/<sha1-of-url>.html`
  - `save_markdown(data_dir: Path, doc: ExtractedContent, topic: str) -> Path` â†’ `data/md/<slug(topic)>/<slug(title)>.md` with YAML frontmatter; returns path.

- [ ] **Step 1: Write failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `python -m pytest tests/test_store.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.store'`.

- [ ] **Step 3: Implement core/store.py**

```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_store.py -q`
Expected: `3 passed`.

- [ ] **Step 5: Commit**

```powershell
git add webcrawler/core/store.py webcrawler/tests/test_store.py
git commit -m "feat(webcrawler): store raw html + frontmattered markdown"
```

---


