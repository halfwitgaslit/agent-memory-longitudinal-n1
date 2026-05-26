"""Build the v0.1 paper PDF from the markdown source via weasyprint.

Usage:
    python paper_build.py [--in path/to/v0.1.md] [--out path/to/v0.1.pdf]

Defaults:
    in:  phd/paper/v0.1.md
    out: phd/paper/v0.1.pdf

Pipeline: markdown → HTML (Python-Markdown with extensions) → PDF (weasyprint).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import markdown
from weasyprint import HTML

DEFAULT_MD = Path(__file__).resolve().parent.parent / "paper" / "v0.1.md"
DEFAULT_PDF = Path(__file__).resolve().parent.parent / "paper" / "v0.1.pdf"

CSS = """
@page { size: letter; margin: 0.75in; }
body { font-family: "Charter", "Georgia", serif; font-size: 11pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 18pt; color: #111; border-bottom: 2px solid #444; padding-bottom: 4pt; }
h2 { font-size: 14pt; color: #222; margin-top: 1.4em; border-bottom: 1px solid #888; padding-bottom: 2pt; }
h3 { font-size: 12pt; color: #333; margin-top: 1.2em; }
h4 { font-size: 11pt; color: #444; font-style: italic; }
p, li { text-align: justify; }
code, pre { font-family: "JetBrains Mono", "Menlo", "Consolas", monospace; font-size: 9.5pt; background: #f7f7f9; color: #111; padding: 1px 3px; border-radius: 2px; }
pre { padding: 6pt 10pt; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 10pt; }
th, td { border: 1px solid #aaa; padding: 4pt 8pt; text-align: left; }
th { background: #eee; }
blockquote { border-left: 4px solid #ccc; padding: 4pt 12pt; color: #444; font-style: italic; margin: 0.8em 0; }
.author { font-size: 10pt; color: #555; }
hr { border: none; border-top: 1px solid #aaa; margin: 1.5em 0; }
"""


def build(md_path: Path, pdf_path: Path) -> dict:
    src = md_path.read_text()
    # Strip YAML frontmatter
    if src.startswith("---"):
        end = src.find("\n---", 4)
        if end > 0:
            front = src[4:end].strip()
            body = src[end + 4 :].lstrip()
            # Use the frontmatter for a header block
            header_lines = []
            for line in front.split("\n"):
                if line.strip():
                    header_lines.append(f"<p class='author'>{line.replace(':', ': ')}</p>")
            preamble = "\n".join(header_lines)
            src = preamble + "\n\n" + body
    html_body = markdown.markdown(
        src,
        extensions=["tables", "fenced_code", "toc", "footnotes"],
        output_format="html5",
    )
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>v0.1 paper draft</title><style>{CSS}</style></head>
<body>{html_body}</body></html>"""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_doc, base_url=str(md_path.parent)).write_pdf(str(pdf_path))
    return {"in": str(md_path), "out": str(pdf_path), "bytes_pdf": pdf_path.stat().st_size}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=str(DEFAULT_MD))
    ap.add_argument("--out", dest="dst", default=str(DEFAULT_PDF))
    args = ap.parse_args()
    res = build(Path(args.src), Path(args.dst))
    print(res)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
