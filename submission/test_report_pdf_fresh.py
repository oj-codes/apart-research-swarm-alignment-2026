#!/usr/bin/env python3
"""test_report_pdf_fresh.py — the committed .pdf still contains the current build's paragraphs.

`submission/report.pdf` is the artifact to view and to upload, and it is produced by hand from
`report.docx`. So it can go stale the same way the docx can: someone edits `build_docx.py`, re-renders
the docx, and the PDF that ships still carries the old sentence. That is the docx failure one step
further down the pipe, on the file a reader actually opens.

    python3 submission/test_report_pdf_fresh.py

**Paragraphs only, and that is deliberate rather than lazy.** Table cells interleave in any flat PDF
text extraction — a two-line cell sits beside a two-line neighbour and the lines alternate — so a cell
sentence is rarely contiguous in the extract. Paragraphs are, verified by rendering: 30 of 30 present
with `pdftotext -layout`, and a single word changed in one of them takes the whole paragraph red.

Stdlib except `pdftotext` (poppler-utils), which CI installs. Missing binary is a skip with a note
rather than a pass, so a machine without poppler cannot look green by accident.

Skips cleanly while the report is not on this ref.
"""
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build_docx.py")
PDF = os.path.join(HERE, "report.pdf")

# Paragraph-shaped entries in BODY: a two-tuple of (short markup tag, text), plus the bare strings
# some blocks use. Table rows are nested lists and drop out, which is the point.
MIN_LENGTH = 60

# A line that is only a page number. `pdftotext -layout` renders the footer into the text stream, and
# where a page break falls inside a paragraph it lands between that paragraph's two halves.
PAGE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")


def paragraphs(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    bodies = [n.value for n in tree.body
              if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
              and n.targets[0].id == "BODY"]
    if not bodies:
        return []
    out = []
    for el in bodies[0].elts:
        if (isinstance(el, ast.Tuple) and len(el.elts) == 2
                and isinstance(el.elts[0], ast.Constant) and isinstance(el.elts[1], ast.Constant)
                and isinstance(el.elts[1].value, str)):
            out.append(el.elts[1].value)
        elif isinstance(el, ast.Constant) and isinstance(el.value, str):
            out.append(el.value)
    return out


def squash(text):
    """Compare without whitespace, markup markers, or the typography a PDF renderer substitutes.

    NFKC folds ligatures (`fi` renders as one glyph) and the quote/dash normalisation covers the
    curly forms both the source and the PDF use inconsistently. Without these the check reports
    differences that are a font, not an edit.
    """
    text = unicodedata.normalize("NFKC", text)
    for a, b in (("\u2019", "'"), ("\u201c", '"'), ("\u201d", '"'),
                 ("\u2013", "-"), ("\u2014", "-"), ("\u00a0", " ")):
        text = text.replace(a, b)
    return re.sub(r"[\s*`\u00ad]+", "", text)


def pdf_text(path):
    """The document's text, with page numbers dropped.

    A paragraph that crosses a page break has its two halves separated by whatever furniture sits
    between them, and `pdftotext -layout` puts a footer into the text stream right there — so
    `squash` sees `...exact is correct.` then `6` then `The harness carries a test...` and the
    paragraph stops being contiguous. Sixteen pages, sixteen numbers, three paragraphs crossing a
    break, and main went red (Corrie, #100).

    Only lines that are *nothing but* a number are dropped, so a body line that is a bare numeral is
    the one thing this could eat. It has not been one yet.
    """
    if not shutil.which("pdftotext"):
        return None
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "t.txt")
        subprocess.run(["pdftotext", "-layout", path, out], check=True,
                       capture_output=True, text=True)
        raw = open(out, encoding="utf-8", errors="replace").read()
    return "\n".join(l for l in raw.splitlines() if not PAGE_NUMBER.match(l))


def main():
    absent = [os.path.relpath(p, UP) for p in (BUILD, PDF) if not os.path.exists(p)]
    if absent:
        print(f"skip: {', '.join(absent)} not on this ref yet")
        return 0
    if not shutil.which("pdftotext"):
        print("skip: pdftotext not installed (poppler-utils); CI installs it")
        return 0

    wanted = [s for s in paragraphs(BUILD) if len(squash(s)) >= MIN_LENGTH]
    body = squash(pdf_text(PDF))
    missing = [s for s in wanted if squash(s) not in body]

    print(f"pdf freshness: {len(wanted) - len(missing)}/{len(wanted)} long paragraphs from the build "
          f"are present in report.pdf")
    if missing:
        print("fail: report.pdf is older than build_docx.py. Re-render the docx and the PDF; do not "
              "re-read the commit message. First missing:")
        for s in missing[:5]:
            print(f"  - {s.strip()[:110]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
