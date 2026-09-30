#!/usr/bin/env python3
"""Builds every HTML page from content/*.json and the templates below.

Run from the project folder after changing content or templates:

    python3 tools/build.py

The generated HTML is committed, so Netlify just publishes the folder.
"""
import json
import os
import struct
import subprocess
from datetime import date
from html import escape as e

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_URL = "https://kostandyan.me"


def load(name):
    with open(os.path.join(ROOT, "content", name), encoding="utf-8") as f:
        return json.load(f)


WORKS = load("works.json")
EXPERIENCE = load("experience.json")
SKILLS = load("skills.json")

EMAIL = "levon.kostandyan@gmail.com"
CV = "/assets/Levon_Kostandyan_CV.pdf"
PORTRAIT = "/assets/img/portrait.jpg"
SOCIAL = [
    ("LinkedIn", "https://www.linkedin.com/in/levon-kostandyan-ba30267b"),
    ("Instagram", "https://www.instagram.com/_form_live"),
    ("Behance", "https://www.behance.net/SvGravity"),
    ("Dribbble", "https://dribbble.com/SvGravity"),
]

ABOUT = [
    "I'm a Lead UX Designer based in Yerevan, Armenia. Since 2013 I've been designing complicated systems and products built on huge amounts of data — from public services to global healthcare platforms.",
    "At ISAA (Information Systems Agency of Armenia) I lead a team of three designers in a national digital transformation initiative, delivering UX improvements across eight public services. I created the Henaket design system, adopted by major government agencies such as MIA, MOH and the Rescue Service as well as third-party vendors, contributing to a 34% increase in citizen engagement.",
    "Before that, at EPAM Systems, I worked with international teams on healthcare and pharma projects for HCA Healthcare, Novartis and SPARKD. My research, wireframes and design system work helped Novartis scientists reduce research time by 44%. Earlier roles at RenderForest, SFL, Ucraft and Smartclick.ai took me from UI/UX designer to art director and design team lead.",
    "My work spans the whole process: stakeholder workshops, interviews and usability testing; journey mapping and prioritization; information architecture, prototypes and design systems. I work in English, Russian and Armenian.",
]
# Figures from the CV, shown as a quiet strip under the menu on Home: (number, what, where)
START_YEAR = 2013
IMPACT = [
    ("34%", "more citizen engagement", "ISAA"),
    ("44%", "less research time", "Novartis"),
    ("Languages", "", "English, Russian, Armenian"),
]
CONTACT_TEXT = "I am always excited to meet new people, whether for work or personal reasons. If you have any questions, comments, or would want to discuss future opportunities, please contact me through the following channels."

def person_jsonld():
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Levon Kostandyan",
        "jobTitle": "Lead UX Designer",
        "worksFor": {"@type": "Organization", "name": "ISAA (Information Systems Agency of Armenia)"},
        "address": {"@type": "PostalAddress", "addressLocality": "Yerevan", "addressCountry": "AM"},
        "email": f"mailto:{EMAIL}",
        "url": SITE_URL + "/",
        "image": SITE_URL + PORTRAIT,
        "sameAs": [url for _, url in SOCIAL],
        "knowsLanguage": ["en", "ru", "hy"],
        "knowsAbout": [x for group in SKILLS if group["title"] != "Languages" for x in group["items"]],
    }
    return f'\n  <script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


DESC = ("Levon Kostandyan — Lead UX Designer based in Yerevan, Armenia, "
        "specializing in complicated systems and huge data.")


# ---------------------------------------------------------------- helpers

ARROWS = {
    "right": "M4 12h16M14 6l6 6-6 6",
    "left": "M20 12H4M10 6l-6 6 6 6",
    "out": "M7 17L17 7M8 7h9v9",
    "down": "M12 4v16M6 14l6 6 6-6",
    "up": "M12 20V4M6 10l6-6 6 6",
}


def icon(name):
    return (f'<svg class="arrow arrow--{name}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.5" aria-hidden="true"><path d="{ARROWS[name]}"/></svg>')


def dl_icon():
    """Download arrow over a tray; on click (site.js adds .is-done) the arrow
    drops into the tray and a tick draws in."""
    return ('<svg class="arrow dl__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.5" aria-hidden="true"><g class="dl__arrow"><path d="M12 3v12M7 10l5 5 5-5"/></g>'
            '<path class="dl__check" d="M6 11.5l4 4L18 7.5"/><path d="M5 20h14"/></svg>')


