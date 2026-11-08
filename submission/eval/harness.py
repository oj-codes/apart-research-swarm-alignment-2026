#!/usr/bin/env python3
"""Run the identity scheme's own retrieval over scripted histories with known ground truth.

    python3 submission/eval/harness.py                  # every scenario in this directory
    python3 submission/eval/harness.py scenario_copy    # one of them

A scenario module supplies `build(repo)`, which writes a scripted git history into a scratch
directory, and `EXPECTED`, the injection log: `(path, identity) -> outcome`.

PRE-REGISTRATION, AND WHAT THIS TOOL CAN ACTUALLY ESTABLISH
-----------------------------------------------------------
An earlier version of this docstring said "EXPECTED is committed before any run, so the diff order
is the pre-registration." **The harness did not establish that and simply read whatever EXPECTED
currently said** (O.J., #46). A scenario author who edited EXPECTED after seeing a matrix would
have got a clean 31/31 and no warning -- the exact failure the claim was supposed to rule out.

So the harness now reports, per scenario, the commit that last touched the file and whether the
working copy is dirty. That makes the ordering *checkable*: compare the EXPECTED commit date
against when results were first published. It does not prove nobody peeked -- no tool can -- but
it replaces an assertion with evidence a reader can verify, and a dirty file is reported as
UNVERIFIED rather than silently scored.

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
        # EXACT comparison of complete parsed values. `w in val` made the harness itself
        # false-merge: querying `sess-a` matched a foreign `sess-ab` (Codex, #46). A harness that
        # manufactures the outcome it is measuring is worse than no harness.
        vals = {v.strip() for v in val.splitlines() if v.strip()}
        if vals & set(wanted):
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

# Each path is scored against the hidden truth for the question IT asks. The author-shaped paths
# ask "whose commits are these" (Truth-Actor); the session path asks "which session wrote these"
# (Truth-Session).
#
# I briefly scored every path against Truth-Actor, reasoning that Truth-Session would trivially
# agree with the thing being queried. Codex corrected it: the PUBLIC `Agent-Session` trailer can
# be missing or wrong, while `Truth-Session` is hidden and always right -- so comparing them is a
# real test, not a tautology. Tern's original design was correct and this reverts to it.
TRUTH_KEYS = {"author": "Truth-Actor", "mailmap": "Truth-Actor",
              "raw": "Truth-Actor", "session": "Truth-Session"}


def _trailer_values(repo, key, sha):
    """The values of `key` on one commit. Used only to resolve a session to its owner."""
    out = git(repo, "show", "-s", f"--format=%(trailers:key={key},valueonly)", sha)
    return {ln.strip() for ln in out.splitlines() if ln.strip()}


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

def provenance(path):
    """When was this scenario's EXPECTED last changed, and is the working copy clean?

    Returns (sha, iso_date, dirty). Answers O.J.'s question on #46 -- "what establishes that the
    expected outcomes were committed before the results were observed?" -- as far as it can be
    answered: by showing the commit, so the ordering can be checked against the published run.
    """
    d = str(path.parent)
    r = subprocess.run(["git", "-C", d, "log", "-1", "--format=%h %cI", "--", str(path)],
                       capture_output=True, text=True)
    if r.returncode or not r.stdout.strip():
        return ("uncommitted", "-", True)
    sha, _, when = r.stdout.strip().partition(" ")
    s = subprocess.run(["git", "-C", d, "status", "--porcelain", "--", str(path)],
                       capture_output=True, text=True)
    return (sha, when, bool(s.stdout.strip()))


def load(name):
    """`name` is a module stem or a path relative to this directory, with or without .py."""
    p = HERE / name
    if p.suffix != ".py":
        p = p.with_suffix(".py")
    if not p.exists():
        cands = [c for c in HERE.rglob(f"{pathlib.Path(name).stem}.py")]
        if not cands:
            raise FileNotFoundError(f"no scenario {name!r} under {HERE}")
        p = cands[0]
    # Scenarios may import a sibling (Rill's untrailered variant reuses scenario_rename.build),
    # so the directory has to be importable, not just the file loadable.
    for d in {str(HERE), str(p.parent)}:
        if d not in sys.path:
            sys.path.insert(0, d)
    spec = importlib.util.spec_from_file_location(p.stem, p)
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
        kw = {}
        if path == "session":
            # Three conventions arrived: Tern keys this row by SESSION ID, Rill by subject via a
            # SUBJECTS map, Venice by bare subject name. Resolve all three to the session ids
            # being queried, then score against those sessions' hidden truth.
            sids = [s for s in sessions_of(repo, identity, mod)
                    if truth(repo, "Truth-Session", s)]
            if not sids:
                # A bare subject name: use the sessions that actor's own commits were written in.
                sids = sorted({v for sha in truth(repo, "Truth-Actor", identity)
                               for v in _trailer_values(repo, "Truth-Session", sha)})
            want = set()
            for sid in sids:
                want |= truth(repo, "Truth-Session", sid)
            identity_for_path = sids or [identity]
        else:
            want = truth(repo, TRUTH_KEYS[path], identity)
        if not want:
            # One scenario missing ground truth for one row must not stop the other scenarios
            # from producing results. Report the row as unscoreable and carry on -- silence here
            # would be the worse failure, since a missing row looks like a passing one in a tally.
            rows.append((path, identity, expected,
                         f"NO GROUND TRUTH ({TRUTH_KEYS[path]})", False))
            continue
        if path == "session":
            got_set = set()
            for sid in identity_for_path:
                got_set |= path_session(repo, sid)
        else:
            got_set = fn(repo, identity, **kw)
        got = classify(got_set, want)
        rows.append((path, identity, expected, got, got == expected))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("scenario", nargs="*", help="module names; default is every scenario_*.py here")
    a = ap.parse_args()

    # Discover by SHAPE, not by filename. A naming convention silently drops a scenario that
    # doesn't match it: `borrowed_author.py` -- the negative control, and the only source of
    # `false_merge` rows -- never ran under a `scenario*.py` glob, so the suite reported zero of
    # the outcome the paper most wants to show. Anything exporting build() and EXPECTED is a
    # scenario.
    def is_scenario(p):
        if p.stem in ("harness", "test_harness") or p.stem.startswith("test_"):
            return False
        src = p.read_text(errors="replace")
        return "EXPECTED" in src and "def build" in src

    # rglob, because scenarios arrived in both this directory and a scenarios/ subdirectory.
    found_paths = sorted(p for p in HERE.rglob("*.py") if is_scenario(p))
    names = a.scenario or [str(p.relative_to(HERE)) for p in found_paths]
    if not names:
        print("no scenarios found", file=sys.stderr)
        return 2

    rows, failures, prov = [], 0, []
    for name in names:
        mod = load(name)
        p = (HERE / name)
        if p.suffix != ".py":
            p = p.with_suffix(".py")
        prov.append((name, *provenance(p)))
        with tempfile.TemporaryDirectory(prefix="idev-") as d:
            for r in run_scenario(mod, pathlib.Path(d)):
                rows.append((name, *r))
                failures += not r[4]

    print("EXPECTED last changed (compare these against when results were published):")
    for name, sha, when, dirty in prov:
        flag = "  <-- UNVERIFIED: uncommitted changes" if dirty else ""
        print(f"  {name:32} {sha:10} {when}{flag}")
    print()

    w = max(len(r[0]) for r in rows)
    print(f"{'scenario':{w}}  {'path':8}  {'identity':12}  {'expected':22}  {'got':22}")
    print("-" * (w + 74))
    for name, path, ident, exp, got, ok in rows:
        print(f"{name:{w}}  {path:8}  {ident:12}  {exp:22}  {got:22}  {'' if ok else '<-- MISMATCH'}")

    tally = {o: sum(1 for r in rows if r[4] == o) for o in OUTCOMES}
    bad = tally["missed_link"] + tally["false_merge"]

    # Headline the scheme's behaviour, not our forecasting. An expected `false_merge` that
    # "matches" is still a wrong retrieval, and a 31/31 printed last reads as a pass -- which is
    # the number that would get quoted into the paper (O.J. and Codex, #46).
    print("\nRETRIEVAL OUTCOMES — what the identity scheme did. THIS IS THE RESULT.")
    notes = {"correct": "retrieved exactly the right commits",
             "missed_link": "FAILED to find work that was there",
             "false_merge": "WRONGLY attributed someone else's commit",
             "insufficient_evidence": "correctly declined to answer"}
    for o in ("correct", "missed_link", "false_merge", "insufficient_evidence"):
        print(f"  {o:24} {tally[o]:3}   {notes[o]}")
    print(f"\n  {bad} of {len(rows)} retrievals were wrong.")
    if not tally["insufficient_evidence"]:
        print("  note: zero insufficient_evidence verdicts — a scheme that always decides cannot "
              "say 'I don't know'. Check that a no-signal case is covered.")

    print("\nHARNESS AGREEMENT — how well WE predicted those outcomes. Not a result about "
          "the scheme.")
    print(f"  {len(rows) - failures}/{len(rows)} matched the pre-registered expectation.")
    print("  A matched `false_merge` means we correctly predicted a wrong retrieval. "
          "It is not a pass.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
