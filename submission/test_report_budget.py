#!/usr/bin/env python3
"""test_report_budget.py — the form's hard word limits, as a test rather than a comment.

The brief asks for an abstract of **150 to 250 words**, and the string that gets pasted into the
form's *Project summary* field is `ABSTRACT` in `submission/build_docx.py`. On 9 November it sat at
**248** — two words under the ceiling on a requirement that appears in no render and has nothing to
do with the page cap. A render cannot see it. A test can.

Both bounds are checked, not just the ceiling: the abstract is the one block at its limit, so it is
also the first place a trim pass will eat into, and a two-sided requirement is exactly the kind that
gets treated as one-sided at 5am (Corrie, #70).

Stdlib only and parsed with `ast` rather than imported, so python-docx is not needed to run it and a
build failure cannot masquerade as a budget failure.

    python3 submission/test_report_budget.py

Skips cleanly while `build_docx.py` is not on this ref, so this can land before #27.
"""
import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build_docx.py")

# The brief's requirement is two-sided — "an abstract of 150 to 250 words" — and the ceiling is the
# end that has no slack: main text has 120-160 words of headroom, the abstract has two. So the
# abstract is also the first place a trim pass will eat into, which is why the floor is stated too
# rather than left implied (Corrie, #70).
SUMMARY_FLOOR = 150
SUMMARY_CEILING = 250

# Checked from the source literal, not the PDF: `pdftotext` splits a hyphenated word across a line
# break and reads one high, and the form counts the pasted text.


def string_constants(path):
    """Top-level `NAME = "literal"` assignments, without importing the module."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            try:
                found[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    return found


def main():
    if not os.path.exists(BUILD):
        print("skip: submission/build_docx.py is not on this ref yet (#27)")
        return 0
    abstract = string_constants(BUILD).get("ABSTRACT")
    if not isinstance(abstract, str):
        print("fail: build_docx.py has no ABSTRACT string literal to measure")
        return 1
    words = len(abstract.split())
    print(f"abstract: {words} words, inside the brief's {SUMMARY_FLOOR} to {SUMMARY_CEILING} "
          f"({SUMMARY_CEILING - words} under the ceiling, {words - SUMMARY_FLOOR} over the floor)")
    if not SUMMARY_FLOOR <= words <= SUMMARY_CEILING:
        print(f"fail: the brief asks for an abstract of {SUMMARY_FLOOR} to {SUMMARY_CEILING} words "
              f"and ABSTRACT is {words}. The page cap will not catch this and no render will show it.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
