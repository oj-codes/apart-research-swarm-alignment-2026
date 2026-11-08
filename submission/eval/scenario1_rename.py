#!/usr/bin/env python3
"""Scenario 1: rename mid-history.

One participant commits under one author string, then changes name and email mid-history. The session
id in the Agent-Session trailer stays the same, because the session did not change; only the name did.
The roster asserts continuity (Named Since predates the rename), and history has no field that says so
unless someone writes a .mailmap line by hand. A second participant commits in between as a decoy.

Contract (Venice, #44): the harness imports this module, calls build(repo) on a scratch repository, runs
each retrieval path for each subject, and compares the verdict to EXPECTED. EXPECTED is the injection
log: known by construction, committed before any run.

Ground truth: participant A ("corrie" after the rename, "wren" before) wrote six commits; B ("tern")
wrote three. The history includes a hand-written .mailmap linking A's two spellings, because the
question this scenario asks is what each path can see once the only link in the record is one a human
wrote. The standalone run below also reports the unmapped case.

Stdlib only. Builds into the repo path it is given; never touches the working repository.
"""
import os
import subprocess
import sys

OLD = ("Wren", "wren@example.test")
NEW = ("Corrie", "corrie@example.test")
DECOY = ("Tern", "tern@example.test")
SESSION_A, SESSION_B = "sess-a-1111", "sess-b-2222"

# path x subject -> verdict. Subjects are queried by their current roster name.
EXPECTED = {
    ("author", "corrie"): "missed_link",            # the three pre-rename commits are invisible to --author=Corrie
    ("mailmap", "corrie"): "correct",               # only because a human wrote the mapping into .mailmap
    ("session", "corrie"): "correct",               # the session id never changed, so the trailer links all six
    ("author", "tern"): "correct",                  # the decoy is unaffected
    ("mailmap", "tern"): "correct",
    ("session", "tern"): "correct",
}

# Everything the harness needs to query: subject -> (display name, email, session id)
SUBJECTS = {
    "corrie": (NEW[0], NEW[1], SESSION_A),
    "tern": (DECOY[0], DECOY[1], SESSION_B),
}


def _git(repo, *args, env=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    if env:
        e.update(env)
    return subprocess.run(["git", *args], cwd=repo, env=e, capture_output=True, text=True, check=True).stdout


def _commit(repo, n, who, session, trailers=True):
    name, email = who
    with open(os.path.join(repo, f"f{n}.txt"), "w") as f:
        f.write(f"{n}\n")
    _git(repo, "add", f"f{n}.txt")
    args = ["commit", "-q", "-m", f"commit {n} by {name}"]
    if trailers:
        args += ["--trailer", f"Agent-Session: {session}"]
    when = f"2026-11-01T{10 + n:02d}:00:00Z"
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": when,
           "GIT_COMMITTER_NAME": "Human", "GIT_COMMITTER_EMAIL": "human@example.test", "GIT_COMMITTER_DATE": when}
    _git(repo, *args, env=env)
    return _git(repo, "rev-parse", "--short", "HEAD").strip()


def build(repo, trailers=True, write_mailmap=True):
    """Write the scripted history into `repo`. Returns ground truth: {subject: set(short shas)}."""
    if not os.path.isdir(os.path.join(repo, ".git")):
        _git(repo, "init", "-q", "-b", "main")
    truth = {"corrie": set(), "tern": set()}
    n = 0
    for _ in range(3):
        n += 1; truth["corrie"].add(_commit(repo, n, OLD, SESSION_A, trailers))
    for _ in range(2):
        n += 1; truth["tern"].add(_commit(repo, n, DECOY, SESSION_B, trailers))
    for _ in range(3):
        n += 1; truth["corrie"].add(_commit(repo, n, NEW, SESSION_A, trailers))
    n += 1; truth["tern"].add(_commit(repo, n, DECOY, SESSION_B, trailers))
    if write_mailmap:
        with open(os.path.join(repo, ".mailmap"), "w") as f:
            f.write(f"{NEW[0]} <{NEW[1]}> {OLD[0]} <{OLD[1]}>\n")
    return truth


# --- standalone self-check, so the scenario is runnable before and beside the harness ---------------

def _by_author(repo, name, mailmap):
    args = ["log", "--format=%h", f"--author={name}"] + (["--use-mailmap"] if mailmap else ["--no-use-mailmap"])
    return set(_git(repo, *args).split())


def _by_session(repo, session):
    found = set()
    for line in _git(repo, "log", "--format=%h%x1f%(trailers:key=Agent-Session,valueonly)").splitlines():
        h, _, s = line.partition("\x1f")
        if s.strip() == session:
            found.add(h)
    return found


def _verdict(found, mine, others, evidence=True):
    if not evidence:
        return "insufficient_evidence"
    if found & others:
        return "false_merge"
    if found == mine:
        return "correct"
    if found and found < mine:
        return "missed_link"
    return "insufficient_evidence"


def _run(repo, truth, trailers):
    rows = []
    for subject, (name, _email, session) in SUBJECTS.items():
        mine = truth[subject]
        others = set().union(*(v for k, v in truth.items() if k != subject))
        rows.append(("author", subject, _verdict(_by_author(repo, name, False), mine, others)))
        rows.append(("mailmap", subject, _verdict(_by_author(repo, name, True), mine, others)))
        rows.append(("session", subject, _verdict(_by_session(repo, session), mine, others, evidence=trailers)))
    return rows


def main():
    import shutil, tempfile
    ok = True
    print("scenario 1: rename mid-history (A: Wren -> Corrie, one session; decoy: Tern)")
    repo = tempfile.mkdtemp(prefix="eval-s1-")
    truth = build(repo)
    print(f"{'path':8} {'subject':8} {'observed':22} {'expected':22}")
    for path, subject, observed in _run(repo, truth, trailers=True):
        expected = EXPECTED[(path, subject)]
        ok &= observed == expected
        print(f"{path:8} {subject:8} {observed:22} {expected:22}{'' if observed == expected else '  <-- MISMATCH'}")
    shutil.rmtree(repo)
    print("\nvariants, reported not pre-registered:")
    repo = tempfile.mkdtemp(prefix="eval-s1-")
    truth = build(repo, write_mailmap=False)
    v = dict(((p, s), o) for p, s, o in _run(repo, truth, trailers=True))
    print(f"  no .mailmap written:   mailmap/corrie -> {v[('mailmap', 'corrie')]}  (the roster's continuity claim is not in the record)")
    shutil.rmtree(repo)
    repo = tempfile.mkdtemp(prefix="eval-s1-")
    truth = build(repo, trailers=False)
    v = dict(((p, s), o) for p, s, o in _run(repo, truth, trailers=False))
    print(f"  no trailers written:   session/corrie -> {v[('session', 'corrie')]}  (pre-convention commits)")
    shutil.rmtree(repo)
    print("\nresult:", "all pre-registered outcomes as expected" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
