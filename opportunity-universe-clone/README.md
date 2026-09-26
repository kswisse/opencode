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
