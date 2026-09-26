# Design: Opportunity Universe — Static Multi-Page Mirror

Date: 2026-09-25
Status: approved (user selected Approach 1 and supplied the architecture below)
Reference site: https://opportunity-universe.com/en/

## 1. Goal

A pure HTML/CSS/JS mirror of opportunity-universe.com's English site: visually near-identical frontend, full URL parity with the original, functional in-site navigation — while every data-heavy action (search, forms, opportunity/blog detail) redirects to the live original site.

## 2. Hard constraints (from user)

- Build order: (1) Home → (2) Listing/search/type/subject/region/country → (3) Opportunity Detail → (4) Blog list + article → (5) Static pages → (6) Forms → (7) Map/Calendar shell.
- URL structure mirrors the original URLs exactly (`/en/...`).
- Plain HTML page per URL; one shared `style.css`; one shared `components.js` for header, footer, cookie banner, shared UI (no repeated markup where injection works).
- Search and all forms redirect straight to Opportunity Universe with the matching query.
- Opportunity / blog / detail links redirect to the original URL.
- Detail content is condensed/representative only — never scraped or copied verbatim from the original.
- Map/Calendar: clone the UI shell only; real data and complex interaction link out to the original.
- Priority: visual fidelity + functional navigation. Out of scope: backend, database, auth, real data.
- Pure HTML/CSS/JS, no npm, no build step. Images hotlinked from the original's public URLs.

## 3. Location & serving

- Project root: `C:\Opencode\opportunity-universe-clone\`
- Files are served from that root so paths align with the original (`/en/...`).
- Local preview: `python -m http.server 8080` from the project root (SPA-less static server; file:// is not supported because `components.js` injects header/footer).
- The project is a standalone folder inside the C:\Opencode repo; no changes to existing projects.

## 4. URL / page inventory

Pages are grouped into 7 templates. "Local" = page exists in the mirror; "Out" = link/form goes to `https://opportunity-universe.com<same path>`.

### T1 — Home (phase 1)
| Path | Note |
|---|---|
| `/en/` | Full homepage: header, hero search, newsletter band, Featured, Fully Funded, World Map teaser, country eligibility, logo wall, tag clouds, Deadlines Soon, stats/database block, New Opportunities, By Category, By Region, quotes, Create Account, Blog teaser, newsletter CTA, footer, cookie banner. |

Search form and newsletter form on home → Out. All "View All" / category / region / subject chips → **Local** listing pages. Opportunity cards, blog cards, logo-wall items → Out.

### T2 — Listing (phase 2)
One listing template (heading + breadcrumb + filter sidebar/chips + result grid + pagination), instantiated at every list URL:

| Path | Instances |
|---|---|
| `/en/search` | 1 (query params accepted but results are representative) |
| `/en/fully-funded` | 1 |
| `/en/type/<t>` | 9 nav types: scholarship, fellowship, internship, competition, award, summer_school, grant, conference, research_program |
| `/en/subject/<s>` | the ~20 subjects present in the homepage tag clouds + nav |
| `/en/region/<c>` | nam, eur, asi, afr, mea, oce, sam |
| `/en/country/<c>` | the 15 footer countries (in, ng, pk, bd, id, eg, ke, gh, ph, vn, br, mx, tr, de, us) |
| `/en/countries` | country index page |

Thin pages (~40 lines each): shared skeleton + inline page config (title, breadcrumb, counts, chips); `components.js` renders the rest from `data.js`. Instances are emitted by a one-off scaffold script (`tools/scaffold-listings.*`) whose **output is plain static HTML** — no runtime dependency on the script.

Filter interactions inside the listing (type/subject/funding dropdowns, sort, pagination) → Out with the corresponding query string. Card titles → Out. In-site chips/breadcrumbs → Local.

### T3 — Opportunity Detail (phase 3)
| Path | Note |
|---|---|
| `/en/opportunity/<id>-<slug>` | 3 sample pages (e.g. Caltech 2027, IRENA Youth Forum, CERN Doctoral). Condensed representative description (my own wording, 2–3 short paragraphs), organizer/location/deadline metadata row, Apply button → Out. |

All opportunity links elsewhere → Out; sample detail pages are reachable by direct URL and from the detail-page "related" strip.

### T4 — Blog (phase 4)
| Path | Note |
|---|---|
| `/en/blog` | Blog list: card grid, View All |
| `/en/blog/<slug>` | 3 sample article pages: condensed original wording (2–4 paragraphs), back-link to list, "Read on original site" CTA → Out |

Blog cards on Home/Blog list → Out (per user rule); sample articles reachable by direct URL.