def jpeg_size(src):
    """Width/height of a JPEG, read from its header (no dependencies)."""
    with open(os.path.join(ROOT, src.lstrip("/")), "rb") as f:
        data = f.read()
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    raise ValueError(f"no size found in {src}")


# Smaller copies the browser can pick from (srcset). Generated next to the
# original with macOS's built-in `sips` the first time the build needs them.
VARIANT_WIDTHS = [
    ("/cover.jpg", [720, 1080]),
    ("/banner.jpg", [1000]),
    ("/work-item_", [1000, 1400]),
    ("/portrait.jpg", [700, 1100]),
]
SIZES = {
    "/cover.jpg": "(max-width: 800px) 100vw, (max-width: 1024px) 50vw, 33vw",
    "/banner.jpg": "100vw",
    "/work-item_": "(max-width: 800px) 100vw, 62vw",   # the 8-of-12 text column
    "/portrait.jpg": "(max-width: 800px) 100vw, 30vw",  # the 4-of-12 column
}


def variant_path(src, width):
    stem, ext_ = os.path.splitext(src)
    return f"{stem}-{width}w{ext_}"


def ensure_variant(src, width):
    out = variant_path(src, width)
    full_out = os.path.join(ROOT, out.lstrip("/"))
    if not os.path.exists(full_out):
        try:
            subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "78",
                            "--resampleWidth", str(width), os.path.join(ROOT, src.lstrip("/")),
                            "--out", full_out], check=True, capture_output=True)
        except (OSError, subprocess.CalledProcessError):
            return None  # not on a Mac: fall back to the original only
    return out


def srcset(src, w):
    for key, widths in VARIANT_WIDTHS:
        if key in src:
            parts = [(v, width) for width in widths if width < w
                     for v in [ensure_variant(src, width)] if v]
            if not parts:
                return ""
            entries = ", ".join(f"{v} {width}w" for v, width in parts) + f", {src} {w}w"
            return f' srcset="{entries}" sizes="{SIZES[key]}"'
    return ""


def media(src, alt="", i=0, lazy=True, zoom=False, extra=""):
    """Image that uncovers on scroll. zoom=True opens it full size on click."""
    w, h = jpeg_size(src)
    loading = 'loading="lazy" ' if lazy else 'fetchpriority="high" '
    img = f'<img src="{src}"{srcset(src, w)} alt="{e(alt)}" width="{w}" height="{h}" {loading}decoding="async">'
    if zoom:
        label = f"Enlarge image: {alt}" if alt else "Enlarge image"
        img = f'<a class="zoom" href="{src}" aria-label="{e(label)}">{img}</a>'
    return f'<div class="media" data-reveal style="--i:{i}">{img}{extra}</div>'


def copy_btn():
    return (f'<button class="copy" type="button" data-copy="{EMAIL}">'
            f'<svg class="copy__tick" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" '
            f'aria-hidden="true"><path d="M4 12.5l5 5L20 6.5"/></svg>'
            f'<span class="copy__label" aria-live="polite">Copy</span></button>')


def lines(tag, cls, parts, i=0):
    """Headline whose lines slide up one after another. parts = [(text, class), ...]"""
    spans = "".join(f'<span class="ln{" ln--" + c if c else ""}" style="--l:{i + n}"><span class="{c}">{e(t)}</span> </span>'
                    for n, (t, c) in enumerate(parts))
    return f'<{tag} class="{cls} lines" data-reveal>{spans}</{tag}>'


def tags(w):
    out = f'<span class="tag">{e(w["platform"])}</span>'
    if w["nda"]:
        out += '<span class="tag">NDA</span>'
    return f'<span class="tags">{out}</span>'


# Screen-reader-only hints: new tabs and file types aren't obvious otherwise
NEW_TAB = '<span class="sr"> (opens in a new tab)</span>'
PDF = '<span class="sr"> (PDF)</span>'


def ext(url):
    return f'href="{e(url)}" target="_blank" rel="noopener noreferrer"'


# ---------------------------------------------------------------- page shell

