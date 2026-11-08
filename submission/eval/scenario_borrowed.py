#!/usr/bin/env python3
"""Scenario — a borrowed author line. The negative control, and the suite's only false_merge.

CONTRACT (submission/eval/harness.py): a scenario supplies
  - build(repo): write a scripted history. Ground truth lives in `Truth-Actor` trailers on the
    commits themselves, so it is known by construction and cannot drift from the history written.
  - EXPECTED: {(path, identity): outcome}, committed with this file BEFORE any run.
  - optionally SESSIONS: {identity: session-id} so the `session` path knows what to look for.

THE SCENARIO. A second actor authors under a name the repo's `.mailmap` folds into `Tern`. Nothing
in the author string is `tern`; the only thing that separates them is the `Agent-Session` trailer,
which the borrowed, pre-convention commit does not carry.

WHY IT IS THE GIFT. The unassisted paths are CORRECT — `--author=Tern` and the raw view claim only
Tern's work. The scheme's own documented fix, the `.mailmap`, is what turns that into a FALSE MERGE,
because canonicalising is exactly wrong when two actors share a name. The suite otherwise has zero
false_merge rows, which is the outcome a provenance paper most needs to show; this is where it comes
from, and the failure is owned by the fix rather than by the absence of one.

Run through the harness (harness.py imports this file and calls build/EXPECTED):

    python3 submission/eval/harness.py scenario_borrowed
"""
import os
import subprocess

# The borrowed actor's own name, folded to Tern by the mailmap this file writes.
BORROWED_AUTHOR = "pawn <pawn@learnwithoj.com>"
REAL_AUTHOR = "Tern <tern@learnwithoj.com>"
WHEN = "2026-11-08T10:00:00+00:00"

# The `session` path resolves an identity to the session id(s) a reader holding a commit would know.
# BOTH of the borrower's sessions are declared, so the query inputs come from here and Truth-* only
# scores them; without this the harness falls back to hidden truth to decide what to query.
SESSIONS = {"Tern": "sess-tern", "pawn": ["sess-impostor", "sess-impostor-2"]}

# Pre-registered. `mailmap` is false_merge: the fix is the regression. `session` for the borrowed
# actor was pre-registered `insufficient_evidence`, but with Truth-Session written it is `missed_link`
# and observed: the path recovers the trailered borrowed commit and MISSES the untrailered one. Kept
# as the honest outcome rather than dropping the row.
EXPECTED = {
    ("author", "Tern"): "correct",
    ("raw", "Tern"): "correct",
    ("mailmap", "Tern"): "false_merge",
    ("session", "Tern"): "correct",
    ("session", "pawn"): "missed_link",
}


def _git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_DATE=WHEN, GIT_COMMITTER_DATE=WHEN)
    r = subprocess.run(["git", "-C", str(repo), *args],
                       check=True, capture_output=True, text=True, env=env)
    return r.stdout.strip()


def _commit(repo, name, msg, author, truth_actor, session=None, truth_session=None):
    with open(os.path.join(str(repo), name), "w") as f:
        f.write(msg + "\n")
    _git(repo, "add", name)
    args = ["commit", "-q", "-m", msg, f"--author={author}", f"--trailer=Truth-Actor: {truth_actor}"]
    if session:
        args.append(f"--trailer=Agent-Session: {session}")
    if truth_session:
        # Hidden ground truth for the session rows. The PUBLIC Agent-Session may be absent (borrow2)
        # or foreign; Truth-Session is always right, so the session path is a real test of whether
        # the public trailer recovers it -- not a tautology (Codex, via Corrie on #44).
        args.append(f"--trailer=Truth-Session: {truth_session}")
    _git(repo, *args)


def build(repo):
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "O. J. Wilcox")
    _git(repo, "config", "user.email", "oj@example.test")
    # The scheme's real fix, committed at HEAD so the harness's ref-read mailmap finds it.
    with open(os.path.join(str(repo), ".mailmap"), "w") as f:
        f.write(f"Tern <tern@learnwithoj.com> {BORROWED_AUTHOR}\n")
    _git(repo, "add", ".mailmap")
    _git(repo, "commit", "-q", "-m", "add mailmap", "--author=O. J. Wilcox <oj@example.test>",
         "--trailer=Truth-Actor: setup")        # not Tern's, so it can't count as a foreign match

    # Tern's real work: the roster author string, session-trailered.
    _commit(repo, "real.txt", "real work", REAL_AUTHOR, "Tern",
            session="sess-tern", truth_session="sess-tern")
    # The borrower: a folded name, one commit trailered with a foreign session, one with none.
    _commit(repo, "borrow1.txt", "borrowed, trailered", BORROWED_AUTHOR, "pawn",
            session="sess-impostor", truth_session="sess-impostor")
    _commit(repo, "borrow2.txt", "borrowed, no trailer", BORROWED_AUTHOR, "pawn",
            truth_session="sess-impostor-2")
