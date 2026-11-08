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
  6. FAIL-CLOSED: a failed `git diff` enumeration BLOCKS the commit
  7. FAIL-CLOSED: a failed `git show :file` blob-read BLOCKS the commit

Requires `trufflehog` and `openssl` on PATH. If trufflehog is missing, the tests
that need the real detector SKIP; the missing-scanner test (4) is simulated via
PATH and always runs.

Test-harness integrity (review by O.J.), so a test cannot pass for the wrong
reason:
  - Every SETUP command is exit-code-checked (`run`); a test can no longer pass
    because `git init`, a baseline commit, or key generation silently failed.
  - Assertions use `require()`, not bare `assert`, so they still fire under
    `python -O` (which strips `assert`).
  - The missing-scanner test PROVES its restricted PATH actually removes
    trufflehog while keeping git/bash reachable -- otherwise "blocked" could
    mean "git itself was missing", a pass for the wrong reason.
  - The enumeration/blob shims intercept the EXACT git subcommands the hook runs
    (`git diff --cached ...` and `git show :file`) and assert the shim was
    actually hit, so the test cannot silently skip the path it claims to cover.

Run: python3 tools/hooks/test_hook.py   (exit 0 = pass, 1 = fail, 2 = skipped)
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCAN = os.path.join(HERE, "trufflehog-scan.sh")


class SetupError(RuntimeError):
    """A test's SETUP command failed -- the result is meaningless, not a pass."""


class TestFailure(AssertionError):
    """An assertion about the hook's behavior failed."""


def require(cond, msg):
    """Assertion that survives `python -O` (unlike bare `assert`)."""
    if not cond:
        raise TestFailure(msg)


def sh(cmd, cwd, env=None):
    """Run a command and RETURN the result (for the thing under test)."""
    return subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                          text=True, env=env)


def run(cmd, cwd, env=None):
    """Run a SETUP command and FAIL LOUDLY if it does not exit 0.

    This is the fix for "a test passes because setup failed, not because the
    hook worked": repo init, baseline commits, key generation and fixture
    staging all go through here, so a broken precondition raises SetupError
    instead of silently leaving the repo in a state where the real assertion is
    hollow.
    """
    r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                       text=True, env=env)
    if r.returncode != 0:
        raise SetupError(f"setup command failed ({r.returncode}): {cmd}\n"
                         f"  stdout: {r.stdout.strip()}\n  stderr: {r.stderr.strip()}")
    return r


