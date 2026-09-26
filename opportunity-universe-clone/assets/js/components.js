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
      if (b.hasAttribute("data-cc-open")) { e.preventDefault(); localStorage.removeItem("ou-cc"); box.hidden = false; return; }
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
