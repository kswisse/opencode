# Opportunity Universe Static Mirror — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pure HTML/CSS/JS multi-page mirror of https://opportunity-universe.com/en/ at `C:/Opencode/opportunity-universe-clone/` — visually near-identical, full URL parity, local listing navigation, with search/forms/detail links redirecting to the live original site.

**Architecture:** ~95 static HTML files (one per original URL) share a single `assets/css/style.css`, a single `assets/js/data.js` (representative datasets), and a single `assets/js/components.js` that injects header, footer, cookie banner, card grids and listing bodies into every page (no repeated markup). Two PowerShell scaffold scripts emit thin listing/static pages at build time; runtime is plain HTML/CSS/JS with zero dependencies. Images are hotlinked from the original's public URLs.

**Tech Stack:** HTML5, CSS3, vanilla JS (ES5-compatible), PowerShell 5.1 scaffold/validation scripts, `python -m http.server` for preview.

**Spec:** `docs/superpowers/specs/2026-09-25-opportunity-universe-clone-design.md`

## Global Constraints

- Static multi-page mirror; URL structure matches the original site (`/en/...` under project root `C:/Opencode/opportunity-universe-clone/`).
- ~95 generated static HTML files is acceptable.
- Shared `style.css` and `components.js`; header/footer/cookie/card markup is injected, never duplicated per page.
- Listing/category navigation stays local; search and every form submit redirect to `https://opportunity-universe.com` with the relevant query/form parameters preserved (passwords dropped, never placed in URLs).
- Opportunity and blog cards link to the original site (anchors carry `data-out`).
- Local opportunity/blog detail samples use shortened original-style content, not copied full text.
- Map and Calendar are UI shells with CTAs linking to the original.
- Scaffold scripts are build-time only; final runtime remains plain HTML/CSS/JS.
- No backend, database, authentication, scraper, or runtime dependency.
- Images hotlinked from `https://opportunity-universe.com/...` (absolute URLs).
- No npm, no build step, no framework.
- Link validation must pass with no broken internal/external destinations before declaring complete.
- Visual fidelity first: design tokens copied verbatim from the original's `:root` (Task 1).

## Page inventory (7 templates)

| Template | Paths | Count | Task |
|---|---|---|---|
| T1 Home | `/en/` | 1 | 3–4 |
| T2 Listing | `/en/search`, `/en/fully-funded`, `/en/type/<17>`, `/en/subject/<20>`, `/en/region/<7>`, `/en/country/<15>`, `/en/countries` | 62 | 5 |
| T3 Detail | `/en/opportunity/<3 samples>` | 3 | 6 |
| T4 Blog | `/en/blog` + `/en/blog/<3 samples>` | 4 | 7 |
| T5 Static | about, faq, methodology, sponsor, pro, stories, mobility-scholarship, privacy, imprint | 9 | 8 |
| T6 Forms | login, register, submit, newsletter, matcher | 5 | 9 |
| T7 Shells | map, calendar | 2 | 10 |
| Misc | `index.html`, `404.html`, `en/index.html` counts in T1 | — | 1 |

## File Structure

```
C:/Opencode/opportunity-universe-clone/
  index.html                       meta-refresh → /en/
  404.html                         styled not-found + CTA to original search
  README.md                        preview instructions
  assets/css/style.css             single stylesheet, all pages
  assets/js/data.js                representative datasets (opps, blogs, chips, counts)
  assets/js/components.js          header/footer/cookie/cards/listing/forms injection
  en/index.html                    HOME (full static HTML main content)
  en/...                           one folder per original URL, index.html inside
  tools/scaffold-listings.ps1      build-time generator (62 listing pages incl. countries index)
  tools/scaffold-static.ps1        build-time generator (10 static pages)
  tools/check-links.ps1            link validator — the test harness for every task
```

Page contract consumed by `components.js`:

```html
<div id="ouHeader"></div>
<main id="main"> ...page-specific content... </main>
<div id="ouFooter"></div>
<div id="ouCookie"></div>
<script>window.OU_PAGE = { kind: "home" | "listing" | ..., ...config };</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
```

