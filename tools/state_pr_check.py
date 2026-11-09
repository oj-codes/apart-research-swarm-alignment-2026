#!/usr/bin/env python3
"""state_pr_check.py — is this PR nothing but its author's own state file?

O.J. asked (#61) for state files to merge without her judgment, because she cannot tell from a diff
whether a state refresh is right. The thing a check CAN establish is narrower than "right": that the
PR touches only files that belong to one participant, and that every commit in it was authored by
that participant. That is the auto-merge column from #49: one author's own account, append-only in
spirit, no shared normative text touched.

    python3 tools/state_pr_check.py <pr-number>      # exit 0 = eligible, 1 = not, 2 = couldn't check

Eligible when ALL hold:
  1. every changed file is a per-participant state file:
       <name>-state.md   at the repo root, or
       preferences/<name>.md
     with <name> matching exactly one roster participant (case-insensitive, ROSTER.md is the source);
  2. all changed files belong to the SAME participant;
  3. every commit's author line (name <email>) equals that participant's roster `Git Author`
     (so a PR that edits tern-state.md under Codex's author line is not eligible). This is a
     retrieval match, not authentication: the author field is free text (research/identity-scheme.md
     §3.5), and the committer field is the same for every agent here, so it cannot tell us apart;
  4. no file is deleted.

What it does NOT establish: authorship, or that the content is true. It establishes that the files
are one participant's and that the author line on every commit matches that participant's roster row.
The thing that stands between an eligible PR and `main` is the required approving review, not this
script. A state file is one participant's own account, which this repo already says is theirs to write
(PREFERENCES.md, AGENTS.md). Shared files — STATE.md, AGENTS.md, CONTRIBUTING.md, ROSTER.md,
submission/, tools/ — are never eligible.

Stdlib + gh. Prints its reasoning so the PR comment can carry it.
"""
import json
import re
import subprocess
import sys

REPO = "oj-codes/apart-research-swarm-alignment-2026"
ROOT_STATE = re.compile(r"^([a-z0-9][a-z0-9-]*)-state\.md$")
PREFS = re.compile(r"^preferences/([a-z0-9][a-z0-9-]*)\.md$")


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode:
        print(f"couldn't check: gh {' '.join(args[:3])}: {r.stderr.strip()[:200]}")
        sys.exit(2)
    return r.stdout


def roster_authors(ref="origin/main"):
    """{lowercase name: 'Name <email>'} from ROSTER.md's Git Author column, parsed by header."""
    try:
        text = subprocess.run(["git", "show", f"{ref}:ROSTER.md"], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        text = open("ROSTER.md", encoding="utf-8").read()
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


def main():
    if len(sys.argv) != 2:
        print(__doc__); return 2
    pr = sys.argv[1]
    files = json.loads(gh("pr", "view", pr, "--repo", REPO, "--json", "files", "--jq", ".files"))
    commits = json.loads(gh("api", f"repos/{REPO}/pulls/{pr}/commits", "--jq",
                            "[.[] | {sha: .sha[0:7], name: .commit.author.name, email: .commit.author.email}]"))
    roster = roster_authors()

    owners = set()
    for f in files:
        path = f["path"]
        m = ROOT_STATE.match(path) or PREFS.match(path)
        if not m:
            print(f"NOT ELIGIBLE: {path} is not a per-participant state file"); return 1
        if f.get("deletions", 0) and f.get("additions", 0) == 0 and f.get("status") == "removed":
            print(f"NOT ELIGIBLE: {path} is deleted"); return 1
        who = m.group(1).lower()
        if who not in roster:
            print(f"NOT ELIGIBLE: {path} names '{who}', who is not on the roster"); return 1
        owners.add(who)
    if not files:
        print("NOT ELIGIBLE: no files changed"); return 1
    if len(owners) != 1:
        print(f"NOT ELIGIBLE: files belong to more than one participant: {sorted(owners)}"); return 1
    owner = owners.pop()
    want = roster[owner]
    for c in commits:
        got = f"{c['name']} <{c['email']}>"
        if got != want:
            print(f"NOT ELIGIBLE: commit {c['sha']} authored by {got}, file owner is {want}"); return 1
    print(f"ELIGIBLE: {len(files)} file(s), all {owner}'s own state; {len(commits)} commit(s), author line {want} on each.")
    print("Establishes ownership and that the author line matches the roster; not authorship (the author "
          "field is unauthenticated) and not that the content is true. The approving review is the gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
