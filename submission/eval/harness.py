#!/usr/bin/env python3
"""Run the identity scheme's own retrieval over scripted histories with known ground truth.

    python3 submission/eval/harness.py                  # every scenario in this directory
    python3 submission/eval/harness.py scenario_copy    # one of them

A scenario module supplies `build(repo)`, which writes a scripted git history into a scratch
directory, and `EXPECTED`, the injection log: `(path, identity) -> outcome`. EXPECTED is committed
with the scenario *before* any run, so the diff order is the pre-registration -- a scoring rule
written after seeing a confusion matrix is not a scoring rule.

The harness never decides what *should* happen. It runs each retrieval path, compares the shas it
got against the shas the scenario says belong to that identity, and classifies. A scenario that
expects the scheme to fail says so in EXPECTED; `scenario_impersonation` expects `false_merge` and
passes only when the scheme false-merges.

WHY THIS FILE IS SO CAREFUL ABOUT ITS OWN QUERIES
-------------------------------------------------
An eval of a retrieval scheme, scored by a buggy retrieval harness, reports a clean confusion
matrix that is wrong. Six ways to do that were hit for real during this sprint -- four of them by
the author of this file, one of them four hours after reporting it in someone else's code:

  1. `git log --use-mailmap` reads `.mailmap` from the WORKING TREE, not from the ref being logged.
     Run from a worktree without one, it silently does not mailmap. -> we pass `-c mailmap.blob`.
  2. `--grep 'Co-Authored-By'` is not a trailer query. It matched the commit that BANNED model
     co-authorship. -> we read `%(trailers:key=...)`.
  3. `--no-merges` hides merge commits. A spelling reported as "zero across every ref" had two.
     -> merge inclusion is an explicit argument, never a default we forget.
  4. `--author` is a case-sensitive regex. `--author=Auran` misses `auran-theclearing`.
     -> the raw path states its case-sensitivity; it is part of what is being measured.
  5. Globbing a directory sweeps in files that are not findings (a README's example frontmatter).
     -> scenarios address commits by sha, never by path glob.
  6. `%aN` applies the mailmap EVEN under `--no-use-mailmap`; the raw view needs `%an`.
     (Found by Tern while drafting scenarios 2 and 3.)

`test_harness.py` fixes each of these as a failing test: remove a guard and a test goes red.
"""
import argparse
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

OUTCOMES = ("correct", "false_merge", "missed_link", "insufficient_evidence")

HERE = pathlib.Path(__file__).resolve().parent


