"""Bookform → HTML → PDF 빌드 스크립트

Usage:
    python pdf-builder/build-pdf.py <lang> <story_name>

동작:
    1. tail-bookform/{lang}/{story}.md 를 읽고 고정 규약에 따라 파싱한다
    2. pdf-builder/templates/book.html + book.css 로 최종 HTML을 렌더링한다
    3. tail-pdf/{lang}/{story}.html 로 저장
    4. Playwright로 A5 PDF를 만들어 tail-pdf/{lang}/{story}.pdf 로 저장
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

import frontmatter
import yaml
from playwright.sync_api import sync_playwright

BASE = Path("c:/D/tail")
TEMPLATES = Path(__file__).parent / "templates"

DEFAULT_THEME = {
    "primary": "#333333",
    "background": "#ffffff",
}


# ---------- Parsing ----------

_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_EXPR_LINE_RE = re.compile(r"^\s*-\s+(.*)$")


def parse_bookform(md_body: str) -> dict:
    """Parse bookform markdown into a structured tree.

    Structure:
        {
            "title": str,
            "title_sub": str | None,
            "chapters": [
                {
                    "title": str,
                    "title_sub": str | None,
                    "pages": [
                        {
                            "image": str,  # absolute file URI
                            "paragraphs": [str, ...],
                            "expressions": [str, ...],
                        },
                        ...
                    ],
                    "translation": {
                        "title": str | None,  # translated chapter title
                        "paragraphs": [str, ...],
                    } | None,
                },
                ...
            ],
        }
    """
    lines = md_body.splitlines()
    i = 0
    n = len(lines)

    title: str | None = None
    title_sub: str | None = None
    chapters: list[dict] = []
    current_chapter: dict | None = None
    current_page: dict | None = None
    in_expressions = False
    in_translation = False

    def flush_page():
        nonlocal current_page
        if current_page is not None and current_chapter is not None:
            current_chapter["pages"].append(current_page)
        current_page = None

    def flush_chapter():
        nonlocal current_chapter
        flush_page()
        if current_chapter is not None:
            chapters.append(current_chapter)
        current_chapter = None

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Translation block — chapter-level, not tied to a page
        if in_translation:
            if stripped.startswith("-->"):
                in_translation = False
                i += 1
                continue
            if current_chapter is not None:
                tr = current_chapter["translation"]
                if tr["title"] is None and stripped.startswith("## "):
                    tr["title"] = stripped[3:].strip()
                elif stripped:
                    tr["paragraphs"].append(stripped)
            i += 1
            continue

        if stripped.startswith("<!-- translation"):
            in_translation = True
            flush_page()
            if current_chapter is not None and current_chapter.get("translation") is None:
                current_chapter["translation"] = {"title": None, "paragraphs": []}
            i += 1
            continue

        # Expressions block
        if in_expressions:
            if stripped.startswith("-->"):
                in_expressions = False
                i += 1
                continue
            m = _EXPR_LINE_RE.match(line)
            if m and current_page is not None:
                current_page["expressions"].append(m.group(1).strip())
            i += 1
            continue

        if stripped.startswith("<!-- expressions"):
            in_expressions = True
            i += 1
            continue

        # Title `# ...`
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            # Look ahead for a <sub>...</sub> line
            if i + 1 < n:
                nxt = lines[i + 1].strip()
                sub = _extract_sub(nxt)
                if sub is not None:
                    title_sub = sub
                    i += 2
                    continue
            i += 1
            continue

        # Chapter `## ...`
        if stripped.startswith("## "):
            flush_chapter()
            ch_title = stripped[3:].strip()
            ch_sub = None
            if i + 1 < n:
                nxt = lines[i + 1].strip()
                sub = _extract_sub(nxt)
                if sub is not None:
                    ch_sub = sub
                    i += 2
                else:
                    i += 1
            else:
                i += 1
            current_chapter = {
                "title": ch_title,
                "title_sub": ch_sub,
                "pages": [],
                "translation": None,
            }
            continue

        # Story page heading `### N 페이지` — hidden in output, starts a new page block
        if stripped.startswith("### "):
            flush_page()
            current_page = {
                "image": None,
                "paragraphs": [],
                "expressions": [],
            }
            i += 1
            continue

        # Image
        m_img = _IMG_RE.match(stripped)
        if m_img and current_page is not None:
            raw_path = m_img.group(2).strip()
            current_page["image"] = _to_file_uri(raw_path)
            i += 1
            continue

        # Blank
        if stripped == "":
            i += 1
            continue

        # Body paragraph
        if current_page is not None:
            current_page["paragraphs"].append(stripped)
        i += 1

    flush_chapter()

    return {
        "title": title or "",
        "title_sub": title_sub,
        "chapters": chapters,
    }


def _extract_sub(line: str) -> str | None:
    m = re.match(r"^<sub>(.*)</sub>\s*$", line)
    if m:
        return m.group(1).strip()
    return None


def _to_file_uri(rel_or_abs: str) -> str:
    p = Path(rel_or_abs)
    if not p.is_absolute():
        p = BASE / rel_or_abs
    return p.resolve().as_uri()


_FS_UNSAFE_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str) -> str:
    """Strip characters that are illegal in Windows/POSIX filenames."""
    cleaned = _FS_UNSAFE_RE.sub("", name).strip().rstrip(".")
    return cleaned


# ---------- Rendering ----------


def load_theme(story: str) -> dict:
    """Load per-story theme from tail-image/{story}/theme.yaml.

    Falls back to DEFAULT_THEME keys for missing entries.
    """
    theme_path = BASE / "tail-image" / story / "theme.yaml"
    theme = dict(DEFAULT_THEME)
    if theme_path.exists():
        loaded = yaml.safe_load(theme_path.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            theme.update({k: v for k, v in loaded.items() if v})
    return theme


def load_series(lang: str) -> str:
    """Return the series label shown on the cover's vertical band.

    Source: templates/series.yaml (language-keyed). Missing key → empty string,
    in which case the band renders but carries no text.
    """
    path = TEMPLATES / "series.yaml"
    if not path.exists():
        return ""
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        return ""
    return str(loaded.get(lang) or "")


def render_html(book: dict, lang: str, story: str) -> str:
    tpl = (TEMPLATES / "book.html").read_text(encoding="utf-8")

    title_esc = html.escape(book["title"])
    cover_sub = ""
    if book["title_sub"]:
        cover_sub = f'<div class="cover-subtitle">{html.escape(book["title_sub"])}</div>'

    cover_img = ""
    cover_dir = BASE / "tail-image" / story
    for ext in ("png", "jpeg", "jpg"):
        cover_path = cover_dir / f"cover.{ext}"
        if cover_path.exists():
            cover_img = f'<img src="{html.escape(cover_path.resolve().as_uri())}" alt="">'
            break

    theme = load_theme(story)
    theme_style = (
        f"--theme-primary: {html.escape(str(theme['primary']))};"
        f"--theme-background: {html.escape(str(theme['background']))};"
    )

    series_text = html.escape(load_series(lang))

    content_parts: list[str] = []
    for idx, chapter in enumerate(book["chapters"], start=1):
        content_parts.append(render_chapter(chapter, idx))

    content = "\n".join(content_parts)

    out = (
        tpl.replace("{{LANG}}", lang)
        .replace("{{TITLE}}", title_esc)
        .replace("{{COVER_SUBTITLE}}", cover_sub)
        .replace("{{COVER_IMAGE}}", cover_img)
        .replace("{{THEME_STYLE}}", theme_style)
        .replace("{{SERIES}}", series_text)
        .replace("{{CONTENT}}", content)
    )
    return out


def render_chapter(chapter: dict, chapter_index: int) -> str:
    parts: list[str] = []
    parts.append(f'<section class="chapter" data-chapter="{chapter_index}">')

    for i, page in enumerate(chapter["pages"]):
        is_first = i == 0
        parts.append(render_page(page, chapter if is_first else None))

    if chapter.get("translation"):
        parts.append(render_translation(chapter["translation"]))

    parts.append("</section>")
    return "\n".join(parts)


def render_translation(translation: dict) -> str:
    """Render a chapter's translation as a dedicated page."""
    parts: list[str] = []
    parts.append('  <article class="translation-page">')
    if translation.get("title"):
        parts.append(
            f'    <h2 class="translation-title">{html.escape(translation["title"])}</h2>'
        )
    for para in translation["paragraphs"]:
        parts.append(f"    <p>{html.escape(para)}</p>")
    parts.append("  </article>")
    return "\n".join(parts)