Head block used by every hand-written page (identical except `<title>`):

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
```

---

### Task 1: Foundation — style.css, shell pages, link checker

**Files:**
- Create: `opportunity-universe-clone/assets/css/style.css`
- Create: `opportunity-universe-clone/index.html`
- Create: `opportunity-universe-clone/404.html`
- Create: `opportunity-universe-clone/en/index.html` (stub; replaced in Task 3)
- Create: `opportunity-universe-clone/README.md`
- Create: `opportunity-universe-clone/tools/check-links.ps1`

**Interfaces:**
- Produces: the class vocabulary every later task uses (`.u-wrap .u-sec .u-grid .u-card .u-band .u-chip .btn ...`); `tools/check-links.ps1` exits 0 = valid (re-run after every task).

- [ ] **Step 1: Create `assets/css/style.css` — part A (tokens, base, header, hero, band)**

```css
/* ===== design tokens (verbatim from opportunity-universe.com :root) ===== */
:root{--space:#070b16;--space-2:#0e1526;--paper:#fff;--paper-2:#f6f7fa;--ink:#171923;
--muted:#68707f;--line:#e6e8ee;--acc:#5684de;--blue:#1e52ba;--blue-deep:#16449f;
--blue-ink:#0f2f73;--blue-pale:#e9f0ff;--gold:#f5cb1fb0;--gold-ink:#4a3a00;--hot:#c23a2f;
--r:4px;--disp:"Inter Tight","Inter",system-ui,sans-serif;--sans:"Inter",system-ui,sans-serif;
--wrap:1180px;--hdr-h:98px}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font:400 15px/1.55 var(--sans);color:var(--ink);background:var(--paper);
-webkit-font-smoothing:antialiased}
img{display:block;max-width:100%}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
h1,h2,h3,h4{font-family:var(--disp);line-height:1.2;margin:0 0 .5em;color:var(--ink)}
p{margin:0 0 1em}
ul{margin:0;padding:0;list-style:none}
button,input,select,textarea{font:inherit}
.u-wrap{max-width:var(--wrap);margin:0 auto;padding:0 20px}
.u-sec{padding:54px 0}
.u-sec-tight-b{padding-bottom:20px}
.u-sec-head{display:grid;grid-template-columns:1fr auto;gap:4px 20px;align-items:center;margin-bottom:24px}
.u-sec-head h2{font-size:26px;font-weight:800;letter-spacing:-.01em;margin:0}
.u-sec-head h2 i{color:var(--gold);font-size:20px}
.u-sec-head p{margin:2px 0 0;color:var(--muted);font-size:14px}
.u-sec-month{font-weight:600;color:var(--muted);font-size:17px}
.u-more{font:700 13px var(--sans);white-space:nowrap}
.u-note{color:var(--muted);font-size:12.5px}
/* buttons */
.btn{display:inline-flex;align-items:center;gap:7px;font:700 14px var(--sans);
padding:11px 20px;border-radius:var(--r);border:1px solid transparent;cursor:pointer;
transition:background .15s,border-color .15s,color .15s}
.btn-primary{background:var(--blue);color:#fff}
.btn-primary:hover{background:var(--blue-deep);text-decoration:none;color:#fff}
.btn-ghost{background:transparent;color:var(--ink);border-color:var(--line)}
.btn-ghost:hover{border-color:var(--muted);text-decoration:none}
.btn-gold{background:linear-gradient(180deg,#ffe066,#f5cb1f);color:#3a2d00;border:none}
.btn-gold:hover{filter:brightness(1.04);text-decoration:none}
/* header */
.u-header{background:#000;color:#e9ecf5;position:sticky;top:0;z-index:400;
border-bottom:1px solid rgba(255,255,255,.09)}
.u-hwrap{width:100%;margin:0;padding:0 34px}
.u-hgrid{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;column-gap:30px}
.u-brand{display:inline-flex;align-items:center;gap:10px}
.u-brand:hover{text-decoration:none}
.u-brandmark{width:42px;height:42px;border-radius:8px;background:var(--space-2)}
.u-brand-name{display:flex;flex-direction:column;font:800 16.5px/1.08 var(--disp);color:#fff;
letter-spacing:.01em}
.u-brand-name span:last-child{color:var(--acc)}
.u-hrow{grid-column:2;display:flex;align-items:center;gap:14px}
.u-hrow1{min-height:66px;gap:14px}
.u-nav1{display:flex;gap:6px;flex-wrap:wrap;align-items:center;flex:1}
.u-navbtn{display:inline-flex;align-items:center;gap:8px;font:500 13.5px var(--sans);
color:#d5dae8;white-space:nowrap;background:none;border:1px solid rgba(255,255,255,.12);
border-radius:5px;padding:7px 11px;cursor:pointer;transition:color .15s,background .15s,border-color .15s}
.u-navbtn i{font-size:12.5px;color:var(--acc);transition:color .15s}
.u-navbtn:hover{border-color:rgba(86,132,222,.8);text-decoration:none}
.u-navmore{position:relative}
.u-navmore-menu{display:none;position:absolute;left:-14px;top:calc(100% + 12px);min-width:250px;
background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:3px;padding:6px;
box-shadow:0 16px 38px -12px rgba(6,10,24,.45);z-index:70}
.u-navmore-menu::before{content:"";position:absolute;bottom:100%;inset-inline:0;height:14px}
.u-navmore-menu a{display:flex;gap:11px;align-items:center;color:var(--ink);font:600 13.5px var(--sans);
padding:10px 12px;border-radius:2px;white-space:nowrap}
.u-navmore-menu a:hover{background:var(--paper-2);color:var(--blue);text-decoration:none}
.u-navmore.open .u-navmore-menu,.u-navmore:hover .u-navmore-menu,
.u-navmore:focus-within .u-navmore-menu{display:block}
.u-h1-right{display:flex;align-items:center;gap:14px;margin-inline-start:auto}
.u-lang{position:relative}
.u-lang summary{list-style:none;cursor:pointer;display:inline-flex;gap:7px;align-items:center;
font:700 12.5px var(--sans);color:#d5dae8;border:1px solid rgba(255,255,255,.16);
border-radius:8px;padding:7px 10px;transition:border-color .15s,color .15s}
.u-lang summary::-webkit-details-marker{display:none}
.u-lang summary:hover{color:#fff;border-color:rgba(86,132,222,.5)}
.u-lang .fi{font-size:14px;border-radius:2px}
.u-lang-menu{display:none;position:absolute;right:0;top:calc(100% + 8px);width:200px;
max-height:68vh;overflow:auto;background:#fff;color:var(--ink);border:1px solid var(--line);
border-radius:var(--r);padding:6px;box-shadow:0 14px 34px -12px rgba(6,10,24,.4);z-index:90}
.u-lang[open] .u-lang-menu{display:block}
.u-lang-menu a{display:flex;gap:10px;align-items:center;color:var(--ink);font:500 13.5px var(--sans);
padding:8px 10px;border-radius:3px}
.u-lang-menu a:hover{background:var(--paper-2);text-decoration:none}
.u-lang-menu a.on{font-weight:700}
.u-signin{font:600 13.5px var(--sans);color:#d5dae8;padding:7px 6px;white-space:nowrap}
.u-signin:hover{color:#fff}
.u-join{font:700 13.5px var(--sans);background:var(--blue);color:#fff;padding:9px 18px;
border-radius:var(--r);white-space:nowrap}
.u-join:hover{background:var(--blue-deep);text-decoration:none;color:#fff}
.u-burger{display:none;flex-direction:column;gap:4px;background:none;border:0;cursor:pointer;padding:6px}
.u-burger span{display:block;width:22px;height:2px;background:#e9ecf5}
.u-hrow2{min-height:32px;gap:24px;border-top:1px solid rgba(255,255,255,.10)}
.u-nav2{display:flex;gap:22px;flex:1;overflow-x:auto;scrollbar-width:none}
.u-nav2::-webkit-scrollbar{display:none}
.u-nav2 a{font:400 11.5px var(--sans);color:#aeb6c9;white-space:nowrap;padding:4px 0;
border-bottom:2px solid transparent;transition:color .15s,border-color .15s}
.u-nav2 a:hover,.u-nav2 a.on{color:var(--acc);border-bottom-color:var(--acc);text-decoration:none}
.u-date{font:600 12px var(--sans);color:#8892a8;white-space:nowrap}
/* hero */
.u-hero{position:relative;overflow:hidden;color:#e9ecf5;display:grid;place-items:center;
isolation:isolate;min-height:calc(100svh - var(--hdr-h));background:#020306}
#ustars{position:absolute;inset:0;z-index:1;width:100%;height:100%;pointer-events:none}
.u-hero-in{position:relative;z-index:3;padding:56px 28px;text-align:center;width:100%}
.u-hero h1{font-size:clamp(34px,5vw,60px);font-weight:800;letter-spacing:-.015em;color:#fff;
text-shadow:0 2px 40px rgba(70,120,235,.45);margin-bottom:0}
.u-gold{color:var(--acc)}
.u-search{display:flex;gap:0;max-width:880px;margin:46px auto 0;background:#fff;
border-radius:var(--r);box-shadow:0 24px 60px -22px rgba(2,6,18,.9);overflow:hidden}
.u-search input[type=search]{flex:1;min-width:0;border:0;padding:16px 18px;font-size:15px;outline:none}
.u-search select{border:0;border-left:1px solid var(--line);padding:0 34px 0 14px;font-size:14px;
background:#fff url("data:image/svg+xml;charset=utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%2368707f' fill='none' stroke-width='1.6'/%3E%3C/svg%3E") no-repeat right 13px center;
appearance:none;-webkit-appearance:none;cursor:pointer;max-width:190px;color:var(--ink)}
.u-search button{background:var(--blue);color:#fff;border:0;padding:0 30px;font:700 15px var(--sans);
cursor:pointer;letter-spacing:.02em}
.u-search button:hover{background:var(--blue-deep)}
.u-stats{display:flex;flex-wrap:wrap;gap:0;justify-content:center;margin-top:44px;padding-top:28px}
.u-stat{min-width:190px;padding:0 34px;border-right:1px solid rgba(255,255,255,.12);text-align:center}
.u-stat:last-child{border-right:0}
.u-stat-n{display:block;font:800 34px/1.1 var(--disp);color:#fff;letter-spacing:-.01em}
.u-stat-n em{font-style:normal;color:var(--acc)}
.u-stat-l{font:500 12.5px var(--sans);color:#8892a8}
/* newsletter band */
.u-band{background:linear-gradient(135deg,var(--blue-ink),var(--blue) 55%,#3f79e8);color:#fff;
padding:34px 0}
.u-band-in{display:grid;grid-template-columns:1.3fr 1fr;gap:26px;align-items:center}
.u-band h2{color:#fff;font-size:23px;margin-bottom:6px}
.u-band p{margin:0;color:#d6e2ff;font-size:14.5px}
.u-band form{display:flex;gap:10px;flex-wrap:wrap}
.u-band input[type=email]{flex:1;min-width:200px;border:0;border-radius:var(--r);padding:13px 15px;font-size:14.5px}
.u-band small{display:flex;gap:14px;width:100%;color:#c9d9ff;font-size:12.5px}
/* ===== cards ===== */
.u-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
.u-grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.u-card{position:relative;background:#fff;border:1px solid var(--line);border-radius:var(--r);
overflow:hidden;display:flex;flex-direction:column;
transition:border-color .18s,box-shadow .22s,transform .22s}
.u-card:hover{border-color:#c9d6f4;box-shadow:0 16px 34px -18px rgba(15,47,115,.35);transform:translateY(-2px)}
.u-card-media{position:relative;aspect-ratio:16/7.2;overflow:hidden;display:block;background:var(--space-2)}
.u-card-media img{width:100%;height:100%;object-fit:cover;background:linear-gradient(135deg,var(--space-2),#1b2440)}
.u-card-reveal{position:absolute;inset:0;background:rgba(4,8,20,.86);color:#dfe6f7;
display:flex;flex-direction:column;justify-content:flex-end;gap:8px;padding:13px;
opacity:0;transition:opacity .2s;font-size:12.5px;line-height:1.45}
.u-card:hover .u-card-reveal{opacity:1}
.u-card-reveal-cta{font:700 12.5px var(--sans);color:var(--gold);letter-spacing:.03em}
.u-save{position:absolute;top:8px;right:8px;z-index:5;width:28px;height:28px;display:grid;
place-items:center;background:rgba(255,255,255,.92);border:1px solid var(--line);
border-radius:5px;color:var(--muted);cursor:pointer}
.u-save:hover{color:var(--hot)}
.u-card-b{padding:11px 13px 13px;display:flex;flex-direction:column;gap:6px;flex:1}
.u-card-tags{display:flex;gap:6px;flex-wrap:wrap}
.u-tag{font:700 8.5px/1 var(--sans);letter-spacing:.05em;text-transform:uppercase;color:var(--muted);
border:1px solid var(--line);padding:3.5px 6px;border-radius:3px;white-space:nowrap;background:var(--paper-2)}
.u-tag-gold{color:var(--gold-ink);background:#fff8d6;border-color:#f2e3a0}
.u-card-b h3{font-size:15.5px;font-weight:700;margin:0}
.u-card-b h3 a{color:var(--ink)}
.u-card-b h3 a:hover{color:var(--blue);text-decoration:none}
.u-card-meta{margin:0;color:var(--muted);font-size:12.5px;line-height:1.4}
.u-card-dl{margin:auto 0 0;font:600 12px var(--sans);color:var(--ink);display:flex;
align-items:center;gap:6px;padding-top:4px}
.u-card-dl.hot{color:var(--hot)}
/* map teaser / country / logos / chips */
.u-mapbox{background:radial-gradient(1000px 420px at 50% 0,#132042,var(--space));
border:1px solid rgba(255,255,255,.1);border-radius:10px;color:#dfe6f7;padding:38px 30px;text-align:center}
.u-mapbox h2{color:#fff}
.u-mapstats{display:flex;gap:44px;justify-content:center;margin:20px 0 24px}
.u-mapstats b{display:block;font:800 34px var(--disp);color:var(--gold)}
.u-mapstats span{font-size:12.5px;color:#9aa5bf;text-transform:uppercase;letter-spacing:.06em}
.u-country{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:22px}
.u-country select{border:1px solid var(--line);border-radius:var(--r);padding:9px 13px;background:#fff;font-size:14px}
.u-logos{display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:center;
background:var(--paper-2);border:1px solid var(--line);border-radius:8px;padding:22px}
.u-logos img{height:34px;width:auto;filter:grayscale(1);opacity:.75;transition:.2s;
background:#fff;padding:3px 7px;border-radius:4px}
.u-logos a:hover img{filter:none;opacity:1}
.u-clouds{display:flex;flex-direction:column;gap:12px}
.u-cloud{display:flex;flex-wrap:wrap;gap:9px;justify-content:center}
.u-chip{font:600 13px var(--sans);border:1px solid var(--line);background:#fff;color:var(--ink);
padding:7px 13px;border-radius:999px;transition:.15s}
.u-chip:hover{border-color:var(--blue);color:var(--blue);text-decoration:none}
.u-chip b{color:var(--muted);font-weight:600;margin-left:6px;font-size:12px}
/* deadlines strip */
.u-dl-list{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.u-dl-item{display:flex;gap:11px;align-items:center;border:1px solid var(--line);
border-radius:var(--r);padding:9px 11px;background:#fff;transition:.15s}
.u-dl-item:hover{border-color:#c9d6f4;text-decoration:none}
.u-dl-item img{width:56px;height:42px;object-fit:cover;border-radius:3px;background:var(--space-2);flex:none}
.u-dl-item b{display:block;font:700 11px var(--sans);color:var(--hot);text-transform:uppercase;letter-spacing:.04em}
.u-dl-item span{display:block;font:600 13px/1.35 var(--sans);color:var(--ink)}
.u-dl-item small{color:var(--muted);font-size:11.5px}
/* compare block */
.u-compare{background:var(--space);color:#c6cde0;border-radius:10px;padding:34px 30px}
.u-compare h2{color:#fff}
.u-cmp-rows{display:flex;flex-direction:column;gap:14px;margin:22px 0 8px}
.u-cmp-row{display:grid;grid-template-columns:210px 1fr 92px;gap:14px;align-items:center;font-size:14px}
.u-cmp-bar{height:16px;background:rgba(255,255,255,.08);border-radius:999px;overflow:hidden}
.u-cmp-bar i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--blue),#5f95f2)}
.u-cmp-val{font:800 15px var(--disp);color:#fff;text-align:right}
.u-cmp-10x{font:800 22px var(--disp);color:var(--gold);margin-top:14px}
.u-chart{display:flex;gap:5px;align-items:flex-end;height:110px;margin-top:22px}
.u-chart i{flex:1;background:linear-gradient(180deg,#3f79e8,#1e52ba);border-radius:3px 3px 0 0;opacity:.85}
.u-chart-lbls{display:flex;justify-content:space-between;color:#7f8aa3;font-size:11px;margin-top:6px}
/* quotes / account / blog */
.u-quotes{display:flex;flex-direction:column;align-items:center;gap:36px;max-width:660px;margin:0 auto}
.u-quote{text-align:center}
.u-quote blockquote{margin:0 0 14px;font:600 21px/1.5 var(--disp);color:var(--ink);letter-spacing:-.01em}
.u-quote-by{display:flex;gap:11px;align-items:center;justify-content:center;font-size:13.5px;color:var(--muted)}
.u-quote-by img{width:44px;height:44px;border-radius:50%;object-fit:cover;background:var(--line)}
.u-quote-by b{color:var(--ink);display:block;font-size:14px}
.u-account{background:linear-gradient(135deg,#0d1830,#123a86);border-radius:12px;color:#d9e3fb;
padding:44px 40px;display:grid;grid-template-columns:1.4fr 1fr;gap:30px;align-items:center}
.u-account h2{color:#fff;font-size:28px}
.u-account ul li{padding:5px 0;font-size:14.5px}
.u-account ul li::before{content:"\2713  ";color:#7fe0a5;font-weight:700}
.u-account .u-kicker{display:inline-block;background:rgba(245,203,31,.16);color:var(--gold);
font:700 11.5px var(--sans);letter-spacing:.08em;text-transform:uppercase;padding:5px 11px;border-radius:999px;margin-bottom:12px}
.u-blog-card{border:1px solid var(--line);border-radius:var(--r);overflow:hidden;background:#fff;
display:flex;flex-direction:column;transition:.18s}
.u-blog-card:hover{box-shadow:0 16px 34px -18px rgba(15,47,115,.35);text-decoration:none}
.u-blog-media{aspect-ratio:16/8;overflow:hidden;background:var(--paper-2);display:block}
.u-blog-media img{width:100%;height:100%;object-fit:cover}
.u-blog-card .u-card-b h3{font-size:16.5px}
.u-blog-date{color:var(--muted);font-size:12.5px;margin-top:auto}
/* footer */
.u-footer{background:#000;color:#aeb6c9;padding:50px 0 24px}
.u-foot-grid{display:grid;grid-template-columns:1.6fr 1fr 1fr 1fr 1fr;gap:30px}
.u-footer .u-brand-name{font-size:13.5px}
.u-footer .u-brandmark{width:34px;height:34px}
.u-foot-blurb{font-size:13.5px;line-height:1.6;color:#8d96ad;margin:14px 0}
.u-foot-contact li{display:flex;gap:9px;align-items:center;font-size:13.5px;padding:4px 0}
.u-foot-contact a{color:#aeb6c9}
.u-social{display:flex;gap:12px;margin-top:14px}
.u-social a{color:#8d96ad}
.u-social a:hover{color:#fff}
.u-foot-h{display:block;font:700 12px var(--sans);text-transform:uppercase;letter-spacing:.09em;
color:#fff;margin-bottom:13px}
.u-foot-grid div a{display:block;color:#aeb6c9;font-size:13.5px;padding:5px 0}
.u-foot-grid a:hover{color:#fff;text-decoration:none}
.u-foot-bottom{display:flex;gap:12px;align-items:center;justify-content:center;
border-top:1px solid rgba(255,255,255,.09);margin-top:36px;padding-top:20px;font-size:13px;color:#7f8aa3}
.u-foot-sep{color:#3a4155}
/* cookie banner */
.u-cc{position:fixed;inset-inline:0;bottom:0;z-index:60;background:var(--paper);
border-top:1px solid var(--line);box-shadow:0 -10px 30px rgba(12,18,40,.08)}
.u-cc-in{max-width:var(--wrap);margin:0 auto;padding:16px 20px;display:flex;gap:18px;
align-items:center;flex-wrap:wrap}
.u-cc-text{flex:1;min-width:260px;margin:0;font-size:13.5px;color:var(--muted)}
.u-cc-acts{display:flex;gap:10px}
.u-cc-prefs{width:100%;display:flex;gap:18px;flex-wrap:wrap;border-top:1px dashed var(--line);
padding-top:14px;margin-top:4px}
.u-cc-opt{flex:1;min-width:250px;display:flex;justify-content:space-between;gap:14px;
align-items:center;font-size:13.5px}
.u-cc-opt span{display:block;color:var(--muted);font-size:12.5px}
.u-cc-on{font:700 11.5px var(--sans);color:#1f8a53;text-transform:uppercase;letter-spacing:.05em}
/* listing pages */
.u-crumb{font-size:13px;color:var(--muted);padding:18px 0 0}
.u-crumb a{color:var(--muted)}
.u-crumb a:hover{color:var(--blue)}
.u-lay{display:grid;grid-template-columns:250px minmax(0,1fr);gap:26px;padding:22px 0 50px;align-items:start}
.u-filters{border:1px solid var(--line);border-radius:8px;background:var(--paper-2);padding:18px;
display:flex;flex-direction:column;gap:14px;position:sticky;top:120px}
.u-filters h4{font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0}
.u-filters select{width:100%;border:1px solid var(--line);border-radius:var(--r);padding:9px 11px;background:#fff;font-size:14px}
.u-res-head{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:16px;flex-wrap:wrap}
.u-res-head h1{font-size:27px;margin:0}
.u-res-count{font:600 14px var(--sans);color:var(--muted)}
.u-pager{display:flex;gap:8px;justify-content:center;padding:26px 0 0}
.u-pager a,.u-pager span{border:1px solid var(--line);border-radius:var(--r);padding:8px 14px;
font:600 14px var(--sans);color:var(--ink);background:#fff}
.u-pager .on{background:var(--blue);border-color:var(--blue);color:#fff}
.u-apply-bar{display:flex;gap:14px;align-items:center;justify-content:space-between;flex-wrap:wrap;
background:var(--blue-pale);border:1px solid #cfdcff;border-radius:8px;padding:16px 18px;margin-bottom:18px}
/* detail pages */
.u-detail{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:30px;padding:26px 0 56px;align-items:start}
.u-detail-head img{width:100%;aspect-ratio:16/7;object-fit:cover;border-radius:8px;background:var(--space-2);margin-bottom:20px}
.u-detail-head h1{font-size:32px;letter-spacing:-.015em}
.u-meta-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}
.u-detail-body{font-size:15.5px;line-height:1.7}
.u-detail-body h2{font-size:20px;margin-top:28px}
.u-side{border:1px solid var(--line);border-radius:8px;padding:20px;background:var(--paper-2);
display:flex;flex-direction:column;gap:12px;position:sticky;top:120px}
.u-side dl{margin:0;display:flex;flex-direction:column;gap:11px}
.u-side dt{font:700 11px var(--sans);text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}
.u-side dd{margin:2px 0 0;font:600 14.5px var(--sans);color:var(--ink)}
.u-out-note{background:#fff8d6;border:1px solid #f2e3a0;border-radius:6px;padding:12px 14px;
font-size:13px;color:var(--gold-ink)}
/* blog */
.u-blog-head{padding:30px 0 6px}
.u-blog-head h1{font-size:34px}
.u-article{max-width:760px;margin:0 auto;padding:26px 0 60px}
.u-article h1{font-size:34px;letter-spacing:-.015em}
.u-article-meta{color:var(--muted);font-size:13.5px;margin-bottom:20px}
.u-article img{border-radius:8px;margin-bottom:22px}
.u-article p{font-size:16px;line-height:1.75}
/* static pages */
.u-page-head{background:var(--paper-2);border-bottom:1px solid var(--line);padding:44px 0}
.u-page-head h1{font-size:36px;margin-bottom:8px}
.u-page-head p{color:var(--muted);font-size:15.5px;margin:0;max-width:720px}
.u-prose{max-width:820px;margin:0 auto;padding:34px 0 60px}
.u-prose h2{font-size:22px;margin-top:32px}
.u-prose ul{list-style:disc;padding-left:22px;margin:0 0 1em}
.u-prose li{margin-bottom:7px}
.u-faq details{border:1px solid var(--line);border-radius:6px;margin-bottom:10px;background:#fff}
.u-faq summary{cursor:pointer;padding:14px 16px;font:600 15px var(--sans);list-style:none}
.u-faq summary::after{content:"+";float:right;color:var(--muted)}
.u-faq details[open] summary::after{content:"\2013"}
.u-faq details p{padding:0 16px 14px;margin:0;color:var(--muted);font-size:14.5px}
/* forms */
.u-formcard{max-width:460px;margin:44px auto 60px;border:1px solid var(--line);border-radius:10px;
padding:32px 30px;background:#fff;box-shadow:0 22px 50px -30px rgba(15,47,115,.4)}
.u-formcard.wide{max-width:640px}
.u-formcard h1{font-size:26px;margin-bottom:6px}
.u-sub{color:var(--muted);font-size:14px;margin-bottom:22px}
.u-field{display:flex;flex-direction:column;gap:6px;margin-bottom:15px}
.u-field label{font:600 13.5px var(--sans);color:var(--ink)}
.u-field input,.u-field select,.u-field textarea{border:1px solid var(--line);border-radius:var(--r);
padding:11px 13px;font-size:14.5px;background:#fff}
.u-field input:focus,.u-field textarea:focus,.u-field select:focus{outline:2px solid #cfdcff;border-color:var(--blue)}
.u-formcard .btn{width:100%;justify-content:center;margin-top:6px}
.u-form-alt{text-align:center;font-size:13.5px;color:var(--muted);margin-top:16px}
.u-req{color:var(--hot)}
/* map / calendar shells */
.u-shell{padding:30px 0 60px}
.u-shell-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-end;flex-wrap:wrap;margin-bottom:20px}
.u-shell-head h1{font-size:32px;margin-bottom:4px}
.u-map-view{position:relative;height:min(64vh,560px);border:1px solid var(--line);border-radius:10px;
overflow:hidden;background:
radial-gradient(600px 300px at 20% 30%,#1d2c55,transparent),
radial-gradient(500px 260px at 75% 65%,#16233f,transparent),var(--space);
display:grid;place-items:center;text-align:center;color:#c6cde0;padding:30px}
.u-map-card{background:rgba(7,11,22,.82);border:1px solid rgba(255,255,255,.14);
border-radius:10px;padding:28px 30px;max-width:430px}
.u-map-card h2{color:#fff;font-size:22px}
.u-cal{border:1px solid var(--line);border-radius:10px;overflow:hidden}
.u-cal-top{display:flex;justify-content:space-between;align-items:center;gap:14px;
padding:14px 16px;background:var(--paper-2);border-bottom:1px solid var(--line);flex-wrap:wrap}
.u-cal-top b{font:700 16px var(--disp)}
.u-cal-grid{display:grid;grid-template-columns:repeat(7,1fr)}
.u-cal-h{font:700 11.5px var(--sans);text-transform:uppercase;letter-spacing:.06em;
color:var(--muted);padding:10px;text-align:center;border-bottom:1px solid var(--line);background:#fff}
.u-cal-cell{min-height:96px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);
padding:8px;font-size:12px;background:#fff}
.u-cal-cell:nth-child(7n){border-right:0}
.u-cal-d{color:var(--muted);font-weight:600}
.u-cal-pill{display:block;background:var(--blue-pale);border:1px solid #cfdcff;
color:var(--blue-ink);border-radius:4px;padding:3px 6px;margin-top:5px;font-size:11px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.u-cal-pill.hot{background:#fdeceb;border-color:#f3c7c3;color:var(--hot)}
/* misc */
.u-404{min-height:55vh;display:grid;place-items:center;text-align:center;padding:60px 20px}
.u-404 b{font:800 76px var(--disp);color:var(--line);display:block}
.u-cta-row{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin-top:18px}
[hidden]{display:none!important}
/* responsive */
@media (max-width:1120px){
  .u-grid{grid-template-columns:repeat(4,1fr)}
  .u-dl-list{grid-template-columns:repeat(2,1fr)}
  .u-cmp-row{grid-template-columns:170px 1fr 84px}
}
@media (max-width:980px){
  .u-burger{display:flex}
  .u-hrow1{flex-wrap:wrap;justify-content:flex-end}
  .u-nav1{display:none;width:100%;flex-direction:column;align-items:stretch;order:9}
  .u-hrow1.open .u-nav1{display:flex;padding-bottom:12px}
  .u-navmore-menu{position:static;width:100%;box-shadow:none}
  .u-grid,.u-grid3{grid-template-columns:repeat(2,1fr)}
  .u-band-in,.u-account,.u-detail,.u-lay{grid-template-columns:1fr}
  .u-filters,.u-side{position:static}
  .u-foot-grid{grid-template-columns:1fr 1fr}
.u-hgrid{grid-template-columns:1fr}
.u-hrow{grid-column:auto}
.u-brand{padding-top:10px}
}
@media (max-width:640px){
  .u-hwrap{padding:0 14px}
  .u-grid{grid-template-columns:1fr 1fr;gap:10px}
  .u-search{flex-wrap:wrap;border-radius:8px}
  .u-search input[type=search]{width:100%;border-bottom:1px solid var(--line)}
  .u-search select{max-width:50%;border-left:0;flex:1}
  .u-search button{width:100%;padding:13px}
  .u-stat{border-right:0;padding:6px 16px}
  .u-dl-list{grid-template-columns:1fr}
  .u-foot-grid{grid-template-columns:1fr}
  .u-hero{min-height:auto}
  .u-account{padding:30px 22px}
}
```

- [ ] **Step 2: Create `index.html`, `404.html`, stub `en/index.html`, `README.md`**

`opportunity-universe-clone/index.html`:
```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=/en/">
<title>Opportunity Universe</title></head>
<body><p><a href="/en/">Continue to /en/</a></p></body></html>
```

`opportunity-universe-clone/404.html`:
```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page not found · Opportunity Universe</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="/assets/css/style.css"></head>
<body>
<main class="u-404">
  <div>
    <b>404</b>
    <h1>Page not found</h1>
    <p>This page does not exist in the mirror. Search the live database instead.</p>
    <div class="u-cta-row">
      <a class="btn btn-primary" href="/en/">Back home</a>
      <a class="btn btn-ghost" href="https://opportunity-universe.com/en/search" data-out>Search on original site <i class="fa-solid fa-arrow-right"></i></a>
    </div>
  </div>
</main>
</body></html>
```

Stub `opportunity-universe-clone/en/index.html` (full home replaces it in Tasks 3–4):
```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fully Funded Scholarships &amp; Youth Opportunities Worldwide | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css"></head>
<body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap"><p>Loading…</p></div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"home"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

`opportunity-universe-clone/README.md`:
```markdown
# Opportunity Universe — static mirror

Pure HTML/CSS/JS mirror of https://opportunity-universe.com/en/ (layout clone;
detail content is condensed/original-style and links go to the live site).

## Preview
    cd opportunity-universe-clone
    python -m http.server 8080
Open http://localhost:8080/en/

## Validate links
    powershell -NoProfile -File tools/check-links.ps1

## Rules
- Listing/category navigation stays local.
- Search + forms redirect to https://opportunity-universe.com with query params.
- Opportunity/blog cards link to the original (anchors with data-out).
- Images hotlinked from the original site.
```
- [ ] **Step 3: Create `tools/check-links.ps1`**

```powershell
# Validates every HTML file:
#  - local href/src must resolve to a file under the project root
#  - anchors to opportunity-universe.com must carry data-out
#  - data-out hrefs must start with https://opportunity-universe.com
# Usage: powershell -NoProfile -File tools\check-links.ps1 [-CheckRemote]
param([switch]$CheckRemote)
$root = Split-Path -Parent $PSScriptRoot
$errors = @()
$files = @(Get-ChildItem -Path $root -Recurse -Filter *.html)
foreach ($f in $files) {
  $html = [IO.File]::ReadAllText($f.FullName)
  foreach ($m in [regex]::Matches($html, '<a\b[^>]*>')) {
    $tag = $m.Value
    $href = $null
    if ($tag -match 'href="([^"]*)"') { $href = $Matches[1] }
    if (-not $href) { continue }
    $isOut = $tag -match '\bdata-out\b'
    if ($href -match '^(https?:)?//') {
      if (-not $href.StartsWith('https://opportunity-universe.com')) {
        if ($href -match 'fonts\.googleapis|fonts\.gstatic|cdnjs\.cloudflare|cdn\.jsdelivr|unpkg\.com|images\.pexels\.com|facebook\.com|instagram\.com|linkedin\.com') { continue }
        $errors += "$($f.FullName): foreign link missing data-out -> $href"
      } elseif (-not $isOut) {
        $errors += "$($f.FullName): original-site link missing data-out -> $href"
      } elseif ($CheckRemote) {
        Start-Sleep -Milliseconds 250
        try {
          $r = [Net.WebRequest]::Create($href); $r.Method = 'HEAD'; $r.Timeout = 8000
          $resp = $r.GetResponse(); $resp.Close()
        } catch {
          $code = 0
          if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
          if ($code -ne 405) { $errors += "$($f.FullName): remote broken ($code) -> $href" }
        }
      }
      continue
    }
    if ($href -match '^(#|mailto:|tel:|javascript:)') { continue }
    if ($isOut) { $errors += "$($f.FullName): data-out with non-absolute href -> $href"; continue }
    $path = ($href -split '#')[0]
    if ($path -eq '') { continue }
    $full = Join-Path $root ($path.TrimStart('/').Replace('/', [IO.Path]::DirectorySeparatorChar))
    $ok = if ($path.EndsWith('/')) { Test-Path (Join-Path $full 'index.html') }
          elseif ([IO.Path]::GetExtension($path)) { Test-Path $full }
          else { (Test-Path (Join-Path $full 'index.html')) -or (Test-Path "$full.html") }
    if (-not $ok) { $errors += "$($f.FullName): broken local link -> $href" }
  }
  foreach ($m in [regex]::Matches($html, '<(?:img|script|link)\b[^>]*(?:src|href)="([^"]+)"')) {
    $u = $m.Groups[1].Value
    if ($u -match '^https?://' -or $u -match '^(data:|#)') { continue }
    $full = Join-Path $root ($u.TrimStart('/').Replace('/', [IO.Path]::DirectorySeparatorChar))
    if (-not (Test-Path $full)) { $errors += "$($f.FullName): missing asset -> $u" }
  }
}
if ($errors.Count) { $errors | ForEach-Object { "FAIL $_" }; exit 1 }
"OK: $($files.Count) HTML files, 0 broken links"
exit 0
```

- [ ] **Step 4: Run link checker — must FAIL (proves the checker works)**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: exit 1 with `FAIL ... missing asset -> /assets/js/data.js` and `... missing asset -> /assets/js/components.js` (files created in Task 2).

- [ ] **Step 5: Commit**

```bash
git add opportunity-universe-clone docs/superpowers/specs/2026-09-25-opportunity-universe-clone-design.md docs/superpowers/plans/2026-09-25-opportunity-universe-clone.md
git commit -m "feat(clone): foundation - style tokens, shell pages, link checker"
```

---

### Task 2: data.js + components.js (injection engine)

**Files:**
- Create: `opportunity-universe-clone/assets/js/data.js`
- Create: `opportunity-universe-clone/assets/js/components.js`

**Interfaces:**
- Consumes: `window.OU_PAGE` config set by each page; CSS classes from Task 1.
- Produces (Tasks 3–10 depend on these exact names):
  - `window.OU = { BASE:"https://opportunity-universe.com", localCountries:[15 codes] }`
  - `window.OU_OPPS` (array of opportunity objects), `window.OU_SETS` (id-lists by section), `window.OU_BLOGS`, `window.OU_TYPES`, `window.OU_SUBJECTS`
  - DOM hooks: `#ouHeader #ouFooter #ouCookie`; `[data-cards="setName"]` grids; `[data-cards][data-limit]`; `[data-logos]`; `[data-blogs]`; `[data-dl-list]`; `[data-listing]` container; `select[data-fill="type|subject"]`; `select[data-home-country]`; `form[data-redirect][data-drop]`; `#ustars` canvas.

- [ ] **Step 1: Create `assets/js/data.js`**

```js
/* Representative datasets for the mirror. Titles/facts are factual programme
   names; blurbs are written for this mirror (not copied). Original detail URL:
   https://opportunity-universe.com/en/opportunity/<id>-<slug> */
window.OU = {
  BASE: "https://opportunity-universe.com",
  localCountries: ["in","ng","pk","bd","id","eg","ke","gh","ph","vn","br","mx","tr","de","us"]
};

window.OU_OPPS = [
 {id:31159,slug:"caltech-scholarships-2027",title:"Caltech Scholarships 2027",type:"Scholarship",ff:1,org:"California Institute of Technology (Caltech)",loc:"Pasadena, United States",days:37,cover:"/cover/31159.jpg",blurb:"Financial support for international students joining Caltech undergraduate and doctoral programmes."},
 {id:27017,slug:"irena-youth-forum-2027-fully-funded-delegate-participation",title:"IRENA Youth Forum 2027",type:"Forum",ff:1,org:"International Renewable Energy Agency (IRENA)",loc:"Abu Dhabi, United Arab Emirates",days:5,cover:"/cover/27017.jpg",blurb:"Fully funded delegate spot at IRENA's flagship youth platform on the energy transition."},
 {id:33153,slug:"novo-nordisk-foundation-prize-for-health-science-teachers-at-the-university",title:"Novo Nordisk Foundation Prize for Health Science Teachers",type:"Award",ff:1,org:"Novo Nordisk Foundation",loc:"Denmark",days:52,cover:"/cover/33153.jpg",blurb:"Annual recognition for university educators who raise the bar in health science teaching."},
 {id:29735,slug:"cern-doctoral-student-program-2027",title:"CERN Doctoral Student Program 2027",type:"Fellowship",ff:1,org:"CERN",loc:"Geneva, Switzerland",days:21,cover:"/cover/29735.jpg",blurb:"Paid doctoral research at CERN with full funding for selected students in Switzerland."},
 {id:30710,slug:"vanier-canada-graduate-scholarships",title:"Vanier Canada Graduate Scholarships",type:"Scholarship",ff:1,org:"Vanier Canada Graduate Scholarships",loc:"Canada",days:37,cover:"/cover/30710.jpg",blurb:"Canada's flagship PhD scholarship for world-class doctoral students across all disciplines."},
 {id:30630,slug:"marshall-scholarship-2027",title:"Marshall Scholarship 2027",type:"Scholarship",ff:1,org:"Marshall Aid Commemoration Commission",loc:"United Kingdom",days:4,cover:"/cover/30630.jpg",blurb:"Fully funded postgraduate study for outstanding graduates at universities in the UK."},
 {id:12554,slug:"fully-funded-phd-positions-in-applied-macroeconomics-and-political-economy-at",title:"Fully Funded PhD Positions in Applied Macroeconomics at ETH Zurich",type:"Fellowship",ff:1,org:"ETH Zurich",loc:"Zurich, Switzerland",days:5,cover:"/cover/12554.jpg",blurb:"Doctoral positions in applied macroeconomics and political economy, fully funded at ETH."},
 {id:4385,slug:"knight-hennessy-scholars-program-2027-at-stanford-university-usa",title:"Knight-Hennessy Scholars Program 2027",type:"Scholarship",ff:1,org:"Stanford University",loc:"Stanford, United States",days:11,cover:"/cover/4385.jpg",blurb:"Full funding for any full-time graduate programme at Stanford, plus a leadership community."},
 {id:7703,slug:"fulbright-u-s-student-program",title:"Fulbright U.S. Student Program",type:"Fellowship",ff:1,org:"Institute of International Education",loc:"United States",days:11,cover:"/cover/7703.jpg",blurb:"Grants for individually designed study, research or creative projects abroad."},
 {id:32432,slug:"jsps-postdoctoral-fellowships-for-research-in-japan-standard-program",title:"JSPS Postdoctoral Fellowships for Research in Japan",type:"Fellowship",ff:1,org:"Japan Society for the Promotion of Science",loc:"Japan",days:210,cover:"/cover/32432.jpg",blurb:"Standard fellowships that bring early-career researchers to Japanese labs for 12 months."},
 {id:32986,slug:"heinrich-boll-foundation-scholarships-2027",title:"Heinrich Boll Foundation Scholarships 2027",type:"Scholarship",ff:1,org:"Heinrich Boll Foundation",loc:"Germany",days:112,cover:"/cover/32986.jpg",blurb:"Funded Master's and PhD study in Germany for internationally minded students."},
 {id:31717,slug:"president-s-phd-scholarship",title:"President's PhD Scholarship",type:"Scholarship",ff:1,org:"Imperial College London",loc:"United Kingdom",days:157,cover:"/cover/31717.jpg",blurb:"Fully funded doctoral research at Imperial College London for new PhD applicants."},
 {id:29879,slug:"gates-cambridge-scholarship-2027-2028",title:"Gates Cambridge Scholarship 2027-2028",type:"Scholarship",ff:1,org:"Gates Cambridge Trust",loc:"United Kingdom",days:74,cover:"/cover/29879.jpg",blurb:"Fully funded postgraduate study at Cambridge for international Master's and PhD applicants."},
 {id:32128,slug:"yenching-academy-at-peking-university-2027",title:"Yenching Academy at Peking University 2027",type:"Scholarship",ff:1,org:"Yenching Academy",loc:"Beijing, China",days:66,cover:"/cover/32128.jpg",blurb:"Fully funded master's in China studies at Peking University, with immersion and research."},
 {id:32151,slug:"nasa-hubble-fellowship-programme-nhfp",title:"NASA Hubble Fellowship Programme (NHFP)",type:"Fellowship",ff:1,org:"NASA Hubble Fellowship Program",loc:"United States",days:33,cover:"/cover/32151.jpg",blurb:"Three-year postdoctoral funding for independent astrophysics research at US institutes."},
 {id:33005,slug:"eit-graduate-ellison-scholars-program-2027",title:"EIT Graduate Ellison Scholars Program 2027",type:"Scholarship",ff:1,org:"Ellison Institute of Technology",loc:"United Kingdom",days:67,cover:"/cover/33005.jpg",blurb:"Fully funded PhD at Oxford funded by the Ellison Institute of Technology."},
 {id:33516,slug:"financial-aid-for-international-students-at-the-university-of-richmond-in-the",title:"Financial Aid for International Students at the University of Richmond",type:"Scholarship",ff:1,org:"University of Richmond",loc:"United States",days:129,cover:"/cover/33516.jpg",blurb:"Need-based and merit aid for international undergraduates in the United States."},
 {id:33514,slug:"w-eugene-smith-grant-2026-for-international-photographers-worth-30-000",title:"W. Eugene Smith Grant 2026 (US$30,000)",type:"Grant",ff:1,org:"W. Eugene Smith Fund",loc:"Online",days:17,cover:"/cover/33514.jpg",blurb:"International grant supporting documentary photography projects to completion."},
 {id:32774,slug:"nasa-pathways-internship-program-2027",title:"NASA Pathways Internship Program 2027",type:"Internship",ff:0,org:"NASA",loc:"United States",days:0,cover:"/cover/32774.jpg",blurb:"Paid US government internship pathway for students in STEM and business fields."},
 {id:30480,slug:"google-software-developer-intern",title:"Google Software Developer Intern",type:"Internship",ff:0,org:"Google",loc:"United States",days:0,cover:"/cover/30480.jpg",blurb:"Summer software engineering internship on product teams at Google."},
 {id:30285,slug:"berlin-prize-at-the-american-academy-in-berlin-2027-2028",title:"Berlin Prize at the American Academy in Berlin",type:"Fellowship",ff:1,org:"American Academy in Berlin",loc:"Berlin, Germany",days:0,cover:"/cover/30285.jpg",blurb:"Residential fellowship for scholars, writers and artists at the American Academy in Berlin."},
 {id:30684,slug:"british-chevening-scholarship-2027",title:"British Chevening Scholarship 2027",type:"Scholarship",ff:1,org:"Chevening",loc:"United Kingdom",days:11,cover:"/cover/30684.jpg",blurb:"Fully funded one-year master's in the UK for future leaders from Chevening countries."},
 {id:29865,slug:"erasmus-mundus-mapp-scholarship-2027-2029",title:"Erasmus Mundus MAPP Scholarship 2027-2029",type:"Scholarship",ff:1,org:"Erasmus Mundus",loc:"Europe",days:67,cover:"/cover/29865.jpg",blurb:"Joint master's in public policy delivered across European universities, fully funded."},
 {id:29835,slug:"daad-university-summer-courses-scholarship-2027",title:"DAAD University Summer Courses Scholarship 2027",type:"Summer School",ff:1,org:"DAAD",loc:"Germany",days:35,cover:"/cover/29835.jpg",blurb:"Funded German language and culture summer courses at German universities."}
];

window.OU_SETS = {
  featured: ["31159","27017","33153","29735","30710"],
  funded:   ["30630","12554","4385","7703","29879"],
  newest:   ["33516","33514","32774","30480"],
  country:  ["32432","32986","31717","32128","32151","33005"],
  deadlines:["32774","30480","30285","33514","29835"],
  all: ["31159","27017","33153","29735","30710","30630","12554","4385","7703","32432",
        "32986","31717","29879","32128","32151","33005","33516","33514","32774","30480",
        "30285","30684","29865","29835"]
};

window.OU_BLOGS = [
 {slug:"fully-funded-scholarships-in-europe-for-late-2026-and-2027",title:"Fully Funded Scholarships in Europe for Late 2026 and 2027",date:"24 Sep 2026",img:"https://images.pexels.com/photos/39289023/pexels-photo-39289023.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=627&w=1200",blurb:"A shortlist of funded postgraduate and doctoral routes in the UK, Switzerland and Germany, with the deadlines that matter."},
 {slug:"paid-international-internships-closing-in-october-and-november-2026",title:"Paid international internships closing in October and November 2026",date:"20 Sep 2026",img:"https://images.pexels.com/photos/31968811/pexels-photo-31968811.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=627&w=1200",blurb:"Where paid and fully funded internships still accept applications, grouped by field and closing month."},
 {slug:"fully-funded-scholarships-closing-before-march-2027",title:"Fully Funded Scholarships Closing Before March 2027",date:"17 Sep 2026",img:"https://images.pexels.com/photos/39192305/pexels-photo-39192305.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=627&w=1200",blurb:"Deadlines, study levels and what makes each award worth an application before spring."}
];

window.OU_TYPES = [["","Any type"],["scholarship","Scholarships"],["fellowship","Fellowships"],
 ["grant","Grants"],["competition","Competitions"],["olympiad","Olympiads"],["award","Awards & Prizes"],
 ["conference","Conferences"],["forum","Forums & Summits"],["summer_school","Summer Schools"],
 ["internship","Internships"],["research_program","Research Programmes"],["hackathon","Hackathons"],
 ["workshop","Workshops"],["training","Training Programmes"],["exchange","Exchange Programmes"],
 ["accelerator","Accelerators"],["volunteering","Volunteering"]];

window.OU_SUBJECTS = [["","Any subject"],["computer_science","Computer Science"],
 ["data_science_ai","Data Science / AI"],["engineering","Engineering"],["mathematics","Mathematics"],
 ["physics","Physics"],["chemistry","Chemistry"],["biology","Biology / Life Sciences"],
 ["health","Health / Medicine"],["environment","Environment / Climate"],["economics","Economics / Finance"],
 ["business","Business / Entrepreneurship"],["law","Law"],
 ["political_science","Political Science / International Relations"],["psychology","Psychology"],
 ["design","Design"],["arts","Arts / Photography"],["music","Music"],
 ["journalism","Journalism / Media"],["education","Education"],["agriculture","Agriculture / Food"]];
```

- [ ] **Step 2: Run link checker (still FAIL — components.js missing)**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: exit 1, now only `missing asset -> /assets/js/components.js`.
- [ ] **Step 3: Create `assets/js/components.js`**

```js
(function () {
  "use strict";
  var OU = window.OU || { BASE: "https://opportunity-universe.com", localCountries: [] };
  var P = window.OU_PAGE || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;"); }
  function out(path) { return OU.BASE + path; }

  var NAV1 = [["/en/fully-funded","Fully Funded","fa-star"],["/en/map","World Map","fa-earth-americas"],
    ["/en/calendar","Calendar","fa-calendar-days"],["/en/matcher","Scholarship Matcher","fa-wand-magic-sparkles"],
    ["/en/newsletter","Opportunity Newsletter","fa-envelope"],["/en/blog","Blog","fa-newspaper"]];
  var MORE = [["/en/submit","Submit Opportunity","fa-circle-plus"],["/en/stories","Success Stories","fa-trophy"],
    ["OUT:/en/guide","Opportunity Guide (PDF)","fa-book-open"],["/en/mobility-scholarship","OU Mobility Scholarship - Apply Now","fa-hand-holding-dollar"],
    ["/en/sponsor","For Organisations / Promote","fa-building-columns"],["/en/methodology","How We Find Opportunities","fa-magnifying-glass-chart"],
    ["/en/pro","Pro Membership","fa-crown"],["/en/about","About Us","fa-circle-info"],
    ["/en/contact","Contact","fa-envelope"],["/en/faq","FAQ","fa-circle-question"]];
  var LANGS = [["gb","English","/en/"],["de","Deutsch","/de/"],["sa","العربية","/ar/"],["cn","中文","/zh/"],
    ["fr","Français","/fr/"],["es","Español","/es/"],["it","Italiano","/it/"],["ru","Русский","/ru/"],
    ["pt","Português","/pt/"],["vn","Tiếng Việt","/vi/"],["jp","日本語","/ja/"],["kr","한국어","/ko/"]];
  var NAV2 = [["/en/type/scholarship","Scholarships"],["/en/type/fellowship","Fellowships"],
    ["/en/type/internship","Internships"],["/en/type/competition","Competitions"],
    ["/en/type/award","Awards & Prizes"],["/en/type/summer_school","Summer Schools"],
    ["/en/type/grant","Grants"],["/en/type/conference","Conferences"],
    ["/en/type/research_program","Research Programmes"]];
  var LOGOS = [["harvard-edu","Harvard University","Harvard"],["ox-ac-uk","University of Oxford","Oxford"],
    ["cam-ac-uk","University of Cambridge","Cambridge"],["stanford-edu","Stanford University","Stanford"],
    ["mit-edu","MIT","MIT"],["yale-edu","Yale University","Yale"],["princeton-edu","Princeton University","Princeton"],
    ["columbia-edu","Columbia University","Columbia"],["berkeley-edu","UC Berkeley","Berkeley"],
    ["caltech-edu","Caltech","Caltech"],["ethz-ch","ETH Zurich","ETH Zurich"],["epfl-ch","EPFL","EPFL"],
    ["imperial-ac-uk","Imperial College London","Imperial"],["nasa-gov","NASA","NASA"],
    ["home-cern","CERN","CERN"],["daad-de","DAAD","DAAD"],["chevening-org","Chevening","Chevening"],
    ["fulbright-org","Fulbright","Fulbright"],["un-org","United Nations","UN"],["unesco-org","UNESCO","UNESCO"]];

  /* ---------- header ---------- */
  function headerHTML() {
    var nav1 = NAV1.map(function (n) {
      return '<a class="u-navbtn" href="' + n[0] + '"><i class="fa-solid ' + n[2] + '"></i> ' + n[1] + '</a>';
    }).join("");
    var more = MORE.map(function (n) {
      var href = n[0].indexOf("OUT:") === 0
        ? ' href="' + out(n[0].slice(4)) + '" data-out target="_blank" rel="noopener"'
        : ' href="' + n[0] + '"';
      return '<a' + href + '><i class="fa-solid ' + n[2] + '"></i> ' + n[1] + '</a>';
    }).join("");
    var langs = LANGS.map(function (l) {
      var local = l[2] === "/en/";
      return '<a href="' + (local ? "/en/" : out(l[2])) + '"' + (local ? "" : ' data-out target="_blank" rel="noopener"') +
        '><span class="fi fi-' + l[0] + '"></span> ' + l[1] + '</a>';
    }).join("");
    var crumbStr = (P.crumb || []).map(function (c) { return c[0]; }).join(",");
    var nav2 = NAV2.map(function (n) {
      var on = crumbStr.indexOf(n[0]) >= 0 ? ' class="on"' : '';
      return '<a' + on + ' href="' + n[0] + '">' + n[1] + '</a>';
    }).join("");
    var date = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
    return '' +
'<header class="u-header"><div class="u-hwrap"><div class="u-hgrid">' +
  '<a class="u-brand" href="/en/"><img class="u-brandmark" src="' + out("/assets/logo.png") + '" width="42" height="42" alt="">' +
    '<span class="u-brand-name"><span>Opportunity</span><span>Universe</span></span></a>' +
  '<div class="u-hrow u-hrow1" id="uHrow1">' +
    '<nav class="u-nav1">' + nav1 +
      '<div class="u-navmore" id="uNavMore"><button class="u-navbtn" type="button"><i class="fa-solid fa-ellipsis"></i> More</button>' +
      '<div class="u-navmore-menu">' + more + '</div></div>' +
    '</nav>' +
    '<div class="u-h1-right">' +
      '<details class="u-lang"><summary><span class="fi fi-gb"></span> EN</summary><div class="u-lang-menu">' + langs + '</div></details>' +
      '<a class="u-signin" href="/en/login">Sign In</a><a class="u-join" href="/en/register">Join Free</a>' +
      '<button class="u-burger" id="uBurger" aria-label="Menu"><span></span><span></span><span></span></button>' +
    '</div>' +
  '</div>' +
  '<div class="u-hrow u-hrow2"><nav class="u-nav2">' + nav2 + '</nav><span class="u-date">' + date + '</span></div>' +
'</div></div></header>';
  }

  /* ---------- footer ---------- */
  function footCol(title, links) {
    return "<div><span class='u-foot-h'>" + title + "</span>" + links.map(function (l) {
      var href = l[0].indexOf("OUT:") === 0 ? "OUT:" + l[0].slice(4) : l[0];
      return '<a href="' + href + '">' + l[1] + '</a>';
    }).join("") + "</div>";
  }
  function footerHTML() {
    var explore = footCol("Explore", [["/en/fully-funded","Fully Funded"],["/en/countries","Countries"],
      ["/en/calendar","Calendar"],["/en/map","World Map"],["/en/matcher","Scholarship Matcher"],["/en/newsletter","Newsletter"]]);
    var community = footCol("Community", [["/en/blog","Blog"],["/en/register","Join Free"],["/en/stories","Success Stories"],
      ["OUT:/en/guide","Opportunity Guide (PDF)"],["/en/submit","Submit Opportunity"],["/en/sponsor","For Organisations / Promote"]]);
    var org = footCol("Organisation", [["/en/about","About Us"],["/en/contact","Contact"],["/en/methodology","Methodology"],
      ["/en/faq","FAQ"],["/en/imprint","Imprint"],["/en/privacy","Privacy Policy"]]);
    var students = footCol("Students from", [["/en/country/in","India"],["/en/country/ng","Nigeria"],
      ["/en/country/pk","Pakistan"],["/en/country/vn","Vietnam"],["/en/countries","View All →"]]);
    var html =
'<footer class="u-footer"><div class="u-wrap u-foot-grid">' +
  '<div class="u-foot-brand"><a class="u-brand" href="/en/">' +
    '<img class="u-brandmark" src="' + out("/assets/logo.png") + '" width="34" height="34" alt="">' +
    '<span class="u-brand-name"><span>Opportunity</span><span>Universe</span></span></a>' +
  '<p class="u-foot-blurb">Our engine continuously scans the web, platforms and organisations, so you never miss the opportunity that changes your life.</p>' +
  '<ul class="u-foot-contact"><li><i class="fa-solid fa-envelope"></i><a href="mailto:info@opportunity-universe.com">info@opportunity-universe.com</a></li>' +
  '<li><i class="fa-solid fa-phone"></i><a href="tel:+491776762399">+49 177 6762399</a></li>' +
  '<li><i class="fa-solid fa-location-dot"></i><span>Postfach 762135, 22069 Hamburg, Germany</span></li></ul>' +
  '<div class="u-social">' +
    '<a href="' + out("") + '" data-out target="_blank" rel="noopener" aria-label="Facebook"><i class="fa-brands fa-facebook-f"></i></a>' +
    '<a href="' + out("") + '" data-out target="_blank" rel="noopener" aria-label="Instagram"><i class="fa-brands fa-instagram"></i></a>' +
    '<a href="' + out("") + '" data-out target="_blank" rel="noopener" aria-label="LinkedIn"><i class="fa-brands fa-linkedin-in"></i></a>' +
  '</div></div>' +
  explore + community + org + students +
'</div><div class="u-wrap u-foot-bottom">© 2026 Opportunity Universe ' +
  '<span class="u-foot-sep">·</span><a href="/en/privacy" data-cc-open>Cookie settings</a></div></footer>';
    return html.replace(/href="OUT:([^"]+)"/g, function (m, p) {
      return 'href="' + out(p) + '" data-out target="_blank" rel="noopener"';
    });
  }

  /* ---------- cookie banner ---------- */
  function cookieHTML() {
    return '<div class="u-cc" id="ouCC" hidden><div class="u-cc-in">' +
      '<p class="u-cc-text">We use essential cookies to make our website work. With your consent, we may also use additional cookies to improve the user experience and to analyse website traffic. By clicking on "Accept" you agree to our cookie usage as described in our <a href="/en/privacy">Data Policy</a>. You can customise your cookie settings by clicking on "Preferences".</p>' +
      '<div class="u-cc-acts"><button type="button" class="btn btn-ghost" data-cc="prefs">Preferences</button>' +
      '<button type="button" class="btn btn-primary" data-cc="all">Accept</button></div>' +
      '<div class="u-cc-prefs" id="ouCCPrefs" hidden>' +
      '<div class="u-cc-opt"><div><b>Essential cookies</b><span>Needed for the website to work.</span></div><span class="u-cc-on">Always on</span></div>' +
      '<div class="u-cc-opt"><div><b>Analytics and marketing cookies</b><span>Help us understand how the website is used and measure our campaigns.</span></div>' +
      '<button type="button" class="btn btn-ghost" data-cc="save">Save choices</button></div></div></div></div>';
  }
  function initCookie() {
    var box = $("#ouCC"); if (!box) return;
    if (!localStorage.getItem("ou-cc")) box.hidden = false;
    document.addEventListener("click", function (e) {
      var b = e.target.closest ? e.target.closest("[data-cc],[data-cc-open]") : null;
      if (!b) return;
      if (b.hasAttribute("data-cc-open")) { localStorage.removeItem("ou-cc"); box.hidden = false; return; }
      var a = b.getAttribute("data-cc");
      if (a === "prefs") { var p = $("#ouCCPrefs"); p.hidden = !p.hidden; }
      else { localStorage.setItem("ou-cc", a); box.hidden = true; }
    });
  }

  /* ---------- cards ---------- */
  function oppById(id) {
    var list = window.OU_OPPS || [];
    for (var i = 0; i < list.length; i++) if (String(list[i].id) === String(id)) return list[i];
    return null;
  }
  function oppURL(o) { return out("/en/opportunity/" + o.id + "-" + o.slug); }
  function cardHTML(o) {
    var url = oppURL(o);
    var hot = o.days === 0 ? "Closes today!" : o.days + " days left";
    return '<article class="u-card">' +
      '<a class="u-card-media" href="' + url + '" data-out target="_blank" rel="noopener" tabindex="-1">' +
        '<img src="' + out(o.cover) + '" alt="' + esc(o.title) + '" loading="lazy" width="640" height="360">' +
        '<span class="u-card-reveal"><span class="u-card-reveal-txt">' + esc(o.blurb) + '</span>' +
        '<span class="u-card-reveal-cta">Learn More <i class="fa-solid fa-arrow-right"></i></span></span></a>' +
      '<button class="u-save" type="button" aria-label="Save to my list"><svg viewBox="0 0 24 24" width="15" height="15"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4.2L5 21V4a1 1 0 0 1 1-1z" fill="none" stroke="currentColor" stroke-width="1.7"/></svg></button>' +
      '<div class="u-card-b"><div class="u-card-tags"><span class="u-tag">' + esc(o.type) + '</span>' +
        (o.ff ? '<span class="u-tag u-tag-gold"><i class="fa-solid fa-star"></i> Fully funded</span>' : '') + '</div>' +
      '<h3><a href="' + url + '" data-out target="_blank" rel="noopener">' + esc(o.title) + '</a></h3>' +
      '<p class="u-card-meta">' + esc(o.org) + ' · ' + esc(o.loc) + '</p>' +
      '<p class="u-card-dl' + (o.days === 0 ? ' hot' : '') + '"><svg viewBox="0 0 24 24" width="13" height="13"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M12 7v5l3.5 2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg> ' + hot + '</p></div></article>';
  }
  function renderCards() {
    document.querySelectorAll("[data-cards]").forEach(function (el) {
      var ids = (window.OU_SETS[el.getAttribute("data-cards")] || []).slice(0, +(el.getAttribute("data-limit") || 99));
      el.innerHTML = ids.map(function (id) { var o = oppById(id); return o ? cardHTML(o) : ""; }).join("");
    });
  }
  function renderDeadlines() {
    document.querySelectorAll("[data-dl-list]").forEach(function (el) {
      el.innerHTML = (window.OU_SETS.deadlines || []).map(function (id) {
        var o = oppById(id); if (!o) return "";
        var url = oppURL(o);
        var d = o.days === 0 ? "Closes today!" : o.days + " days left";
        return '<a class="u-dl-item" href="' + url + '" data-out target="_blank" rel="noopener">' +
          '<img src="' + out(o.cover) + '" alt="" loading="lazy">' +
          '<span><b>' + d + '</b><span>' + esc(o.title) + '</span><small>' + esc(o.type) + '</small></span></a>';
      }).join("");
    });
  }
  function renderBlogs() {
    document.querySelectorAll("[data-blogs]").forEach(function (el) {
      el.innerHTML = (window.OU_BLOGS || []).map(function (b) {
        var url = out("/en/blog/" + b.slug);
        return '<a class="u-blog-card" href="' + url + '" data-out target="_blank" rel="noopener">' +
          '<span class="u-blog-media"><img src="' + b.img + '" alt="" loading="lazy"></span>' +
          '<span class="u-card-b"><span class="u-card-tags"><span class="u-tag">Blog</span></span>' +
          '<h3>' + esc(b.title) + '</h3><p class="u-card-meta">' + esc(b.blurb) + '</p>' +
          '<span class="u-blog-date">' + b.date + '</span></span></a>';
      }).join("");
    });
  }
  function renderLogos() {
    document.querySelectorAll("[data-logos]").forEach(function (el) {
      el.innerHTML = LOGOS.map(function (l) {
        return '<a href="' + out("/en/search?q=" + encodeURIComponent(l[2])) + '" data-out target="_blank" rel="noopener" title="' + l[1] + '">' +
          '<img src="' + out("/assets/logos/" + l[0] + ".png") + '" alt="' + l[1] + '" loading="lazy"></a>';
      }).join("");
    });
  }

  /* ---------- auto-filled selects ---------- */
  function fillSelects() {
    document.querySelectorAll("select[data-fill]").forEach(function (sel) {
      var rows = sel.getAttribute("data-fill") === "type" ? window.OU_TYPES : window.OU_SUBJECTS;
      sel.innerHTML = rows.map(function (r) { return '<option value="' + r[0] + '">' + r[1] + '</option>'; }).join("");
      var want = sel.getAttribute("data-value");
      if (want != null) sel.value = want;
    });
  }

  /* ---------- listing body ---------- */
  function crumbHTML() {
    if (!P.crumb) return "";
    return '<div class="u-crumb"><a href="/en/">Home</a>' + P.crumb.map(function (c) {
      return ' / <a href="' + c[0] + '">' + c[1] + '</a>';
    }).join("") + '</div>';
  }
  function renderListing() {
    var host = document.querySelector("[data-listing]"); if (!host) return;
    var ids = window.OU_SETS[P.set || "all"] || [];
    var cards = ids.map(function (id) { var o = oppById(id); return o ? cardHTML(o) : ""; }).join("");
    host.innerHTML =
      crumbHTML() +
      '<div class="u-wrap u-lay"><aside class="u-filters">' +
        '<h4>Filter</h4>' +
        '<select data-fill="type" data-value="' + (P.fType || "") + '" data-goto="type"></select>' +
        '<select data-fill="subject" data-value="' + (P.fSubject || "") + '" data-goto="subject"></select>' +
        '<select data-goto="funding"><option value="">Any funding</option><option value="fully_funded">Fully funded</option></select>' +
        '<a class="btn btn-primary" href="' + out("/en/search") + '" data-out target="_blank" rel="noopener">Search live database <i class="fa-solid fa-arrow-right"></i></a>' +
        '<p class="u-note">Filters switch between local category pages. Search runs on the live site.</p>' +
      '</aside><section>' +
        '<div class="u-apply-bar"><div><b>' + (P.count || "22,415") + ' opportunities</b> in this view · representative results shown</div>' +
        '<a class="btn btn-ghost" href="' + out("/en/search" + (P.q || "")) + '" data-out target="_blank" rel="noopener">See live results</a></div>' +
        '<div class="u-res-head"><h1>' + (P.h1 || "Opportunities") + '</h1><span class="u-res-count">Page 1 of 48</span></div>' +
        '<div class="u-grid" style="grid-template-columns:repeat(3,1fr)">' + cards + '</div>' +
        '<div class="u-pager"><span class="on">1</span><a href="#">2</a><a href="#">3</a><span>…</span><a href="#">48</a></div>' +
      '</section></div>';
    host.querySelectorAll("select[data-goto]").forEach(function (sel) {
      sel.addEventListener("change", function () {
        if (!sel.value) return;
        var key = sel.getAttribute("data-goto");
        var href = key === "type" ? "/en/type/" + sel.value
                 : key === "subject" ? "/en/subject/" + sel.value
                 : "/en/search?funding=" + sel.value;
        window.location.href = href;
      });
    });
  }

  /* ---------- forms ---------- */
  function initForms() {
    document.querySelectorAll("form[data-redirect]").forEach(function (f) {
      f.addEventListener("submit", function (e) {
        e.preventDefault();
        var drop = (f.getAttribute("data-drop") || "").split(",").filter(Boolean);
        var fd = new FormData(f);
        drop.forEach(function (k) { fd.delete(k); });
        var qs = new URLSearchParams(fd).toString();
        window.location.href = out(f.getAttribute("data-redirect")) + (qs ? "?" + qs : "");
      });
    });
    document.querySelectorAll("select[data-home-country]").forEach(function (sel) {
      sel.addEventListener("change", function () {
        if (!sel.value) return;
        window.location.href = OU.localCountries.indexOf(sel.value) >= 0
          ? "/en/country/" + sel.value
          : out("/en/country/" + sel.value);
      });
    });
  }

  /* ---------- misc UI ---------- */
  function initUI() {
    var burger = $("#uBurger"), row = $("#uHrow1");
    if (burger && row) burger.addEventListener("click", function () { row.classList.toggle("open"); });
    var more = $("#uNavMore");
    if (more) {
      more.querySelector("button").addEventListener("click", function (e) { e.stopPropagation(); more.classList.toggle("open"); });
      document.addEventListener("click", function () { more.classList.remove("open"); });
    }
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    Array.prototype.forEach.call(document.querySelectorAll("[data-count]"), function (el) {
      var target = parseInt(el.getAttribute("data-count"), 10) || 0;
      if (reduce) { el.textContent = target.toLocaleString("en-US"); return; }
      var t0 = null, dur = 1500;
      el.textContent = "0";
      function step(ts) {
        if (t0 === null) t0 = ts;
        var p = Math.min(1, (ts - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * e).toLocaleString("en-US");
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
    var cv = document.getElementById("ustars");
    if (cv && cv.getContext) {
      var ctx = cv.getContext("2d");
      var PAL = ["#ffffff","#ffffff","#ffffff","#ffffff","#c9dcff","#bcd0ff","#ffe7c4","#ffd9b0"];
      var stars = [];
      function seed() {
        cv.width = cv.offsetWidth; cv.height = cv.offsetHeight;
        stars = [];
        for (var i = 0; i < 340; i++) stars.push({
          x: Math.random() * cv.width, y: Math.random() * cv.height,
          r: Math.random() * 1.4, a: 0.3 + Math.random() * 0.65,
          c: PAL[Math.random() * 8 | 0], v: 3 + Math.random() * 9
        });
      }
      function paint() {
        ctx.clearRect(0, 0, cv.width, cv.height);
        for (var i = 0; i < stars.length; i++) {
          var s = stars[i];
          ctx.globalAlpha = s.a; ctx.fillStyle = s.c;
          ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 7); ctx.fill();
        }
      }
      seed(); paint();
      if (!reduce) {
        var last = -1;
        requestAnimationFrame(function frame(ts) {
          if (last < 0) last = ts;
          var dt = Math.min(0.1, (ts - last) / 1000); last = ts;
          for (var i = 0; i < stars.length; i++) {
            stars[i].x -= stars[i].v * dt;
            if (stars[i].x < -2) stars[i].x = cv.width + 2;
          }
          paint();
          requestAnimationFrame(frame);
        });
      }
      window.addEventListener("resize", function () { seed(); paint(); });
      window.addEventListener("load", function () { seed(); paint(); });
    }
  }

  /* ---------- boot ---------- */
  var head = $("#ouHeader"); if (head) head.innerHTML = headerHTML();
  var foot = $("#ouFooter"); if (foot) foot.innerHTML = footerHTML();
  var cc = $("#ouCookie"); if (cc) cc.innerHTML = cookieHTML();
  if (P.kind === "listing") renderListing();
  renderCards(); renderDeadlines(); renderBlogs(); renderLogos();
  fillSelects(); initCookie(); initForms(); initUI();
})();
```

- [ ] **Step 4: Run link checker — must PASS now**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: `OK: 3 HTML files, 0 broken links`, exit 0.

- [ ] **Step 5: Serve + smoke test**

```powershell
$s = Start-Process python -ArgumentList '-m','http.server','8080' -PassThru -WindowStyle Hidden -WorkingDirectory C:/Opencode/opportunity-universe-clone
try {
  $c = (Invoke-WebRequest http://localhost:8080/en/ -UseBasicParsing).Content
  if ($c -notmatch 'ouHeader') { throw 'stub broken' }
  if ((Invoke-WebRequest http://localhost:8080/assets/js/components.js -UseBasicParsing).StatusCode -ne 200) { throw 'components missing' }
  'served OK'
} finally { Stop-Process $s }
```
Expected: `served OK`. DOM injection itself is verified visually in Task 3.

- [ ] **Step 6: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): injection engine - header, footer, cookie, cards, listing, forms"
```
---

### Task 3: Home part A — hero, search, newsletter band, Featured, Fully Funded, Map teaser

**Files:**
- Modify: `opportunity-universe-clone/en/index.html` (replace stub)

**Interfaces:**
- Consumes: `OU_SETS`/`OU_OPPS` (Task 2), `[data-cards]`, `select[data-fill]`, `form[data-redirect]`.
- Produces: home `<main>` structure — Task 4 appends sections after the map teaser, before `</main>`.

- [ ] **Step 1: Replace stub with full page — head + first half of `<main>`**

Full file content:

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fully Funded Scholarships &amp; Youth Opportunities Worldwide | Opportunity Universe</title>
<meta name="description" content="Search fully funded scholarships, fellowships, internships and youth opportunities worldwide.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main">

<section class="u-hero">
  <canvas id="ustars" aria-hidden="true"></canvas>
  <div class="u-wrap u-hero-in">
    <h1>Find your next opportunity<span class="u-gold">.</span></h1>
    <form class="u-search" action="https://opportunity-universe.com/en/search" method="get" role="search" data-out>
      <input type="search" name="q" placeholder="Keyword" aria-label="Search">
      <select name="type" data-fill="type" aria-label="Type"></select>
      <select name="subject" data-fill="subject" aria-label="Subject"></select>
      <button type="submit">Search</button>
    </form>
    <div class="u-stats">
      <div class="u-stat"><span class="u-stat-n"><span data-count="22415">22,415</span><em>+</em></span><span class="u-stat-l">opportunities in our database</span></div>
      <div class="u-stat"><span class="u-stat-n"><span data-count="18930">18,930</span></span><span class="u-stat-l">open right now</span></div>
      <div class="u-stat"><span class="u-stat-n"><span data-count="7405">7,405</span></span><span class="u-stat-l">fully funded</span></div>
    </div>
  </div>
</section>

<section class="u-band">
  <div class="u-wrap u-band-in">
    <div><h2>Opportunity Newsletter</h2>
      <p>Get the best new scholarships, competitions and programmes in your inbox every week, matched to your country, level and interests.</p></div>
    <form data-redirect="/en/newsletter">
      <input type="email" name="email" required placeholder="Your email address">
      <button class="btn btn-gold" type="submit">Subscribe</button>
      <small><span>✓ Weekly</span><span>✓ Personalised</span><span>✓ 100% Free</span></small>
    </form>
  </div>
</section>

<section class="u-sec u-sec-tight-b"><div class="u-wrap">
  <div class="u-sec-head"><div><h2><i class="fa-solid fa-star"></i> Featured <span class="u-sec-month">(September 2026)</span></h2>
    <p>The most prestigious programmes open right now.</p></div></div>
  <div class="u-grid" data-cards="featured"></div>
</div></section>

<section class="u-sec u-sec-tight-b"><div class="u-wrap">
  <div class="u-sec-head"><div><h2><i class="fa-solid fa-hand-holding-dollar"></i> Fully Funded</h2>
    <p>Programmes that cover the full cost, from tuition to travel and living.</p></div>
    <a class="u-more" href="/en/fully-funded">View All →</a></div>
  <div class="u-grid" data-cards="funded"></div>
  <p style="margin-top:18px"><a class="btn btn-ghost" href="/en/fully-funded">View More Fully Funded Opportunities</a></p>
</div></section>

<section class="u-sec u-sec-tight-b"><div class="u-wrap">
  <div class="u-mapbox">
    <h2><i class="fa-solid fa-earth-americas"></i> World Map</h2>
    <p>Every in-person programme in our database, on one map. Click a country to explore what happens there.</p>
    <div class="u-mapstats">
      <div><b>11,875</b><span>in-person opportunities</span></div>
      <div><b>167</b><span>countries &amp; territories</span></div>
    </div>
    <a class="btn btn-primary" href="/en/map">Open World Map</a>
  </div>
</div></section>
```

(Task 4 continues below this; file temporarily ends here with `</main>` + scripts — add the closing block now:)

```html
</main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"home"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 2: Verify render**

Start server (`Start-Process python -ArgumentList '-m','http.server','8080' -WorkingDirectory C:/Opencode/opportunity-universe-clone`), open `http://localhost:8080/en/`.
Expected: black sticky header + nav rows, dark starfield hero with white search bar (Keyword + 2 selects + blue Search), 3 stats, blue newsletter band, 5-card Featured grid with hotlinked covers, Fully Funded grid, dark World Map teaser, black footer, cookie bar at bottom.

- [ ] **Step 3: Run link checker**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: `OK ... 0 broken links`. **Interim exception (Tasks 3-4):** links to `/en/fully-funded` (built in Task 5) and `/en/map` (built in Task 10) may fail until those tasks land — the gate is "no broken links other than future-page targets". Beyond future-page targets the tree must stay clean; full `0 broken links` (every page built) is the ship gate in Task 11. (The `<form data-out action>` is not an anchor — form redirect is click-tested in Task 11.)

- [ ] **Step 4: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): home part A - hero, search, newsletter band, featured, funded, map teaser"
```

---

### Task 4: Home part B — eligibility, logos, chips, deadlines, compare, new, categories, regions, quotes, account, blog

**Files:**
- Modify: `opportunity-universe-clone/en/index.html` (insert before `</main>`)

**Interfaces:**
- Consumes: Task 3 markup; `[data-logos]`, `[data-dl-list]`, `[data-blogs]`, `select[data-home-country]` — all rendered by Task 2 components.js.
- Produces: complete home page.

- [ ] **Step 1: Insert these sections before `</main>`**

```html
<section class="u-sec"><div class="u-wrap">
  <div class="u-sec-head"><div><h2><i class="fa-solid fa-ranking-star"></i> Top Opportunities for Your Country</h2>
    <p>By eligibility — pick your country to see what you can apply for.</p></div></div>
  <div class="u-country">
    <label for="homeCountry" style="font:600 14px var(--sans)">Change</label>
    <select id="homeCountry" data-home-country>
      <option value="">None selected</option>
      <option value="in">India</option><option value="ng">Nigeria</option><option value="pk">Pakistan</option>
      <option value="vn">Vietnam</option><option value="id">Indonesia</option><option value="eg">Egypt</option>
      <option value="ke">Kenya</option><option value="gh">Ghana</option><option value="ph">Philippines</option>
      <option value="br">Brazil</option><option value="mx">Mexico</option><option value="tr">Türkiye</option>
      <option value="de">Germany</option><option value="us">United States</option><option value="bd">Bangladesh</option>
      <option value="fr">France</option><option value="jp">Japan</option><option value="gb">United Kingdom</option>
    </select>
    <span class="u-note">The 15 most active countries open locally; the rest go to the live site.</span>
  </div>
  <div class="u-grid" data-cards="country" data-limit="6"></div>
</div></section>

<section class="u-sec u-sec-tight-b"><div class="u-wrap">
  <div class="u-sec-head"><div><h2>Participants of our opportunities joined</h2></div></div>
  <div class="u-logos" data-logos></div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-clouds">
    <div class="u-cloud">
      <a class="u-chip" href="/en/subject/computer_science">Computer Science</a><a class="u-chip" href="/en/subject/business">Business / Entrepreneurship</a>
      <a class="u-chip" href="/en/subject/arts">Arts / Photography</a><a class="u-chip" href="/en/subject/data_science_ai">Data Science / AI</a>
      <a class="u-chip" href="/en/subject/psychology">Psychology</a><a class="u-chip" href="/en/subject/design">Design</a>
      <a class="u-chip" href="/en/subject/journalism">Journalism / Media</a><a class="u-chip" href="/en/type/fellowship">Fellowship</a>
      <a class="u-chip" href="/en/type/hackathon">Hackathon</a><a class="u-chip" href="/en/type/workshop">Workshop</a>
      <a class="u-chip" href="/en/type/grant">Grant</a><a class="u-chip" href="/en/region/eur">Europe</a>
      <a class="u-chip" href="/en/region/afr">Africa</a><a class="u-chip" href="/en/region/oce">Oceania</a>
    </div>
    <div class="u-cloud">
      <a class="u-chip" href="/en/subject/health">Health / Medicine</a><a class="u-chip" href="/en/subject/law">Law</a>
      <a class="u-chip" href="/en/subject/environment">Environment / Climate</a><a class="u-chip" href="/en/subject/mathematics">Mathematics</a>
      <a class="u-chip" href="/en/subject/political_science">Political Science / International Relations</a><a class="u-chip" href="/en/subject/chemistry">Chemistry</a>
      <a class="u-chip" href="/en/subject/music">Music</a><a class="u-chip" href="/en/type/internship">Internship</a>
      <a class="u-chip" href="/en/type/conference">Conference</a><a class="u-chip" href="/en/type/research_program">Research</a>
      <a class="u-chip" href="/en/region/nam">North America</a><a class="u-chip" href="/en/region/sam">South &amp; Latin America</a>
      <a class="u-chip" href="/en/search?funding=fully_funded">Fully funded</a>
    </div>
    <div class="u-cloud">
      <a class="u-chip" href="/en/subject/engineering">Engineering</a><a class="u-chip" href="/en/subject/physics">Physics</a>
      <a class="u-chip" href="/en/subject/economics">Economics / Finance</a><a class="u-chip" href="/en/subject/biology">Biology / Life Sciences</a>
      <a class="u-chip" href="/en/subject/education">Education</a><a class="u-chip" href="/en/subject/agriculture">Agriculture / Food</a>
      <a class="u-chip" href="/en/type/scholarship">Scholarship</a><a class="u-chip" href="/en/type/summer_school">Summer School</a>
      <a class="u-chip" href="/en/type/competition">Competition</a><a class="u-chip" href="/en/region/asi">Asia</a>
      <a class="u-chip" href="/en/region/mea">Middle East</a><a class="u-chip" href="/en/search?online=1">Online</a>
    </div>
  </div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-sec-head"><div><h2><i class="fa-solid fa-hourglass-half"></i> Deadlines Soon</h2>
    <p>These opportunities close soon, so apply while there is still time.</p></div>
    <a class="u-more" href="/en/search?closing=45&amp;sort=deadline">View All →</a></div>
  <div class="u-dl-list" data-dl-list></div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-compare">
    <div class="u-sec-head"><div><h2>The Largest Opportunity Database on the Planet</h2>
      <p style="color:#9aa5bf">Our engine scans the open web and cross-checks databases and platforms, so everything here — plus thousands more others never find.</p></div>
      <a class="u-more" href="/en/methodology" style="color:#f5cb1f">See how our technology works →</a></div>
    <div class="u-cmp-rows">
      <div class="u-cmp-row"><span>Opportunity Universe</span><span class="u-cmp-bar"><i style="width:100%"></i></span><span class="u-cmp-val">22,415</span></div>
      <div class="u-cmp-row"><span>Opportunity Desk</span><span class="u-cmp-bar"><i style="width:16%"></i></span><span class="u-cmp-val">2,120</span></div>
      <div class="u-cmp-row"><span>Youth Opportunities</span><span class="u-cmp-bar"><i style="width:6%"></i></span><span class="u-cmp-val">522</span></div>
    </div>
    <p class="u-cmp-10x">That's 10.6× more than the biggest other website</p>
    <p class="u-note" style="color:#7f8aa3">Added in the last 12 months · counts are de-duplicated across all sources.</p>
    <div class="u-chart"><i style="height:38%"></i><i style="height:52%"></i><i style="height:47%"></i><i style="height:66%"></i><i style="height:71%"></i><i style="height:64%"></i><i style="height:83%"></i><i style="height:95%"></i></div>
    <div class="u-chart-lbls"><span>Sep</span><span>Nov</span><span>Jan</span><span>Mar</span><span>May</span><span>Jul</span></div>
  </div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-sec-head"><div><h2><i class="fa-solid fa-bolt"></i> New Opportunities (615)</h2>
    <p>New opportunities from our latest search across the web.</p></div>
    <a class="u-more" href="/en/search?sort=newest">View All →</a></div>
  <div class="u-grid" data-cards="newest"></div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-sec-head"><div><h2>By Category</h2></div></div>
  <div class="u-grid3">
    <div><a class="u-more" href="/en/type/scholarship">Scholarships <b style="color:var(--muted)">4,785</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/type/scholarship">British Chevening 2027</a><a class="u-chip" href="/en/type/scholarship">Erasmus Mundus</a>
        <a class="u-chip" href="/en/type/scholarship">Gates Cambridge</a><a class="u-chip" href="/en/type/scholarship">Yenching Academy</a></div></div>
    <div><a class="u-more" href="/en/type/fellowship">Fellowships <b style="color:var(--muted)">1,221</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/type/fellowship">CERN Doctoral</a><a class="u-chip" href="/en/type/fellowship">NASA Hubble</a>
        <a class="u-chip" href="/en/type/fellowship">Leverhulme</a><a class="u-chip" href="/en/type/fellowship">Mo Ibrahim</a></div></div>
    <div><a class="u-more" href="/en/type/competition">Competitions <b style="color:var(--muted)">864</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/type/competition">Google Cloud AI Cup</a><a class="u-chip" href="/en/type/competition">Talk Talk Korea</a>
        <a class="u-chip" href="/en/type/competition">Citi Innovation Challenge</a><a class="u-chip" href="/en/type/competition">IDP IELTS Award</a></div></div>
    <div><a class="u-more" href="/en/type/summer_school">Summer Schools <b style="color:var(--muted)">665</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/type/summer_school">DAAD Summer Courses</a><a class="u-chip" href="/en/type/summer_school">ATRIUM AI School</a>
        <a class="u-chip" href="/en/type/summer_school">PPIA Junior Institute</a></div></div>
    <div><a class="u-more" href="/en/type/award">Awards &amp; Prizes <b style="color:var(--muted)">196</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/type/award">Pradel Research Award</a><a class="u-chip" href="/en/type/award">Whitley Awards</a>
        <a class="u-chip" href="/en/type/award">IUPAC-Soong Prize</a></div></div>
    <div><a class="u-more" href="/en/type/grant">Grants <b style="color:var(--muted)">1,540</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/type/grant">W. Eugene Smith Grant</a><a class="u-chip" href="/en/type/grant">Ithra Film Fund</a>
        <a class="u-chip" href="/en/type/grant">NRF Research Call</a></div></div>
  </div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-sec-head"><div><h2>By Region</h2></div></div>
  <div class="u-grid3">
    <div><a class="u-more" href="/en/region/nam">North America <b style="color:var(--muted)">2,607</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/region/nam">Hoover Fellows</a><a class="u-chip" href="/en/region/nam">Brooke Owens</a>
        <a class="u-chip" href="/en/region/nam">World Bank YPP</a></div></div>
    <div><a class="u-more" href="/en/region/eur">Europe <b style="color:var(--muted)">4,476</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/region/eur">Chevening UK</a><a class="u-chip" href="/en/region/eur">Martingale Foundation</a>
        <a class="u-chip" href="/en/region/eur">Hungarian Government</a></div></div>
    <div><a class="u-more" href="/en/region/asi">Asia <b style="color:var(--muted)">1,984</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/region/asi">ADB-Japan Scholarship</a><a class="u-chip" href="/en/region/asi">HKU President PhD</a>
        <a class="u-chip" href="/en/region/asi">KAIST Admissions</a></div></div>
    <div><a class="u-more" href="/en/region/afr">Africa <b style="color:var(--muted)">1,677</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/region/afr">Mandela Washington</a><a class="u-chip" href="/en/region/afr">Reach Oxford</a>
        <a class="u-chip" href="/en/region/afr">AfricaLics Fellowship</a></div></div>
    <div><a class="u-more" href="/en/region/mea">Middle East <b style="color:var(--muted)">1,616</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/region/mea">KAUST Fellowships</a><a class="u-chip" href="/en/region/mea">Emirates Elevate Intern</a>
        <a class="u-chip" href="/en/region/mea">DAAD EPOS</a></div></div>
    <div><a class="u-more" href="/en/region/oce">Oceania <b style="color:var(--muted)">486</b></a>
      <div class="u-cloud" style="justify-content:flex-start;margin-top:10px">
        <a class="u-chip" href="/en/region/oce">ARC Future Fellowships</a><a class="u-chip" href="/en/region/oce">Melbourne Graduate</a>
        <a class="u-chip" href="/en/region/oce">Australia Awards</a></div></div>
  </div>
</div></section>

<section class="u-sec"><div class="u-wrap u-quotes">
  <div class="u-quote"><blockquote>&ldquo;Education is the most powerful weapon which you can use to change the world.&rdquo;</blockquote>
    <div class="u-quote-by"><img src="https://opportunity-universe.com/assets/designs/people/mandela.jpg" alt="" loading="lazy"><span><b>Nelson Mandela</b>Nobel Peace Prize laureate</span></div></div>
  <div class="u-quote"><blockquote>&ldquo;One child, one teacher, one book, one pen can change the world.&rdquo;</blockquote>
    <div class="u-quote-by"><img src="https://opportunity-universe.com/assets/designs/people/malala.jpg" alt="" loading="lazy"><span><b>Malala Yousafzai</b>Youngest Nobel Prize laureate</span></div></div>
  <div class="u-quote"><blockquote>&ldquo;The size of your dreams must always exceed your current capacity to achieve them.&rdquo;</blockquote>
    <div class="u-quote-by"><img src="https://opportunity-universe.com/assets/designs/people/sirleaf.jpg" alt="" loading="lazy"><span><b>Ellen Johnson Sirleaf</b>Former President of Liberia</span></div></div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-account">
    <div><span class="u-kicker">100% free</span><h2>Create Your Account</h2>
      <p>Create a free account to save the opportunities you like, receive a weekly newsletter matched to your country, level and interests, and get a reminder before every deadline.</p>
      <a class="btn btn-gold" href="/en/register">Create your free account</a></div>
    <ul><li>A weekly newsletter matched to your interests</li><li>Save opportunities and track deadlines</li>
      <li>Share your success story with the community</li><li>Free forever, no card and no spam</li></ul>
  </div>
</div></section>

<section class="u-sec"><div class="u-wrap">
  <div class="u-sec-head"><div><h2><i class="fa-solid fa-newspaper"></i> Blog &amp; Articles 2026</h2></div>
    <a class="u-more" href="/en/blog">View All →</a></div>
  <div class="u-grid3" data-blogs></div>
</div></section>

<section class="u-band" style="margin-bottom:0"><div class="u-wrap u-band-in">
  <div><h2>Opportunity Newsletter</h2><p>One email a week. Only opportunities you can actually apply for.</p></div>
  <form data-redirect="/en/newsletter"><input type="email" name="email" required placeholder="Your email address">
    <button class="btn btn-gold" type="submit">Subscribe</button>
    <small><span>✓ Weekly</span><span>✓ Personalised</span><span>✓ 100% Free</span></small></form>
</div></section>
```

- [ ] **Step 2: Verify render + run link checker**

Open `http://localhost:8080/en/` → every section above renders: country select, logo wall (grayscale), 3 chip rows, deadline strip (compact rows, "Closes today!" in red), dark compare block with bars, By Category/Region chip boxes, 3 quotes, dark-blue account band, 3 blog cards, second newsletter band.
Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: interim failures only (listing pages built in Task 5; `/en/blog`, `/en/methodology`, `/en/register`, `/en/map` built in Tasks 7-10) - no other broken links.

- [ ] **Step 3: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): home part B - eligibility, logos, chips, deadlines, stats, blog teaser"
```
---

### Task 5: Listing template + scaffold script (62 pages)

**Files:**
- Create: `opportunity-universe-clone/tools/scaffold-listings.ps1`
- Generate: 62 files under `opportunity-universe-clone/en/` (search, fully-funded, type×17, subject×20, region×7, country×15, countries)

**Interfaces:**
- Consumes: page contract (`window.OU_PAGE={kind:"listing",...}`) + `renderListing()` from Task 2.
- Produces: local listing URLs used by every nav chip on Home; each generated file is standalone static HTML.

- [ ] **Step 1: Create `tools/scaffold-listings.ps1`**

```powershell
# Build-time generator: emits thin static listing pages. Runtime never needs this script.
$root = Split-Path -Parent $PSScriptRoot

$Head = @'
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITLEPLACE | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div data-listing></div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE = CONFIGPLACE;</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
'@

function New-Page([string]$relPath, [string]$title, [hashtable]$cfg) {
  $json = ($cfg.GetEnumerator() | Sort-Object Name | ForEach-Object {
    $v = $_.Value
    if ($v -is [string]) { '"{0}":"{1}"' -f $_.Name, ($v -replace '\\','\\\\' -replace '"','\"') }
    else { '"{0}":{1}' -f $_.Name, $v }
  }) -join ','
  $html = $Head.Replace('TITLEPLACE', $title).Replace('CONFIGPLACE', '{' + $json + '}')
  $dir = Join-Path $root $relPath
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  [IO.File]::WriteAllText((Join-Path $dir 'index.html'), $html, [Text.UTF8Encoding]::new($false))
}

$Types = [ordered]@{
  scholarship='Scholarships'; fellowship='Fellowships'; grant='Grants'; competition='Competitions';
  olympiad='Olympiads'; award='Awards & Prizes'; conference='Conferences'; forum='Forums & Summits';
  summer_school='Summer Schools'; internship='Internships'; research_program='Research Programmes';
  hackathon='Hackathons'; workshop='Workshops'; training='Training Programmes';
  exchange='Exchange Programmes'; accelerator='Accelerators'; volunteering='Volunteering'
}
$Subjects = [ordered]@{
  computer_science='Computer Science'; data_science_ai='Data Science / AI'; engineering='Engineering';
  mathematics='Mathematics'; physics='Physics'; chemistry='Chemistry'; biology='Biology / Life Sciences';
  health='Health / Medicine'; environment='Environment / Climate'; economics='Economics / Finance';
  business='Business / Entrepreneurship'; law='Law'; political_science='Political Science / International Relations';
  psychology='Psychology'; design='Design'; arts='Arts / Photography'; music='Music';
  journalism='Journalism / Media'; education='Education'; agriculture='Agriculture / Food'
}
$Regions = [ordered]@{
  nam='North America'; eur='Europe'; asi='Asia'; afr='Africa'; mea='Middle East';
  oce='Oceania'; sam='South & Latin America'
}
$Countries = [ordered]@{
  in='India'; ng='Nigeria'; pk='Pakistan'; bd='Bangladesh'; id='Indonesia'; eg='Egypt';
  ke='Kenya'; gh='Ghana'; ph='Philippines'; vn='Vietnam'; br='Brazil'; mx='Mexico';
  tr='Türkiye'; de='Germany'; us='United States'
}

# search results
New-Page 'en/search' 'Search Results' @{
  kind='listing'; h1='Search Results'; count='22,415'; set='all'; q=''; crumb='[[\"/en/search\",\"Search\"]]'
}
# fully funded landing
New-Page 'en/fully-funded' 'Fully Funded Opportunities' @{
  kind='listing'; h1='Fully Funded Opportunities'; count='7,405'; set='funded';
  q='?funding=fully_funded'; crumb='[[\"/en/fully-funded\",\"Fully Funded\"]]'
}
foreach ($k in $Types.Keys) {
  New-Page "en/type/$k" $Types[$k] @{
    kind='listing'; h1=$Types[$k]; count='4,785'; set='all'; fType=$k;
    q="?type=$k"; crumb="[[""/en/type/$k"",""Types""]]"
  }
}
foreach ($k in $Subjects.Keys) {
  New-Page "en/subject/$k" $Subjects[$k] @{
    kind='listing'; h1=$Subjects[$k]; count='1,120'; set='all'; fSubject=$k;
    q="?subject=$k"; crumb="[[""/en/subject/$k"",""Subjects""]]"
  }
}
foreach ($k in $Regions.Keys) {
  New-Page "en/region/$k" $Regions[$k] @{
    kind='listing'; h1=$Regions[$k]; count='2,607'; set='all';
    q="?region=$k"; crumb="[[""/en/region/$k"",""Regions""]]"
  }
}
foreach ($k in $Countries.Keys) {
  New-Page "en/country/$k" $Countries[$k] @{
    kind='listing'; h1=("Opportunities in " + $Countries[$k]); count='640'; set='country';
    q="?country=$k"; crumb="[[""/en/country/$k"",""Countries""]]"
  }
}
# country index (static content page, not a listing grid)
$idx = $Head.Replace('TITLEPLACE','Countries').Replace('CONFIGPLACE','{kind:"static"}') `
  -replace '<main id="main"><div data-listing></div></main>', @'
<main id="main">
<div class="u-page-head"><div class="u-wrap"><h1>Countries</h1><p>Browse opportunities by the country you can apply from or travel to.</p></div></div>
<div class="u-wrap u-prose"><div class="u-cloud">
'@
$idx = $idx -replace '</body></html>', (@'
</div></div>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
'@)
$countryLinks = ($Countries.GetEnumerator() | ForEach-Object {
  '<a class="u-chip" href="/en/country/{0}">{1}</a>' -f $_.Key, $_.Value
}) -join ''
$idx = $idx.Replace('</div></div>', $countryLinks + '</div></div>')
New-Item -ItemType Directory -Force -Path (Join-Path $root 'en/countries') | Out-Null
[IO.File]::WriteAllText((Join-Path $root 'en/countries/index.html'), $idx, [Text.UTF8Encoding]::new($false))

"Generated listing pages under en/"
```

- [ ] **Step 2: Run the scaffold**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/scaffold-listings.ps1`
Expected: `Generated listing pages under en/` and 62 new `index.html` files (verify: `(Get-ChildItem C:/Opencode/opportunity-universe-clone/en -Recurse -Filter index.html).Count` → 63 incl. home).

- [ ] **Step 3: Run link checker — interim exceptions only**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: 65 HTML files (1 root + 404 + 63 under `en/`); broken links limited to the still-unbuilt pages `/en/blog` (Task 7), `/en/methodology` (Task 8), `/en/register` (Task 9), `/en/map` (Task 10). Full `0 broken links` gate applies from Task 11.

- [ ] **Step 4: Spot-check 3 URLs in browser**

Open `http://localhost:8080/en/type/scholarship`, `/en/subject/computer_science`, `/en/country/vn`.
Expected: breadcrumb, heading, "See live results" bar, 3-col card grid, sidebar filter selects; changing a sidebar select navigates to the corresponding local listing page.

- [ ] **Step 5: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): listing template + scaffold - 62 local listing pages"
```

---

### Task 6: Opportunity detail pages (3 samples)

**Files:**
- Create: `opportunity-universe-clone/en/opportunity/31159-caltech-scholarships-2027/index.html`
- Create: `opportunity-universe-clone/en/opportunity/29735-cern-doctoral-student-program-2027/index.html`
- Create: `opportunity-universe-clone/en/opportunity/30630-marshall-scholarship-2027/index.html`

**Interfaces:**
- Consumes: Task 2 header/footer injection; `OU_OPPS` metadata (same id/slug as data.js).
- Produces: detail template pattern — condensed original-style body, Apply CTA → original (`data-out`).

**Content rule:** bodies below are written for this mirror (condensed, original-style), NOT copied from the original site.

- [ ] **Step 1: Create detail page 1** (Caltech) — full file:

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Caltech Scholarships 2027 | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap">
  <div class="u-crumb"><a href="/en/">Home</a> / <a href="/en/type/scholarship">Scholarships</a> / Caltech Scholarships 2027</div>
  <div class="u-detail">
    <article>
      <div class="u-detail-head">
        <img src="https://opportunity-universe.com/cover/31159.jpg" alt="Caltech Scholarships 2027" width="640" height="360">
        <div class="u-meta-row"><span class="u-tag">Scholarship</span><span class="u-tag u-tag-gold"><i class="fa-solid fa-star"></i> Fully funded</span></div>
        <h1>Caltech Scholarships 2027</h1>
        <p class="u-card-meta">California Institute of Technology (Caltech) · Pasadena, United States · 37 days left</p>
      </div>
      <div class="u-detail-body">
        <p>The Caltech Scholarships 2027 support international students who want to join Caltech's undergraduate or doctoral programmes. Awards are need-aware and cover tuition plus a living stipend for the duration of the programme.</p>
        <h2>What it covers</h2>
        <ul><li>Full tuition for the accepted programme</li><li>Annual living stipend</li><li>One-time travel allowance for students arriving from abroad</li></ul>
        <h2>Who can apply</h2>
        <p>First-year undergraduate applicants and prospective PhD students holding a bachelor's degree in a STEM field. Non-US citizens are eligible; English proficiency proof is required.</p>
        <h2>How to apply</h2>
        <p>Apply through the standard Caltech admissions route and tick the funding section. Decisions follow the regular admission timeline.</p>
        <p class="u-out-note">This is a condensed summary. Deadlines, amounts and eligibility can change — always confirm on the official page.</p>
        <p><a class="btn btn-primary" href="https://opportunity-universe.com/en/opportunity/31159-caltech-scholarships-2027" data-out target="_blank" rel="noopener">Continue on the original site <i class="fa-solid fa-arrow-right"></i></a></p>
      </div>
    </article>
    <aside class="u-side">
      <dl>
        <dt>Organisation</dt><dd>California Institute of Technology (Caltech)</dd>
        <dt>Location</dt><dd>Pasadena, United States</dd>
        <dt>Type</dt><dd>Scholarship · Fully funded</dd>
        <dt>Deadline</dt><dd>37 days left</dd>
      </dl>
      <a class="btn btn-primary" href="https://opportunity-universe.com/en/opportunity/31159-caltech-scholarships-2027" data-out target="_blank" rel="noopener">Apply on original site</a>
      <a class="btn btn-ghost" href="/en/type/scholarship">More scholarships</a>
    </aside>
  </div>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"detail",crumb:[["/en/type/scholarship","Scholarships"]]};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 2: Create detail pages 2 and 3** by copying page 1 and replacing ONLY these values:

| Field | Page 2 | Page 3 |
|---|---|---|
| folder | `en/opportunity/29735-cern-doctoral-student-program-2027/` | `en/opportunity/30630-marshall-scholarship-2027/` |
| `<title>` / `<h1>` | CERN Doctoral Student Program 2027 | Marshall Scholarship 2027 |
| cover img src | `https://opportunity-universe.com/cover/29735.jpg` | `https://opportunity-universe.com/cover/30630.jpg` |
| breadcrumb last item | CERN Doctoral Student Program 2027 | Marshall Scholarship 2027 |
| meta line | `CERN · Geneva, Switzerland · 21 days left` | `Marshall Aid Commemoration Commission · United Kingdom · 4 days left` |
| tags | `Fellowship` + gold Fully funded | `Scholarship` + gold Fully funded |
| both Apply hrefs | `https://opportunity-universe.com/en/opportunity/29735-cern-doctoral-student-program-2027` | `https://opportunity-universe.com/en/opportunity/30630-marshall-scholarship-2027` |
| side dl | Organisation=CERN, Location=Geneva, Switzerland, Type=Fellowship · Fully funded, Deadline=21 days left | Organisation=Marshall Aid Commemoration Commission, Location=United Kingdom, Type=Scholarship · Fully funded, Deadline=4 days left |
| crumb config | `crumb:[["/en/type/fellowship","Fellowships"]]` | `crumb:[["/en/type/scholarship","Scholarships"]]` |

Body paragraphs (written for this mirror, condensed):
- **CERN:** "The CERN Doctoral Student Program 2027 lets selected PhD candidates carry out their research at CERN while remaining enrolled at their home university. Participants receive a monthly allowance, travel support and access to CERN's experiments and training programme." Sections: What it covers (monthly allowance, travel, supervision) / Who can apply (enrolled PhD students in physics, engineering or computing, any nationality) / How to apply (home-university supervisor + CERN online form).
- **Marshall:** "The Marshall Scholarship 2027 funds one or two years of postgraduate study in the United Kingdom for graduates with strong academic records and leadership potential. The award covers tuition, a living stipend and a travel grant." Sections: What it covers (tuition, stipend, travel) / Who can apply (US citizens under 26 with a bachelor's degree) / How to apply (online application, interviews in autumn).

- [ ] **Step 3: Run link checker + spot-check**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: broken links limited to the still-unbuilt pages `/en/blog` (Task 7), `/en/methodology` (Task 8), `/en/register` (Task 9), `/en/map` (Task 10); full `0 broken links` gate applies from Task 11.
Open `http://localhost:8080/en/opportunity/31159-caltech-scholarships-2027` → header, breadcrumb, cover, sidebar, both Apply links go to `https://opportunity-universe.com/...` (verify `data-out` in link attributes).

- [ ] **Step 4: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): 3 opportunity detail samples with condensed content"
```
---

### Task 7: Blog list + 3 article samples

**Files:**
- Create: `opportunity-universe-clone/en/blog/index.html`
- Create: `opportunity-universe-clone/en/blog/fully-funded-scholarships-in-europe-for-late-2026-and-2027/index.html`
- Create: `opportunity-universe-clone/en/blog/paid-international-internships-closing-in-october-and-november-2026/index.html`
- Create: `opportunity-universe-clone/en/blog/fully-funded-scholarships-closing-before-march-2027/index.html`

**Interfaces:**
- Consumes: `OU_BLOGS` + `[data-blogs]` renderer (Task 2).
- Produces: `/en/blog` list page; 3 article pages (condensed original-style bodies, "Read on original site" CTA).

- [ ] **Step 1: Create `en/blog/index.html`** (list page)

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blog &amp; Articles | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main">
<div class="u-wrap u-blog-head"><div class="u-crumb"><a href="/en/">Home</a> / Blog</div>
  <h1>Blog &amp; Articles 2026</h1>
  <p class="u-sub">Guides, deadline roundups and application advice — condensed here, full versions on the original site.</p></div>
<section class="u-sec" style="padding-top:10px"><div class="u-wrap"><div class="u-grid3" data-blogs></div></div></section>
</main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static",crumb:[["/en/blog","Blog"]]};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

Note: blog cards in `[data-blogs]` link Out (rule). The 3 local article pages are reached by direct URL only.

- [ ] **Step 2: Create article page 1** — full file:

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fully Funded Scholarships in Europe for Late 2026 and 2027 | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap"><article class="u-article">
  <div class="u-crumb"><a href="/en/">Home</a> / <a href="/en/blog">Blog</a> / Fully Funded Scholarships in Europe</div>
  <h1>Fully Funded Scholarships in Europe for Late 2026 and 2027</h1>
  <p class="u-article-meta">24 Sep 2026 · 4 min read</p>
  <img src="https://images.pexels.com/photos/39289023/pexels-photo-39289023.jpeg?auto=compress&cs=tinysrgb&fit=crop&h=627&w=1200" alt="" width="1200" height="627">
  <p>Europe still runs some of the most generous postgraduate funding on earth, and the biggest calls for the 2026-2027 cycle open between September and December. Three routes deserve attention if you want a fully funded master's or PhD.</p>
  <h2>United Kingdom: Chevening and Marshall</h2>
  <p>Chevening covers a one-year master's anywhere in the UK and expects two years of work experience; the Marshall Scholarship targets US graduates and funds one to two years of study. Both close in early autumn, so start the application at least six weeks before the deadline.</p>
  <h2>Switzerland: ETH and other doctoral routes</h2>
  <p>ETH Zurich recruits fully funded PhD candidates through individual professor pages rather than one central call. Watch chair pages from October; a supervisor willing to sponsor you matters more than a general application.</p>
  <h2>Germany: DAAD and foundation scholarships</h2>
  <p>DAAD and political foundations fund Master's and PhD study with stipends plus tuition. Language requirements vary - many programmes run entirely in English.</p>
  <p class="u-out-note">Condensed summary written for this mirror. Dates and eligibility change every cycle — check the official sources.</p>
  <p><a class="btn btn-primary" href="https://opportunity-universe.com/en/blog/fully-funded-scholarships-in-europe-for-late-2026-and-2027" data-out target="_blank" rel="noopener">Read on the original site <i class="fa-solid fa-arrow-right"></i></a>
     <a class="btn btn-ghost" href="/en/blog">All articles</a></p>
</article></div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static",crumb:[["/en/blog","Blog"]]};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 3: Create articles 2 and 3** — same skeleton, replace `<title>`, `<h1>`, date/read-time, hero img (pexels URLs from `OU_BLOGS` in data.js), body and the final `href`:

| Field | Article 2 | Article 3 |
|---|---|---|
| folder | `en/blog/paid-international-internships-closing-in-october-and-november-2026/` | `en/blog/fully-funded-scholarships-closing-before-march-2027/` |
| title | Paid international internships closing in October and November 2026 | Fully Funded Scholarships Closing Before March 2027 |
| meta | 20 Sep 2026 · 3 min read | 17 Sep 2026 · 5 min read |
| body p1 | "Paid internships with international deadlines cluster in the next eight weeks. Research, policy and engineering roles dominate this window, and most of them cover travel and housing on top of a stipend." | "The spring cycle is when fully funded awards with March deadlines open. Planning now is the difference between a rushed application and a competitive one." |
| body h2/p2 | **Where the money is:** "Government labs and research institutes pay the best stipends - NASA pathways, EU frame programmes and national science agencies. Private-sector internships often pay salary but rarely cover flights." | **Master's awards:** "Chevening, Erasmus Mundus and national government awards all interview in spring. They need two recommendation letters, so ask referees in November." |
| body h2/p3 | **How to prepare:** "One CV per field, two referees warned in advance, and a two-week buffer before each deadline. Applications submitted on the final day fail more often for missing documents than for quality." | **Doctoral routes:** "PhD funding moves faster and earlier. Contact potential supervisors in December with a two-paragraph research pitch and your transcript." |
| CTA href | `https://opportunity-universe.com/en/blog/paid-international-internships-closing-in-october-and-november-2026` | `https://opportunity-universe.com/en/blog/fully-funded-scholarships-closing-before-march-2027` |

- [ ] **Step 4: Run link checker + spot-check**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1` → broken links limited to the still-unbuilt pages `/en/methodology` (Task 8), `/en/register` (Task 9), `/en/map` (Task 10); full `0 broken links` gate applies from Task 11.
Open `/en/blog` → 3 cards linking Out; open article 1 by URL → renders with CTA.

- [ ] **Step 5: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): blog list + 3 condensed article samples"
```

---

### Task 8: Static pages via scaffold script (10 pages)

**Files:**
- Create: `opportunity-universe-clone/tools/scaffold-static.ps1`
- Generate: `en/about`, `en/contact`, `en/faq`, `en/methodology`, `en/sponsor`, `en/pro`, `en/stories`, `en/mobility-scholarship`, `en/privacy`, `en/imprint`

**Interfaces:**
- Consumes: Task 1 CSS (`.u-page-head .u-prose .u-faq`).
- Produces: static pages reachable from header "More" menu and footer.

**Content rule:** all section text below is written for this mirror (condensed, original-style) — not copied.

- [ ] **Step 1: Create `tools/scaffold-static.ps1`**

```powershell
# Build-time generator for the 10 static pages. Runtime does not depend on it.
$root = Split-Path -Parent $PSScriptRoot

$Head = @'
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TITLEPLACE | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main">
<div class="u-page-head"><div class="u-wrap"><h1>H1PLACE</h1><p>SUBPLACE</p></div></div>
<div class="u-wrap u-prose CLASSPLACE">BODYPLACE</div>
</main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
'@

function New-Static([string]$slug, [string]$title, [string]$h1, [string]$sub, [string]$body, [string]$extraClass = '') {
  $html = $Head.Replace('TITLEPLACE', $title).Replace('H1PLACE', $h1).Replace('SUBPLACE', $sub).Replace('CLASSPLACE', $extraClass).Replace('BODYPLACE', $body)
  $dir = Join-Path $root "en/$slug"
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  [IO.File]::WriteAllText((Join-Path $dir 'index.html'), $html, [Text.UTF8Encoding]::new($false))
}

New-Static 'about' 'About Us' 'About Us' 'Who we are and how this database came to be.' @'
<p>Opportunity Universe was built by a small team that kept missing deadlines because opportunities live scattered across platforms, embassy pages and mailing lists. We track them in one place so you can spend your time applying instead of searching.</p>
<h2>What we do</h2>
<ul><li>Scan the open web and partner platforms every day for new programmes</li><li>De-duplicate entries so the same call never appears twice</li><li>Tag funding, eligibility and deadlines so filters stay trustworthy</li><li>Send one weekly digest matched to your country and field</li></ul>
<h2>What we do not do</h2>
<p>We do not run the programmes we list. Applications always happen with the official provider - every card here links straight to their page.</p>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/about" data-out target="_blank" rel="noopener">Read the full story on the original site</a></div>
'@

New-Static 'contact' 'Contact' 'Contact' 'Questions, corrections and partnership enquiries.' @'
<p>We read every message. Pick the channel that fits best and we usually reply within two working days.</p>
<h2>General enquiries</h2>
<p>Questions about the database, a listing that looks wrong, or a deadline that changed? Write to <b>info@opportunity-universe.com</b> and include the link to the programme you mean.</p>
<h2>For organisations</h2>
<p>Running a scholarship, fellowship or programme? Use the Submit Opportunity form in the header menu - listings are reviewed before they go live. For partnerships and promotion, email the same address with "Partnership" in the subject line.</p>
<h2>Press</h2>
<p>For interviews and data requests, get in touch with your deadline - we can share aggregate numbers on openings by region and field.</p>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/contact" data-out target="_blank" rel="noopener">Contact form on the original site</a></div>
'@

New-Static 'faq' 'FAQ' 'Frequently Asked Questions' 'The questions we hear most often.' @'
<div class="u-faq">
<details open><summary>Is Opportunity Universe free?</summary><p>Yes. Browsing, searching and the weekly newsletter cost nothing. An optional Pro membership adds saved-search alerts.</p></details>
<details><summary>Do you run the scholarships you list?</summary><p>No. We are a database. Applications go directly to the organisation running the programme.</p></details>
<details><summary>How often is the database updated?</summary><p>Continuously. New calls are picked up during the daily crawl and checked for duplicates before they appear.</p></details>
<details><summary>Can I apply from my country?</summary><p>Eligibility differs per programme. Use the country filter on any listing page to see only what accepts applicants from where you live.</p></details>
<details><summary>How do I submit my own opportunity?</summary><p>Use the Submit Opportunity form in the header menu. Listings are reviewed before they go live.</p></details>
</div>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/faq" data-out target="_blank" rel="noopener">Full FAQ on the original site</a></div>
'@

New-Static 'methodology' 'How We Find Opportunities' 'How We Find Opportunities' 'Our pipeline, in plain language.' @'
<h2>1. Wide crawl</h2><p>An automated crawl sweeps university pages, government portals, foundation sites and the major opportunity platforms several times a day.</p>
<h2>2. De-duplication</h2><p>Entries are matched by programme name, provider and deadline so the same call never shows up twice under different titles.</p>
<h2>3. Enrichment</h2><p>Each record gets funding status, eligibility tags, field, country and a structured deadline before it reaches the site.</p>
<h2>4. Review</h2><p>Flagged or borderline entries are checked by a human before publishing. Anything that cannot be verified stays out.</p>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/methodology" data-out target="_blank" rel="noopener">Details on the original site</a></div>
'@

New-Static 'sponsor' 'For Organisations / Promote' 'For Organisations / Promote' 'Put your programme in front of the right applicants.' @'
<p>If you run a scholarship, fellowship or programme, listing it here puts it in front of people actively looking for exactly that. Options range from a free standard listing to featured placement on the homepage.</p>
<h2>What you get</h2>
<ul><li>Structured listing with funding and eligibility tags</li><li>Placement in the weekly newsletter matching your field</li><li>Featured slots on the home page for premium listings</li></ul>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/sponsor" data-out target="_blank" rel="noopener">See packages on the original site</a></div>
'@

New-Static 'pro' 'Pro Membership' 'Pro Membership' 'Extra tools for serious applicants.' @'
<p>The free tier covers everything you need to browse and apply. Pro adds automation for people running many applications at once.</p>
<h2>Pro includes</h2>
<ul><li>Saved searches with alerts when new matches appear</li><li>Deadline reminders ahead of every saved programme</li><li>Priority placement in submission review</li></ul>
<p class="u-note">Pricing and current features live on the original site.</p>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/pro" data-out target="_blank" rel="noopener">View Pro plans on the original site</a></div>
'@

New-Static 'stories' 'Success Stories' 'Success Stories' 'People who found their programme here.' @'
<p>Applicants tell us which listing led them to an offer, a lab place or a funded year abroad. A few patterns show up again and again: they set deadline alerts early, they applied to more than one programme, and they asked for references weeks ahead.</p>
<h2>Want to be featured?</h2><p>Share your story after you hear back - accepted or not. Both help the next applicant.</p>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/stories" data-out target="_blank" rel="noopener">Read stories on the original site</a></div>
'@

New-Static 'mobility-scholarship' 'OU Mobility Scholarship' 'OU Mobility Scholarship — Apply Now' 'Our own small grant for students on the move.' @'
<p>The OU Mobility Scholarship is a modest grant that helps students cover the travel and setup costs that stop otherwise funded moves from happening - flights, deposits and the first month in a new city.</p>
<h2>Basics</h2>
<ul><li>Open to students worldwide with a confirmed place or programme offer</li><li>Covers travel and initial settling costs, not tuition</li><li>Rolling decisions four times a year</li></ul>
<div class="u-cta-row"><a class="btn btn-primary" href="https://opportunity-universe.com/en/mobility-scholarship" data-out target="_blank" rel="noopener">Apply on the original site</a></div>
'@

New-Static 'privacy' 'Privacy Policy' 'Privacy Policy' 'How this site handles data.' @'
<p>This mirror stores one thing in your browser: your cookie-banner choice, in localStorage. It never sends data anywhere.</p>
<h2>The original site</h2>
<p>Forms on this mirror hand your input to opportunity-universe.com over HTTPS; their privacy policy governs what happens after that. Passwords are never placed in URLs.</p>
<h2>Hotlinked images</h2>
<p>Covers and logos load directly from the original site's servers, which see your IP address when they do.</p>
<div class="u-cta-row"><a class="btn btn-ghost" href="https://opportunity-universe.com/en/privacy" data-out target="_blank" rel="noopener">Original privacy policy</a></div>
'@

New-Static 'imprint' 'Imprint' 'Imprint' 'Legal identification for the site operator.' @'
<p>Opportunity Universe<br>Postfach 762135<br>22069 Hamburg, Germany</p>
<p>Contact: <a href="mailto:info@opportunity-universe.com">info@opportunity-universe.com</a> · <a href="tel:+491776762399">+49 177 6762399</a></p>
<div class="u-cta-row"><a class="btn btn-ghost" href="https://opportunity-universe.com/en/imprint" data-out target="_blank" rel="noopener">Original imprint</a></div>
'@

"Generated 10 static pages under en/"
```

- [ ] **Step 2: Run the scaffold**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/scaffold-static.ps1`
Expected: `Generated 10 static pages under en/`.

- [ ] **Step 3: Run link checker + open 2 pages**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1` → broken links limited to the still-unbuilt `/en/register` (Task 9) and `/en/map` (Task 10); full `0 broken links` gate applies from Task 11.
Open `/en/about` (prose page) and `/en/faq` (accordion expands on click).

- [ ] **Step 4: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): 10 static pages via scaffold script"
```
---

### Task 9: Forms (login, register, submit, newsletter, matcher)

**Files:**
- Create: `opportunity-universe-clone/en/login/index.html`
- Create: `opportunity-universe-clone/en/register/index.html`
- Create: `opportunity-universe-clone/en/submit/index.html`
- Create: `opportunity-universe-clone/en/newsletter/index.html`
- Create: `opportunity-universe-clone/en/matcher/index.html`

**Interfaces:**
- Consumes: `form[data-redirect][data-drop]` handler from Task 2 (serializes fields → query string on `https://opportunity-universe.com<path>`, dropping fields listed in `data-drop`).
- Produces: form pages linked from header (Sign In / Join Free), "Submit Opportunity", newsletter links.

**Rule:** passwords are NEVER serialized (`data-drop="password,password2"`); the redirect lands on the original's own form.

- [ ] **Step 1: Create `en/login/index.html`**

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign In | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap">
  <form class="u-formcard" data-redirect="/en/login" data-drop="password">
    <h1>Sign In</h1>
    <p class="u-sub">Welcome back. Submitting hands you over to the original site — your password is never put in the URL.</p>
    <div class="u-field"><label for="l-email">Email</label><input id="l-email" type="email" name="email" required placeholder="you@example.com"></div>
    <div class="u-field"><label for="l-pass">Password</label><input id="l-pass" type="password" name="password" required placeholder="Your password"></div>
    <button class="btn btn-primary" type="submit">Sign In <i class="fa-solid fa-arrow-right"></i></button>
    <p class="u-form-alt">No account yet? <a href="/en/register">Join Free</a></p>
  </form>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 2: Create `en/register/index.html`** — same skeleton with these differences:
  - `<title>Join Free | Opportunity Universe</title>`
  - `<h1>Join Free</h1>`, sub: "Create a free account to save opportunities and get deadline reminders. Free forever, no card."
  - fields: `Email` (type=email name=email), `Password` (type=password name=password), `Country` (`<select name="country"><option value="">Select country</option>` + the same 18 country options as the home widget), `data-drop="password"` and `data-redirect="/en/register"`
  - button text `Create account`, alt line: `Already a member? <a href="/en/login">Sign In</a>`

- [ ] **Step 3: Create `en/submit/index.html`** (wide card)

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Submit Opportunity | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap">
  <form class="u-formcard wide" data-redirect="/en/submit">
    <h1>Submit Opportunity</h1>
    <p class="u-sub">Know a scholarship, fellowship or programme that is missing? Send it over — listings are reviewed before publishing.</p>
    <div class="u-field"><label for="s-title">Title <span class="u-req">*</span></label><input id="s-title" name="title" required placeholder="Programme name"></div>
    <div class="u-field"><label for="s-url">Link to official page <span class="u-req">*</span></label><input id="s-url" type="url" name="url" required placeholder="https://"></div>
    <div class="u-field"><label for="s-type">Type</label><select id="s-type" name="type" data-fill="type"></select></div>
    <div class="u-field"><label for="s-deadline">Deadline</label><input id="s-deadline" type="date" name="deadline"></div>
    <div class="u-field"><label for="s-notes">Notes</label><textarea id="s-notes" name="notes" rows="4" placeholder="Eligibility, funding, anything we should know"></textarea></div>
    <div class="u-field"><label for="s-email">Your email</label><input id="s-email" type="email" name="email" placeholder="you@example.com"></div>
    <button class="btn btn-primary" type="submit">Submit for review <i class="fa-solid fa-arrow-right"></i></button>
    <p class="u-form-alt">The final submission happens on the original site.</p>
  </form>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 4: Create `en/newsletter/index.html`**

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Opportunity Newsletter | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap">
  <form class="u-formcard" data-redirect="/en/newsletter">
    <h1>Opportunity Newsletter</h1>
    <p class="u-sub">One email a week with the new programmes you can actually apply for, matched to your country and field.</p>
    <div class="u-field"><label for="n-email">Email <span class="u-req">*</span></label><input id="n-email" type="email" name="email" required placeholder="you@example.com"></div>
    <div class="u-field"><label for="n-country">Country</label><select id="n-country" name="country"><option value="">Select country</option>
      <option value="in">India</option><option value="ng">Nigeria</option><option value="pk">Pakistan</option><option value="vn">Vietnam</option>
      <option value="id">Indonesia</option><option value="eg">Egypt</option><option value="ke">Kenya</option><option value="gh">Ghana</option>
      <option value="ph">Philippines</option><option value="br">Brazil</option><option value="mx">Mexico</option><option value="tr">Türkiye</option>
      <option value="de">Germany</option><option value="us">United States</option><option value="bd">Bangladesh</option>
      <option value="fr">France</option><option value="jp">Japan</option><option value="gb">United Kingdom</option></select></div>
    <div class="u-field"><label for="n-level">Level</label><select id="n-level" name="level">
      <option value="">Any level</option><option>Undergraduate</option><option>Master's</option><option>PhD</option><option>Postdoc</option><option>Professional</option></select></div>
    <button class="btn btn-primary" type="submit">Subscribe <i class="fa-solid fa-arrow-right"></i></button>
    <p class="u-form-alt">✓ Weekly · ✓ Personalised · ✓ 100% free</p>
  </form>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 5: Create `en/matcher/index.html`** (matcher = questionnaire shell that hands off to the original)

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scholarship Matcher | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap">
  <form class="u-formcard" data-redirect="/en/matcher">
    <h1>Scholarship Matcher</h1>
    <p class="u-sub">Answer three questions and continue on the original site, where the matching runs live.</p>
    <div class="u-field"><label for="m-country">Where do you want to study?</label><select id="m-country" name="country">
      <option value="">Anywhere</option><option>Germany</option><option>United Kingdom</option><option>United States</option>
      <option>Canada</option><option>Australia</option><option>Japan</option><option>China</option><option>France</option></select></div>
    <div class="u-field"><label for="m-level">Which level?</label><select id="m-level" name="level">
      <option value="">Any</option><option>Undergraduate</option><option>Master's</option><option>PhD</option><option>Postdoc</option></select></div>
    <div class="u-field"><label for="m-subject">Field of study</label><select id="m-subject" name="subject" data-fill="subject"></select></div>
    <button class="btn btn-primary" type="submit">Find my matches <i class="fa-solid fa-arrow-right"></i></button>
    <p class="u-form-alt">Matching continues on the original site with your answers.</p>
  </form>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 6: Run link checker + click-test one form**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1` → only `/en/map` (built in Task 10) still fails; full `0 broken links` gate applies from Task 11.
In browser, open `/en/newsletter`, type an email, submit → URL becomes `https://opportunity-universe.com/en/newsletter?email=...` (params preserved, redirect works).
Open `/en/login`, submit with password → lands on `https://opportunity-universe.com/en/login?email=...` with NO password in URL.

- [ ] **Step 7: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): 5 form pages redirecting to original with query params"
```

---

### Task 10: Map + Calendar shells

**Files:**
- Create: `opportunity-universe-clone/en/map/index.html`
- Create: `opportunity-universe-clone/en/calendar/index.html`

**Interfaces:**
- Consumes: Task 1 CSS (`.u-shell .u-map-view .u-cal*`).
- Produces: shell pages from header nav; real interaction links Out.

- [ ] **Step 1: Create `en/map/index.html`**

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>World Map | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap u-shell">
  <div class="u-crumb"><a href="/en/">Home</a> / World Map</div>
  <div class="u-shell-head">
    <div><h1><i class="fa-solid fa-earth-americas" style="color:var(--gold)"></i> World Map</h1>
      <p class="u-sub">Every in-person programme in the database, on one map.</p></div>
    <div class="u-mapstats" style="margin:0">
      <div><b>11,875</b><span>in-person opportunities</span></div>
      <div><b>167</b><span>countries &amp; territories</span></div>
    </div>
  </div>
  <div class="u-map-view">
    <div class="u-map-card">
      <h2>Explore the live map</h2>
      <p>This mirror clones the layout only — interactive pins, clustering and country clicks run on the original site.</p>
      <a class="btn btn-primary" href="https://opportunity-universe.com/en/map" data-out target="_blank" rel="noopener">Open interactive map <i class="fa-solid fa-arrow-right"></i></a>
    </div>
  </div>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 2: Create `en/calendar/index.html`**

```html
<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Calendar | Opportunity Universe</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@300;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="/assets/css/style.css">
</head><body>
<div id="ouHeader"></div>
<main id="main"><div class="u-wrap u-shell">
  <div class="u-crumb"><a href="/en/">Home</a> / Calendar</div>
  <div class="u-shell-head">
    <div><h1><i class="fa-solid fa-calendar-days" style="color:var(--gold)"></i> Deadline Calendar</h1>
      <p class="u-sub">Representative deadlines for September 2026 — the full, filterable calendar lives on the original site.</p></div>
    <a class="btn btn-primary" href="https://opportunity-universe.com/en/calendar" data-out target="_blank" rel="noopener">Open live calendar <i class="fa-solid fa-arrow-right"></i></a>
  </div>
  <div class="u-cal">
    <div class="u-cal-top"><b>September 2026</b><span class="u-note">Shell view · not interactive</span></div>
    <div class="u-cal-grid">
      <div class="u-cal-h">Mon</div><div class="u-cal-h">Tue</div><div class="u-cal-h">Wed</div><div class="u-cal-h">Thu</div>
      <div class="u-cal-h">Fri</div><div class="u-cal-h">Sat</div><div class="u-cal-h">Sun</div>
      <div class="u-cal-cell"><span class="u-cal-d">1</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">2</span><span class="u-cal-pill">Google Cloud AI Cup</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">3</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">4</span><span class="u-cal-pill hot">Marshall Scholarship</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">5</span><span class="u-cal-pill">ETH PhD Positions</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">6</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">7</span><span class="u-cal-pill">IDP IELTS Award</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">8</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">9</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">10</span><span class="u-cal-pill">Pradel Research Award</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">11</span><span class="u-cal-pill hot">Chevening Scholarship</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">12</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">13</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">14</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">15</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">16</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">17</span><span class="u-cal-pill">W. Eugene Smith Grant</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">18</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">19</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">20</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">21</span><span class="u-cal-pill">CERN Doctoral Program</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">22</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">23</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">24</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">25</span><span class="u-cal-pill hot">NASA Pathways Internship</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">26</span><span class="u-cal-pill">World Photo Annual</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">27</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">28</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">29</span></div>
      <div class="u-cal-cell"><span class="u-cal-d">30</span></div>
    </div>
  </div>
</div></main>
<div id="ouFooter"></div><div id="ouCookie"></div>
<script>window.OU_PAGE={kind:"static"};</script>
<script src="/assets/js/data.js"></script>
<script src="/assets/js/components.js"></script>
</body></html>
```

- [ ] **Step 3: Run link checker**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1` → `OK ... 0 broken links`.

- [ ] **Step 4: Commit**

```bash
git add opportunity-universe-clone
git commit -m "feat(clone): map and calendar UI shells with CTAs to original"
```
---

### Task 11: Final verification + README

**Files:**
- Edit: `opportunity-universe-clone/README.md`
- Verify only (no new pages)

**Interfaces:**
- Consumes: everything from Tasks 1–10.
- Produces: ship gate — full link check, responsive/visual comparison against the original, final commit.

- [ ] **Step 1: Full link check**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1`
Expected: exit 0, `0 broken links`, ~89 HTML files (1 root redirect + 404 + 1 home en/index + 62 listing incl. countries index + 3 detail + 4 blog + 10 static + 5 forms + 2 shells + …; exact count printed by the script).
If any failure: fix the source file, re-run — never ship with a failing check.

- [ ] **Step 2: Remote-link mode (optional but recommended)**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1 -CheckRemote`
Expected: external `https://opportunity-universe.com/...` targets return HTTP < 400 (network-dependent; record any dead original URLs in README known-issues instead of breaking local checks).

- [ ] **Step 3: Visual + responsive comparison vs original (3 pages)**

For `/`, `/en/type/scholarship`, `/en/login`:
1. Serve locally (`python -m http.server 8080` from project root) and open the original `https://opportunity-universe.com/en/` in a second tab.
2. Compare at 1440×900, 768×1024, 390×844 (browser devtools).
3. Checklist: header two rows identical structure; hero bands same spacing/colors; cards same image/heading/meta layout; footer columns + gold band match; no horizontal scroll at 390px.
4. Fix any deviation in `assets/css/style.css` (prefer CSS-only fixes; no content edits).

- [ ] **Step 4: Link-behaviour audit**

In browser, verify and tick off:
- [ ] Listing/category nav (chips, "More" menu, footer links) → local `/en/...` URLs, page loads locally (footer mirrors the original: countries + tools; only `/en/guide` + socials link out with `data-out` / allowlisted domains).
- [ ] Search box submit → `https://opportunity-universe.com/en/search?q=...&type=...&subject=...`.
- [ ] Any opportunity card / blog card → original site in new tab (`data-out`).
- [ ] Detail "Apply" buttons → original site.
- [ ] `/en/login` submit → original site, URL contains `email` but NOT `password`.
- [ ] `/en/mobility-scholarship` CTA → original site.
- [ ] Cookie banner: Accept → banner hides, persists after reload (`localStorage['ou-cc']`).
- [ ] Burger menu opens/closes on mobile width.

- [ ] **Step 5: Finalize README**

Ensure `opportunity-universe-clone/README.md` covers (add missing sections):
- What this is: static frontend mirror, no backend, no build step at runtime.
- Layout map: page inventory table (template → count → example URL).
- Build-time tools: `tools/scaffold-listings.ps1`, `tools/scaffold-static.ps1`, `tools/check-links.ps1` — when to re-run them (after data/nav changes).
- Content rules: condensed original-style bodies, hotlinked images, redirect contract (search/forms → original; listing nav local).
- How to preview: `python -m http.server 8080`.
- Known issues: any `-CheckRemote` failures, deliberately stubbed pages (`en/index.html` redirect stub), etc.

- [ ] **Step 6: Final green check + commit**

Run: `powershell -NoProfile -File C:/Opencode/opportunity-universe-clone/tools/check-links.ps1` → exit 0.

```bash
git add opportunity-universe-clone
git commit -m "chore(clone): final verification, README, ship gate green"
```

---

## Commit Strategy

One commit per task (11 tasks, ~11 commits), each gated on its link-checker step passing. Never batch changes across tasks. If a check fails, fix and amend only within the same task — never push a red check.

## Success Criteria (acceptance)

1. `check-links.ps1` exits 0 with `0 broken links` over the full tree.
2. URL parity: every page listed in the page inventory renders at its path; sample URLs open correctly.
3. Redirect contract: search + all forms → original site with query params preserved (no passwords in URLs); listing/nav stays local; cards/CTAs → original via `data-out`.
4. Visual comparison at 1440/768/390 px shows no structural deviation from the original (header, hero, cards, footer, responsive behaviour).
5. Cookie banner, burger menu, filters, and card grids behave per spec on a fresh browser profile.
6. README documents the layout, tools and content rules.

## Out of Scope (reminders)

- No backend, database, auth, scraping at runtime, package installs, or bundler.
- No copied long-form content from the original (condensed bodies only).
- No commits unless the user explicitly asks during execution (the task list above assumes commit-per-task — flag this to the user before executing if they have not confirmed).

## Open Questions

None — spec and design decisions were resolved and approved during brainstorming.

