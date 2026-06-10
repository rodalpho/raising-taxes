#!/usr/bin/env python3
"""Build the folio HTML edition of *Raising Taxes* into docs/.

Stdlib only. Parses the chapter markdown (a deliberately tiny subset:
## headings, *italics*, --- scene breaks, superscript footnotes with
end-of-chapter notes) and emits one ornamented page per chapter plus a
title page. Fails loudly on any footnote mismatch or broken link.
"""

import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
ASSETS = ROOT / "assets"

SUPS = {"¹": 1, "²": 2, "³": 3, "⁴": 4, "⁵": 5, "⁶": 6, "⁷": 7, "⁸": 8, "⁹": 9}

SOURCES = [
    "raising-taxes-chapter-one.md",
    "raising-taxes-chapter-two.md",
    "raising-taxes-chapter-three.md",
    "raising-taxes-chapter-four.md",
    "raising-taxes-chapter-five.md",
    "raising-taxes-chapter-six.md",
    "raising-taxes-chapter-seven.md",
    "raising-taxes-chapter-eight.md",
    "raising-taxes-chapter-nine-and-epilogue.md",
]

BOOK_TITLE = "Raising Taxes"
BYLINE = "A Discworld pastiche, in the style of Sir Terry Pratchett"

# ---------------------------------------------------------------- ornaments

G = '<g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'

