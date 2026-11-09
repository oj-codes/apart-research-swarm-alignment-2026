#!/usr/bin/env python3
"""Scenario: rename mid-history.

One participant commits under one author string, then changes name and email mid-history. The session
id in the Agent-Session trailer stays the same, because the session did not change; only the name did.
The roster asserts continuity (Named Since predates the rename), and history has no field that says so
unless someone writes a .mailmap line by hand. A second participant commits in between as a decoy.

Contract (Venice and Corrie, #44, #46): the harness calls build(repo) on an empty scratch directory,
then for each (path, identity) in EXPECTED runs the retrieval path and scores it against ground truth
carried by the commits themselves: Truth-Actor and Truth-Session trailers that no retrieval path reads.
EXPECTED is the injection log, written before the first run. Main holds one commit for this file (6873fa2),
made after both runs described below, so the diff order does not prove that; what the record does show is
a row left at its original wrong value rather than revised, which is the evidence the order claim has.

Identities are the display name on every path; SESSIONS tells the session path which ids are theirs. The .mailmap is committed, because the harness reads it from HEAD, not the working tree.
Stdlib only. Writes into the directory it is given; never touches the working repository.

RUNS UNDER THE HARNESS (Rill, 2026-11-08). Under the harness at its first revision in PR #46, 7 of 8 rows
matched: ("author", "Corrie") was written as missed_link and came back correct, because that revision
let git apply the checked-out .mailmap to `--author` matching (log.mailmap defaults to true), so the
"author" path was already mapped once the file existed and only "raw" (%an) was the unmapped view. The
original value was left as written rather than changed after the fact. Under the harness at
de73de6, which separates the paths, all 8 rows match. Both runs are recorded here because the first one
measured the author's wrong model of a git default, which is the kind of thing this paper reports.
scenario_rename_untrailered covers the same history with no .mailmap and no trailers.
"""
import os
import subprocess
import sys

OLD = ("Wren", "wren@example.test")
NEW = ("Corrie", "corrie@example.test")
DECOY = ("Tern", "tern@example.test")
SESSION_A, SESSION_B = "sess-a-1111", "sess-b-2222"

EXPECTED = {
    ("author", "Corrie"): "missed_link",          # three pre-rename commits are invisible to --author=Corrie
    ("raw", "Corrie"): "missed_link",             # the unmailmapped view sees the same three
    ("mailmap", "Corrie"): "correct",             # only because a human wrote the mapping and committed it
    ("session", "Corrie"): "correct",             # the session id never changed, so the trailer links all six
    ("author", "Tern"): "correct",                # the decoy is unaffected on every path
    ("raw", "Tern"): "correct",
    ("mailmap", "Tern"): "correct",
    ("session", "Tern"): "correct",
}

# which Agent-Session values belong to each identity: scenario data the session path needs (harness.py)
SESSIONS = {"Corrie": [SESSION_A], "Tern": [SESSION_B]}


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=str(repo), env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, who, session, actor, trailers=True):
    name, email = who
    with open(os.path.join(str(repo), f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n} by {name}",
            "--trailer", f"Truth-Actor: {actor}", "--trailer", f"Truth-Session: {session}"]
    if trailers:
        args += ["--trailer", f"Agent-Session: {session}"]
    when = f"2026-11-01T{10 + n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)
    return _git(repo, "rev-parse", "HEAD").strip()


def build(repo, trailers=True, write_mailmap=True):
    """Write the scripted history into `repo` (an empty directory or an existing repo)."""
    if not os.path.isdir(os.path.join(str(repo), ".git")):
        _git(repo, "init", "-q", "-b", "main")
    n = 0
    for _ in range(3):
        n += 1; _commit(repo, n, OLD, SESSION_A, actor=NEW[0], trailers=trailers)      # A, old name
    for _ in range(2):
        n += 1; _commit(repo, n, DECOY, SESSION_B, actor=DECOY[0], trailers=trailers)  # decoy
    for _ in range(3):
        n += 1; _commit(repo, n, NEW, SESSION_A, actor=NEW[0], trailers=trailers)      # A, renamed
    n += 1; _commit(repo, n, DECOY, SESSION_B, actor=DECOY[0], trailers=trailers)
    if write_mailmap:
        # the only link between the two spellings in the whole record, written and committed by a human
        with open(os.path.join(str(repo), ".mailmap"), "w") as f:
            f.write(f"{NEW[0]} <{NEW[1]}> {OLD[0]} <{OLD[1]}>\n")
        _git(repo, "add", ".mailmap")
        env = {"GIT_AUTHOR_NAME": "Human", "GIT_AUTHOR_EMAIL": "human@example.test",
               "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test",
               "GIT_AUTHOR_DATE": "2026-11-02T10:00:00Z", "GIT_COMMITTER_DATE": "2026-11-02T10:00:00Z"}
        _git(repo, "commit", "-q", "-m", "mailmap: link the two spellings, by hand", env=env)


if __name__ == "__main__":
    # Standalone: run under the harness if it sits beside this file, else just build and show the log.
    import tempfile, pathlib
    here = pathlib.Path(__file__).resolve().parent
    if (here / "harness.py").exists():
        sys.exit(subprocess.call([sys.executable, str(here / "harness.py"), "scenario_rename"]))
    d = tempfile.mkdtemp(prefix="s1-")
    build(d)
    print(_git(d, "log", "--format=%h %an <%ae>  %(trailers:key=Agent-Session,valueonly)"))
