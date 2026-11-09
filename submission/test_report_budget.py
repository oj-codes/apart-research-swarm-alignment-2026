#!/usr/bin/env python3
"""test_report_budget.py — the form's hard ceilings, as a test rather than a comment.

The brief caps the *Project summary* pasted into the submission form at **250 words**. The string
that gets pasted is `ABSTRACT` in `submission/build_docx.py`, and on 9 November it sat at **248** —
two words of margin, on a requirement that appears in no render and has nothing to do with the page
cap. A render cannot see it. A test can.

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

# The brief's ceiling for the form's Project summary field, and the one number in this file that is
# not ours to choose. Checked from the source literal, not the PDF: `pdftotext` splits a hyphenated
# word across a line break and reads one high, and the form counts the pasted text.
SUMMARY_CEILING = 250


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
    print(f"abstract: {words} words against a {SUMMARY_CEILING}-word ceiling "
          f"({SUMMARY_CEILING - words} to spare)")
    if words > SUMMARY_CEILING:
        print(f"fail: the form's Project summary ceiling is {SUMMARY_CEILING} words and ABSTRACT is "
              f"{words}. The page cap will not catch this and no render will show it.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
