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
TRAILER = re.compile(r"trailer: (\d+) of (\d+)")
FINDINGS = re.compile(r"\b([A-Za-z]+|\d{1,2}) findings\b")
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}


def claim_pair(text):
    """The (numerator, denominator) the report quotes, or None."""
    m = ADOPTION.search(text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def claimed_findings(text):
    """Every number the report attaches to the word 'findings'. 'The findings' attaches none, and a
    sentence that says 'seven findings' when there are nine is the stale-phrase failure, so all of
    them have to agree with the count at the pin."""
    out = set()
    for word in FINDINGS.findall(text):
        n = int(word) if word.isdigit() else WORDS.get(word.lower())
        if n:
            out.add(n)
    return out


def findings_at(sha):
    """The findings on the pinned ref. README.md is the directory's own front page, not a finding."""
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", sha, "--", "findings/"],
                       cwd=UP, capture_output=True, text=True)
    if r.returncode:
        return None
    return [f for f in r.stdout.splitlines()
            if f.endswith(".md") and not f.endswith("README.md")]


def view_pairs(block):
    """Every (n, m) the counter anchored as `trailer: n of m` in one view."""
    return {(int(n), int(m)) for n, m in TRAILER.findall(block)}


# A substring is not a numbers match. `3 of 107` and `63 of 10` are both substrings of `63 of 107`,
# so the first version reported reproduction on figures that disagree (Codex, #82). These run on every
# invocation, before the live check, so a guard that quietly stops comparing numbers says so itself.
SELF_CHECK = [
    ("63 of 107 agent commits", "trailer: 63 of 107", True),
    ("3 of 107 agent commits", "trailer: 63 of 107", False),
    ("63 of 10 agent commits", "trailer: 63 of 107", False),
]


def self_check():
    broken = [(c, v, want, claim_pair(c) in view_pairs(v))
              for c, v, want in SELF_CHECK if (claim_pair(c) in view_pairs(v)) != want]
    for text, want in (("seven findings", {7}), ("9 findings", {9}), ("the findings", set())):
        if claimed_findings(text) != want:
            broken.append((text, "claimed_findings", want, claimed_findings(text)))
    return broken


def main():
    broken = self_check()
    if broken:
        print("fail: the guard's own comparison is wrong, before it even reaches the report:")
        for claim, view, want, got in broken:
            print(f"  - {claim!r} against {view!r}: wanted {want}, got {got}")
        return 1

    absent = [os.path.relpath(p, UP) for p in (BUILD, COUNTER) if not os.path.exists(p)]
    if absent:
        print(f"skip: {', '.join(absent)} not on this ref yet")
        return 0

    text = open(BUILD, encoding="utf-8").read()
    pin, want = PIN.search(text), claim_pair(text)
    if not pin:
        print("fail: the report does not say which commit it is pinned to, so nothing is checkable")
        return 1
    if want is None:
        print("fail: no '<n> of <n> agent commits' figure in the report to reproduce")
        return 1
    sha = pin.group(1)

    claimed_n, on_disk = claimed_findings(text), findings_at(sha)
    if on_disk is None:
        print(f"fail: git could not list findings/ at {sha}; needs a full-history checkout")
        return 1
    if claimed_n != {len(on_disk)}:
        print(f"fail: the report attaches {sorted(claimed_n)} to the word 'findings' and {sha} holds "
              f"{len(on_disk)}. Re-derive rather than editing. (README.md is excluded as the "
              f"directory's own front page.)")
        return 1
    print(f"findings at {sha}: {len(on_disk)}, and every 'findings' figure in the report agrees")

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

    here, there = want in view_pairs(mapped), want in view_pairs(raw)
    recount = sorted(view_pairs(mapped) | view_pairs(raw))
    print(f"report pins {sha} and quotes '{want[0]} of {want[1]} agent commits'; exact pair found in "
          f"mapped={'yes' if here else 'NO'}, raw={'yes' if there else 'NO'}")
    if not here:
        print(f"fail: §4.1 cites the mapped view and {want[0]} of {want[1]} does not reproduce there; "
              f"the recount says {recount} at {sha}. Re-derive the figure rather than editing it.")
        return 1
    if not there:
        print(f"fail: {want[0]} of {want[1]} reproduces in the mapped view, which is the one the "
              f"paper cites, but not the raw ({recount}). The two views disagree at the pin; §4.1's "
              f"sentence about which view adoption uses is now load-bearing and should say so.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
