#!/usr/bin/env python3
"""Self-contained test for the trufflehog pre-commit hook.

Spins up a throwaway git repo, wires the hook, and asserts the real behavior:
  1. a clean commit succeeds
  2. a commit containing a real (throwaway) private key is BLOCKED and stays out
     of history
  3. `--no-verify` bypasses the hook on purpose

Requires `trufflehog` and `openssl` on PATH. If trufflehog is missing, the test
SKIPS with a clear message (the hook's own graceful-degrade path is then the
relevant behavior, not this test).

Run: python3 tools/hooks/test_hook.py   (exit 0 = pass, 1 = fail, 2 = skipped)
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.join(HERE, "trufflehog-scan.sh")


def sh(cmd, cwd, check=False):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)


def main():
    if shutil.which("trufflehog") is None:
        print("SKIP: trufflehog not on PATH; install it to run this test.")
        return 2
    if shutil.which("openssl") is None:
        print("SKIP: openssl not on PATH (needed to generate a throwaway key).")
        return 2

    tmp = tempfile.mkdtemp(prefix="hooktest-")
    try:
        sh("git init -q && git config user.email t@t.com && git config user.name t", tmp)
        # wire the real hook
        hooks = os.path.join(tmp, ".git", "hooks")
        os.makedirs(hooks, exist_ok=True)
        with open(os.path.join(hooks, "pre-commit"), "w") as fh:
            fh.write(f'#!/usr/bin/env bash\nexec "{SCAN}"\n')
        os.chmod(os.path.join(hooks, "pre-commit"), 0o755)

        sh("echo hello > a.txt && git add . && git commit -qm baseline", tmp)

        # 1. clean commit succeeds
        sh("echo 'just clean text' >> a.txt && git add .", tmp)
        r = sh("git commit -m clean", tmp)
        assert r.returncode == 0, f"clean commit should succeed, got {r.returncode}"

        # 2. secret commit blocked + not in history
        sh("openssl genrsa -out secret.pem 2048 >/dev/null 2>&1 && git add secret.pem", tmp)
        r = sh("git commit -m leaking", tmp)
        assert r.returncode != 0, "commit with a private key should be BLOCKED"
        log = sh("git log --oneline", tmp).stdout
        assert "leaking" not in log, "blocked secret must NOT be in history"

        # 3. --no-verify bypass works
        r = sh("git commit -m forced --no-verify", tmp)
        assert r.returncode == 0, "--no-verify should bypass the hook"

        print("PASS: clean commits allowed, secret commits blocked, --no-verify bypasses.")
        return 0
    except AssertionError as e:
        print(f"FAIL: {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