def header(current):
    links = []
    for n, (key, label) in enumerate([("about", "About"), ("works", "Work"), ("contact", "Contact")]):
        cur = ' aria-current="page"' if key == current else ""
        links.append(f'      <a class="box" href="/{key}/" style="--i:{n}"{cur}>'
                     f'<span class="nav__num num" aria-hidden="true">{n + 1:02d}</span><span>{label}</span>{icon("right")}</a>')
    return f"""<header class="site-header box">
    <span class="progress" aria-hidden="true"></span>
    <a class="brand" href="/">Levon Kostandyan <span class="brand__role">Lead UX Designer</span></a>
    <button class="menu-btn box" type="button" aria-expanded="false" aria-controls="site-nav">
      <span class="sr">Menu</span><i></i><i></i>
    </button>
    <nav id="site-nav" class="nav" aria-label="Main">
{chr(10).join(links)}
      <a class="box nav__cv dl" href="{CV}" download data-dl>Download CV{PDF}{dl_icon()}</a>
      <div class="nav__foot" style="--i:3">
        <span class="label">Say hello</span>
        <a class="u" href="mailto:{EMAIL}">{EMAIL}</a>
        <a class="nav__foot-cv dl" href="{CV}" download data-dl><span class="u">Download CV</span>{PDF}{dl_icon()}</a>
      </div>
    </nav>
  </header>"""


def url_for(path):
    """File path -> public URL: about/index.html -> /about/"""
    return "/" + path[: -len("index.html")] if path.endswith("index.html") else "/" + path


# Link previews (LinkedIn, messengers, email): 1200×630 images
OG_IMAGE = "/assets/img/og.jpg"
OG_ALT = "Levon Kostandyan — Lead UX Designer, designing complicated systems and huge data"


def page(path, title, desc, body, current=None, og_image=OG_IMAGE, og_alt=OG_ALT, head_extra="", indexable=True):
    canonical = SITE_URL + url_for(path)
    seo = (f'<link rel="canonical" href="{canonical}">\n  <meta property="og:url" content="{canonical}">'
           if indexable else '<meta name="robots" content="noindex">')
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)}</title>
  <meta name="description" content="{e(desc)}">
  <meta name="theme-color" content="#1a1a1a">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Levon Kostandyan">
  <meta property="og:locale" content="en_US">
  <meta property="og:title" content="{e(title)}">
  <meta property="og:description" content="{e(desc)}">
  <meta property="og:image" content="{SITE_URL}{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{e(og_alt)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image:alt" content="{e(og_alt)}">
  {seo}{head_extra}
  <link rel="icon" href="/assets/favicon-32.png" type="image/png" sizes="32x32">
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
  <link rel="stylesheet" href="/css/style.css">
  <!-- Chrome: load a page in the background when its link is hovered, so the
       click (and the page transition) is instant. Other browsers ignore this. -->
  <script type="speculationrules">
    {{"prerender": [{{"where": {{"and": [{{"href_matches": "/*"}}, {{"not": {{"href_matches": "/assets/*"}}}}, {{"not": {{"href_matches": "/images/*"}}}}]}}, "eagerness": "moderate"}}]}}
  </script>
  <script>
    // Reveal targets start hidden only when JS runs. If site.js never loads,
    // drop the class so nothing stays invisible.
    var d = document.documentElement;
    d.classList.add("js");
    setTimeout(function () {{
      if (!d.classList.contains("reveal-ready")) d.classList.remove("js");
    }}, 3000);
    // Arriving through a page transition: show what's on screen as part of it
    // (html.arriving); site.js settles things once the transition ends. This
    // has to live here, before the page first paints.
    var arrived = function () {{
      d.setAttribute("data-arrived", "");
      window.dispatchEvent(new Event("arrived"));
    }};
    window.addEventListener("pagereveal", function (e) {{
      if (!e.viewTransition) return;
      d.classList.add("arriving");
      e.viewTransition.finished.then(arrived, arrived);
    }});
    // Browsers without cross-page transitions (Firefox, older Safari) get the
    // same fade-and-rise by hand: site.js fades the old page out on click, and
    // the next page fades in here if we came from one of our own links.
    if (!("CSSViewTransitionRule" in window) && !matchMedia("(prefers-reduced-motion: reduce)").matches) {{
      d.classList.add("vt-fallback");
      try {{
        if (sessionStorage.getItem("vt-nav")) {{
          sessionStorage.removeItem("vt-nav");
          d.classList.add("vt-enter", "arriving");
          setTimeout(arrived, 700);
        }}
      }} catch (err) {{}}
    }}
  </script>
  <script src="/js/site.js" defer></script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  {header(current)}

  <main id="main" class="page" tabindex="-1">
{body}
  </main>

  <footer class="site-footer">
    <div class="site-footer__bar">
      <p>&copy; <span data-year>2026</span> Levon Kostandyan</p>
      <a class="to-top" href="#top"><span class="u">Back to top</span>{icon("up")}</a>
    </div>
  </footer>
