#!/usr/bin/env python3
"""test_report_provenance.py — the report's cited provenance numbers still reproduce from its pin.

The report pins `main` at one commit and quotes what the record holds there. Those numbers were
re-derived by hand on every render tonight — `63 of 107`, `nine findings`, `31 scripted` — and a
hand check done ten times is a check that will eventually be done from memory.

This automates the part that is scriptable: take the commit the report *itself* pins, re-run
`count_provenance.py` against it, and require the adoption figure the report quotes to come back. If
someone edits the number without re-deriving, or edits the pin without re-checking, this goes red.

**The mapped view is the load-bearing arm**, because §4.1 says so — *"adoption uses the mapped view,
the identity-fork finding the raw one."* The raw view is checked too as a stricter extra, and if the
two ever diverge the failure says which one the paper actually rests on rather than just going red.

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

    # count_provenance prints a raw and a mapped view. §4.1 says which one the report cites:
    # "adoption uses the mapped view, the identity-fork finding the raw one" — so the mapped view is
    # the load-bearing arm and the raw check is the stricter extra (Rill, #82). Requiring both is
    # tighter than the paper's own claim; while they agree that costs nothing, and if they ever
    # diverge the failure says which one the paper actually rests on.
    def view_after(label):
        """The block under the '--- label ---' header. Splitting on the dashes would lose the label,
        since it lives between them."""
        out, on = [], False
        for line in r.stdout.splitlines():
            if line.startswith("---"):
                on = label in line
                continue
            if on:
                out.append(line)
        return "\n".join(out)

    mapped, raw = view_after("mapped through"), view_after("raw author spellings")
    if not mapped or not raw:
        print(f"fail: count_provenance printed no raw/mapped pair to check: {r.stdout[:200]}")
        return 1

    print(f"report pins {sha} and quotes '{want} agent commits'; reproduced in "
          f"mapped={'yes' if want in mapped else 'NO'}, raw={'yes' if want in raw else 'NO'}")
    recount = sorted(set(re.findall(r"trailer: (\d+ of \d+)", r.stdout)))
    if want not in mapped:
        print(f"fail: §4.1 cites the mapped view and '{want}' does not reproduce there; the recount "
              f"says {recount} at {sha}. Re-derive the figure rather than editing it.")
        return 1
    if want not in raw:
        print(f"fail: '{want}' reproduces in the mapped view, which is the one the paper cites, but not "
              f"in the raw view ({recount}). The two views disagree at the pin; §4.1's sentence about "
              f"which view adoption uses is now load-bearing and should say so.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
