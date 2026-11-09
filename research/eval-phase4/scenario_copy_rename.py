#!/usr/bin/env python3
"""Phase 4 case A: copy plus rename. Two sessions under one name; the name changes mid-window.

One participant, "Wren", runs two sessions at once (sess-p, sess-q). After commit 3 the participant
renames to "Linnet" with a new email; no .mailmap row is ever written. Five of six commits carry the
Agent-Session trailer; the one without it is sess-q's, after the rename.

Contract (submission/eval/harness.py): build(repo) writes the history; every commit carries Truth-Actor
("Wren" throughout, the rename does not change who acted) and Truth-Session; EXPECTED is the injection
log. Identity for author/mailmap/raw is the pre-rename name, which is what a reader holding the roster
row would query; identity for session is the session id.

Predicted outcomes, written before any run of the harness on this file (see ../README.md for the freeze):
  author  / Wren    -> missed_link.  `--author=Wren` is a regex on the author line; the post-rename
                                      commits say Linnet and are missed. Trailers do not help this path.
  mailmap / Wren    -> missed_link.  No row maps Linnet to Wren; identical to author.
  raw     / Wren    -> missed_link.  Exact %an equality; same three commits.
  session / sess-p  -> correct.      All three sess-p commits carry the trailer; the rename is invisible
                                      to a path that never reads the author line.
  session / sess-q  -> missed_link.  Two of three; the untrailered post-rename commit is lost.

The combination under test: a rename defeats every participant-level path regardless of trailers, and a
missing trailer defeats the session path regardless of the rename. Neither path covers the other's gap.
Stdlib only. Builds into the repo path it is given; never touches the working repository.
"""
import os
import subprocess
import sys

OLD = ("Wren", "wren@example.test")
NEW = ("Linnet", "linnet@example.test")
SESSION_P, SESSION_Q = "sess-p-0001", "sess-q-0002"

EXPECTED = {
    ("author",  "Wren"): "missed_link",
    ("mailmap", "Wren"): "missed_link",
    ("raw",     "Wren"): "missed_link",
    ("session", SESSION_P): "correct",
    ("session", SESSION_Q): "missed_link",
}

# (session, author spelling, Agent-Session trailer written?) in commit order; rename after commit 3
PLAN = [(SESSION_P, OLD, True), (SESSION_Q, OLD, True), (SESSION_P, OLD, True),
        (SESSION_Q, NEW, True), (SESSION_P, NEW, True), (SESSION_Q, NEW, False)]


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(repo), env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, session, who, trailer):
    name, email = who
    with open(os.path.join(repo, f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n} from {session}",
            "--trailer", f"Truth-Actor: {OLD[0]}", "--trailer", f"Truth-Session: {session}"]
    if trailer:
        args += ["--trailer", f"Agent-Session: {session}", "--trailer", "Model: model-x"]
    when = f"2026-11-09T{n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)


def build(repo):
    if not os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "init", "-q", "-b", "main")
    for n, (session, who, trailer) in enumerate(PLAN, start=1):
        _commit(repo, n, session, who, trailer)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    harness = os.path.join(here, "..", "..", "submission", "eval", "harness.py")
    sys.exit(subprocess.call([sys.executable, harness, os.path.relpath(__file__, os.path.dirname(harness))]))