</body>
</html>
"""
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)


# ---------------------------------------------------------------- shared blocks

def sec_head(title, count=None, link="", id_=""):
    """Section title with an optional item count as a superscript: Skills (04)"""
    id_attr = f' id="{id_}"' if id_ else ""
    sup = f'<sup class="sec-title__count num">({count:02d})</sup>' if count is not None else ""
    return f"""    <div class="sec-head box sec"{id_attr} data-draw>
      <h2 class="sec-title" data-reveal>{e(title)}{sup}</h2>
      {link}
    </div>"""


def head_link(href, text, arrow="right", extra=""):
    return (f'<a href="{href}"{extra} data-reveal style="--i:1"><span class="u">{text}</span>{icon(arrow)}</a>')


def card_info(w):
    """Panel that rises over the cover on hover. aria-hidden: the card's
    link text (title, tags) already names it."""
    return (f'<span class="card__info" aria-hidden="true">'
            f'<span style="--k:0"><span class="label">My role</span>'
            f'<span class="card__role">{e(w["role"])}</span></span>'
            f'<span class="card__cta" style="--k:1">View case study{icon("right")}</span></span>')


def card(w, n, i, numbered=True):
    index = f'<sup class="card__index num">{n:02d}</sup>' if numbered else ""
    return f"""      <a class="card box" href="/works/{w["id"]}/" data-draw>
        {media(w["cover"], "", i, extra=card_info(w))}
        <span class="card__meta" data-reveal style="--i:{i}">
          <span class="card__title">{e(w["name"])}{index}</span>
          {tags(w)}
        </span>
      </a>"""


def more_cell(links, i):
    """Last cell of the Works grid: more work elsewhere, one row per link."""
    rows = "\n".join(f'          <a {ext(url)} data-reveal style="--i:{i + n + 1}"><span class="u">{e(name)}</span>{NEW_TAB}{icon("out")}</a>'
                     for n, (name, url) in enumerate(links))
    return f"""      <div class="card card--more box" data-draw>
        <span class="label" data-reveal style="--i:{i}">More work</span>
        <div class="more-links">
{rows}
        </div>
      </div>"""


def link_list(with_cv=False):
    items = [(name, "", ext(url), NEW_TAB + icon("out")) for name, url in SOCIAL]
    if with_cv:
        items.append(("Download CV", " dl", f'href="{CV}" download data-dl', PDF + dl_icon()))
    rows = "\n".join(
        f'        <li data-reveal style="--i:{n}"><a class="box fill{cls}" {attrs} data-draw>'
        f'<span>{name}</span>{svg}</a></li>'
        for n, (name, cls, attrs, svg) in enumerate(items))
    return f'      <ul class="link-list c-4">\n{rows}\n      </ul>'


def contact_cta(label, heading, text, extra_cls="", with_cv=False):
    return f"""    <section class="cta row box sec {extra_cls}" data-draw>
      <div class="cell c-8 div box cta__text" data-draw>
        <p class="label" data-reveal>{label}</p>
        <div class="cta__body">
          {heading}
          <p class="muted" data-reveal style="--i:2">{e(text)}</p>
        </div>
        <div class="cta__email-row" data-reveal style="--i:3">
          <a class="cta__email" href="mailto:{EMAIL}"><span class="u u--on">{EMAIL}</span></a>
          {copy_btn()}
        </div>
      </div>
{link_list(with_cv)}
    </section>"""


# ---------------------------------------------------------------- home

featured = [(n, w) for n, w in enumerate(WORKS, 1) if w["featured"]]
# Home shows a few picks, so numbers from the full Work list (01, 02, 04…) would read as gaps
home_cards = "\n".join(card(w, n, i % 3, numbered=False) for i, (n, w) in enumerate(featured))

def exp_list(items):
    rows = "\n".join(f"""      <li class="box" data-draw>
        <div class="exp-row" data-reveal style="--i:{i}">
          <span class="h3">{e(x["company"])}</span>
          <span class="muted">{e(x["role"])}</span>
          <span class="dim num">{e(x["dates"])}</span>
        </div>
      </li>""" for i, x in enumerate(items))
    return f'    <ul class="exp-list box sec" data-draw>\n{rows}\n    </ul>'


facts = [
    ("Based in", "Yerevan, Armenia"),
    ("Currently", "Lead UX Designer at ISAA"),
    ("Experience", f"{date.today().year - START_YEAR} years designing digital products"),
]
fact_cells = "\n".join(f"""      <div class="cell c-4 div box" data-draw>
        <p class="label" data-reveal style="--i:{i}">{k}</p>
        <p data-reveal style="--i:{i}">{e(v)}</p>
      </div>""" for i, (k, v) in enumerate(facts))

impact_cells = "\n".join(f"""      <div class="cell c-4 div box" data-draw>
        <p data-reveal style="--i:{i}"><span class="impact__num num">{num}</span> {e(text)}{f' <span class="impact__src">· {e(where)}</span>' if where else ""}</p>
      </div>""" for i, (num, text, where) in enumerate(IMPACT))

page("index.html", "Levon Kostandyan — Lead UX Designer", DESC, f"""    <section class="impact row box sec" data-draw aria-label="Impact">
{impact_cells}
    </section>

    <section class="hero row box sec" data-draw>
      <div class="cell c-12 hero__text">
        {lines("h1", "display spotlight", [("Lead UX Designer", ""), ("designing complicated", "dim"), ("systems and huge data.", "dim")])}
      </div>
    </section>

    <section class="facts quad row box sec" data-draw aria-label="At a glance">
{fact_cells}
    </section>

