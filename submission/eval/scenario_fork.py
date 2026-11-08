#!/usr/bin/env python3
"""Scenario 3: credential fork. One participant, two author spellings inside one session.

Shape taken from the real 8 November window (seven commits, two spellings interleaved, one commit
trailered, PR #43). The spellings are synthetic so the .mailmap under test has never seen them:
replaying the real spellings would score the mailmap written against exactly those spellings
seventeen hours earlier (Corrie, #44). build() writes a .mailmap listing the participant's FIRST
alternate spelling, the way a real one is written after the first fork is noticed; the window then
introduces a SECOND spelling, a new name on a noreply address, that the mailmap does not list.

Contract (harness.py, #46): build(repo) writes the history; every commit carries Truth-Actor and
Truth-Session trailers the retrieval paths never read; EXPECTED is the injection log, committed
before any run. Identity is the author name for author/mailmap/raw and the session id for session.

Pre-registered, with the reason:
  author, raw / Wren -> missed_link. The canonical spelling is on 2 of 7.
  mailmap / Wren     -> missed_link. The mailmap recovers the listed alternate (5 of 7) and cannot
      recover the spelling it has never seen. A mailmap is a lookup of spellings already noticed.
  session / cron-watch-0001  -> correct. The one commit that wrote the trailer is found.
  session / interactive-0001 -> insufficient_evidence. Six commits, no trailer, no signal.

Pre-registration note, kept because it is the error this eval exists to catch: the first draft made
the unseen spelling `Wren <noreply>`, same name, new email, and expected mailmap -> missed_link. The
check returned correct, because --author matches on the name and the name had not changed. The
expectation was wrong, not the retrieval. The unseen spelling is now a new NAME.

Stdlib only. Builds into the repo path it is given; never touches the working repository.
"""
import os
import subprocess
import sys

CANON = ("Wren", "wren@example.test")
LISTED = ("wren-theridge", "wren@example.test")                        # in the mailmap
UNSEEN = ("wren-ridge", "123+wren-ridge@users.noreply.example.test")   # not in the mailmap
CRON, INTERACTIVE = "cron-watch-0001", "interactive-0001"

EXPECTED = {
    ("author",  CANON[0]): "missed_link",            # 2 of 7
    ("raw",     CANON[0]): "missed_link",            # 2 of 7
    ("mailmap", CANON[0]): "missed_link",            # 5 of 7; the unseen spelling is not listed
    ("session", CRON): "correct",                    # the one trailered commit
    ("session", INTERACTIVE): "insufficient_evidence",  # six commits, no trailer written
}

# (spelling, session) in commit order; only the cron commit writes a trailer
WINDOW = [(CANON, INTERACTIVE), (LISTED, INTERACTIVE), (UNSEEN, INTERACTIVE), (LISTED, INTERACTIVE),
          (CANON, CRON), (UNSEEN, INTERACTIVE), (LISTED, INTERACTIVE)]


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(repo), env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, who, session):
    name, email = who
    with open(os.path.join(repo, f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n} as {name}",
            "--trailer", f"Truth-Actor: {CANON[0]}", "--trailer", f"Truth-Session: {session}"]
    if session == CRON:
        args += ["--trailer", f"Agent-Session: {session}", "--trailer", "Model: model-x"]
    when = f"2026-11-08T{10 + n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)


def build(repo):
    """Write the scripted history and the pre-fork .mailmap into `repo`."""
    if not os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "init", "-q", "-b", "main")
    for n, (who, session) in enumerate(WINDOW, start=1):
        _commit(repo, n, who, session)
    with open(os.path.join(repo, ".mailmap"), "w") as f:
        f.write(f"{CANON[0]} <{CANON[1]}> {LISTED[0]} <{LISTED[1]}>\n")
    _git(repo, "add", ".mailmap")
    _git(repo, "commit", "-q", "-m", "mailmap after the first fork was noticed",
         "--trailer", f"Truth-Actor: Human", "--trailer", "Truth-Session: human",
         env={"GIT_AUTHOR_NAME": "Human", "GIT_AUTHOR_EMAIL": "human@example.test",
              "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test",
              "GIT_AUTHOR_DATE": "2026-11-08T18:00:00Z", "GIT_COMMITTER_DATE": "2026-11-08T18:00:00Z"})


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.exit(subprocess.call([sys.executable, os.path.join(here, "harness.py"), "scenario_fork"]))
