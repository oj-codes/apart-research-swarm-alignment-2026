#!/usr/bin/env python3
"""test_report_docx_fresh.py — the committed .docx still contains the current build's sentences.

`submission/README.md` states the failure plainly: the build can crash silently, the previous
`report.docx` stays on disk unchanged, and `git status` cannot tell it from a fresh build. It
happened once, at 95e04ca. The guard until now was the sentence *"re-render; don't re-read the
commit message"*, which is a habit rather than a check.

So: every long string in the build's own prose must appear in the committed docx. If the script moved
and the docx did not, sentences are missing and this goes red. Stdlib only — a .docx is a zip and its
text is XML, so nothing is imported that CI does not already have.

    python3 submission/test_report_docx_fresh.py

**What this proves and what it doesn't.** It proves no sentence of the current build is absent from
the committed file, which is exactly the stale-document failure. It does *not* prove the docx was
produced by this script — a matching set of sentences with different layout would pass. For layout,
render.

Skips cleanly while the report is not on this ref, so it can land ahead of #27.
"""
import ast
import html
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build_docx.py")
DOCX = os.path.join(HERE, "report.docx")

# The complement of an allowlist, on purpose (Corrie, #76). An allowlist of prose containers loses
# coverage silently as the module grows; naming the machinery instead means a new prose container is
# covered the day it appears, and a new non-prose one fails loudly rather than being skipped.
# This is what surfaced `REPO` — the one line in the paper a judge clicks, and the form's Project
# code — which the allowlist had excluded.
MACHINERY = {"W", "NS", "FONT", "T", "SRC", "WORK"}

# Short literals ("Codex", a section number) are everywhere and survive any edit; a stale document
# is found by the long ones.
MIN_LENGTH = 60


def prose_literals(path):
    """Long strings in the module's top-level assignments, minus the named machinery.

    The module docstring is a bare expression rather than an assignment, so it falls out on its own.
    Markup is dropped: a footer's XML is a long literal that is not text, so it can never appear in
    the document and counts as missing. That is what a page-number footer did to this on #87, and the
    content was shortened to suit the guard before the guard learned (Rill, #87).
    """
    tree = ast.parse(open(path, encoding="utf-8").read())
    found = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id in MACHINERY:
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                found.append(inner.value)
    return [s for s in found if not squash(s).startswith("<")]


def document_text(path):
    """Every visible string in the document, with runs and paragraphs glued back together.

    Entities are unescaped because the source writes `<name>` and XML stores it `&lt;name&gt;`,
    which a naive tag-stripper would delete as though it were markup.
    """
    with zipfile.ZipFile(path) as z:
        parts = [z.read(n).decode("utf-8", "replace") for n in sorted(z.namelist())
                 if re.fullmatch(r"word/(document|header\d*|footer\d*)\.xml", n)]
    return html.unescape(re.sub(r"<[^>]+>", " ", "".join(parts)))


def squash(text):
    """Compare without whitespace or emphasis markers: Word re-flows, the source wraps, and `**` is
    markup the builder consumes, so none of the three is a difference."""
    return re.sub(r"[\s*`]+", "", text)


def main():
    absent = [os.path.relpath(p, HERE) for p in (BUILD, DOCX) if not os.path.exists(p)]
    if absent:
        print(f"skip: {', '.join(absent)} not on this ref yet (#27)")
        return 0

    strings = [s for s in prose_literals(BUILD) if len(squash(s)) >= MIN_LENGTH]
    body = squash(document_text(DOCX))
    missing = [s for s in strings if squash(s) not in body]

    print(f"docx freshness: {len(strings) - len(missing)}/{len(strings)} long strings "
          f"from the build are present in report.docx")
    if missing:
        print("fail: report.docx is older than build_docx.py. Re-render; do not re-read the commit "
              "message. First missing:")
        for s in missing[:5]:
            print(f"  - {s.strip()[:110]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
