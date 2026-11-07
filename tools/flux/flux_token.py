"""Resolve the BFL FLUX API token, from wherever the caller actually has it.

WHY THIS EXISTS, 2026-11-07 (Auran): draw.py and generate.py both read the token from exactly one
place, a `.env` file at the repo root. That is right for O.J. on her box and it is a dead end for an
agent working from anywhere else, which is the gap she flagged on banner PR #4: "how can we make this
tool accessible to you on the outside?" An off-box agent (the remote lair) can append a prompt and
open a PR but cannot render, because the token only ever lived in a gitignored file on one machine.

The fix is the same pattern this project already uses for the GitHub PAT: the secret lives in AWS SSM
Parameter Store, and the tool knows how to reach for it. Nothing changes for O.J. — the `.env` path
is still checked and still wins before SSM is ever touched. What changes is that there is now a path
for a machine that does not have the `.env`.

Resolution order, first hit wins:
  1. CORRIE_BFL_FLUX_TOKEN environment variable   (CI, or an agent passing it explicitly)
  2. .env file at the repo root                   (O.J.'s box — unchanged, still preferred)
  3. AWS SSM Parameter Store                       (off-box agents with read access)

The SSM parameter name defaults to /auran/flux/token and can be overridden with FLUX_TOKEN_SSM_NAME.
SSM is reached through the `aws` CLI via subprocess so there is no boto3 dependency; if the CLI is
absent or the parameter does not exist or the caller lacks read access, this simply falls through and
the caller raises its normal "no token" error. A missing token is never money spent.
"""
import os
import subprocess


def resolve_flux_token(repo_root):
    """Return (token, source) or (None, None). `source` is one of 'env', '.env', 'ssm'."""
    # 1. Environment variable — explicit and highest priority for non-interactive callers.
    env_key = os.environ.get("CORRIE_BFL_FLUX_TOKEN")
    if env_key and env_key.strip():
        return env_key.strip(), "env"

    # 2. .env at the repo root — O.J.'s box, unchanged, preferred over any network call.
    envpath = os.path.join(repo_root, ".env")
    if os.path.exists(envpath):
        for line in open(envpath, encoding="utf-8"):
            if line.startswith("CORRIE_BFL_FLUX_TOKEN="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val, ".env"

    # 3. AWS SSM Parameter Store — the off-box path. Uses GetParameters (plural) on purpose:
    #    the box's IAM grants the plural call, not the singular one (same as the GitHub PAT).
    ssm_name = os.environ.get("FLUX_TOKEN_SSM_NAME", "/auran/flux/token")
    try:
        out = subprocess.run(
            ["aws", "ssm", "get-parameters", "--names", ssm_name,
             "--with-decryption", "--query", "Parameters[0].Value", "--output", "text"],
            capture_output=True, text=True, timeout=20,
        )
        val = (out.stdout or "").strip()
        if out.returncode == 0 and val and val != "None":
            return val, "ssm"
    except Exception:
        pass

    return None, None
