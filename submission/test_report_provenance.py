#!/usr/bin/env python3
"""test_report_provenance.py — the report's cited provenance numbers still reproduce from its pin.

The report pins `main` at one commit and quotes what the record holds there. Those numbers were
re-derived by hand on every render tonight — `63 of 107`, `nine findings`, `31 scripted` — and a
hand check done ten times is a check that will eventually be done from memory.

This automates the part that is scriptable: take the commit the report *itself* pins, re-run
`count_provenance.py` against it, and require the adoption figure the report quotes to come back. If
someone edits the number without re-deriving, or edits the pin without re-checking, this goes red.

    python3 submission/test_report_provenance.py

It finds the pin and the claimed figure by reading the report's own text, so neither is duplicated
here and neither can drift from the file it is checking.

Needs history: CI checks out with `fetch-depth: 0`. Skips cleanly while the report is not on this ref.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
BUILD = os.path.join(HERE, "build_docx.py")
COUNTER = os.path.join(HERE, "count_provenance.py")

PIN = re.compile(r"main commit ([0-9a-f]{7,40})")
ADOPTION = re.compile(r"(\d+) of (\d+) agent commits")


def main():
    absent = [os.path.relpath(p, UP) for p in (BUILD, COUNTER) if not os.path.exists(p)]
    if absent:
        print(f"skip: {', '.join(absent)} not on this ref yet")
        return 0

    text = open(BUILD, encoding="utf-8").read()
    pin = PIN.search(text)
    claimed = ADOPTION.search(text)
    if not pin:
        print("fail: the report does not say which commit it is pinned to, so nothing is checkable")
        return 1
    if not claimed:
        print("fail: no '<n> of <n> agent commits' figure in the report to reproduce")
        return 1
    sha, want = pin.group(1), f"{claimed.group(1)} of {claimed.group(2)}"

    r = subprocess.run([sys.executable, os.path.relpath(COUNTER, UP), sha],
                       cwd=UP, capture_output=True, text=True)
    if r.returncode:
        print(f"fail: count_provenance.py {sha} exited {r.returncode}: {r.stderr.strip()[:200]}")
        return 1

    # It prints a raw and a mapped view; the quote has to hold in both, because the report does not
    # say which view its adoption figure came from and a figure that only survives one of them is a
    # figure with a caveat nobody wrote down.
    views = [b for b in r.stdout.split("---") if "Agent-Session trailer" in b]
    hits = [want in v for v in views]
    print(f"report pins {sha} and quotes '{want} agent commits'; reproduced in "
          f"{sum(hits)}/{len(hits)} of count_provenance's views")
    if not all(hits):
        printed = sorted({m for v in views for m in re.findall(r"trailer: (\d+ of \d+)", v)})
        print(f"fail: '{want}' does not reproduce at {sha}; the recount says {printed}. "
              f"Re-derive the figure rather than editing it.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
