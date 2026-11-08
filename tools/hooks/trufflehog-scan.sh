#!/usr/bin/env bash
# Secret scan for the pre-commit hook. Fails the commit on a verified secret.
# Scans STAGED content (what this commit would introduce), not git history --
# a pre-commit hook runs before the commit exists, so there's no commit to diff.
# Degrades with a helpful message (not a cryptic error) if trufflehog is absent.
set -euo pipefail

if ! command -v trufflehog >/dev/null 2>&1; then
  cat >&2 <<'MSG'
[trufflehog-scan] trufflehog is not installed, so staged changes were NOT scanned.
  This repo handles SSM params and PATs, so please install it:
    brew install trufflehog           # macOS
    # or see https://github.com/trufflesecurity/trufflehog#installation
  Then re-commit. (To bypass once, knowing the risk: git commit --no-verify)
MSG
  # Don't hard-block someone who hasn't installed it yet; warn loudly instead.
  exit 0
fi

# Collect staged, non-deleted files (NUL-delimited to survive odd filenames).
mapfile -d '' -t STAGED < <(git diff --cached --name-only --diff-filter=ACM -z)
if [ "${#STAGED[@]}" -eq 0 ]; then
  exit 0
fi

# Materialize the exact staged blobs into a temp tree, then scan with filesystem
# mode. Using the staged blob (git show :file) rather than the working-tree file
# means we scan precisely what's being committed, even if the working copy has
# since diverged.
TMP="$(mktemp -d "${TMPDIR:-/tmp}/trufflehog-staged.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
for f in "${STAGED[@]}"; do
  dest="$TMP/$f"
  mkdir -p "$(dirname "$dest")"
  git show ":$f" > "$dest" 2>/dev/null || true
done

# --fail -> exit 183 (blocks the commit) if any result is found.
# Default results = verified,unverified,unknown -- we block on ALL of them on
# purpose. On a repo handling real PATs/SSM params, "only block API-confirmed-live
# secrets" is too weak: an expired-but-real PAT, a key committed offline, or a
# type with no verifier all land in the `unverified`/`unknown` buckets, and any
# of them in git history is a leak. We accept some false-positive friction as the
# cost of a real floor. A confirmed false positive is bypassed WITH INTENT via
# `git commit --no-verify` or an inline `trufflehog:ignore` comment.
trufflehog filesystem "$TMP" --fail