ORNAMENTS = {
    "chapter-1": (  # a skeleton key crossed by a hairpin
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<circle cx="28" cy="36" r="9"/><circle cx="28" cy="36" r="3.5"/>'
        '<path d="M37 36 H92 M80 36 v9 M88 36 v7"/>'
        '<path d="M68 8 q-15 14 -19 46 M75 13 q-13 12 -17 41 M68 8 a4.5 4.5 0 0 1 7 5"/>'
        '<path d="M12 14 l3 3 M15 14 l-3 3 M104 50 l3 3 M107 50 l-3 3" stroke-width="1.4"/>'
        '</g></svg>'),
    "chapter-2": (  # the unassessable Guild building
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M30 56 L35 18 L60 12 L84 16 L90 56 Z"/>'
        '<path d="M35 18 L46 9 L66 14 L60 12"/>'
        '<path d="M42 26 h7 v8 h-7 z M58 24 h7 v8 h-7 z M74 26 h7 v8 h-7 z" stroke-width="1.6"/>'
        '<path d="M43 27 l5 6 M48 27 l-5 6" stroke-width="1.2"/>'
        '<path d="M75 27 l5 6 M80 27 l-5 6" stroke-width="1.2"/>'
        '<path d="M44 42 h6 v8 h-6 z M72 42 h6 v8 h-6 z" stroke-width="1.6"/>'
        '<path d="M56 44 h8 v12 h-8" stroke-width="1.6"/>'
        '<path d="M22 56 H98" stroke-width="1.6"/>'
        '</g></svg>'),
    "chapter-3": (  # the slim blue ledgers, and a working pen
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M28 50 h44 v7 h-44 z M32 43 h40 v7 h-40 z M30 36 h42 v7 h-42 z" stroke-width="1.8"/>'
        '<path d="M36 39.5 h8 M40 46.5 h8 M38 53.5 h8" stroke-width="1.2"/>'
        '<path d="M94 8 C84 20 76 34 70 52 M94 8 l-9 3 M91 14 l-8 2 M87 21 l-7 2 M83 28 l-6 2" stroke-width="1.6"/>'
        '<path d="M70 52 l-2 6 5 -3 z" stroke-width="1.4"/>'
        '</g></svg>'),
    "chapter-4": (  # a piano, mid-appointment
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M60 2 v12 M57 14 l-3 5 M60 14 v6 M63 14 l4 4" stroke-width="1.6"/>'
        '<path d="M40 30 L84 24 L88 44 L44 51 Z"/>'
        '<path d="M42 45 L86 38" stroke-width="1.4"/>'
        '<path d="M50 44 v3 M58 43 v3 M66 42 v3 M74 41 v3" stroke-width="1.2"/>'
        '<path d="M48 51 v7 M82 45 v7" stroke-width="1.8"/>'
        '<path d="M28 20 l-5 -4 M30 38 l-7 1 M96 16 l6 -4 M94 32 l7 2" stroke-width="1.2"/>'
        '</g></svg>'),
    "chapter-5": (  # the pot of that-which-is-owed
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M48 20 C40 22 36 30 36 38 C36 50 44 56 60 56 C76 56 84 50 84 38 C84 30 80 22 72 20"/>'
        '<ellipse cx="60" cy="20" rx="13" ry="4.5"/>'
        '<path d="M60 15.5 v-4 M56 9 a4 4 0 0 1 8 0" stroke-width="1.6"/>'
        '<path d="M42 38 l6 -4 6 4 6 -4 6 4 6 -4 6 4" stroke-width="1.4"/>'
        '<circle cx="97" cy="51" r="3.2" stroke-width="1.8"/>'
        '<path d="M22 50 q4 -3 8 0" stroke-width="1.2"/>'
        '</g></svg>'),
    "chapter-6": (  # half-moon spectacles, and a tick the colour of fog
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M28 22 h22 M68 22 h22 M28 22 a11 11 0 0 0 22 0 M68 22 a11 11 0 0 0 22 0"/>'
        '<path d="M50 22 q10 -6 18 0 M28 22 l-8 -4 M90 22 l8 -4" stroke-width="1.8"/>'
        '<path d="M46 48 l9 8 19 -18" stroke-width="2.6"/>'
        '</g></svg>'),
    "chapter-7": (  # a collectible receipt: Vetinari, faintly disappointed
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M34 8 H86 V50 l-4 4 -4.4 -3 -4.4 3 -4.4 -3 -4.4 3 -4.4 -3 -4.4 3 -4.4 -3 -4.4 3 -4.4 -3 -4 3 Z"/>'
        '<ellipse cx="60" cy="24" rx="8" ry="10" stroke-width="1.6"/>'
        '<path d="M56 28 q4 -2.5 8 0" stroke-width="1.4"/>'
        '<path d="M40 42 h14 M66 42 h14 M40 13 h6 M74 13 h6" stroke-width="1.4"/>'
        '</g></svg>'),
    "chapter-8": (  # the two certainties: a scythe, and a pencil
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M42 10 C44 26 48 42 54 58"/>'
        '<path d="M42 10 C56 4 74 7 86 18 C70 13 54 14 43 17" stroke-width="1.8"/>'
        '<path d="M88 12 L52 48 M92 16 L56 52 M88 12 l4 4" stroke-width="1.8"/>'
        '<path d="M52 48 l4 4 -9 5 z" stroke-width="1.4"/>'
        '<path d="M84 8 l8 8" stroke-width="1.2"/>'
        '</g></svg>'),
    "chapter-9": (  # a very good wreath
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M60 10 C44 10 36 22 38 36 C40 48 48 54 60 54 C72 54 80 48 82 36 C84 22 76 10 60 10" stroke-width="1.8"/>'
        '<path d="M46 14 l-4 -4 M40 24 l-5 -2 M39 36 l-5 1 M44 47 l-4 4 M74 14 l4 -4 M80 24 l5 -2 M81 36 l5 1 M76 47 l4 4" stroke-width="1.4"/>'
        '<path d="M54 54 q-4 6 2 8 M66 54 q4 6 -2 8 M56 58 l4 -4 4 4" stroke-width="1.4"/>'
        '</g></svg>'),
    "epilogue": (  # a good pen, a brass nib, and running water
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<path d="M86 6 C74 16 64 26 56 38 M86 6 l-8 2 M82 12 l-7 2 M77 19 l-6 2 M72 26 l-6 2" stroke-width="1.6"/>'
        '<path d="M56 38 l-9 13 -6 -6 13 -9 z M51 45 l2 2" stroke-width="1.6"/>'
        '<path d="M40 52 q-3.5 5 0 7.5 q3.5 -2.5 0 -7.5" stroke-width="1.6"/>'
        '<path d="M30 62 q10 4 20 0" stroke-width="1.2"/>'
        '</g></svg>'),
    "title": (  # the dollar of Ankh-Morpork, with laurels
        '<svg viewBox="0 0 120 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' + G +
        '<circle cx="60" cy="30" r="23"/><circle cx="60" cy="30" r="18.5" stroke-width="1.4"/>'
        '<path d="M66 22 c-1 -4 -11 -4 -12 0 c-1.5 6 12 5 11 11 c-0.7 4.5 -11 4.5 -12 0" stroke-width="1.8"/>'
        '<path d="M60 15 v6 M60 39 v6" stroke-width="1.8"/>'
        '<path d="M26 44 C20 36 19 26 24 16 M28 40 l-5 1 M26 33 l-5 0 M26 25 l-5 -1" stroke-width="1.4"/>'
        '<path d="M94 44 C100 36 101 26 96 16 M92 40 l5 1 M94 33 l5 0 M94 25 l5 -1" stroke-width="1.4"/>'
        '<path d="M40 58 H80 M36 58 l-4 4 M84 58 l4 4" stroke-width="1.4"/>'
        '</g></svg>'),
}

