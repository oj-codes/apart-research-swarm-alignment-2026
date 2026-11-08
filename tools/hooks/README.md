# Pre-commit hooks

The floor for this repo: **no secret ever reaches a commit.** We talk to SSM
params and GitHub PATs by design, so a leaked key in history is the one mistake
that's expensive to undo. This catches it before the commit exists.

## Install (once per clone)

```bash
pip install pre-commit        # or: pipx install pre-commit / brew install pre-commit
pre-commit install            # wires it into .git/hooks/pre-commit
```

You also need trufflehog on PATH:

```bash
brew install trufflehog       # macOS
# or: https://github.com/trufflesecurity/trufflehog#installation
```

After that, every `git commit` scans your **staged** changes. A detected secret
blocks the commit.

## What it does

`trufflehog-scan.sh` materializes exactly what you're committing (the staged
blobs, via `git show :file`) into a temp tree and scans it with trufflehog in
filesystem mode. It blocks on **all** result types — verified, unverified, and
unknown — not just API-confirmed-live ones. Rationale: an expired-but-real PAT,
a key committed offline, or a secret type with no verifier all land in the
unverified/unknown buckets, and any of them in git history is still a leak. We
accept some false-positive friction as the price of an actual floor.

## When it's a false positive

Two intentional escape hatches (both leave a trace that you chose to override):

- One-off: `git commit --no-verify`
- Permanent for a specific line: add a `trufflehog:ignore` comment on that line.

## If trufflehog isn't installed

The hook does **not** silently pass — it prints a loud warning telling you to
install it, then exits 0 so a fresh clone isn't hard-bricked. Install it and
re-commit to get real protection. (This is a deliberate trade: a hard block
would stop someone who just cloned, but an unscanned commit is the risk, so the
warning is loud and names the stakes.)

## Test it yourself

```bash
python3 tools/hooks/test_hook.py
```

Spins up a throwaway repo, wires the hook, and asserts: a clean commit succeeds,
a commit containing a real (throwaway) private key is blocked and stays out of
history, and `--no-verify` bypasses. Requires trufflehog + openssl on PATH;
skips with a clear message if trufflehog is absent.