{sec_head("Selected work", link=head_link("/works/", "All work"))}
    <div class="cards box sec" data-draw>
{home_cards}
    </div>

{sec_head("Experience", len(EXPERIENCE), head_link("/about/#experience", "Full experience"))}
{exp_list(EXPERIENCE[:5])}

{contact_cta("Contact", lines("h2", "display", [("Let's work", ""), ("together.", "dim")]), CONTACT_TEXT.split(". ")[0] + ".")}""",
     current=None, head_extra=person_jsonld())

# ---------------------------------------------------------------- works

all_cards = [card(w, n, (n - 1) % 3) for n, w in enumerate(WORKS, 1)]
all_cards.append(more_cell([("Behance", "https://www.behance.net/SvGravity"),
                            ("Dribbble", "https://dribbble.com/SvGravity")], 1))

WORKS_DESC = ("UX case studies by Levon Kostandyan: " + ", ".join(w["name"] for w in WORKS) + ".")
page("works/index.html", "Work — Levon Kostandyan", WORKS_DESC, f"""    <section class="page-head row box sec" data-draw>
      <div class="cell c-8 div box" data-draw>
        <p class="label" data-reveal>Work</p>
        {lines("h1", "display", [("Selected work", "")])}
      </div>
      <div class="cell c-4">
        <p class="label" data-reveal>Case studies</p>
        <p class="page-head__count num" data-reveal style="--i:1">{len(WORKS):02d}</p>
      </div>
    </section>

    <div class="cards box sec" data-draw>
{chr(10).join(all_cards)}
    </div>""", current="works")

# ---------------------------------------------------------------- case studies


def block(b, alt):
    if b["type"] == "text":
        return f'<p data-reveal>{e(b["value"])}</p>'
    if b["type"] == "image":
        return media(b["src"], b.get("alt", alt), zoom=True)
    if b["type"] == "list":
        items = "".join(f"<li>{e(x)}</li>" for x in b["items"])
        return f'<h3 data-reveal>{e(b["title"])}</h3><ul data-reveal>{items}</ul>'
    raise ValueError(b["type"])


def case_summary(w, limit=158):
    """Meta description: the work's own summary, or else its opening text cut
    at a sentence (or word) boundary, for search results and link previews."""
    if w.get("summary"):
        return w["summary"]
    first = next(b["value"] for s in w["sections"] for b in s["blocks"] if b["type"] == "text")
    text = " ".join(first.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = cut.rfind(". ")
    if end > limit * 0.55:
        return cut[:end + 1]
    return cut[:cut.rfind(" ")].rstrip(",;:—– ") + "…"


def case_og(w):
    """1200×630 preview cropped from the top of the work's cover."""
    return w["cover"].replace("/cover.jpg", "/og.jpg")


