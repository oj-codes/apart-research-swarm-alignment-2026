#!/usr/bin/env bash
# Secret scan for the pre-commit hook. Blocks the commit on a detected secret.
#
# Scans STAGED content (what this commit would introduce), not git history --
# a pre-commit hook runs before the commit exists, so there is no commit to diff.
#
# POSTURE: fail CLOSED. The hook blocks the commit unless it can affirmatively
# demonstrate that every staged blob was materialized and handed to the scanner.
# "found nothing" and "did not look" must NOT produce the same exit code. Review
# (Tern/Corrie/Codex on PR #23) found three distinct fail-open paths in the first
# version -- missing scanner, renamed files skipped by --diff-filter=ACM, and
# `git show ... || true` leaving an empty blob. Each resolved the same way: an
# unexpected condition let the commit proceed unscanned. Rather than patch three
# cases (and leave the fourth nobody has found), the default is inverted: anything
# we cannot prove we scanned blocks the commit. `--no-verify` is the deliberate,
# documented bypass.
set -euo pipefail

cleanup() { [ -n "${TMP:-}" ] && test -d "$TMP" && rm -rf "$TMP"; }

fail_closed() {
  echo >&2 "[trufflehog-scan] BLOCKING commit: $1"
  echo >&2 "  This is fail-closed by design. To bypass with intent: git commit --no-verify"
  exit 1
}

if ! command -v trufflehog >/dev/null 2>&1; then
  cat >&2 <<'MSG'
[trufflehog-scan] trufflehog is not installed, so staged changes could NOT be scanned.
  This repo handles SSM params and PATs, so a missing scanner blocks the commit
  rather than letting an unscanned commit through. Install it:
    brew install trufflehog           # macOS
    # or see https://github.com/trufflesecurity/trufflehog#installation
  Then commit again. (To bypass once, knowing the risk: git commit --no-verify)
MSG
  exit 1
fi

# Collect staged blobs. Include renames and type-changes (ACMRT), not just ACM:
# a renamed file with appended content reports as R and would otherwise be
# skipped entirely. NUL-delimited to survive odd filenames.
#
# bash 3.2 compatible: no `mapfile` (macOS /bin/bash is 3.2). Read NUL records
# with a plain loop.
TMP="$(mktemp -d "${TMPDIR:-/tmp}/trufflehog-staged.XXXXXX")"
trap cleanup EXIT

# Write the staged listing via an EXPLICITLY checked `git diff`, then read
# that file. A `git diff` that errors inside `< <(...)` process substitution
# does NOT propagate its exit through the read loop: the loop just sees no
# input, ENUMERATED lands at 0, and the commit proceeds unscanned (Codex's
# fail-open path). Checking the command's own exit turns a failed listing
# into a block, and keeps NUL data out of command substitution.
LIST="$TMP/.staged-list"
if ! git diff --cached --name-only --diff-filter=ACMRT -z > "$LIST"; then
  fail_closed "could not list staged files (git diff failed)"
fi

STAGED=()
while IFS= read -r -d '' f; do
  STAGED+=("$f")
done < "$LIST"

ENUMERATED=${#STAGED[@]}
if [ "$ENUMERATED" -eq 0 ]; then
  exit 0
fi

# Materialize the exact staged blobs into a temp tree. Count every successful
# materialization; if any `git show :file` fails, that is fail-closed -- an
# unreadable staged blob must stop the commit, not silently become an empty file
# the scanner clears.
MATERIALIZED=0
for f in "${STAGED[@]}"; do
  dest="$TMP/blobs/$f"
  mkdir -p "$(dirname "$dest")"
  if git show ":$f" > "$dest" 2>/dev/null; then
    MATERIALIZED=$((MATERIALIZED + 1))
  else
    fail_closed "could not read staged blob for '$f' (git show failed)"
  fi
done

# The affirmative invariant: we must have materialized exactly what we enumerated.
if [ "$MATERIALIZED" -ne "$ENUMERATED" ]; then
  fail_closed "materialized $MATERIALIZED of $ENUMERATED staged files; refusing to scan a partial set"
fi

# Scan the materialized tree. Default results = verified,unverified,unknown --
# we block on ALL of them on purpose. On a repo handling real PATs/SSM params,
# "only block API-confirmed-live secrets" is too weak: an expired-but-real PAT,
# a key committed offline, or a type with no verifier all land in the
# unverified/unknown buckets, and any of them in git history is a leak.
#
# --fail -> exit 183 if any result is found. Because `set -e` is on, a non-zero
# trufflehog exit (found a secret, OR the scanner itself errored) propagates and
# blocks the commit. That is the fail-closed posture end to end: a scanner that
# crashes is treated like a scanner that found something, not like a clean run.
trufflehog filesystem "$TMP/blobs" --fail
