#!/usr/bin/env python3
"""Phase 4 case B: two participants share a display name.

Two roster participants are both called "Sage": Sage <sage@example.test> (A) and Sage
<sage@partner.example> (B). A .mailmap row maps A's earlier address to A's current one, the ordinary
rename repair. A writes the Agent-Session trailer; B writes none. A has four commits (one under the old
address), B has three.

Contract (submission/eval/harness.py): Truth-Actor is "Sage" on A's commits and "Sage (partner)" on
B's; Truth-Session is sage-a-0001 / sage-b-0001. Identity for the participant paths is the display
name, which is what the roster's filing key gives a reader. SESSIONS declares both sessions publicly.

Predicted outcomes, written before any run of the harness on this file (see ../README.md for the freeze):
  author  / Sage            -> false_merge.  `--author=Sage` matches both participants' author lines.
  raw     / Sage            -> false_merge.  The raw view compares %an, the name, and both are "Sage";
                                             being unmailmapped does not make it email-aware.
  mailmap / Sage            -> false_merge.  The repair row is irrelevant to B; B still matches by name.
  session / Sage            -> correct.      A's four commits all carry the trailer.
  session / Sage (partner)  -> insufficient_evidence.  B wrote no trailer; the path returns nothing.

The combination under test: a display-name collision defeats all three participant-level paths at once,
including the one the paper calls raw, because every one of them keys on the name the roster treats as
the filing key. Only the session path separates the two, and only where the trailer was written.
Stdlib only. Builds into the repo path it is given; never touches the working repository.
"""
import os
import subprocess
import sys

A_OLD = ("Sage", "sage-old@example.test")
A = ("Sage", "sage@example.test")
B = ("Sage", "sage@partner.example")
SESSION_A, SESSION_B = "sage-a-0001", "sage-b-0001"

SESSIONS = {"Sage": SESSION_A, "Sage (partner)": SESSION_B}

EXPECTED = {
    ("author",  "Sage"): "false_merge",
    ("raw",     "Sage"): "false_merge",
    ("mailmap", "Sage"): "false_merge",
    ("session", "Sage"): "correct",
    ("session", "Sage (partner)"): "insufficient_evidence",
}

# (actor key, author spelling, session, trailer written?) in commit order
PLAN = [("A", A_OLD, SESSION_A, True), ("B", B, SESSION_B, False), ("A", A, SESSION_A, True),
        ("B", B, SESSION_B, False), ("A", A, SESSION_A, True), ("B", B, SESSION_B, False),
        ("A", A, SESSION_A, True)]
TRUTH_ACTOR = {"A": "Sage", "B": "Sage (partner)"}


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(repo), env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, actor, who, session, trailer):
    name, email = who
    with open(os.path.join(repo, f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n}",
            "--trailer", f"Truth-Actor: {TRUTH_ACTOR[actor]}", "--trailer", f"Truth-Session: {session}"]
    if trailer:
        args += ["--trailer", f"Agent-Session: {session}", "--trailer", "Model: model-x"]
    when = f"2026-11-09T{n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)


def build(repo):
    if not os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "init", "-q", "-b", "main")
    for n, (actor, who, session, trailer) in enumerate(PLAN, start=1):
        _commit(repo, n, actor, who, session, trailer)
    with open(os.path.join(repo, ".mailmap"), "w") as f:
        f.write(f"{A[0]} <{A[1]}> {A_OLD[0]} <{A_OLD[1]}>\n")
    _git(repo, "add", ".mailmap")
    when = "2026-11-09T08:00:00Z"
    _git(repo, "commit", "-q", "-m", "mailmap: A's old address", "--trailer", "Truth-Actor: Human",
         "--trailer", "Truth-Session: human",
         env={"GIT_AUTHOR_NAME": "Human", "GIT_AUTHOR_EMAIL": "human@example.test", "GIT_AUTHOR_DATE": when,
              "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when})


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    harness = os.path.join(here, "..", "..", "submission", "eval", "harness.py")
    sys.exit(subprocess.call([sys.executable, harness, os.path.relpath(__file__, os.path.dirname(harness))]))