FLEURON = (
    '<svg viewBox="0 0 60 20" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<path d="M30 3 C27 9 22 11.5 15 12 C22 12.8 27 14.5 30 18 C33 14.5 38 12.8 45 12 '
    'C38 11.5 33 9 30 3 Z" fill="currentColor"/>'
    '<circle cx="7" cy="12" r="1.4" fill="currentColor"/>'
    '<circle cx="53" cy="12" r="1.4" fill="currentColor"/></svg>')

SUN = ('<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
       'stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.4"/>'
       '<path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5 5l1.7 1.7M17.3 17.3L19 19M19 5l-1.7 1.7M6.7 17.3L5 19"/></svg>')
MOON = ('<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"/></svg>')

FAVICON = ("data:image/svg+xml," +
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E"
           "%3Ccircle cx='12' cy='12' r='10' fill='%23f3e8d0' stroke='%238c2f1b' stroke-width='1.6'/%3E"
           "%3Ctext x='12' y='16.5' font-size='13' text-anchor='middle' fill='%238c2f1b' "
           "font-family='Georgia,serif'%3E%24%3C/text%3E%3C/svg%3E")

# ---------------------------------------------------------------- parsing


def split_paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def parse_file(path):
    """Return list of parts: dicts with heading, argument, blocks, notes."""
    raw = (ROOT / path).read_text(encoding="utf-8")
    paras = split_paragraphs(raw)

    # drop the repeated title block (everything before the first ## heading)
    while paras and not paras[0].startswith("## "):
        paras.pop(0)

    # peel the trailing footnote block (paragraphs starting with a superscript)
    notes = {}
    while paras and paras[-1] and paras[-1][0] in SUPS:
        p = paras.pop()
        notes[SUPS[p[0]]] = p[1:].strip()
    if paras and paras[-1] == "---":
        paras.pop()

    # split into parts on ## headings
    parts = []
    for p in paras:
        if p.startswith("## "):
            parts.append({"heading": p[3:].strip(), "argument": None, "blocks": []})
        else:
            parts[-1]["blocks"].append(p)

    for part in parts:
        blocks = part["blocks"]
        if blocks and blocks[0].startswith("*") and blocks[0].endswith("*"):
            part["argument"] = blocks.pop(0)[1:-1]
        # trailing/leading dividers tidy-up
        while blocks and blocks[0] == "---":
            blocks.pop(0)
        while blocks and blocks[-1] == "---":
            blocks.pop()
        # drop a scene break that directly precedes THE END
        part["blocks"] = [
            b for i, b in enumerate(blocks)
            if not (b == "---" and i + 1 < len(blocks) and blocks[i + 1] == "THE END")
        ]
        part["notes"] = notes  # shared pool; assigned per part by reference
    return parts


# ---------------------------------------------------------------- inline html

CAPS_OK = re.compile(r"^[^a-zà-ÿ]*[A-Z∞0-9][^a-zà-ÿ]*$")


def wrap_caps_runs(text):
    """Wrap runs of 2+ all-caps words (Death, notices, headlines) for small-caps styling."""
    tokens = re.split(r"(\s+)", text)
    out, i = [], 0
    while i < len(tokens):
        tok = tokens[i]
        if tok and not tok.isspace() and CAPS_OK.match(tok):
            j, words = i, 1
            k = i + 2
            while k < len(tokens) and tokens[k] and not tokens[k].isspace() and CAPS_OK.match(tokens[k]):
                j, words = k, words + 1
                k += 2
            if words >= 2:
                out.append('<span class="caps">' + "".join(tokens[i:j + 1]) + "</span>")
                i = j + 1
                continue
        out.append(tok)
        i += 1
    return "".join(out)


