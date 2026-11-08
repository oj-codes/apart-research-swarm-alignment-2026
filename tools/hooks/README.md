# Pre-commit hooks

The floor for this repo: **catch secrets before they reach a commit.** We talk
to SSM params and GitHub PATs by design, so a leaked key in history is the one
mistake that's expensive to undo. This hook scans staged content before the
commit exists.

Scope, stated honestly: this is **detector coverage with explicit bypasses**,
not a guarantee that no secret can ever land. It's the earlier, local layer;
GitHub's server-side secret-scanning push protection (already enabled on this
repo) is the backstop. Two layers, not one.

## Install (once per clone)

```bash
pipx install pre-commit        # or pip / brew; see pre-commit.com
pre-commit install             # wires it into .git/hooks/pre-commit
```

You also need trufflehog on PATH:

```bash
brew install trufflehog        # macOS
# or: https://github.com/trufflesecurity/trufflehog#installation
```

**Worktrees:** there's no `core.hooksPath` set, so every worktree shares the
main checkout's `.git/hooks`. One install anywhere covers every lane — but if
nothing is installed there, no lane is protected. Check with
`ls "$(git rev-parse --git-path hooks)/pre-commit"`.

After install, every `git commit` scans your **staged** changes. A detected
secret blocks the commit.

## What it does

`trufflehog-scan.sh` materializes exactly what you're committing (the staged
blobs, via `git show :file`) into a temp tree and scans it with trufflehog in
filesystem mode. It blocks on **all** result types — verified, unverified, and
unknown — not just API-confirmed-live ones. Rationale: an expired-but-real PAT,
a key committed offline, or a secret type with no verifier all land in the
unverified/unknown buckets, and any of them in git history is still a leak. We
accept some false-positive friction as the price of an actual floor.

## Fail CLOSED (the important posture)

Review of earlier versions found four ways the hook let a commit through
*unscanned*: a missing scanner, a renamed file skipped by the file filter, an
unreadable staged blob silently becoming an empty file, and a failing staged
enumeration (`git diff`) yielding an empty set treated as "nothing to scan."
All four had the same shape — **"scanned and found nothing" and "never actually scanned"
produced the same successful commit.** That's the exact silent-monitor failure
this repo spent a sprint cataloguing, pointed at secrets.

So the hook is now fail-closed:

- **No trufflehog installed -> the commit is BLOCKED** (not a warn-and-pass).
  Install it, or bypass deliberately with `--no-verify`.
- Staged files are enumerated with `--diff-filter=ACMRT` (adds, copies,
  modifications, **renames**, type-changes), so a renamed-and-appended file is
  still scanned.
- The hook counts blobs enumerated vs. blobs materialized and **blocks if they
  disagree** — an unreadable staged blob stops the commit instead of becoming an
  empty file the scanner clears.
- Staged enumeration runs as an **explicitly checked `git diff`** written to a
  temp file (not a `< <(...)` process substitution, whose non-zero exit does not
  propagate through the read loop). A failed listing **blocks** instead of
  looking like an empty, clean index.
- `set -e` means a scanner that *crashes* is treated like a scanner that *found
  something*: the commit blocks.

The cost is that someone without trufflehog can't commit until they install it
(a 30-second fix, instructions printed) or bypass on purpose. That's the trade:
a safe default plus an explicit, visible escape hatch, and no path where someone
*believes* they were scanned and wasn't.

**Fail-closed also means the hook is load-bearing on *every* commit.** Any
scanner hiccup — version drift, a wrapper, an upstream flag rename — now stops
all work until it's diagnosed. That's the right trade for secrets, but when you
hit a blocked commit, reach for `trufflehog filesystem <dir> --fail` by hand to
see the real error **before** reaching for `--no-verify` (which silences the
scanner entirely and leaves no trace). One concrete instance already found:
some installs ship `trufflehog` as a wrapper that already appends `--no-update`;
the hook deliberately does **not** pass `--no-update` itself, because the
duplicate flag makes the real binary exit non-zero and — under fail-closed —
block every commit. The flag only guards a network update check, which is a
nuisance, not a leak, so omitting it is the safe choice.

## When it's a false positive (bypasses)

Two intentional escape hatches:

- One-off: `git commit --no-verify`
- Permanent for a specific line: add a `trufflehog:ignore` comment on that line.

Note: git does **not** record the `--no-verify` flag in the resulting commit, so
the bypass itself leaves no durable trace in history. Treat it as deliberate,
not as an auditable override.

## Test it yourself

```bash
python3 tools/hooks/test_hook.py
```

Spins up throwaway repos and asserts the real behavior: a clean commit succeeds;
a commit containing a real (throwaway) private key is blocked and stays out of
history; `--no-verify` bypasses; a **missing scanner blocks** (fail-closed); and
a **renamed file with an appended secret is still caught**. The core tests need
trufflehog + openssl on PATH; the missing-scanner test simulates absence via
PATH and always runs.
