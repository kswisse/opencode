# Opportunity Universe — static mirror

Pure HTML/CSS/JS frontend mirror of https://opportunity-universe.com/en/
(layout clone, URL parity; no backend, no build step, no npm). Detail and
article bodies are condensed/original-style text — long-form content is not
copied. Images are hotlinked from the original site.

## Preview

    cd opportunity-universe-clone
    python -m http.server 8080

Open http://localhost:8080/en/

## Page inventory (89 HTML files)

| Template | Count | Example |
|---|---|---|
| Root redirect + 404 | 2 | `/index.html`, `/404.html` |
| Home | 1 | `/en/` |
| Type listing | 17 | `/en/type/scholarship/` |
| Subject listing | 20 | `/en/subject/computer_science/` |
| Region listing | 7 | `/en/region/eur/` |
| Country listing | 15 | `/en/country/vn/` |
| Countries index | 1 | `/en/countries/` |
| Search results (shell) | 1 | `/en/search/` |
| Fully-funded list | 1 | `/en/fully-funded/` |
| Opportunity detail (samples) | 3 | `/en/opportunity/31159-caltech-scholarships-2027/` |
| Blog list + articles | 4 | `/en/blog/` |
| Static content | 10 | `/en/about/`, `/en/faq/` |
| Forms | 5 | `/en/login/`, `/en/register/` |
| Map + Calendar (shells) | 2 | `/en/map/`, `/en/calendar/` |

## Redirect contract

- Listing / category / chips / More-menu / footer navigation stays **local**.
- Search (`/en/search`) and all forms redirect to
  `https://opportunity-universe.com<path>` with query params preserved;
  passwords are never serialized (`data-drop` on the form).
- Opportunity cards, blog cards, Apply buttons, language switcher and other
  CTAs open the original site via `data-out` anchors (`target="_blank"`).
- Map and Calendar are layout shells — their CTAs link out to the live tools.

## Content rules

- Condensed original-style bodies only; never copy long-form content.
- Images hotlink to the original site's `/cover/…` and CDN assets.
- Data lives in `assets/js/data.js` (`OU_TYPES`, subjects, countries, sample
  cards); markup is injected by `assets/js/components.js`.
- Styling is a single shared stylesheet: `assets/css/style.css`
  (class vocabulary mirrors the original: `u-h*`, `u-card`, `u-foot-*`, …).

## Build-time tools

| Tool | When to re-run |
|---|---|
| `tools/scaffold-listings.ps1` | after changing types/subjects/regions/countries in `data.js` — regenerates the 62 listing pages |
| `tools/scaffold-static.ps1` | after editing the static-page content table — regenerates the 10 static pages |
| `tools/check-links.ps1` | before every commit; `-CheckRemote` additionally HEAD-checks `data-out` URLs (network) |

Validate links (ship gate — must exit 0):

    powershell -NoProfile -File tools/check-links.ps1

## Known issues / deliberate deviations

- Only 3 opportunity detail pages and 3 blog articles are cloned as samples;
  every other card links out to the original.
- The original's `/en/login` renders a minimal page without the two-row
  header; the mirror keeps the shared header sitewide for consistency.
- Listing h1s are the plain type label (original appends " 2026/2027").
- Home shows 20 opportunity cards vs the original's 25 (condensed).
- The link checker only scans static HTML; JS-injected links are covered by
  the behavioural audit (search/forms/cards/cookie/burger checks).
- `-CheckRemote` was green at build time; network-dependent pages on the
  original site may change later.