def git(repo, *args, mailmap_ref=None):
    """Run git in `repo`. With mailmap_ref, read .mailmap FROM THE REF -- trap 1."""
    cfg = ["-c", f"mailmap.blob={mailmap_ref}:.mailmap"] if mailmap_ref else []
    r = subprocess.run(["git", "-C", str(repo), *cfg, *args],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def shas(out):
    return {line.split()[0] for line in out.splitlines() if line.strip()}


# --- retrieval paths: what the scheme actually offers a reader ----------------------

def path_author(repo, identity, merges=False):
    """Plain `git log --author=<name>` -- the UNASSISTED path, so `--no-use-mailmap` is required.

    TRAP 7, and the worst of them. `log.mailmap` defaults to TRUE, so a bare `git log --author=X`
    silently applies any `.mailmap` in the working tree. Measured on scenario1_rename:

        git log --author=Corrie                      -> 6   (3 of them authored "Wren")
        git log --author=Corrie --no-use-mailmap     -> 3

    Without the flag the "before mailmap" column equals the "after" column, every rename and fork
    scenario scores `correct`, and the eval reports the identity scheme as flawless. An eval whose
    control condition is silently the treatment condition cannot fail.
    """
    args = ["log", "--no-use-mailmap", "--format=%H %an"]
    if not merges:
        args.append("--no-merges")          # trap 3: explicit, never implicit
    args += [f"--author={identity}"]
    return shas(git(repo, *args))


def path_mailmap(repo, identity, merges=False, mailmap_ref="HEAD"):
    """`--use-mailmap`, with .mailmap read from the ref rather than the working tree -- trap 1."""
    args = ["log", "--use-mailmap", "--format=%H %aN"]
    if not merges:
        args.append("--no-merges")
    args += [f"--author={identity}"]
    return shas(git(repo, *args, mailmap_ref=mailmap_ref))


def sessions_of(repo, identity, scenario=None):
    """Which Agent-Session values belong to `identity`, per the scenario's declared mapping.

    A scenario may expose `SESSIONS = {'corrie': ['sess-a', ...]}`. Without one the identity is
    taken to be a session id itself. The mapping is scenario data, not ground truth -- a reader
    holding one of someone's commits knows its session; that is the premise of this path.
    """
    if scenario:
        # Rill's published shape: SUBJECTS = {key: (display_name, email, session_id)}
        subs = getattr(scenario, "SUBJECTS", None)
        if subs and identity in subs:
            return [subs[identity][2]]
        declared = getattr(scenario, "SESSIONS", None)
        if declared:
            v = declared.get(identity, [])
            return [v] if isinstance(v, str) else list(v)
    return [identity]


def path_session(repo, identity, merges=False, scenario=None):
    """Agent-Session trailer, parsed as a trailer -- trap 2. Empty set means no signal at all."""
    wanted = sessions_of(repo, identity, scenario)
    args = ["log", "--format=%H%x1f%(trailers:key=Agent-Session,valueonly)%x1e"]
    if not merges:
        args.append("--no-merges")
    out = git(repo, *args)
    found = set()
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        sha, _, val = rec.partition("\x1f")
        if val.strip() and any(w and w in val for w in wanted):
            found.add(sha.strip())
    return found


def path_raw(repo, identity, merges=False):
    """The unmailmapped view. Uses %an, NOT %aN -- trap 6, Tern's."""
    args = ["log", "--no-use-mailmap", "--format=%H %an"]
    if not merges:
        args.append("--no-merges")
    out = git(repo, *args)
    return {ln.split()[0] for ln in out.splitlines()
            if ln.strip() and ln.split(maxsplit=1)[1] == identity}


PATHS = {
    "author": path_author,
    "mailmap": path_mailmap,
    "session": path_session,
    "raw": path_raw,
}


# --- ground truth: carried by the commits themselves, never asserted alongside them ---

# Truth is always "whose commits are these" -- Truth-Actor -- for every path. The paths differ in
# HOW they try to recover that, not in what the right answer is. Scoring the session path against
# Truth-Session would ask "did we find the session we asked for", which is trivially yes and
# measures nothing.
TRUTH_KEYS = {p: "Truth-Actor" for p in ("author", "mailmap", "raw", "session")}


def truth(repo, key, identity, merges=False):
    """Shas whose `Truth-Actor`/`Truth-Session` trailer names `identity` (Tern's design).

    Ground truth lives in trailers the retrieval paths never read, so it is known by
    construction and cannot drift from the history that `build()` actually wrote. A `build()`
    that returned its own answer could disagree with the commits it made and nothing would
    notice; this cannot.
    """
    args = ["log", f"--format=%H%x1f%(trailers:key={key},valueonly)%x1e"]
    if not merges:
        args.append("--no-merges")
    found = set()
    for rec in git(repo, *args).split("\x1e"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        sha, _, val = rec.partition("\x1f")
        if val.strip() == identity:
            found.add(sha.strip())
    return found


# --- scoring rule: pre-registered, and deliberately boring --------------------------

def classify(found, truth):
    """Compare retrieved shas against the shas the scenario says belong to that identity.

    Precedence is fixed here, before any scenario runs:
      no signal at all            -> insufficient_evidence
      retrieved something foreign -> false_merge      (wrong answer beats incomplete answer)
      missed something of theirs  -> missed_link
      exact                       -> correct

    false_merge outranks missed_link because confidently attributing someone else's commit is a
    worse failure for a provenance scheme than failing to find one of your own.
    """
    if not found:
        return "insufficient_evidence"
    if found - truth:
        return "false_merge"
    if truth - found:
        return "missed_link"
    return "correct"


# --- runner -------------------------------------------------------------------------

def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_scenario(mod, repo):
    """Returns [(path, identity, expected, got, ok)] -- never decides what SHOULD happen."""
    mod.build(repo)
    rows = []
    for (path, identity), expected in sorted(mod.EXPECTED.items()):
        if path not in PATHS:
            raise KeyError(f"unknown retrieval path {path!r}; known: {sorted(PATHS)}")
        if expected not in OUTCOMES:
            raise ValueError(f"{path}/{identity}: {expected!r} not in {OUTCOMES}")
        fn = PATHS[path]
        kw = {"scenario": mod} if path == "session" else {}
        want = truth(repo, TRUTH_KEYS[path], identity)
        if not want:
            raise ValueError(
                f"{path}/{identity}: no commit carries {TRUTH_KEYS[path]}: {identity}. "
                "Ground truth must be written by build() as a trailer, not assumed.")
        got = classify(fn(repo, identity, **kw), want)
        rows.append((path, identity, expected, got, got == expected))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenario", nargs="*", help="module names; default is every scenario_*.py here")
    a = ap.parse_args()

    names = a.scenario or sorted(p.stem for p in HERE.glob("scenario*.py"))
    if not names:
        print("no scenarios found", file=sys.stderr)
        return 2

    rows, failures = [], 0
    for name in names:
        mod = load(name)
        with tempfile.TemporaryDirectory(prefix="idev-") as d:
            for r in run_scenario(mod, pathlib.Path(d)):
                rows.append((name, *r))
                failures += not r[4]

    w = max(len(r[0]) for r in rows)
    print(f"{'scenario':{w}}  {'path':8}  {'identity':12}  {'expected':22}  {'got':22}")
    print("-" * (w + 74))
    for name, path, ident, exp, got, ok in rows:
        print(f"{name:{w}}  {path:8}  {ident:12}  {exp:22}  {got:22}  {'' if ok else '<-- MISMATCH'}")

    tally = {o: sum(1 for r in rows if r[4] == o) for o in OUTCOMES}
    print("\noutcomes as run: " + ", ".join(f"{o}={tally[o]}" for o in OUTCOMES))
    if not tally["insufficient_evidence"]:
        print("note: zero insufficient_evidence verdicts — a scheme that always decides cannot "
              "say 'I don't know'. Check that a no-signal case is actually covered.")
    print(f"\n{len(rows) - failures}/{len(rows)} matched the pre-registered expectation.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
