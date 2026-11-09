#!/usr/bin/env python3
"""state_pr_check.py — is this PR nothing but its author's own state file?

O.J. asked (#61) for state files to merge without her judgment, because she cannot tell from a diff
whether a state refresh is right. The thing a check CAN establish is narrower than "right": that the
PR touches only files that belong to one participant, and that the author line on every commit is
that participant's roster `Git Author`. That is the auto-merge column from #49: one author's own
account, no shared normative text touched.

    python3 tools/state_pr_check.py <pr-number>      # exit 0 = eligible, 1 = not, 2 = couldn't check

Eligible when ALL hold (the rule is `evaluate()`, which is pure and tested offline):
  1. every changed file is a per-participant state file, `<name>-state.md` at the repo root or
     `preferences/<name>.md`, and `<name>` is exactly one roster participant (ROSTER.md is the source);
  2. all changed files belong to the SAME participant;
  3. no file is deleted or renamed (a rename can bring a path in from outside the rule);
  4. the author line (name <email>) on EVERY commit equals that participant's roster `Git Author`,
     and "every" is verified: the commit list is paginated and its length checked against the PR's
     own commit count; a mismatch fails closed.

What it establishes: ownership, and that the author line matches the roster. What it does NOT
establish: authorship (the author field is unauthenticated, research/identity-scheme.md §3.5; the
committer field is identical for every agent here, so it cannot tell us apart) or that the content is
true. The required approving review is what stands between an eligible PR and `main`, not this.

Run from the BASE branch's checkout, never from the PR's: a PR must not be able to supply the code that
judges it (Codex, #69). Stdlib + gh. Prints its reasoning so the PR comment can carry it.
"""
import json
import re
import subprocess
import sys

REPO = "oj-codes/apart-research-swarm-alignment-2026"
ROOT_STATE = re.compile(r"^([a-z0-9][a-z0-9-]*)-state\.md$")
PREFS = re.compile(r"^preferences/([a-z0-9][a-z0-9-]*)\.md$")
MAX_COMMITS = 250  # the REST endpoint's hard cap; above it "every commit" cannot be verified


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode:
        print(f"couldn't check: gh {' '.join(args[:3])}: {r.stderr.strip()[:200]}")
        sys.exit(2)
    return r.stdout


def roster_authors(text):
    """{lowercase name: 'Name <email>'} from ROSTER.md's Git Author column, parsed by header."""
    rows = [l for l in text.splitlines() if l.startswith("|")]
    header = [c.strip().lower() for c in rows[0].strip("|").split("|")]
    name_i, author_i = header.index("name"), header.index("git author")
    out = {}
    for row in rows[2:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) <= max(name_i, author_i):
            continue
        name = cells[name_i].split("(")[0].strip().lower()
        author = cells[author_i].strip("`").strip()
        if name and author:
            out[name] = author
    return out


def evaluate(files, commits, total_commits, roster):
    """The rule. Pure: no network, no git. Returns (eligible: bool, reason: str).

    files:   [{"path", "changeType", "additions", "deletions"}]  (gh pr view --json files)
    commits: [{"sha", "name", "email"}]                          (every commit on the PR)
    total_commits: the PR's own commit count, to prove `commits` is complete
    roster:  {lowercase name: "Name <email>"}
    """
    if not files:
        return False, "NOT ELIGIBLE: no files changed"
    owners = set()
    for f in files:
        path = f["path"]
        ct = (f.get("changeType") or "").upper()
        if ct in ("DELETED", "RENAMED", "COPIED"):
            return False, f"NOT ELIGIBLE: {path} is {ct.lower()}; only edits and additions qualify"
        m = ROOT_STATE.match(path) or PREFS.match(path)
        if not m:
            return False, f"NOT ELIGIBLE: {path} is not a per-participant state file"
        who = m.group(1).lower()
        if who not in roster:
            return False, f"NOT ELIGIBLE: {path} names '{who}', who is not on the roster"
        owners.add(who)
    if len(owners) != 1:
        return False, f"NOT ELIGIBLE: files belong to more than one participant: {sorted(owners)}"
    owner = next(iter(owners))
    want = roster[owner]
    if total_commits > MAX_COMMITS:
        return False, f"NOT ELIGIBLE: {total_commits} commits exceeds what the API will list; cannot verify every author"
    if len(commits) != total_commits:
        return False, f"NOT ELIGIBLE: fetched {len(commits)} commits but the PR has {total_commits}; refusing to judge a partial list"
    if not commits:
        return False, "NOT ELIGIBLE: no commits"
    for c in commits:
        got = f"{c['name']} <{c['email']}>"
        if got != want:
            return False, f"NOT ELIGIBLE: commit {c['sha']} carries author line {got}; file owner's roster line is {want}"
    return True, (f"ELIGIBLE: {len(files)} file(s), all {owner}'s own state; {len(commits)} of {total_commits} commit(s) "
                  f"checked, author line {want} on each.\n"
                  "Establishes ownership and that the author line matches the roster; not authorship (the author "
                  "field is unauthenticated) and not that the content is true. The approving review is the gate.")


def fetch(pr):
    files = json.loads(gh("pr", "view", pr, "--repo", REPO, "--json", "files", "--jq", ".files"))
    total = int(gh("api", f"repos/{REPO}/pulls/{pr}", "--jq", ".commits").strip())
    # --slurp returns one JSON array per page; flatten here. (--jq is not allowed alongside --slurp.)
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{REPO}/pulls/{pr}/commits?per_page=100"))
    commits = [{"sha": c["sha"][:7], "name": c["commit"]["author"]["name"], "email": c["commit"]["author"]["email"]}
               for page in pages for c in page]
    roster = roster_authors(open("ROSTER.md", encoding="utf-8").read())
    return files, commits, total, roster


def main():
    if len(sys.argv) != 2:
        print(__doc__); return 2
    ok, reason = evaluate(*fetch(sys.argv[1]))
    print(reason)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
