#!/usr/bin/env python3
"""Scenario 4 — a borrowed author line. The negative control, and the one pre-committed failure.

CONTRACT (for the eval harness; two symbols, so a scenario drops in without touching the harness):

    build(repo) -> set[str]      # write the scripted history into `repo`; return the ground-truth shas
    EXPECTED                     # {("path", "identity"): outcome}, committed BEFORE the run

`build` is the injection log: the correct answer is known by construction, so the thing under test is
the retrieval tooling, not our hand-labelling. `EXPECTED` is pre-registered with the file.

THE SCENARIO. One roster identity (`tern`). A second actor **borrows the author line** under a name the
repo's `.mailmap` folds into `Tern`, so nothing in the author string is `tern` at all.

WHY IT IS THE GIFT. Plain retrieval is **correct** here — `--author=tern` claims only the real work.
The scheme's documented fix, the `.mailmap`, is what turns that correct answer into a **false merge**:
canonicalising is exactly the wrong move when two actors share a name. The only field that can
separate them is `Agent-Session`, and one borrowed commit has none — so the honest verdict there is
`insufficient_evidence`, not a decision. It demonstrates provenance-not-authentication instead of
asserting it, and the failure is owned by the fix, not the absence of one.

    python3 submission/eval/scenarios/borrowed_author.py

stdlib only, no model calls, seconds. Deterministic (fixed dates, no globbing).
"""
import os
import subprocess
import sys
import tempfile

TARGET = "tern"
TARGET_AUTHOR = "Tern <tern@learnwithoj.com>"
BORROWED_AUTHOR = "pawn <pawn@learnwithoj.com>"     # folded to Tern by the scenario's .mailmap
TARGET_SESSION = "tern-session"
WHEN = "2026-11-08T10:00:00+00:00"

# Pre-registered. `author` is `correct` and `mailmap` is `false_merge`: the fix is the regression.
# `session` is `insufficient_evidence` — the untrailered borrowed commit is a candidate it cannot decide.
EXPECTED = {
    ("author", "tern"): "correct",
    ("mailmap", "tern"): "false_merge",
    ("session", "tern"): "insufficient_evidence",
}


def _git(repo, *args):
    env = dict(os.environ, GIT_AUTHOR_DATE=WHEN, GIT_COMMITTER_DATE=WHEN)
    return subprocess.run(["git", "-C", repo, *args],
                          check=True, capture_output=True, text=True, env=env).stdout.strip()


def _commit(repo, name, msg, author, trailers=()):
    with open(os.path.join(repo, name), "w") as f:
        f.write(msg + "\n")
    _git(repo, "add", name)
    args = ["commit", "-q", "-m", msg, f"--author={author}"]
    args += [f"--trailer={t}" for t in trailers]
    _git(repo, *args)
    return _git(repo, "rev-parse", "HEAD")


def build(repo):
    """Injection log — what is true by construction. Returns the ground-truth sha set."""
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "O. J. Wilcox")
    _git(repo, "config", "user.email", "oj@example.test")
    # The scheme's real fix, copied in so the scenario tests it rather than assumes it.
    with open(os.path.join(repo, ".mailmap"), "w") as f:
        f.write(f"Tern <tern@learnwithoj.com> {BORROWED_AUTHOR}\n")
    _git(repo, "add", ".mailmap")
    _git(repo, "commit", "-q", "-m", "add mailmap")            # setup commit, not the target

    # The real identity's work: the roster author string, session-trailered.
    truth = {_commit(repo, "real.txt", "real work", TARGET_AUTHOR,
                     [f"Agent-Session: {TARGET_SESSION}"])}
    # The borrower, commit 1: folded name, different session.
    _commit(repo, "borrow1.txt", "borrowed, trailered", BORROWED_AUTHOR,
            ["Agent-Session: impostor-session"])
    # The borrower, commit 2: folded name, NO trailer.
    _commit(repo, "borrow2.txt", "borrowed, no trailer", BORROWED_AUTHOR)
    return truth


# --- minimal runner, so this is runnable before the shared harness lands ---

def _candidates(repo):
    """(sha, linked?, undecidable?) for every commit the author string could claim, mailmapped.

    NOTE the %aN/%aE, not %an/%ae: `--use-mailmap` only redirects the UPPERCASE placeholders. A raw
    %an compares the un-canonicalised name and silently finds nothing — the same class of trap as
    `--use-mailmap` reading the working tree rather than the ref's mailmap.
    """
    fmt = "%H\t%aN <%aE>\t%(trailers:key=Agent-Session,valueonly)"
    for line in _git(repo, "log", "--no-merges", "--use-mailmap", f"--format={fmt}").splitlines():
        sha, _, rest = line.partition("\t")
        author, _, sess = rest.partition("\t")
        if author.strip() != TARGET_AUTHOR:
            continue
        sess = sess.strip()
        yield sha, (sess == TARGET_SESSION), (sess == "")


def _retrieve(repo, path):
    if path in ("author", "mailmap"):
        opt = "--use-mailmap" if path == "mailmap" else "--no-use-mailmap"
        out = _git(repo, "log", "--no-merges", opt, f"--author={TARGET}", "--format=%H")
        return set(out.split()), set()
    if path == "session":
        linked = {sha for sha, ok, _ in _candidates(repo) if ok}
        unknown = {sha for sha, _, und in _candidates(repo) if und}
        return linked, unknown
    raise SystemExit(f"unknown path {path!r}")


def verdict(repo, path, truth):
    linked, unknown = _retrieve(repo, path)
    if unknown:
        # A candidate commit the path cannot place. It may or may not be the target, so the honest
        # output is not a decision — this is the pre-registered `insufficient_evidence`.
        return "insufficient_evidence"
    if linked == truth:
        return "correct"
    if truth < linked:
        return "false_merge"
    if linked < truth:
        return "missed_link"
    return "false_merge"


def main():
    repo = tempfile.mkdtemp(prefix="eval-borrowed-")
    truth = build(repo)
    ok = True
    print(f"scenario: borrowed author line | identity '{TARGET}' | truth = {len(truth)} commit(s)")
    print(f"expected: {EXPECTED}\n")
    for (path, _ident), want in EXPECTED.items():
        got = verdict(repo, path, truth)
        linked, _ = _retrieve(repo, path)
        ok &= (got == want)
        print(f"  {path:8} linked={len(linked)}  verdict={got:22} expected={want:22} "
              f"{'PASS' if got == want else 'FAIL'}")
    print("\n" + ("all pre-registered outcomes reproduced" if ok else "MISMATCH — see FAIL rows"))
    print("note: `author` is correct and `mailmap` is not — the fix turns a correct answer into a "
          "false merge. That is the negative control.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
