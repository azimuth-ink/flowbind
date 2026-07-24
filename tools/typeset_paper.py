#!/usr/bin/env python3
"""Typeset a preprint markdown file to a Zenodo-ready PDF (markdown -> HTML -> WeasyPrint).

Usage: python3 tools/typeset_paper.py paper/<paper>.md <output>.pdf
Deps:  pip install weasyprint markdown   (WeasyPrint needs pango system libs)
"""
import markdown
import pathlib
import re
import sys
from weasyprint import HTML

CSS = """
@page {
  size: Letter;
  margin: 24mm 22mm 26mm 22mm;
  @bottom-center { content: counter(page); font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif; font-size: 8.5pt; color: #555; }
  @top-right { content: string(doctitle); font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif; font-size: 7.5pt; color: #888; }
}
@page :first { @top-right { content: none; } }
html { font-size: 10.5pt; }
body {
  font-family: 'Liberation Serif', 'DejaVu Serif', serif;
  line-height: 1.45; color: #111; text-align: justify; hyphens: auto;
}
h1 {
  string-set: doctitle content();
  font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
  font-size: 17.5pt; line-height: 1.25; text-align: center;
  margin: 0 0 10pt 0; font-weight: 700; text-wrap: balance;
}
h1 + p, h1 + p + p { text-align: center; margin: 3pt 0; }
h1 + p { font-size: 10.5pt; }
h1 + p + p { font-size: 9pt; color: #444; }
h2 {
  font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
  font-size: 12.5pt; margin: 16pt 0 6pt 0; page-break-after: avoid;
}
h3 {
  font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
  font-size: 10.8pt; margin: 12pt 0 4pt 0; page-break-after: avoid;
}
p { margin: 0 0 6pt 0; orphans: 2; widows: 2; }
a { color: #17457a; text-decoration: none; }
strong { font-weight: 700; }
hr { border: 0; border-top: 0.6pt solid #bbb; margin: 12pt 0; }
ul, ol { margin: 2pt 0 7pt 0; padding-left: 18pt; }
li { margin-bottom: 3pt; }
blockquote {
  margin: 7pt 6pt 9pt 6pt; padding: 5pt 10pt;
  border-left: 2.2pt solid #17457a; background: #f4f6f9;
  font-style: italic; page-break-inside: avoid;
}
blockquote p { margin: 0; }
code {
  font-family: 'DejaVu Sans Mono', monospace;
  font-size: 85%; background: #f4f3ef; padding: 0 2pt; border-radius: 2pt;
}
pre {
  font-family: 'DejaVu Sans Mono', monospace;
  font-size: 8.3pt; line-height: 1.35;
  background: #f6f5f1; border: 0.5pt solid #ddd; border-radius: 3pt;
  padding: 7pt 9pt; margin: 6pt 0 9pt 0;
  white-space: pre-wrap; overflow-wrap: break-word;
}
pre code { background: none; padding: 0; font-size: 100%; }
table {
  border-collapse: collapse; width: 100%;
  font-family: 'Liberation Sans', 'DejaVu Sans', sans-serif;
  font-size: 8.8pt; margin: 7pt 0 10pt 0; page-break-inside: avoid;
}
th, td { border: 0.5pt solid #bbb; padding: 3.5pt 6pt; text-align: left; vertical-align: top; }
th { background: #efeeea; font-weight: 700; }
em { font-style: italic; }
.refs p, li { text-align: left; }
h2#references ~ ul li { margin-bottom: 2.5pt; font-size: 9.6pt; }
"""

TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>{title}</title>
<meta name="author" content="Jeff Gray">
<meta name="description" content="{title}">
<style>{css}</style>
</head><body>{body}</body></html>"""


def build(md_path: str, out_path: str):
    src = pathlib.Path(md_path).read_text()
    title = re.match(r"^# (.+)$", src, re.M).group(1)
    body = markdown.markdown(
        src,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )
    html = TEMPLATE.format(title=title, css=CSS, body=body)
    HTML(string=html, base_url=str(pathlib.Path(md_path).resolve().parent)).write_pdf(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
