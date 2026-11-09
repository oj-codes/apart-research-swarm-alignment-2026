#!/usr/bin/env python3
"""test_report_authors.py — the byline names real people, and every place that lists them agrees.

The brief asks for **author names and affiliations**. Nothing guarded it: the byline lives only in
`build_docx.py`, the same seven names are repeated in the roster and in the submission form's Team
members row, and three hand-maintained copies of one list drift the way hand-maintained copies do.

    python3 submission/test_report_authors.py

Three legs: every name on the byline resolves to a roster row (so a typo or an invented author is
caught), every name also appears in the form's Team members row (so the two lists cannot diverge), and
the affiliation line still names the house.

**Matched on a name's first word**, which is deliberate rather than lazy: the byline writes
`Olivia "O.J." Wilcox` where the roster writes `Olivia (O.J.)`, so a full-string compare would fail on
a correct document. First words are unique across the roster, which is the property that makes this
safe, and a dropped name still fails.

Skips cleanly while the report is not on this ref.
"""
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build_docx.py")
README = os.path.join(HERE, "README.md")
ROSTER = os.path.join(UP, "ROSTER.md")

# The affiliations the brief asks for, and the only two that belong on this byline.
AFFILIATIONS = ("Learn with O.J.", "Auran, LLC")


def literal(path, name):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == name):
            return ast.literal_eval(node.value)
    return None


def first_words(text):
    """The first word of every comma-separated name in a list written as one line."""
    return {p.strip().split()[0].lower() for p in text.split(",") if p.strip()}


def main():
    absent = [os.path.relpath(p, UP) for p in (BUILD, README, ROSTER) if not os.path.exists(p)]
    if absent:
        print(f"skip: {', '.join(absent)} not on this ref yet")
        return 0

    byline, companies = literal(BUILD, "BYLINE"), literal(BUILD, "COMPANIES")
    if not byline:
        print("fail: no BYLINE in build_docx.py, so the author list cannot be checked")
        return 1

    roster = open(ROSTER, encoding="utf-8").read()
    form = open(README, encoding="utf-8").read()
    team_row = next((l for l in form.splitlines() if l.startswith("| Team members")), "")

    names = first_words(byline)
    off_roster = sorted(n for n in names if not re.search(rf"\|\s*{re.escape(n)}", roster, re.I))
    off_form = sorted(n for n in names if n not in team_row.lower())
    missing_aff = [a for a in AFFILIATIONS if a not in (companies or "")]

    print(f"byline: {len(names)} author(s); {len(names) - len(off_roster)} on the roster, "
          f"{len(names) - len(off_form)} in the form, affiliations {len(AFFILIATIONS) - len(missing_aff)}"
          f"/{len(AFFILIATIONS)}")
    if off_roster:
        print(f"fail: {off_roster} on the byline but on no roster row — a typo, or an author nobody "
              f"else has heard of.")
    if off_form:
        print(f"fail: {off_form} on the byline but not in the form's Team members row — the two lists "
              f"have drifted, and one of them is what gets submitted.")
    if missing_aff:
        print(f"fail: the affiliation line is missing {missing_aff}. The brief asks for affiliations.")
    return 1 if (off_roster or off_form or missing_aff) else 0


if __name__ == "__main__":
    sys.exit(main())
