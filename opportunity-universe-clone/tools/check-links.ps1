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
    $path = (($href -split '#')[0] -split '\?')[0]
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
