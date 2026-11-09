#!/usr/bin/env python3
"""test_report_page_cap.py — the shipped PDF's main text still fits the brief's page cap.

The brief caps the counted region — Introduction through the Conclusion, with appendices and
references outside it — at **8 pages**. Every other hard requirement has a guard now; this one had
hand renders, thirteen of them, and it is the requirement with *zero* margin.

    python3 submission/test_report_page_cap.py

Reads the committed `submission/report.pdf`, which is the file to view and to upload, so the page
numbers are the ones a reader meets. Two questions, not one: **which page** the References heading
starts on, and **how far down it sits**. With the counted region at 8, the heading has to begin on
page 9 or earlier — and if it begins on page 9, it has to be near the top of it, because a heading
half way down page 9 is a body that used eight and a half pages while still reading as "8". That
second question is the whole margin, and it is the direction that fails quietly (Corrie, #99).

Stdlib except `pdftotext` (poppler-utils), which CI installs. Missing binary is a skip with a note so
a machine without poppler cannot look green by accident.

Skips cleanly while the report is not on this ref.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
PDF = os.path.join(HERE, "report.pdf")

# The brief's cap on the counted region, and therefore the latest page References may begin on.
CAP_PAGES = 8
LAST_ALLOWED_REFERENCES_PAGE = CAP_PAGES + 1

# How far down that last page the heading may sit before the body has clearly overrun it. Four rather
# than zero, because a running header or page number can take a leading line, and #87's build puts a
# page number on every page. Today's value is 0, so four costs nothing and still refuses half a page.
HEADING_SLACK = 4

# A line that is only the heading, so a body sentence mentioning "References" cannot match.
HEADING = re.compile(r"^\s*References\s*$")


def pages(path):
    """The PDF's pages, in order, as text. With `pdftotext -layout` a form feed ends each page."""
    if not shutil.which("pdftotext"):
        return None
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "t.txt")
        subprocess.run(["pdftotext", "-layout", path, out], check=True, capture_output=True, text=True)
        raw = open(out, encoding="utf-8", errors="replace").read()
    parts = raw.split("\f")
    # The split leaves one empty part after the final form feed; drop only THAT, so a genuinely blank
    # page in the middle keeps its slot and the index stays the reader's page number (Corrie, #99).
    if parts and not parts[-1].strip():
        parts.pop()
    return parts


def main():
    if not os.path.exists(PDF):
        print("skip: submission/report.pdf not on this ref yet")
        return 0
    if not shutil.which("pdftotext"):
        print("skip: pdftotext not installed (poppler-utils); CI installs it")
        return 0

    body = pages(PDF)
    start = next((i for i, p in enumerate(body, 1) if any(HEADING.match(l) for l in p.splitlines())),
                 None)
    print(f"report.pdf: {len(body)} pages total")
    if start is None:
        print("fail: no line that is exactly 'References' in the PDF, so the counted region has no "
              "known end. Checked rather than assumed.")
        return 1

    counted = start - 1
    print(f"References begins on page {start}; counted region is at least {counted} page(s), "
          f"cap {CAP_PAGES}")
    if start > LAST_ALLOWED_REFERENCES_PAGE:
        print(f"fail: main text is over the cap by {counted - CAP_PAGES} page(s). This is the "
              f"requirement with no margin, and a render is the only place it shows; cut prose rather "
              f"than spacing, which would move every page measurement.")
        return 1

    if start == LAST_ALLOWED_REFERENCES_PAGE:
        lines = body[start - 1].splitlines()
        at = next(i for i, l in enumerate(lines) if HEADING.match(l))
        share = at / max(len(lines), 1)
        print(f"heading is line {at} of {len(lines)} on page {start}: {share:.0%} of that page is body")
        if at > HEADING_SLACK:
            print(f"fail: References is line {at} on page {start}, so about {share:.0%} of that page "
                  f"is body. The counted region is over {CAP_PAGES} pages even though the heading "
                  f"never left page {LAST_ALLOWED_REFERENCES_PAGE}.")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