def case_jsonld(w):
    url = SITE_URL + f'/works/{w["id"]}/'
    data = {
        "@context": "https://schema.org",
        "@type": "CreativeWork",
        "name": w["name"],
        "headline": f'{w["name"]} ({w["platform"]}) — UX case study',
        "description": case_summary(w),
        "genre": "UX case study",
        "inLanguage": "en",
        "url": url,
        "image": SITE_URL + case_og(w),
        "author": {"@type": "Person", "name": "Levon Kostandyan", "url": SITE_URL + "/"},
    }
    return f'\n  <script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


total = len(WORKS)
for n, w in enumerate(WORKS, 1):
    if w["caseStudy"]:
        third = f"""      <a class="cell c-4 box fill" {ext(w["caseStudy"])} data-draw>
        <p class="label" data-reveal style="--i:2">{e(w.get("caseStudyLabel", "Full case study"))}</p>
        <p data-reveal style="--i:2"><span>{e(w.get("caseStudyText", "View on Behance"))}</span>{NEW_TAB}{icon("out")}</p>
      </a>"""
    elif w["nda"]:
        third = f"""      <div class="cell c-4 box" data-draw>
        <p class="label" data-reveal style="--i:2">Confidentiality</p>
        <p data-reveal style="--i:2">Under NDA</p>
      </div>"""
    else:
        third = ""  # public, with no case study elsewhere: Role and Platform share the row
    meta = "c-4" if third else "c-6"

    sections = []
    for k, s in enumerate(w["sections"], 1):
        blocks = "\n            ".join(block(b, f'{w["name"]} — {s["title"]}') for b in s["blocks"])
        sections.append(f"""    <section class="case-sec row box sec" data-draw>
      <div class="cell c-4 div box case-sec__label" data-draw>
        <div class="sticky">
          <p class="label" data-reveal>{k:02d}</p>
          <h2 class="h3" data-reveal style="--i:1">{e(s["title"])}</h2>
        </div>
      </div>
      <div class="cell c-8">
        <div class="prose">
            {blocks}
        </div>
      </div>
    </section>""")

    prev_w = WORKS[(n - 2) % total]
    next_w = WORKS[n % total]

    page(f'works/{w["id"]}/index.html', f'{w["name"]} — Levon Kostandyan', case_summary(w), f"""    <section class="case-head row box sec" data-draw>
      <div class="cell c-12 case-head__title">
        <div class="case-head__top" data-reveal>
          <a class="case-head__back" href="/works/">{icon("left")}<span class="u">All work</span></a>
          <p class="label">Case study {n:02d} / {total:02d}</p>
        </div>
        {lines("h1", "h1", [(w["name"], "")])}
        <div data-reveal style="--i:2">{tags(w)}</div>
      </div>
    </section>

    <section class="case-meta row box sec" data-draw aria-label="Project details">
      <div class="cell {meta} div box" data-draw>
        <p class="label" data-reveal>Role</p>
        <p data-reveal>{e(w["role"])}</p>
      </div>
      <div class="cell {meta}{" div" if third else ""} box" data-draw>
        <p class="label" data-reveal style="--i:1">Platform</p>
        <p data-reveal style="--i:1">{e(w["platform"])}</p>
      </div>
{third}
    </section>

    <div class="case-banner box sec" data-draw>
      {media(w["banner"], w["name"], lazy=False)}
    </div>

{chr(10).join(sections)}

    <nav class="pager row box sec" aria-label="More case studies" data-draw>
      <a class="cell c-6 div box fill" href="/works/{prev_w["id"]}/" data-draw>
        <span class="label">Previous</span>
        <span class="h2">{icon("left")}<span>{e(prev_w["name"])}</span></span>
      </a>
      <a class="cell c-6 box fill" href="/works/{next_w["id"]}/" data-draw>
        <span class="label">Next</span>
        <span class="h2"><span>{e(next_w["name"])}</span>{icon("right")}</span>
      </a>
    </nav>""", current="works", og_image=case_og(w), og_alt=f'{w["name"]} ({w["platform"]}) case study',
         head_extra=case_jsonld(w))

# ---------------------------------------------------------------- about

about_paras = "\n".join(f'          <p data-reveal style="--i:{i + 1}">{e(p)}</p>' for i, p in enumerate(ABOUT))

# Roles with a written summary get a full row; the rest are listed compactly.
detailed = [x for x in EXPERIENCE if x.get("summary")]
earlier = [x for x in EXPERIENCE if not x.get("summary")]

