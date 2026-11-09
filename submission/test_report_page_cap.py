#!/usr/bin/env python3
"""test_report_page_cap.py — the shipped PDF's main text still fits the brief's page cap.

The brief caps the counted region — Introduction through the Conclusion, with appendices and
references outside it — at **8 pages**. Every other hard requirement has a guard now; this one had
hand renders, thirteen of them, and it is the requirement with *zero* margin.

    python3 submission/test_report_page_cap.py

Reads the committed `submission/report.pdf`, which is the file to view and to upload, so the page
numbers are the ones a reader meets. Locates the page the References heading starts on: with the
counted region at 8, that has to be page 9 or earlier, because a prose edit that pushes it to 10 is a
prose edit that pushed the body over.

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

# A line that is only the heading. Anchoring this way keeps a body sentence mentioning "References"
# from matching.
HEADING = re.compile(r"^\s*References\s*$")


def pages(path):
    if not shutil.which("pdftotext"):
        return None
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "t.txt")
        subprocess.run(["pdftotext", "-layout", path, out], check=True, capture_output=True, text=True)
        raw = open(out, encoding="utf-8", errors="replace").read()
    return [p for p in raw.split("\f") if p.strip()]


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
    print(f"References begins on page {start}; counted region is {counted} pages against a "
          f"cap of {CAP_PAGES}")
    if start > LAST_ALLOWED_REFERENCES_PAGE:
        print(f"fail: main text is over the cap by {counted - CAP_PAGES} page(s). This is the "
              f"requirement with no margin, and a render is the only place it shows; cut prose rather "
              f"than spacing, which would move every page measurement.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