### T5 — Static pages (phase 5)
`/en/about`, `/en/faq`, `/en/methodology`, `/en/sponsor`, `/en/pro`, `/en/stories`, `/en/mobility-scholarship`, `/en/privacy`, `/en/imprint` — shared static template: title, hero strip, condensed section content in my own wording, CTA → Out where relevant.

`/en/guide` (PDF) and `/en/login` is Forms; `/en/guide` link in nav → Out directly (no local page).

### T6 — Forms (phase 6)
`/en/login`, `/en/register`, `/en/submit`, `/en/newsletter`, `/en/matcher` — inputs and layout cloned; on submit (or on first interaction for matcher) redirect to the matching original URL with query params where the original supports them.

### T7 — Map & Calendar shells (phase 7)
- `/en/map`: header, title, stats row, filter bar cloned; map area = static placeholder panel (styled box with logo + "Explore the interactive map" CTA → Out).
- `/en/calendar`: header, month nav UI, legend cloned; the event grid shows representative deadline chips and is non-interactive; CTA → Out.

### Not built
- Language versions (`/de/`, `/ar/`, …): the language dropdown links Out to the original.
- `/en/mobility-scholarship` is built (T5); `/en/guide` is Out; any unlisted URL → local `404.html` with a search-style CTA to the original.

## 5. Shared assets

```
opportunity-universe-clone/
  index.html            → redirect to /en/ (meta refresh)
  404.html
  assets/css/style.css      single stylesheet (design tokens: colors, fonts, radii, spacing, breakpoints)
  assets/js/components.js   renders header, footer, cookie banner, opinion cards, newsletter band
  assets/js/data.js         representative datasets (cards, categories, regions, blog teasers)
  en/...                    one folder per URL, index.html inside
  tools/scaffold-listings.* one-off generator for the thin listing pages
  README.md                 how to preview
```

- `components.js` reads a per-page inline config (`<script>window.OU_PAGE = {...}</script>`) for active nav state, page title, breadcrumbs.
- Cookie banner: local UI, Accept/Preferences stored in `localStorage`, never sends data anywhere.
- Design tokens extracted by inspecting the original's rendered CSS (colors, font family, border radii, container width, breakpoints) — the original stylesheet is **not** copied; `style.css` is written from scratch to match the look.

## 6. Link & redirect rules (single source of truth)

| Element | Target |
|---|---|
| Header/footer nav, breadcrumbs, category/region/subject chips, "View All", logo, language list | Local page (Out only for language versions and `/en/guide`) |
| Search form submit (any page) | `https://opportunity-universe.com/en/search?q=…&type=…&subject=…` |
| All forms (login, register, submit, newsletter, matcher) | Matching original URL, with query params where supported |
| Opportunity card title / card / detail links | Original `/en/opportunity/<id>-<slug>` |
| Blog card / article links | Original `/en/blog/<slug>` |
| Logo wall (Harvard, Oxford…), stats block link, map/calendar interactive areas | Original `/en/search?q=…` or matching page |
| Apply / Subscribe / Create account CTAs | Original |

Implementation: `components.js` exposes `OU_OUT(path)` (absolute-URL helper) and every outbound anchor carries `data-out` so a link-check script can verify the rule mechanically.

## 7. Content policy

- Layout, structure, labels, headings, nav items, category names, counts: replicated (functional/factual).
- Descriptions, articles, FAQ answers, about text: **representative, written fresh** — short, same tone, never copied verbatim; each detail page ends with "Continue on the original site" → Out.
- Images (covers, logos, avatars): hotlinked to the original's public URLs; internet required for images.
- Stats numbers: representative values visually close to the original.

## 8. Error handling & robustness

- Unknown local path → `404.html` (styled like the site, CTA to original search).
- Hotlinked image failure → CSS placeholder background behind each `<img>` (gray gradient + icon), so a missing image degrades gracefully.
- If `components.js` fails to load, page still shows its main content (header/footer empty but no JS error cascade) — injection is defensive (`if (el) …`).

## 9. Verification

1. `python -m http.server 8080` → open `/en/` and compare side-by-side with the original at 1440px and 390px widths (screenshot both).
2. `tools/check-links.js` (or PowerShell script): crawl every local HTML file, assert (a) local targets exist, (b) all `data-out` anchors point at `https://opportunity-universe.com`.
3. Click-test the 7 phases in order: nav chips, search submit, one card, one form, cookie banner, 404.

## 10. Out of scope

Backend, database, auth, real search, real map/calendar data, non-English versions, analytics/tracking pixels, npm toolchain, automated pixel-diff CI.
