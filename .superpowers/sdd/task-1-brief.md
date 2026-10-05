### Task 1: Project scaffold + dependencies

**Files:**
- Create: `webcrawler/requirements.txt`
- Create: `webcrawler/.gitignore`
- Create: `webcrawler/core/__init__.py`, `webcrawler/core/sources/__init__.py`
- Create: `webcrawler/tests/__init__.py`, `webcrawler/tests/fixtures/` (empty dir via placeholder file)
- Create: `webcrawler/runners/__init__.py`

**Interfaces:**
- Consumes: nothing.
- Produces: importable empty package `core`; pytest discovery works.

- [ ] **Step 1: Write requirements.txt**

```
feedparser>=6.0
trafilatura>=1.8
httpx>=0.27
pytest>=8.0
```

- [ ] **Step 2: Write .gitignore**

```
data/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Create package files (empty is fine)**

Create the five files listed above; `tests/fixtures/.gitkeep` keeps the fixture dir.

- [ ] **Step 4: Install dependencies**

Run: `pip install -r C:\Opencode\webcrawler\requirements.txt`
Expected: `Successfully installed ...` (feedparser, trafilatura, httpx, pytest + deps).

- [ ] **Step 5: Verify pytest runs**

Run (in `C:\Opencode\webcrawler`): `python -m pytest -q`
Expected: `collected 0 items` / `no tests ran`.

- [ ] **Step 6: Commit**

```powershell
git add webcrawler/requirements.txt webcrawler/.gitignore webcrawler/core webcrawler/runners webcrawler/tests
git commit -m "feat(webcrawler): scaffold project, deps, pytest"
```

---


