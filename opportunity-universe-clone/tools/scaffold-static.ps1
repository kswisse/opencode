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