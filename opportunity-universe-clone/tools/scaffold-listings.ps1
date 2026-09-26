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