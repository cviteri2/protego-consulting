#!/usr/bin/env python3
"""Genera las páginas del blog a partir de los artículos Markdown de content/blog/.

Cada archivo content/blog/AAAA-MM-DD-slug.md produce blog/slug.html y una tarjeta
en blog.html (entre los marcadores BLOG:AUTO), además de su entrada en sitemap.xml.
Es idempotente: ejecutarlo dos veces sin cambios en content/ no modifica nada.

Formato esperado (el que entrega la tarea programada del blog):

    **Categoría:** [ISO 27001]
    # Título del artículo
    **Meta descripción:** Texto de 150-160 caracteres.
    ## Introducción
    Párrafos...

Uso: python3 scripts/build_blog.py   (solo biblioteca estándar)
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content" / "blog"
OUT = ROOT / "blog"
TEMPLATE = ROOT / "scripts" / "blog" / "template.html"
INDEX = ROOT / "blog.html"
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://protego-consulting.com"

AUTO_START = "<!-- BLOG:AUTO:START (generado por scripts/build_blog.py, no editar a mano) -->"
AUTO_END = "<!-- BLOG:AUTO:END -->"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-([a-z0-9-]+)\.md$")


class PostError(Exception):
    pass


# ---------------------------------------------------------------- Markdown

def clean_url(url):
    """Quita los redireccionamientos de Google que Gmail agrega a los enlaces."""
    url = url.strip().strip("[]")
    parsed = urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q")
        if target:
            url = unquote(target[0])
    return url


def site_relative(url):
    """Convierte enlaces absolutos al propio sitio en rutas relativas desde blog/."""
    parsed = urlparse(url)
    if parsed.netloc in ("protego-consulting.com", "www.protego-consulting.com"):
        path = parsed.path.lstrip("/")
        if path.startswith("blog/"):
            path = path[len("blog/"):]
        elif path:
            path = "../" + path
        else:
            path = "/"
        return path + (("#" + parsed.fragment) if parsed.fragment else ""), False
    external = parsed.scheme in ("http", "https")
    return url, external


def inline(text):
    """Markdown en línea: enlaces, negrita, cursiva y código."""
    links = []

    def stash_link(m):
        label, url = m.group(1), clean_url(m.group(2))
        href, external = site_relative(url)
        attrs = ' target="_blank" rel="noopener"' if external else ""
        links.append(f'<a href="{html.escape(href, quote=True)}"{attrs}>{inline_fmt(html.escape(label, quote=False))}</a>')
        return f"\x00{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", stash_link, text)
    text = inline_fmt(html.escape(text, quote=False))
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], text)


def inline_fmt(text):
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", text)
    return text


def markdown_blocks(lines):
    """Convierte líneas Markdown en una lista de bloques HTML."""
    blocks, para, items, list_tag = [], [], [], None

    def flush():
        nonlocal para, items, list_tag
        if para:
            blocks.append(f"<p>{inline(' '.join(para))}</p>")
            para = []
        if items:
            lis = "\n".join(f"        <li>{inline(i)}</li>" for i in items)
            blocks.append(f"<{list_tag}>\n{lis}\n      </{list_tag}>")
            items, list_tag = [], None

    for raw in lines:
        line = raw.strip()
        if not line:
            flush()
            continue
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", line):
            flush()
            blocks.append('<hr class="divider">')
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", line)
        if m:
            flush()
            level = len(m.group(1))
            blocks.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            continue
        m = re.match(r"^[-*+]\s+(.*)$", line)
        if m:
            if para or list_tag == "ol":
                flush()
            list_tag = "ul"
            items.append(m.group(1))
            continue
        m = re.match(r"^\d+[.)]\s+(.*)$", line)
        if m:
            if para or list_tag == "ul":
                flush()
            list_tag = "ol"
            items.append(m.group(1))
            continue
        if line.startswith(">"):
            flush()
            blocks.append(f"<blockquote><p>{inline(line.lstrip('> '))}</p></blockquote>")
            continue
        if items:
            flush()
        para.append(line)
    flush()
    return blocks


# ---------------------------------------------------------------- Artículos

def strip_md(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"[*_`]", "", text).strip()


def parse_post(path):
    m = FILENAME_RE.match(path.name)
    if not m:
        raise PostError(f"{path.name}: el nombre debe ser AAAA-MM-DD-slug.md (minúsculas, números y guiones)")
    year, month, day, slug = m.groups()
    raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    # Las exportaciones de Google Drive a veces escapan la sintaxis Markdown.
    raw = re.sub(r"\\([*#\[\]_()>.-])", r"\1", raw)
    lines = raw.split("\n")

    category = title = description = None
    body = []
    for line in lines:
        s = line.strip()
        plain = strip_md(s)
        if category is None and re.match(r"(?i)^categor[ií]a\s*:", plain):
            category = re.sub(r"(?i)^categor[ií]a\s*:\s*", "", plain).strip("[] ")
            continue
        if description is None and re.match(r"(?i)^meta\s*descripci[oó]n\s*:", plain):
            description = re.sub(r"(?i)^meta\s*descripci[oó]n\s*:\s*", "", plain)
            continue
        if title is None and re.match(r"^#\s+", s):
            title = strip_md(s[1:])
            continue
        body.append(line)

    missing = [n for n, v in (("Categoría", category), ("título (# ...)", title), ("Meta descripción", description)) if not v]
    if missing:
        raise PostError(f"{path.name}: falta {', '.join(missing)}")

    # El encabezado "Introducción" (o un separador ---) no se muestra: su primer
    # párrafo pasa a ser la entradilla.
    while body and (not body[0].strip() or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", body[0].strip())):
        body.pop(0)
    if body and re.match(r"(?i)^##\s+introducci[oó]n\s*$", body[0].strip()):
        body.pop(0)
    blocks = markdown_blocks(body)
    if not blocks or not blocks[0].startswith("<p>"):
        raise PostError(f"{path.name}: el artículo debe empezar con un párrafo de introducción")
    lead = blocks.pop(0)[3:-4]

    words = len(re.findall(r"\w+", strip_md(raw)))
    return {
        "slug": slug,
        "date": f"{year}-{month}-{day}",
        "date_long": f"{int(day)} de {MESES[int(month) - 1]} de {year}",
        "date_short": f"{int(day)} {MESES_CORTOS[int(month) - 1]} {year}",
        "category": category,
        "title": title,
        "description": description,
        "lead": lead,
        "content": "\n\n".join("      " + b for b in blocks),
        "read_min": max(1, round(words / 200)),
        "href": f"blog/{slug}.html",
        "url": f"{SITE}/blog/{slug}.html",
    }


def jsonld(post):
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "headline": post["title"],
                "description": post["description"],
                "datePublished": post["date"],
                "dateModified": post["date"],
                "author": {
                    "@type": "Person",
                    "@id": f"{SITE}/nosotros.html#cesar-viteri",
                    "name": "César Viteri",
                    "url": f"{SITE}/nosotros.html",
                    "sameAs": ["https://www.linkedin.com/in/cesarviteri/"],
                },
                "image": f"{SITE}/assets/logos/logo-horizontal-color.png",
                "publisher": {
                    "@type": "Organization",
                    "@id": f"{SITE}/#organization",
                    "name": "Protego Consulting",
                    "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logos/logo-horizontal-color.png"},
                },
                "mainEntityOfPage": post["url"],
                "inLanguage": "es-EC",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Inicio", "item": f"{SITE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{SITE}/blog.html"},
                    {"@type": "ListItem", "position": 3, "name": post["title"], "item": post["url"]},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


# ---------------------------------------------------------------- Índice y tarjetas

CARD_RE = re.compile(
    r'<a href="blog/([^"]+)\.html" class="card post-card"[^>]*>\s*'
    r'<span class="tag">(.*?)</span>\s*<h3>(.*?)</h3>.*?'
    r'<time class="post-date" datetime="([^"]+)">(.*?)</time>\s*</a>',
    re.S,
)


def index_card(post):
    e = lambda s: html.escape(s, quote=False)
    return (
        f'      <a href="{post["href"]}" class="card post-card" style="text-decoration:none; color:inherit;">\n'
        f'        <span class="tag">{e(post["category"])}</span>\n'
        f'        <h3>{e(post["title"])}</h3>\n'
        f'        <p>{e(post["description"])}</p>\n'
        f'        <time class="post-date" datetime="{post["date"]}">{post["date_short"]}</time>\n'
        f'      </a>'
    )


def related_card(slug, tag, title, date, label):
    return (
        f'      <a href="{slug}.html" class="card post-card" style="text-decoration:none; color:inherit;">\n'
        f'        <span class="tag">{tag}</span>\n'
        f'        <h3>{title}</h3>\n'
        f'        <time class="post-date" datetime="{date}">{label}</time>\n'
        f'      </a>'
    )


def update_index(posts):
    text = INDEX.read_text(encoding="utf-8")
    if AUTO_START not in text:
        anchor = '<div class="grid-4">'
        if anchor not in text:
            raise PostError("blog.html: no se encontró la grilla de artículos")
        text = text.replace(anchor, f"{anchor}\n      {AUTO_START}\n      {AUTO_END}", 1)
    start = text.index(AUTO_START) + len(AUTO_START)
    end = text.index(AUTO_END)
    cards = "\n".join(index_card(p) for p in posts)
    text = text[:start] + ("\n" + cards if cards else "") + "\n      " + text[end:]
    write_if_changed(INDEX, text)
    return text


def update_sitemap(posts):
    text = SITEMAP.read_text(encoding="utf-8")
    for p in posts:
        if f"<loc>{p['url']}</loc>" in text:
            continue
        entry = f"  <url><loc>{p['url']}</loc><lastmod>{p['date']}</lastmod></url>\n"
        anchor = f"  <url><loc>{SITE}/blog.html</loc>"
        i = text.find(anchor)
        if i == -1:
            text = text.replace("</urlset>", entry + "</urlset>")
        else:
            i = text.index("\n", i) + 1
            text = text[:i] + entry + text[i:]
        text = re.sub(
            rf"(<loc>{re.escape(SITE)}/blog\.html</loc><lastmod>)[^<]+",
            lambda m: m.group(1) + max(p["date"] for p in posts),
            text,
        )
    write_if_changed(SITEMAP, text)


def write_if_changed(path, text):
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        print(f"  actualizado {path.relative_to(ROOT)}")


def main():
    files = sorted(CONTENT.glob("*.md"))
    posts, errors = [], []
    for f in files:
        try:
            posts.append(parse_post(f))
        except PostError as exc:
            errors.append(str(exc))
    if errors:
        print("Errores en content/blog/:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 1
    slugs = [p["slug"] for p in posts]
    dup = {s for s in slugs if slugs.count(s) > 1}
    if dup:
        print(f"Slugs duplicados: {', '.join(sorted(dup))}", file=sys.stderr)
        return 1
    for p in posts:
        manual = OUT / f"{p['slug']}.html"
        if manual.exists() and "<!-- generado por scripts/build_blog.py" not in manual.read_text(encoding="utf-8"):
            print(f"{manual.relative_to(ROOT)} ya existe y no fue generado automáticamente; renombre el slug.", file=sys.stderr)
            return 1

    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    index_text = update_index(posts)
    update_sitemap(posts)

    all_cards = sorted(CARD_RE.findall(index_text), key=lambda c: c[3], reverse=True)
    template = TEMPLATE.read_text(encoding="utf-8")
    for p in posts:
        same = [c for c in all_cards if c[0] != p["slug"] and c[1] == html.escape(p["category"], quote=False)]
        others = [c for c in all_cards if c[0] != p["slug"] and c not in same]
        related = "\n".join(related_card(*c) for c in (same + others)[:3])
        e = lambda s: html.escape(s, quote=True)
        page = template
        for key, value in {
            "title": e(p["title"]),
            "description": e(p["description"]),
            "url": p["url"],
            "jsonld": jsonld(p),
            "category": e(p["category"]),
            "lead": p["lead"],
            "date_long": p["date_long"],
            "read_min": str(p["read_min"]),
            "content": p["content"],
            "related": related,
        }.items():
            page = page.replace("{{" + key + "}}", value)
        page = page.replace("<!DOCTYPE html>\n", f"<!DOCTYPE html>\n<!-- generado por scripts/build_blog.py desde content/blog/{p['date']}-{p['slug']}.md -->\n", 1)
        write_if_changed(OUT / f"{p['slug']}.html", page)

    print(f"{len(posts)} artículo(s) automáticos procesados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
