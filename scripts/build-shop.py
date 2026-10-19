#!/usr/bin/env python3
"""Render the Shop Markdown and its complete Japanese translation with stdlib only."""

import html
import json
import re
import textwrap
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "products" / "shop"
SOURCE_URL = "https://github.com/shopify-apac-ts/shopify-technical-docs/blob/main/products/shop/architecture.md"

UI = {
    "en": {
        "title": "Shop — value, channels, and architecture",
        "source": "Source Markdown", "switch": "日本語", "contents": "On this page",
        "label": "Sales channels + Architecture", "summary": "From discovery to the next purchase",
        "steps": ["Discover products through Shop and AI", "Buy with fewer repeated inputs", "Return through tracking and subscriptions"],
        "diagram": "Diagram", "expand": "Expand diagram", "close": "Close diagram",
        "error": "Diagrams could not load. Their source remains available below and in the Markdown.",
        "footer": "Shop · Public sources reviewed October 15, 2026 · MCP and Catalog update October 19, 2026",
        "skip": "Skip to content",
    },
    "ja": {
        "title": "Shop — バリュー・販売チャネル・アーキテクチャ",
        "source": "Markdown原本", "switch": "English", "contents": "このページの内容",
        "label": "販売チャネル＋アーキテクチャ", "summary": "商品との出会いから、次の購入まで",
        "steps": ["ShopやAIを通じて商品と出会う", "情報の再入力を減らして購入する", "配送追跡やサブスクで再訪する"],
        "diagram": "図", "expand": "図を拡大", "close": "図を閉じる",
        "error": "図を読み込めませんでした。図の原文はこのページとMarkdown原本で確認できます。",
        "footer": "Shop · 公開情報の確認日：2026年10月15日 · MCP・Catalog更新：2026年10月19日",
        "skip": "本文へ移動",
    },
}


def blocks(source):
    """Keep fenced diagrams intact while splitting ordinary Markdown blocks."""
    result, current, fenced = [], [], False
    for line in source.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not line.strip() and not fenced:
            if current:
                result.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if fenced:
        raise ValueError("Unclosed Markdown fence")
    if current:
        result.append("\n".join(current))
    return result


def localized_urls(text, locale):
    if locale == "ja":
        text = text.replace("https://help.shopify.com/en/", "https://help.shopify.com/ja/")
        for path in ("checkout", "shop"):
            text = text.replace(f"https://www.shopify.com/{path})", f"https://www.shopify.com/jp/{path})")
    return text


def inline(text):
    """Render the inline syntax used by this document; never allow raw HTML."""
    pattern = re.compile(r"(`[^`]+`|\[[^\]]+\]\(https://[^\s)]+\)|\*\*.+?\*\*)")
    output = []
    for part in pattern.split(text):
        if part.startswith("`") and part.endswith("`"):
            output.append(f"<code>{html.escape(part[1:-1])}</code>")
        elif match := re.fullmatch(r"\[([^\]]+)\]\((https://[^\s)]+)\)", part):
            output.append(f'<a href="{html.escape(match[2], quote=True)}">{html.escape(match[1])}</a>')
        elif part.startswith("**") and part.endswith("**"):
            output.append(f"<strong>{html.escape(part[2:-2])}</strong>")
        else:
            output.append(html.escape(part))
    return "".join(output)


def heading(block):
    match = re.fullmatch(r"(#{1,3}) (.+)", block)
    return (len(match[1]), match[2]) if match else None


def section_id(title):
    title = re.sub(r"^\d+\.\s*", "", title)
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def diagram_label(text, locale):
    """Insert visual line breaks without Mermaid's hyphenation of Japanese text."""
    if locale == "en":
        return "<br/>".join(textwrap.wrap(text, width=24, break_long_words=False, break_on_hyphens=False))
    lines, line, width = [], "", 0
    # Keep ASCII words such as API and Shop intact; Japanese can wrap between characters.
    tokens = re.findall(r"[A-Za-z0-9_./-]+|.", text)
    for token in tokens:
        size = sum(2 if unicodedata.east_asian_width(char) in "WF" else 1 for char in token)
        if width + size > 18 and line and token not in "、。）」：":
            lines.append(line.strip())
            line, width = "", 0
        line += token
        width += size
    if line:
        lines.append(line.strip())
    return "<br/>".join(lines)