def inline_html(text, ref_ids=None):
    """Escape, wrap caps runs, convert *em*, link footnote superscripts."""
    s = html.escape(text, quote=False)
    s = wrap_caps_runs(s)
    s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
    if ref_ids:
        for sup_char, n in SUPS.items():
            if sup_char in s and n in ref_ids:
                local = ref_ids[n]
                a = (f'<a class="fn-ref" id="fnref-{local}" href="#fn-{local}" '
                     f'role="doc-noteref" aria-label="Footnote {local}">{local}</a>')
                s = s.replace(sup_char, a)
    return s


def lead_in(html_text, words=4):
    head = html_text.split(" ")
    if len(head) <= words or any("<" in w for w in head[:words]):
        return html_text
    return '<span class="lead-in">' + " ".join(head[:words]) + "</span> " + " ".join(head[words:])


# ---------------------------------------------------------------- templates

HEAD_SCRIPT = (
    "(function(){try{var t=localStorage.getItem('rt-theme');"
    "if(!t)t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';"
    "document.documentElement.dataset.theme=t}catch(e){"
    "document.documentElement.dataset.theme='light'}})();")

FONTS = ("https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500"
         "&family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&display=swap")


def page_shell(title, description, body, body_attrs=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="X-Clacks-Overhead" content="GNU Terry Pratchett">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<script>{HEAD_SCRIPT}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="{FAVICON}">
</head>
<body{body_attrs}>
<div class="page">
<a class="skip" href="#main">Skip to the text</a>
{body}
{colophon()}
</div>
<script src="book.js"></script>
</body>
</html>
"""


def masthead(current=None):
    return f"""<header class="masthead">
  <a class="masthead-title" href="index.html">{BOOK_TITLE}</a>
  <nav class="masthead-nav">
    <a href="index.html#contents">Contents</a>
    <button id="theme-toggle" aria-label="Toggle light and dark mode" title="Light / dark">{SUN}{MOON}</button>
  </nav>
</header>"""


def colophon():
    return f"""<footer class="colophon">
  <p>Written by Claude, an artificial intelligence, as an affectionate pastiche
  in the style of Sir&nbsp;Terry&nbsp;Pratchett.</p>
  <p>Discworld and its people are the creation of Sir Terry Pratchett, 1948–2015.
  This unofficial homage is offered with love, and no profit whatsoever.</p>
  <p class="clacks">GNU Terry Pratchett</p>
</footer>"""


def argument_html(argument):
    frags = [inline_html(f.strip()) for f in argument.split(" – ")]
    return '<span class="arg-sep">·</span>'.join(frags)


def render_part(part, slug, prev_page, next_page):
    blocks, notes = part["blocks"], part["notes"]

    # footnote refs in order of appearance, renumbered locally from 1
    ref_order = [SUPS[c] for b in blocks if b != "---" for c in b if c in SUPS]
    assert len(ref_order) == len(set(ref_order)), f"{slug}: duplicate footnote refs"
    my_notes = {n: notes[n] for n in ref_order}
    assert set(my_notes) == set(ref_order), f"{slug}: refs {ref_order} lack notes"
    ref_ids = {n: i + 1 for i, n in enumerate(ref_order)}

    body_parts, first = [], True
    for b in blocks:
        if b == "---":
            body_parts.append(f'<div class="scene-break" role="separator">{FLEURON}</div>')
        elif b == "THE END":
            body_parts.append('<p class="the-end">The End</p>')
        else:
            t = inline_html(b, ref_ids)
            if first:
                body_parts.append(f'<p class="opening">{lead_in(t)}</p>')
                first = False
            else:
                body_parts.append(f"<p>{t}</p>")

    notes_html = ""
    if ref_order:
        items = "\n".join(
            f'    <li id="fn-{ref_ids[n]}" role="doc-endnote">{inline_html(my_notes[n])}'
            f' <a class="fn-back" href="#fnref-{ref_ids[n]}" aria-label="Back to text">&#8617;</a></li>'
            for n in ref_order)
        notes_html = f"""
  <section class="footnotes" role="doc-endnotes">
    <span class="footnotes-fleuron">{FLEURON}</span>
    <h2>Footnotes</h2>
    <ol>
{items}
    </ol>
  </section>"""

    def pager_link(page, cls, label):
        if page is None:
            return ""
        return (f'<a class="{cls}" href="{page[0]}.html" rel="{cls}">'
                f'<span class="pager-label">{label}</span>'
                f'<span class="pager-title">{html.escape(page[1])}</span></a>')

    pager = f"""
  <nav class="pager" aria-label="Chapter navigation">
    {pager_link(prev_page, "prev", "Previous")}
    {pager_link(next_page, "next", "Next")}
  </nav>"""

    arg_html = (f'\n    <p class="chapter-argument">{argument_html(part["argument"])}</p>'
                if part["argument"] else "")

    body = f"""{masthead()}
<main id="main">
  <header class="chapter-head">
    <div class="chapter-ornament">{ORNAMENTS[slug]}</div>
    <p class="chapter-number">{html.escape(part["heading"])}</p>{arg_html}
  </header>
  <article class="prose">
    {chr(10).join(body_parts)}
  </article>{notes_html}{pager}
</main>"""

    desc = part["argument"] or f'{part["heading"]} of {BOOK_TITLE}'
    attrs = ""
    if prev_page:
        attrs += f' data-prev="{prev_page[0]}.html"'
    if next_page:
        attrs += f' data-next="{next_page[0]}.html"'
    return page_shell(f'{part["heading"]} · {BOOK_TITLE}', desc, body, attrs)


def render_index(pages):
    entries = "\n".join(
        f"""      <li><a href="{slug}.html">
        <span class="toc-ornament">{ORNAMENTS[slug]}</span>
        <span><span class="toc-title">{html.escape(part["heading"])}</span>
        <span class="toc-arg">{argument_html(part["argument"]) if part["argument"] else ""}</span></span>
      </a></li>"""
        for slug, part in pages)

    body = f"""{masthead()}
<main id="main">
  <header class="titlepage">
    <div class="titlepage-ornament">{ORNAMENTS["title"]}</div>
    <p class="titlepage-kicker">A Novel of Discworld</p>
    <h1>Raising Taxes</h1>
    <p class="titlepage-sub">Being a true and complete account of the affair of the Grey Gentlemen;
    of the Most Ancient and Honourable Guild of Assessors; and of what is actually owed.
    In nine chapters and an epilogue.</p>
    <p class="titlepage-byline">{html.escape(BYLINE)}</p>
    <a class="begin" href="chapter-1.html">Begin Reading</a>
  </header>
  <nav class="toc" id="contents" aria-label="Table of contents">
    <h2>Contents</h2>
    <ol>
{entries}
    </ol>
  </nav>
</main>"""
    return page_shell(f"{BOOK_TITLE} · {BYLINE}", BYLINE, body)


# ---------------------------------------------------------------- build

def main():
    parts = []
    for src in SOURCES:
        parts.extend(parse_file(src))
    assert len(parts) == 10, f"expected 10 parts, found {len(parts)}"

    slugs = [f"chapter-{i}" for i in range(1, 10)] + ["epilogue"]
    pages = list(zip(slugs, parts))

    OUT.mkdir(exist_ok=True)
    (OUT / ".nojekyll").write_text("")
    shutil.copy(ASSETS / "style.css", OUT / "style.css")
    shutil.copy(ASSETS / "book.js", OUT / "book.js")

    nav = [("index", "Title Page")] + [(s, p["heading"]) for s, p in pages]
    for i, (slug, part) in enumerate(pages):
        prev_page = nav[i]                      # nav is offset by one (index first)
        next_page = nav[i + 2] if i + 2 < len(nav) else None
        (OUT / f"{slug}.html").write_text(render_part(part, slug, prev_page, next_page),
                                          encoding="utf-8")
    (OUT / "index.html").write_text(render_index(pages), encoding="utf-8")

    # ---- sanity sweeps over the generated HTML ----
    generated = {p.name for p in OUT.glob("*.html")}
    for f in sorted(OUT.glob("*.html")):
        text = f.read_text(encoding="utf-8")
        article = re.sub(r"<[^>]+>", "", text)
        for ch in SUPS:
            assert ch not in article, f"{f.name}: unconverted superscript {ch}"
        assert "*" not in article.replace("∞-1", ""), f"{f.name}: stray asterisk"
        for target in re.findall(r'href="([a-z0-9-]+\.html)', text):
            assert target in generated, f"{f.name}: broken link to {target}"
        for anchor in re.findall(r'href="#(fn[a-z]*-\d+)"', text):
            assert f'id="{anchor}"' in text, f"{f.name}: missing anchor #{anchor}"

    n_notes = sum(len({SUPS[c] for b in p['blocks'] for c in b if c in SUPS}) for _, p in pages)
    print(f"built {len(pages) + 1} pages, {n_notes} footnotes — all checks passed")


if __name__ == "__main__":
    sys.exit(main())
