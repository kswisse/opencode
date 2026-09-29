# opencode

Personal [OpenCode](https://opencode.ai) workstation — skills, agents, MCP servers, and side projects in one monorepo.

## What's inside

| Path | What it is |
|------|-----------|
| `.opencode/skills/` | 180+ agent skills (UI/UX, data, dev workflows, content, security…) |
| `.opencode/agents/` | Subagent definitions (general, explore, code-reviewer, …) |
| `.claude/skills/` | Hyperresearch V8 — 16-step deep-research pipeline |
| `.opencode/opencode.json` | OpenCode config: MCP servers (autoclip, hyperresearch, context7) |
| `webcrawler/` | Polite multi-source web crawler (Python, see below) |
| `docs/superpowers/` | Design specs + implementation plans for each project |
| `research/` | Hyperresearch vault (markdown notes, runs, final reports) |

The remaining top-level folders are independent side projects (dashboards, games, clones) — each has its own README or docs.

## Web crawler (`webcrawler/`)

A free, local-first crawler for building research corpora: RSS/Atom discovery → polite fetching (robots.txt + 2 s/d rate limit) → trafilatura extraction → dedup (URL + content-hash) → markdown with YAML frontmatter.

**Requirements:** Python 3.12, no API keys, no Docker.

```bash
cd webcrawler
pip install -r requirements.txt

# crawl 10 articles into data/md/<topic>/
python runners/research_crawl.py --topic "AI research" --limit 10

# tests (32)
python -m pytest -q
```

Output layout (gitignored):

```
data/
├── url_db.sqlite          # URL registry: status, dedup hashes, retries
├── raw/<domain>/<sha1>.html
└── md/<topic>/<slug>.md   # title, topic, url, source, dates in frontmatter
```

Design specs and the full 8-task implementation plan live in `docs/superpowers/`.

## Notes

- Personal setup shared as-is; expect rough edges.
- Secrets live in environment variables only — never in this repo.