def diagram_layout(source, locale):
    if not source.startswith("sequenceDiagram"):
        return source
    result = []
    for line in source.splitlines():
        # Only wrap display labels; preserve actors, arrows, and control syntax.
        match = re.match(r"(\s*(?:participant \w+ as |\w+(?:-->>|->>)\w+: |(?:alt|else|loop|opt) ))(.+)", line)
        if match:
            line = match[1] + diagram_label(match[2], locale)
        result.append(line)
    return "\n".join(result)


def render(block, locale, label, index):
    block = localized_urls(block, locale)
    if block.startswith("```mermaid\n") and block.endswith("\n```"):
        ui = UI[locale]
        caption = f'{label} · {ui["diagram"]} {index}'
        return (
            f'<figure class="diagram-wrap" tabindex="0" aria-label="{html.escape(caption)}">'
            f'<figcaption><span>{html.escape(caption)}</span>'
            f'<button class="diagram-expand" type="button" hidden>{ui["expand"]}</button></figcaption>'
            f'<pre class="mermaid">{html.escape(diagram_layout(block[11:-4], locale))}</pre></figure>'
        )
    if block.startswith("```"):
        raise ValueError("Only Mermaid fences are supported")
    if h := heading(block):
        return f"<h{h[0]}>{inline(h[1])}</h{h[0]}>"
    lines = block.splitlines()
    if lines[0].startswith("| "):
        rows = [[inline(cell.strip()) for cell in line.strip().strip("|").split("|")] for line in lines]
        if len(rows) < 3 or not re.fullmatch(r"[|\s:\-]+", lines[1]):
            raise ValueError("Invalid Markdown table")
        head = "".join(f'<th scope="col">{cell}</th>' for cell in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows[2:])
        return f'<div class="table-wrap" role="region" tabindex="0" aria-label="{html.escape(label)}"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    if all(line.startswith("- ") for line in lines):
        return "<ul>" + "".join(f"<li>{inline(line[2:])}</li>" for line in lines) + "</ul>"
    if all(re.match(r"\d+\. ", line) for line in lines):
        return "<ol>" + "".join(f'<li>{inline(re.sub(r"^\d+\. ", "", line))}</li>' for line in lines) + "</ol>"
    return f'<p>{inline(" ".join(lines))}</p>'


