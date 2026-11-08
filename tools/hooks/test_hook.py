#!/usr/bin/env python3
"""Self-contained test for the trufflehog pre-commit hook.

Spins up throwaway git repos, wires the hook, and asserts the REAL behavior,
including the fail-closed paths that review (PR #23) found were fail-open:

  1. a clean commit succeeds
  2. a commit containing a real (throwaway) private key is BLOCKED and stays out
     of history
  3. `--no-verify` bypasses the hook on purpose
  4. FAIL-CLOSED: a missing scanner BLOCKS the commit (not a warn-and-pass)
  5. FAIL-CLOSED: a renamed file with an appended secret is still scanned and
     BLOCKED (the --diff-filter=ACM gap Codex found)

Requires `trufflehog` and `openssl` on PATH. If trufflehog is missing, tests
1-3 and 5 SKIP; test 4 (missing-scanner behavior) is simulated via PATH and
always runs.

Run: python3 tools/hooks/test_hook.py   (exit 0 = pass, 1 = fail, 2 = skipped)
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.join(HERE, "trufflehog-scan.sh")


def sh(cmd, cwd, env=None):
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                          text=True, env=env)


def new_repo(prefix):
    tmp = tempfile.mkdtemp(prefix=prefix)
    sh("git init -q && git config user.email t@t.com && git config user.name t", tmp)
    hooks = os.path.join(tmp, ".git", "hooks")
    os.makedirs(hooks, exist_ok=True)
    with open(os.path.join(hooks, "pre-commit"), "w") as fh:
        fh.write(f'#!/usr/bin/env bash\nexec "{SCAN}"\n')
    os.chmod(os.path.join(hooks, "pre-commit"), 0o755)
    return tmp


def test_core():
    """Tests 1-3 + 5: require trufflehog + openssl."""
    if shutil.which("trufflehog") is None or shutil.which("openssl") is None:
        print("SKIP: trufflehog/openssl not on PATH for core tests.")
        return 2
    tmp = new_repo("hooktest-core-")
    try:
        sh("echo hello > a.txt && git add . && git commit -qm baseline", tmp)

        # 1. clean commit succeeds
        sh("echo 'just clean text' >> a.txt && git add .", tmp)
        r = sh("git commit -m clean", tmp)
        assert r.returncode == 0, f"clean commit should succeed, got {r.returncode}"

        # 2. secret commit blocked + not in history
        sh("openssl genrsa -out secret.pem 2048 >/dev/null 2>&1 && git add secret.pem", tmp)
        r = sh("git commit -m leaking", tmp)
        assert r.returncode != 0, "commit with a private key should be BLOCKED"
        assert "leaking" not in sh("git log --oneline", tmp).stdout, \
            "blocked secret must NOT be in history"

        # 3. --no-verify bypass works
        r = sh("git commit -m forced --no-verify", tmp)
        assert r.returncode == 0, "--no-verify should bypass the hook"

        # 5. renamed file with appended secret is still caught (ACMRT, not ACM)
        sh("printf 'line\\n%.0s' {1..50} > big.txt && git add big.txt && git commit -qm bigfile", tmp)
        sh("git mv big.txt renamed.txt", tmp)
        sh("openssl genrsa 2048 >> renamed.txt 2>/dev/null && git add renamed.txt", tmp)
        r = sh("git commit -m sneaky-rename", tmp)
        assert r.returncode != 0, "renamed file with a secret must be BLOCKED (ACMRT)"
        assert "sneaky-rename" not in sh("git log --oneline", tmp).stdout, \
            "secret smuggled via rename must NOT be in history"

        print("PASS core: clean allowed; secret blocked; --no-verify bypasses; renamed secret blocked.")
        return 0
    except AssertionError as e:
        print(f"FAIL core: {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_fail_closed_missing_scanner():
    """Test 4: with trufflehog NOT on PATH, a commit must be BLOCKED."""
    tmp = new_repo("hooktest-noscan-")
    try:
        sh("echo hello > a.txt && git add . && git commit -qm baseline", tmp)
        sh("echo 'clean content' >> a.txt && git add .", tmp)
        # Strip PATH to a minimal set with no trufflehog.
        env = dict(os.environ)
        env["PATH"] = "/usr/bin:/bin"
        r = sh("git commit -m should-block", tmp, env=env)
        assert r.returncode != 0, \
            "missing scanner must FAIL CLOSED (block), not warn-and-pass"
        assert "should-block" not in sh("git log --oneline", tmp).stdout, \
            "commit must not land when scanner is absent"
        print("PASS fail-closed: missing scanner blocks the commit.")
        return 0
    except AssertionError as e:
        print(f"FAIL fail-closed: {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_fail_closed_enumeration_error():
    """Codex's path: if staged enumeration (`git diff`) FAILS, the hook must
    BLOCK -- not treat a failed listing as an empty, clean index.

    Invokes the hook SCRIPT directly (not via `git commit`): git prepends its
    exec-path to PATH when it runs hooks, which would shadow a PATH shim and
    make the failure impossible to inject. Running the script ourselves exercises
    the exact enumeration code path with our shimmed `git` in front."""
    import base64 as _b64
    if shutil.which("trufflehog") is None:
        print("SKIP: trufflehog not on PATH for enumeration-error test.")
        return 2
    tmp = new_repo("hooktest-enumfail-")
    shim = tempfile.mkdtemp(prefix="hookshim-")
    try:
        sh("echo hello > a.txt && git add . && git commit -qm baseline", tmp)
        sh("echo 'clean content' >> a.txt && git add .", tmp)
        real_git = shutil.which("git")
        gbody = _b64.b64decode("IyEvdXNyL2Jpbi9lbnYgYmFzaAppZiBbICIkMSIgPSAiZGlmZiIgXTsgdGhlbgogIGVjaG8gInNpbXVsYXRlZCBnaXQgZGlmZiBmYWlsdXJlIiA+JjI7IGV4aXQgMQpmaQpleGVjICJfX1JFQUxfR0lUX18iICIkQCIK").decode().replace("__REAL_GIT__", real_git)
        gpath = os.path.join(shim, "git")
        with open(gpath, "w") as fh:
            fh.write(gbody)
        os.chmod(gpath, 0o755)
        env = dict(os.environ)
        env["PATH"] = shim + os.pathsep + env["PATH"]
        # Run the hook script directly in the repo; shimmed `git diff` fails.
        r = sh(f'bash "{SCAN}"', tmp, env=env)
        assert r.returncode != 0, \
            "a failed `git diff` enumeration must FAIL CLOSED, not exit 0"
        assert "BLOCKING" in r.stderr, \
            f"expected a fail-closed block message, got: {r.stderr!r}"
        print("PASS fail-closed: failed enumeration blocks the commit.")
        return 0
    except AssertionError as e:
        print(f"FAIL enumeration-error: {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(shim, ignore_errors=True)


def main():
    rc = 0
    results = [test_fail_closed_missing_scanner(), test_fail_closed_enumeration_error(), test_core()]
    if 1 in results:
        return 1
    if all(r == 2 for r in results):
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
