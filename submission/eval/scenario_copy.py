#!/usr/bin/env python3
"""Scenario 2: copy. Two sessions hold one name at the same time.

One participant, "Tern", runs two sessions at once (sess-a and sess-b), both committing under the
same author string. Four of the six commits carry an Agent-Session trailer; two do not, one from
each session, which is the paper's bimodal trailer adoption in miniature.

Contract (harness.py, #46): build(repo) writes the history into a scratch repo; every commit carries
Truth-Actor and Truth-Session trailers that the retrieval paths never read; EXPECTED is the injection
log, `(path, identity) -> outcome`, committed before any harness run. Identity is the author name for
author/mailmap/raw and the session id for session.

Expected outcomes, with the reason. Committed with the file; the revision history is in git:
  author, mailmap, raw / Tern -> correct. At the participant level the copy is invisible: every
      commit is Tern's and every path says so. Nothing here can tell a reader there were two.
  session / sess-a-0001, sess-b-0002 -> missed_link. The trailer is the only path that separates the
      sessions, and it finds exactly the commits that wrote it: 2 of 3 for each. The missed one per
      session is the untrailered commit, the pre-convention case.

Stdlib only. Builds into the repo path it is given; never touches the working repository.
"""
import os
import subprocess
import sys

NAME, EMAIL = "Tern", "tern@example.test"
SESSION_A, SESSION_B = "sess-a-0001", "sess-b-0002"

EXPECTED = {
    ("author",  NAME): "correct",
    ("mailmap", NAME): "correct",
    ("raw",     NAME): "correct",
    ("session", SESSION_A): "missed_link",   # 2 of sess-a's 3 commits carry the trailer
    ("session", SESSION_B): "missed_link",   # 2 of sess-b's 3 commits carry the trailer
}

# (session, Agent-Session trailer written?) in commit order
PLAN = [(SESSION_A, True), (SESSION_B, True), (SESSION_A, False),
        (SESSION_B, True), (SESSION_B, False), (SESSION_A, True)]


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(repo), env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, session, trailer):
    with open(os.path.join(repo, f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n} from {session}",
            "--trailer", f"Truth-Actor: {NAME}", "--trailer", f"Truth-Session: {session}"]
    if trailer:
        args += ["--trailer", f"Agent-Session: {session}", "--trailer", "Model: model-x"]
    when = f"2026-11-08T{10 + n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": EMAIL, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)


def build(repo):
    """Write the scripted history into `repo`. Ground truth is in the commits' Truth-* trailers."""
    if not os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "init", "-q", "-b", "main")
    for n, (session, trailer) in enumerate(PLAN, start=1):
        _commit(repo, n, session, trailer)


if __name__ == "__main__":
    # Standalone: run this scenario through the harness beside it.
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(subprocess.call([sys.executable, os.path.join(here, "harness.py"), "scenario_copy"]))