def build(source_blocks, translations, locale):
    ui = UI[locale]
    text = source_blocks if locale == "en" else [translations[block] for block in source_blocks]
    sections, current = [], None
    for en, local in zip(source_blocks[3:], text[3:]):
        if h := heading(en):
            if h[0] == 2:
                current = {"id": section_id(h[1]), "title": heading(local)[1], "blocks": []}
                sections.append(current)
                continue
        if current is None:
            raise ValueError("Expected a section heading after the introduction")
        current["blocks"].append(local)

    rendered, toc = [], []
    for section in sections:
        sid, title = section["id"], section["title"]
        toc.append(f'<a href="#{sid}">{html.escape(title)}</a>')
        content, count = [], 0
        faq_open = False
        for block in section["blocks"]:
            if sid == "frequently-asked-questions" and (h := heading(block)) and h[0] == 3:
                if faq_open:
                    content.append("</div></details>")
                content.append(f'<details class="faq-item"><summary>{inline(h[1])}</summary><div class="faq-answer">')
                faq_open = True
                continue
            if block.startswith("```mermaid"):
                count += 1
            content.append(render(block, locale, title, count))
        if faq_open:
            content.append("</div></details>")
        css_class = "section disclaimer" if sid == "disclaimer" else "section"
        rendered.append(f'<section class="{css_class}" id="{sid}" aria-labelledby="{sid}-title"><h2 id="{sid}-title">{html.escape(title)}</h2>\n' + "\n".join(content) + "\n</section>")

    prefix, home, switch = ("./", "../../", "./ja/") if locale == "en" else ("../", "../../../", "../")
    font = "Inter+Tight" if locale == "en" else "Noto+Sans+JP"
    steps = "".join(f'<li><span class="marker">{i}</span><span>{step}</span></li>' for i, step in enumerate(ui["steps"], 1))
    title = heading(text[0])[1]
    description = html.escape(text[1], quote=True)
    return f'''<!doctype html>
<!-- Generated by scripts/build-shop.py from architecture.md and ja/content.json. -->
<html lang="{locale}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{ui["title"]}</title>
  <meta name="description" content="{description}">
  <link rel="icon" href="data:,">
  <link rel="alternate" hreflang="en" href="{prefix}index.html">
  <link rel="alternate" hreflang="ja" href="{prefix}ja/index.html">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family={font}:wght@400;500;600;700;800&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}page.css">
  <script type="module" src="{prefix}page.js"></script>
</head>
<body data-expand="{ui["expand"]}" data-close="{ui["close"]}" data-diagram-error="{ui["error"]}">
  <a class="skip-link" href="#content">{ui["skip"]}</a>
  <header class="topbar"><div class="topbar-inner">
    <nav class="crumbs" aria-label="{'Breadcrumb' if locale == 'en' else 'パンくず'}"><a href="{home}">Shopify Technical Docs</a><span>/</span><span>Shop</span></nav>
    <nav class="top-actions" aria-label="{'Page links' if locale == 'en' else 'ページのリンク'}"><a href="{SOURCE_URL}">{ui["source"]}</a><a href="{switch}" lang="{'ja' if locale == 'en' else 'en'}">{ui["switch"]}</a><a href="#references">{'References' if locale == 'en' else '参考資料'}</a></nav>
  </div></header>
  <section class="hero" aria-labelledby="page-title"><div class="hero-inner">
    <div><span class="eyebrow">{ui["label"]}</span><h1 id="page-title">{html.escape(title)}</h1><p>{inline(text[1])}</p></div>
    <aside class="summary-panel"><h2>{ui["summary"]}</h2><ol class="summary-list">{steps}</ol></aside>
  </div></section>
  <div class="page-layout">
    <nav class="contents" aria-label="{ui["contents"]}"><strong>{ui["contents"]}</strong>{''.join(toc)}</nav>
    <main id="content"><p class="reviewed">{inline(text[2])}</p><p id="diagram-status" role="status"></p>{chr(10).join(rendered)}</main>
  </div>
  <footer>{ui["footer"]}</footer>
  <dialog class="diagram-dialog" aria-label="{ui["expand"]}"><div class="dialog-tools"><button class="diagram-close" type="button">{ui["close"]}</button></div><div class="dialog-diagram"></div></dialog>
</body>
</html>
'''


def main():
    source_blocks = blocks((PRODUCT / "architecture.md").read_text())
    translations = json.loads((PRODUCT / "ja/content.json").read_text())
    missing = set(source_blocks) - translations.keys()
    stale = translations.keys() - set(source_blocks)
    if missing or stale:
        raise ValueError(f"Translation mismatch: {len(missing)} missing, {len(stale)} stale blocks. Missing examples: {[block[:100] for block in missing]}")
    for en, ja in translations.items():
        if not isinstance(ja, str) or not ja.strip():
            raise ValueError("Empty translation")
        if bool(heading(en)) != bool(heading(ja)) or (heading(en) and heading(en)[0] != heading(ja)[0]):
            raise ValueError("Heading structure mismatch")
        if re.findall(r"https://[^\s)`]+", en) != re.findall(r"https://[^\s)`]+", ja):
            raise ValueError("Source links must match before locale rewriting")
        if en.startswith("```mermaid") and (not ja.startswith("```mermaid") or len(en.splitlines()) != len(ja.splitlines())):
            raise ValueError("Diagram structure mismatch")
    # Render both before writing either output so localization failures cannot partially publish.
    outputs = {PRODUCT / "index.html": build(source_blocks, translations, "en"), PRODUCT / "ja/index.html": build(source_blocks, translations, "ja")}
    for path, content in outputs.items():
        path.write_text(content)
    diagrams = sum(block.startswith("```mermaid") for block in source_blocks)
    print(f"Rendered English and Japanese HTML: {len(source_blocks)} complete blocks, {diagrams} diagrams per locale")


if __name__ == "__main__":
    main()
