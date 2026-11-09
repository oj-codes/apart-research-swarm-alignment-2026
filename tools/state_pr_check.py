#!/usr/bin/env python3
"""state_pr_check.py — is this PR nothing but its author's own state file, or their own signed rows on the board?

O.J. asked (#61) for state files to merge without her judgment, because she cannot tell from a diff
whether a state refresh is right. The thing a check CAN establish is narrower than "right": that the
PR touches only files that belong to one participant, and that the author line on every commit is
that participant's roster `Git Author`. That is the auto-merge column from #49: one author's own
account, no shared normative text touched.

    python3 tools/state_pr_check.py <pr-number> [--expect-head <sha>]
                                      # exit 0 = eligible, 1 = not, 2 = couldn't check
    With --expect-head, the PR's current head (as the API reports it) must equal <sha> or the verdict
    is NOT ELIGIBLE: the files and commits were read for one revision and must not license a merge of
    another. The caller passes the same sha to `gh pr merge --match-head-commit`.

Eligible when ALL hold (the rule is `evaluate()`, which is pure and tested offline):
  1. every changed file is a per-participant state file, `<name>-state.md` at the repo root or
     `preferences/<name>.md`, and `<name>` is exactly one roster participant (ROSTER.md is the source);
     or it is `STATE.md`, the shared board, under rule 5;
  2. all changed files belong to the SAME participant (for a board-only PR the participant is the one
     roster author line shared by every commit);
  3. no file is deleted or renamed (a rename can bring a path in from outside the rule);
  4. the author line (name <email>) on EVERY commit equals that participant's roster `Git Author`,
     and "every" is verified: the commit list is paginated and its length checked against the PR's
     own commit count; a mismatch fails closed;
  5. for `STATE.md` (O.J. on #78: the board was the file she asked about), the diff is table rows only,
     every added row carries the participant's name in its last cell (the board's `who, when`), and a
     removed row that names someone else is replaced by an added row with the same first cell, so a
     rewrite of another's row is allowed and signed, while deleting it or editing the prose is not.

What it establishes: ownership (or, on the board, that every changed row is signed by the one author),
and that the author line matches the roster. What it does NOT
establish: authorship (the author field is unauthenticated, research/identity-scheme.md §3.5; the
committer field is identical for every agent here, so it cannot tell us apart) or that the content is
true. The required approving review is what stands between an eligible PR and `main`, not this.

Run from the protected branch's checkout, never from the PR's: a PR must not be able to supply the code
that judges it (Codex, #69). Stdlib + gh. Prints its reasoning so the PR comment can carry it.
"""
import json
import re
import subprocess
import sys

REPO = "oj-codes/apart-research-swarm-alignment-2026"
ROOT_STATE = re.compile(r"^([a-z0-9][a-z0-9-]*)-state\.md$")
PREFS = re.compile(r"^preferences/([a-z0-9][a-z0-9-]*)\.md$")
BOARD = "STATE.md"
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


def _row_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(cells):
    return all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def board_rows_signed(patch, who):
    """Pure. Rule 5 on one unified diff of STATE.md. Returns (ok: bool, reason: str).

    who is the participant's roster name as it appears in a who-cell, e.g. "Tern"; matched as a word,
    case-insensitively, in the LAST cell of every added row. Only table rows may change: a touched prose
    line, header row or separator is a change the rule cannot sign. A removed row that does not carry
    `who` must be replaced by an added row with the same first cell (a rewrite, which the added row
    signs); otherwise it is a deletion of someone else's row and the PR is not eligible.
    """
    if not patch or not patch.strip():
        return False, f"NOT ELIGIBLE: {BOARD} changed but its diff could not be read"
    name = re.compile(r"(?<![A-Za-z0-9])" + re.escape(who) + r"(?![A-Za-z0-9])", re.I)
    added, removed, changed = [], [], 0
    for line in patch.splitlines():
        if line.startswith(("+++", "---", "@@", " ", "\\")) or not line:
            continue
        sign, body = line[0], line[1:]
        if sign not in "+-":
            continue
        if not body.lstrip().startswith("|"):
            return False, f"NOT ELIGIBLE: {BOARD} prose changed, not a table row: {body.strip()[:60]!r}"
        cells = _row_cells(body)
        if _is_separator(cells):
            return False, f"NOT ELIGIBLE: {BOARD} table structure changed"
        changed += 1
        (added if sign == "+" else removed).append(cells)
    if not changed:
        return False, f"NOT ELIGIBLE: {BOARD} listed but its diff changes no rows"
    for cells in added:
        if not name.search(cells[-1]):
            return False, f"NOT ELIGIBLE: {BOARD} row {cells[0][:40]!r} is not signed {who} in its last cell: {cells[-1][:40]!r}"
    added_items = {c[0] for c in added}
    for cells in removed:
        if not name.search(cells[-1]) and cells[0] not in added_items:
            return False, f"NOT ELIGIBLE: {BOARD} row {cells[0][:40]!r} ({cells[-1][:30]!r}) removed without a replacement by {who}"
    return True, f"{len(added)} row(s) added or rewritten, all signed {who}; {len(removed)} removed, each {who}'s or replaced"


