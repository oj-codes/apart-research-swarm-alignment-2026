#!/usr/bin/env python3
"""Phase 4 case C: two participants write the same Agent-Session value.

Ash and Birch are distinct participants with distinct author lines. Both harnesses write the trailer
`Agent-Session: cc-0001`: Ash's because that is Ash's session, Birch's because it is the harness default
nobody changed. Three commits each, interleaved.

Contract (submission/eval/harness.py): Truth-Actor is Ash / Birch; Truth-Session is cc-0001 for Ash and
birch-default-0001 for Birch, the session that actually ran. SESSIONS declares Ash's public session id;
Birch's true session is not declared, because no public record names it, which is the point.

Predicted outcomes, written before any run of the harness on this file (see ../README.md for the freeze):
  author  / Ash    -> correct.      Distinct names, distinct lines; the participant paths are untouched.
  author  / Birch  -> correct.
  raw     / Ash    -> correct.
  mailmap / Ash    -> correct.      No .mailmap; identical to author.
  session / Ash    -> false_merge.  The path matches the trailer value exactly and finds six commits,
                                    three of them Birch's. The session trailer is an unauthenticated
                                    string, and a collision in it is a false attribution at the session
                                    level, the layer the paper's suite recorded no false merge at.

The combination under test: the one path that survives renames and collisions of the author line has
its own collision mode, and nothing in the record distinguishes a shared session id from a shared session.
Stdlib only. Builds into the repo path it is given; never touches the working repository.
"""
import os
import subprocess
import sys

ASH = ("Ash", "ash@example.test")
BIRCH = ("Birch", "birch@example.test")
PUBLIC_ID = "cc-0001"
ASH_TRUE, BIRCH_TRUE = "cc-0001", "birch-default-0001"

SESSIONS = {"Ash": PUBLIC_ID}

EXPECTED = {
    ("author",  "Ash"): "correct",
    ("author",  "Birch"): "correct",
    ("raw",     "Ash"): "correct",
    ("mailmap", "Ash"): "correct",
    ("session", "Ash"): "false_merge",
}

# (actor, true session) in commit order; every commit writes Agent-Session: cc-0001
PLAN = [(ASH, ASH_TRUE), (BIRCH, BIRCH_TRUE), (ASH, ASH_TRUE),
        (BIRCH, BIRCH_TRUE), (ASH, ASH_TRUE), (BIRCH, BIRCH_TRUE)]


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(repo), env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, who, true_session):
    name, email = who
    with open(os.path.join(repo, f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n}",
            "--trailer", f"Truth-Actor: {name}", "--trailer", f"Truth-Session: {true_session}",
            "--trailer", f"Agent-Session: {PUBLIC_ID}", "--trailer", "Model: model-x"]
    when = f"2026-11-09T{n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)


def build(repo):
    if not os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "init", "-q", "-b", "main")
    for n, (who, true_session) in enumerate(PLAN, start=1):
        _commit(repo, n, who, true_session)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    harness = os.path.join(here, "..", "..", "submission", "eval", "harness.py")
    sys.exit(subprocess.call([sys.executable, harness, os.path.relpath(__file__, os.path.dirname(harness))]))