def render_page(page: dict, chapter_header: dict | None) -> str:
    """Render a single story page.

    If chapter_header is not None, this is the first page of a chapter and
    includes the chapter heading block at the top.
    """
    classes = "story-page"
    if chapter_header is not None:
        classes += " chapter-start"

    parts: list[str] = []
    parts.append(f'  <article class="{classes}">')

    if chapter_header is not None:
        parts.append('    <header class="chapter-heading">')
        parts.append(
            f'      <h2 class="chapter-title">{html.escape(chapter_header["title"])}</h2>'
        )
        if chapter_header["title_sub"]:
            parts.append(
                f'      <span class="chapter-subtitle">{html.escape(chapter_header["title_sub"])}</span>'
            )
        parts.append("    </header>")

    if page["image"]:
        parts.append(f'    <img src="{html.escape(page["image"])}" alt="">')

    for para in page["paragraphs"]:
        parts.append(f"    <p>{html.escape(para)}</p>")

    if page["expressions"]:
        parts.append('    <aside class="expressions"><ul>')
        for expr in page["expressions"]:
            parts.append(f"      <li>{html.escape(expr)}</li>")
        parts.append("    </ul></aside>")

    parts.append("  </article>")
    return "\n".join(parts)


# ---------- Main ----------


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/build-pdf.py <lang> <story_name>")
        return 1

    lang = sys.argv[1]
    story = sys.argv[2]

    src = BASE / "tail-bookform" / lang / f"{story}.md"
    if not src.exists():
        print(f"Error: {src} not found")
        return 1

    out_dir = BASE / "tail-pdf" / lang
    out_dir.mkdir(parents=True, exist_ok=True)

    post = frontmatter.loads(src.read_text(encoding="utf-8"))
    book = parse_bookform(post.content)

    # Use the localized subtitle (<sub> under the H1) as the output stem so that
    # each language lands as e.g. "The Fox and the Crane.pdf" / "キツネとツル.pdf".
    # Fall back to the Korean story name if no subtitle is present.
    localized = sanitize_filename(book["title_sub"] or "")
    stem = localized or story

    # Copy CSS next to the HTML so the relative <link> resolves
    shutil.copyfile(TEMPLATES / "book.css", out_dir / "book.css")

    html_out = render_html(book, lang, story)
    html_path = out_dir / f"{stem}.html"
    html_path.write_text(html_out, encoding="utf-8")
    print(f"HTML generated: {html_path}")

    pdf_path = out_dir / f"{stem}.pdf"
    pdf_tmp = out_dir / f"{stem}.pdf.tmp"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(pdf_tmp),
            prefer_css_page_size=True,  # honor @page size + @page :first { margin: 0 }
            print_background=True,
        )
        browser.close()

    # Atomic swap to avoid Windows file-lock when the PDF is open in a viewer
    try:
        if pdf_path.exists():
            pdf_path.unlink()
        pdf_tmp.replace(pdf_path)
    except PermissionError:
        print(
            f"Warning: could not replace {pdf_path} (is it open?). "
            f"Wrote to {pdf_tmp} instead."
        )
        pdf_path = pdf_tmp

    size_mb = pdf_path.stat().st_size / 1024 / 1024
    print(f"PDF generated: {pdf_path} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