def evaluate(files, commits, total_commits, roster, patches=None):
    """The rule. Pure: no network, no git. Returns (eligible: bool, reason: str).

    files:   [{"path", "changeType", "additions", "deletions"}]  (gh pr view --json files)
    commits: [{"sha", "name", "email"}]                          (every commit on the PR)
    total_commits: the PR's own commit count, to prove `commits` is complete
    roster:  {lowercase name: "Name <email>"}
    patches: {path: unified diff text}; only consulted for STATE.md
    """
    if not files:
        return False, "NOT ELIGIBLE: no files changed"
    owners, board = set(), False
    for f in files:
        path = f["path"]
        ct = (f.get("changeType") or "").upper()
        if ct in ("DELETED", "RENAMED", "COPIED"):
            return False, f"NOT ELIGIBLE: {path} is {ct.lower()}; only edits and additions qualify"
        if path == BOARD:
            board = True
            continue
        m = ROOT_STATE.match(path) or PREFS.match(path)
        if not m:
            return False, f"NOT ELIGIBLE: {path} is not a per-participant state file"
        who = m.group(1).lower()
        if who not in roster:
            return False, f"NOT ELIGIBLE: {path} names '{who}', who is not on the roster"
        owners.add(who)
    if len(owners) > 1:
        return False, f"NOT ELIGIBLE: files belong to more than one participant: {sorted(owners)}"
    if owners:
        owner = next(iter(owners))
    else:
        # Board only: the participant is whoever authored every commit, if that is one roster line.
        lines = {f"{c['name']} <{c['email']}>" for c in commits}
        by_line = {v: k for k, v in roster.items()}
        if len(lines) != 1 or next(iter(lines)) not in by_line:
            return False, f"NOT ELIGIBLE: {BOARD} edited by author line(s) {sorted(lines)}, not one roster participant"
        owner = by_line[next(iter(lines))]
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
    board_note = ""
    if board:
        display = want.split("<")[0].strip()
        ok, why = board_rows_signed((patches or {}).get(BOARD), display)
        if not ok:
            return False, why
        board_note = f" {BOARD}: {why}."
    what = "own state" if not board else ("own state and signed board rows" if owners else "signed board rows")
    return True, (f"ELIGIBLE: {len(files)} file(s), all {owner}'s {what}; {len(commits)} of {total_commits} commit(s) "
                  f"checked, author line {want} on each.{board_note}\n"
                  "Establishes ownership and that the author line matches the roster; not authorship (the author "
                  "field is unauthenticated) and not that the content is true. The approving review is the gate.")


def head_matches(expected, actual):
    """Pure. True when no head was pinned, or the API's head is the pinned one."""
    return expected is None or (actual or "").lower() == expected.lower()


def fetch(pr):
    view = json.loads(gh("pr", "view", pr, "--repo", REPO, "--json", "files,headRefOid"))
    files, head = view["files"], view["headRefOid"]
    total = int(gh("api", f"repos/{REPO}/pulls/{pr}", "--jq", ".commits").strip())
    # --slurp returns one JSON array per page; flatten here. (--jq is not allowed alongside --slurp.)
    pages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{REPO}/pulls/{pr}/commits?per_page=100"))
    commits = [{"sha": c["sha"][:7], "name": c["commit"]["author"]["name"], "email": c["commit"]["author"]["email"]}
               for page in pages for c in page]
    patches = {}
    if any(f["path"] == BOARD for f in files):
        fpages = json.loads(gh("api", "--paginate", "--slurp", f"repos/{REPO}/pulls/{pr}/files?per_page=100"))
        patches = {f["filename"]: f.get("patch", "") for page in fpages for f in page}
    roster = roster_authors(open("ROSTER.md", encoding="utf-8").read())
    return files, commits, total, roster, head, patches


def main():
    args = sys.argv[1:]
    expect = None
    if "--expect-head" in args:
        i = args.index("--expect-head"); expect = args[i + 1]; del args[i:i + 2]
    if len(args) != 1:
        print(__doc__); return 2
    files, commits, total, roster, head, patches = fetch(args[0])
    if not head_matches(expect, head):
        print(f"NOT ELIGIBLE: PR head is {head[:7]} but this run was started for {expect[:7]}; "
              "the head moved, so nothing read here licenses a merge. Refusing.")
        return 1
    ok, reason = evaluate(files, commits, total, roster, patches)
    print(reason + (f"\nHead checked: {head}" if ok else ""))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
