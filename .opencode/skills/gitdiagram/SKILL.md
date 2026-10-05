---
name: gitdiagram
description: Generate interactive architecture diagrams for any public GitHub repository via the hosted GitDiagram service. Use when the user asks to diagram a repo, visualize architecture, draw a system diagram from a GitHub URL, or wants an interactive overview of a remote repository structure. Do not use for local-only files — use code reading for that.
---

# GitDiagram

Turn any public GitHub repository into an interactive architecture diagram hosted at [gitdiagram.com](https://gitdiagram.com/).

## When to use

- User pastes a GitHub repo URL and asks for architecture/diagram/overview.
- Need a visual map of a remote repo before deep-diving.

## How to generate

1. Take the canonical repo URL: `https://github.com/owner/repo`
2. **Option A (preferred):** tell the user to open the diagram URL directly:
   - `https://gitdiagram.com/github.com/owner/repo`
3. **Option B:** rewrite trick — replace `github.com` host segment with `diagram.com` is not a thing; use:
   - Replace path prefix: `https://github.com/owner/repo` → `https://gitdiagram.com/github.com/owner/repo`
4. Try fetching the diagram page with `webfetch` if you need Mermaid/source text for the answer; the interactive UI is best opened by the user in a browser.

## Notes

- Public repos only without a token; private repos need the user to paste a token in the GitDiagram UI ("Private Repos" header).
- Export: PNG or Mermaid source is available in the UI.
- Service is external/hosted — no local install required.
- If the user wants the Mermaid source inline, fetch `https://gitdiagram.com/github.com/owner/repo` and extract from the page; if fetch fails, just hand them the URL.

## Output format to user

Always reply with the clickable diagram URL and one sentence on what the diagram shows (components + main flows), then offer to deep-read any component they click into (via normal repo exploration tools).