def new_repo(prefix):
    tmp = tempfile.mkdtemp(prefix=prefix)
    run("git init -q", tmp)
    run("git config user.email t@t.com", tmp)
    run("git config user.name t", tmp)
    run("git config commit.gpgsign false", tmp)
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
        run("echo hello > a.txt", tmp)
        run("git add .", tmp)
        run("git commit -qm baseline", tmp)

        # 1. clean commit succeeds
        run("echo 'just clean text' >> a.txt", tmp)
        run("git add .", tmp)
        r = sh("git commit -m clean", tmp)
        require(r.returncode == 0,
                f"clean commit should succeed, got {r.returncode}: {r.stderr}")

        # 2. secret commit blocked + not in history
        run("openssl genrsa -out secret.pem 2048 >/dev/null 2>&1", tmp)
        run("git add secret.pem", tmp)
        r = sh("git commit -m leaking", tmp)
        require(r.returncode != 0, "commit with a private key should be BLOCKED")
        require("leaking" not in sh("git log --oneline", tmp).stdout,
                "blocked secret must NOT be in history")

        # 3. --no-verify bypass works
        r = sh("git commit -m forced --no-verify", tmp)
        require(r.returncode == 0, "--no-verify should bypass the hook")

        # 5. renamed file with appended secret is still caught (ACMRT, not ACM).
        # The body must be large enough that Git classifies the change as a
        # rename (R) rather than delete+add (D/A) -- otherwise the ACM filter
        # already catches the added file and the test passes WITHOUT exercising
        # the ACMRT path (the fixture-hollowness Codex found). `yes | head`
        # avoids brace expansion, which does not happen under /bin/sh and
        # previously yielded a tiny literal file that degraded R into D+A.
        run("yes line | head -n 2000 > big.txt", tmp)
        run("git add big.txt", tmp)
        run("git commit -qm bigfile", tmp)
        run("git mv big.txt renamed.txt", tmp)
        run("openssl genrsa 2048 >> renamed.txt 2>/dev/null", tmp)
        run("git add renamed.txt", tmp)
        status = run("git diff --cached --name-status -M", tmp).stdout
        require(status.startswith("R"),
                f"fixture must be a rename (R) to exercise ACMRT, Git reports: {status!r}")
        r = sh("git commit -m sneaky-rename", tmp)
        require(r.returncode != 0, "renamed file with a secret must be BLOCKED (ACMRT)")
        require("sneaky-rename" not in sh("git log --oneline", tmp).stdout,
                "secret smuggled via rename must NOT be in history")

        print("PASS core: clean allowed; secret blocked; --no-verify bypasses; renamed secret blocked.")
        return 0
    except TestFailure as e:
        print(f"FAIL core: {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_fail_closed_missing_scanner():
    """Test 4: with trufflehog NOT on PATH, a commit must be BLOCKED.

    First PROVES the restricted PATH is a valid simulation of "scanner absent":
    trufflehog must be unreachable while git/bash stay reachable. Without that
    proof, a block could mean "git was missing", not "the hook failed closed" --
    the test would pass for the wrong reason (O.J.'s point 3).
    """
    tmp = new_repo("hooktest-noscan-")
    try:
        run("echo hello > a.txt", tmp)
        run("git add .", tmp)
        run("git commit -qm baseline", tmp)
        run("echo 'clean content' >> a.txt", tmp)
        run("git add .", tmp)

        restricted = "/usr/bin:/bin"
        # The restricted PATH must genuinely remove trufflehog...
        require(shutil.which("trufflehog", path=restricted) is None,
                "restricted PATH must NOT contain trufflehog (else the test is hollow)")
        # ...while keeping the hook's real dependencies reachable.
        for dep in ("git", "bash"):
            require(shutil.which(dep, path=restricted) is not None,
                    f"restricted PATH must still provide '{dep}', else a block is meaningless")

        env = dict(os.environ)
        env["PATH"] = restricted
        r = sh("git commit -m should-block", tmp, env=env)
        require(r.returncode != 0,
                "missing scanner must FAIL CLOSED (block), not warn-and-pass")
        require("should-block" not in sh("git log --oneline", tmp).stdout,
                "commit must not land when scanner is absent")
        print("PASS fail-closed: missing scanner blocks (PATH isolation verified).")
        return 0
    except TestFailure as e:
        print(f"FAIL fail-closed-missing-scanner: {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _git_shim(shim_dir, fail_on):
    """Write a `git` shim that fails on a specific subcommand and execs real git
    otherwise. `fail_on` is the first arg to intercept ('diff' or 'show') -- the
    exact subcommands the hook issues. The shim touches a marker file so the test
    can PROVE it was actually hit (not bypassed by git prepending its exec-path,
    which would make the failure impossible to inject and the test silently
    green)."""
    real_git = shutil.which("git")
    marker = os.path.join(shim_dir, f"hit-{fail_on}")
    body = (
        "#!/usr/bin/env bash\n"
        f'if [ "$1" = "{fail_on}" ]; then\n'
        f'  touch "{marker}"\n'
        f'  echo "simulated git {fail_on} failure" >&2\n'
        "  exit 1\n"
        "fi\n"
        f'exec "{real_git}" "$@"\n'
    )
    gpath = os.path.join(shim_dir, "git")
    with open(gpath, "w") as fh:
        fh.write(body)
    os.chmod(gpath, 0o755)
    return marker


def _enumeration_error_case(fail_on):
    """Shared body: inject a failure on the EXACT git subcommand the hook runs
    (`git diff --cached ...` for enumeration, `git show :file` for blob
    materialization) and assert the hook FAILS CLOSED and the shim was hit.

    Invokes the hook SCRIPT directly (not via `git commit`): git prepends its
    exec-path to PATH when running hooks, which would shadow the shim and make
    the failure impossible to inject.
    """
    if shutil.which("trufflehog") is None:
        print(f"SKIP: trufflehog not on PATH for enumeration-error ({fail_on}) test.")
        return 2
    tmp = new_repo(f"hooktest-enumfail-{fail_on}-")
    shim = tempfile.mkdtemp(prefix="hookshim-")
    try:
        run("echo hello > a.txt", tmp)
        run("git add .", tmp)
        run("git commit -qm baseline", tmp)
        # Stage real content so `git show` has a blob to (fail to) read.
        run("openssl genrsa -out staged.pem 2048 >/dev/null 2>&1", tmp)
        run("git add staged.pem", tmp)

        marker = _git_shim(shim, fail_on)
        env = dict(os.environ)
        env["PATH"] = shim + os.pathsep + env["PATH"]
        r = sh(f'bash "{SCAN}"', tmp, env=env)
        require(os.path.exists(marker),
                f"shim for `git {fail_on}` was never invoked -- the test did not "
                f"exercise the path it claims to (hook output: {r.stderr!r})")
        require(r.returncode != 0,
                f"a failed `git {fail_on}` must FAIL CLOSED, not exit 0")
        require("BLOCKING" in r.stderr,
                f"expected a fail-closed block message, got: {r.stderr!r}")
        print(f"PASS fail-closed: failed `git {fail_on}` blocks (shim hit verified).")
        return 0
    except TestFailure as e:
        print(f"FAIL enumeration-error ({fail_on}): {e}")
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(shim, ignore_errors=True)


def test_fail_closed_enumeration_error():
    """Codex's path 1: `git diff` (staged enumeration) fails -> must BLOCK."""
    return _enumeration_error_case("diff")


def test_fail_closed_blobread_error():
    """Codex's path 2: `git show :file` (blob materialization) fails -> must BLOCK.
    Previously `git show ... || true` left an empty blob the scanner cleared."""
    return _enumeration_error_case("show")


def main():
    tests = [
        test_fail_closed_missing_scanner,
        test_fail_closed_enumeration_error,
        test_fail_closed_blobread_error,
        test_core,
    ]
    results = []
    for t in tests:
        try:
            results.append(t())
        except SetupError as e:
            print(f"FAIL setup ({t.__name__}): {e}")
            results.append(1)
    if 1 in results:
        return 1
    if all(r == 2 for r in results):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