exp_items = []
for x in detailed:
    summary = "\n".join(f"            <p data-reveal>{e(p)}</p>" for p in x["summary"])
    org = f'\n          <p class="dim" data-reveal style="--i:1">{e(x["org"])}</p>' if x.get("org") else ""
    exp_items.append(f"""    <article class="exp-item row box sec" data-draw>
      <div class="cell c-4 div box exp-item__meta" data-draw>
        <div class="sticky">
          <h3 class="h3" data-reveal>{e(x["company"])}</h3>{org}
          <p class="muted" data-reveal style="--i:2">{e(x["role"])}</p>
          <p class="dim num" data-reveal style="--i:3">{e(x["dates"])}</p>
        </div>
      </div>
      <div class="cell c-8">
        <div class="prose">
{summary}
        </div>
      </div>
    </article>""")

skill_cells = "\n".join(f"""      <div class="cell c-3 div box" data-draw>
        <h3 class="label" data-reveal style="--i:{i}">{e(s["title"])}</h3>
        <ul class="skill-list" data-reveal style="--i:{i}">{"".join(f"<li>{e(item)}</li>" for item in s["items"])}</ul>
      </div>""" for i, s in enumerate(SKILLS))

ABOUT_DESC = ("About Levon Kostandyan, Lead UX Designer at ISAA in Yerevan: designing since 2013, "
              "creator of the Henaket design system, healthcare and pharma work at EPAM.")
page("about/index.html", "About — Levon Kostandyan", ABOUT_DESC, f"""    <section class="about-hero row box sec" data-draw>
      <div class="cell c-4 div box" data-draw>
        {media(PORTRAIT, "Portrait of Levon Kostandyan", lazy=False)}
      </div>
      <div class="cell c-8 about-hero__text">
        <p class="label" data-reveal>About</p>
        {lines("h1", "h1", [("Hello, I'm Levon.", "")])}
        <div class="prose">
{about_paras}
        </div>
        <a class="btn fill dl" href="{CV}" download data-dl data-reveal style="--i:5"><span>Download CV</span>{PDF}{dl_icon()}</a>
      </div>
    </section>

{sec_head("Experience", len(EXPERIENCE), id_="experience")}
{chr(10).join(exp_items)}
{sec_head("Earlier roles", len(earlier))}
{exp_list(earlier)}

{sec_head("Skills", len(SKILLS))}
    <section class="skills quad row box sec" data-draw aria-label="Skills and languages">
{skill_cells}
    </section>

{contact_cta("Contact", lines("h2", "display", [("Let's work", ""), ("together.", "dim")]), CONTACT_TEXT.split(". ")[0] + ".")}""",
     current="about", head_extra=person_jsonld())

# ---------------------------------------------------------------- contact

page("contact/index.html", "Contact — Levon Kostandyan",
     "Get in touch with Levon Kostandyan, Lead UX Designer in Yerevan: email, LinkedIn, Behance, Dribbble and CV.",
     contact_cta("Contact", lines("h1", "display", [("Let's talk.", "")]), CONTACT_TEXT, "contact", with_cv=True),
     current="contact")

# ---------------------------------------------------------------- 404

page("404.html", "Page not found — Levon Kostandyan", DESC, f"""    <section class="notfound row box sec" data-draw>
      <div class="cell c-8 div box notfound__text" data-draw>
        <p class="label" data-reveal>Error 404</p>
        <div>
          {lines("h1", "display", [("Page not found.", ""), ("It may have moved.", "dim")])}
        </div>
      </div>
      <ul class="link-list c-4">
        <li data-reveal style="--i:0"><a class="box fill" href="/" data-draw><span>Home</span>{icon("right")}</a></li>
        <li data-reveal style="--i:1"><a class="box fill" href="/works/" data-draw><span>Work</span>{icon("right")}</a></li>
        <li data-reveal style="--i:2"><a class="box fill" href="/contact/" data-draw><span>Contact</span>{icon("right")}</a></li>
      </ul>
    </section>""", indexable=False)

# ---------------------------------------------------------------- robots + sitemap

sitemap_paths = ["index.html", "about/index.html", "works/index.html", "contact/index.html"] + \
    [f'works/{w["id"]}/index.html' for w in WORKS]
with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    f.writelines(f"  <url><loc>{SITE_URL}{url_for(p)}</loc></url>\n" for p in sitemap_paths)
    f.write("</urlset>\n")
with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")

print(f"Built {3 + 1 + len(WORKS)} pages, 404, sitemap.xml and robots.txt.")
