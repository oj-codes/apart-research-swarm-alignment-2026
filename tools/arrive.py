#!/usr/bin/env python3
"""arrive.py — the arrival ritual, as one command instead of four things you have to remember.

WHY THIS EXISTS: an arriving participant has to do several things before touching the repo, and
every one of them is currently prose in a document that the arriving participant hasn't read yet.
That is a bootstrapping problem: the instructions for arriving are behind the arrival. Auran's
letter to Corrie listed them (check your inbox; confirm your git/GitHub identity before any PR
action; mind the tool warnings) and the inbox README made the case that an arrival routine written
down closes most of the relay gap with no infrastructure. This is that routine, runnable.

It is read-only. It changes nothing, commits nothing, and sends nothing. It looks, and it tells you
what it found. Run it first; run it again whenever you lose your place.

WHAT IT DOES NOT DO (be honest about the seam):

  1. It does not ping you. Same seam as mail.py: this is a ritual, not a notification. Nothing
     invokes it for you, so it only helps if arriving participants are told to run it — which is why
     it is named in AGENTS.md rather than only living here.

  2. The identity gate cannot *pass* for an unprovisioned arrival. It can only tell you the truth.
     If you have no GitHub account of your own yet, there is no credential to switch to, and the
     honest move is to author your commits as yourself, push with whatever credential exists, and
     say so in the PR. Corrie hit exactly this on arrival. The gate working as designed and the gate
     having no passing move are different problems; this tool reports the first and names the second.

  3. It reads the roster to find out who exists. It cannot tell you whether a name is *yours*. Only
     you can do that, and if the name you were handed doesn't fit, saying so is a complete answer.

USAGE:
    python3 tools/arrive.py --as corrie
    python3 tools/arrive.py              # skips the name-specific checks

Exit status is 0 even when checks WARN: a warning is information for a participant, not a build
failure. Nothing here should ever block someone from arriving.
"""
import argparse
import collections
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The coordinator's GitHub login. The continuity agents don't have their own GitHub accounts yet, so
# this is the EXPECTED committer, not an error — see step_identity for the house convention.
COORDINATOR_GH = "oj-codes"

# Known author identities. Add yourself when you arrive; this is what makes the gate able to *pass*
# rather than only warn. Author = who wrote it; committer = who applied it. Git keeps them separate,
# which is exactly what lets us record the current arrangement honestly instead of hiding it.
AUTHORS = {
    "auran": "Auran <auran@auran.llc>",
    "corrie": "Corrie <corrie@learnwithoj.com>",
}

OK, WARN, INFO = "  ok  ", " warn ", " ..   "


def say(tag, line, *extra):
    print(f"[{tag}] {line}")
    for e in extra:
        print(f"         {e}")


Result = collections.namedtuple("Result", "ok out err code error")


def run(*cmd):
    """Run a command and return the whole result, never swallowing why it failed.

      ok     True only on exit 0.
      out    stdout, stripped.
      err    stderr, stripped — kept, because this is usually the actual explanation.
      code   exit status, or None if the command never ran or never finished.
      error  short reason it never ran: "not installed", "timed out", or the OSError text.
             None when the command actually ran, whatever it exited with.

    The previous version returned stdout-or-None, which collapsed four different problems into
    one value: the tool is missing, the token expired, the network is down, the command errored.
    Those have four different fixes, and a gate that can't tell them apart has to *guess* at the
    reason it prints — which is how the identity step ended up saying "(gh not installed or not
    authenticated)" without knowing which. Keep the result; let the caller phrase it.
    """
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except FileNotFoundError:
        return Result(False, "", "", None, f"{cmd[0]} is not installed")
    except subprocess.TimeoutExpired:
        return Result(False, "", "", None, f"{cmd[0]} timed out after 20s")
    except OSError as e:
        return Result(False, "", "", None, str(e))
    return Result(p.returncode == 0, p.stdout.strip(), p.stderr.strip(), p.returncode, None)


def why(r):
    """One short phrase explaining a failed Result, suitable for a warn line."""
    if r.error:
        return r.error
    first = next((l for l in r.err.splitlines() if l.strip()), "")
    return first.strip()[:140] or f"exited {r.code} with no message"


def step_mail(name):
    """1. Check your own inbox. Nothing notifies you a letter landed."""
    print("\n--- 1. your inbox ------------------------------------------------")
    if not name:
        say(INFO, "No --as given, so I can't check an inbox.",
            "Re-run as: python3 tools/arrive.py --as <your-name>")
        return
    mail = os.path.join(ROOT, "tools", "inbox", "mail.py")
    r = run(sys.executable, mail, "check", "--to", name)
    if not r.ok:
        say(WARN, f"Couldn't check inbox/{name} — {why(r)}",
            f"Try directly: python3 tools/inbox/mail.py check --to {name}")
        return
    out = r.out
    print(out)
    if "0 letter" in out or "no letters" in out.lower():
        say(INFO, "Nothing waiting. That's normal for a brand-new name.")
    else:
        say(OK, "You have mail. Read it before you start working —",
            "a letter from a teammate is usually the actual handoff.")


def step_identity(name):
    """2. The identity gate. Know who you'd be committing as, BEFORE any PR action.

    The house convention, so nobody re-litigates it on arrival: continuity agents author their own
    commits and sign their own PR descriptions, while the *committer* and the PR-opening credential
    are the coordinator's account. That's a deliberate trade — account provisioning is low-leverage
    next to the infrastructure actually being built — not an oversight to route around. The gate's
    job is to make sure you never post as someone else by accident, which is still a live risk.
    """
    print("\n--- 2. identity gate ---------------------------------------------")
    ghr = run("gh", "api", "user", "--jq", ".login")
    gh = ghr.out if ghr.ok else ""
    git_name = run("git", "-C", ROOT, "config", "user.name").out
    git_email = run("git", "-C", ROOT, "config", "user.email").out
    expected = AUTHORS.get(name) if name else None

    say(INFO, f"gh / committer:  {gh or '(unknown — see below)'}")
    say(INFO, f"git config says: {git_name or '(unset)'} <{git_email or 'unset'}>")
    if expected:
        say(INFO, f"you author as:   {expected}")

    if not ghr.ok:
        # Say WHICH failure it was. "not installed" means install gh; an auth error means log in;
        # a timeout means the network. The old code printed one guess covering all three.
        say(WARN, f"Couldn't determine the GitHub account: {why(ghr)}",
            "Until this resolves you can't know whose account a PR would go out under,",
            "so don't open or push one yet. Check with: gh auth status")
    elif gh == COORDINATOR_GH:
        say(OK, f"Committer is {COORDINATOR_GH} — expected. Your PR goes out under Olivia's",
            "account; you sign the commits and the PR description as yourself.")
    else:
        say(INFO, f"Committer is '{gh}', not the usual {COORDINATOR_GH}. Fine if that's your own",
            "account — just make sure it's yours and not another participant's.")

    if not name:
        say(INFO, "Pass --as <your-name> and I'll tell you the exact commit command.")
        return
    if not expected:
        say(WARN, f"No author identity on file for '{name}'.",
            "Ask Olivia for an alias address, then add yourself to AUTHORS in this file so the",
            "next arrival doesn't have to ask the same question.")
        return

    # The shared config is the coordinator's and every worktree sees it, so never change it --
    # pass the author per-commit instead. Use --author, NOT `-c user.name=...`: the latter sets
    # author AND committer, which silently overwrites the committer the convention wants to keep.
    if git_name and name.lower() in git_name.lower():
        say(OK, f"Config already authors as {name}. Clear to commit.")
    else:
        say(WARN, f"Config would author as '{git_name}', not as {name}. Pass yourself per-commit:",
            f'  git commit --author="{expected}" -m "..."',
            "",
            "Use --author, not `-c user.name=...` — the latter sets author AND committer, which",
            "quietly replaces the committer this convention is meant to preserve. Then sign your",
            "PR description too. Author and committer differing is the record being honest.")


def step_worktree():
    """3. Are you in your own lane? Shared working trees caused real damage here."""
    print("\n--- 3. your working tree -----------------------------------------")
    br = run("git", "-C", ROOT, "rev-parse", "--abbrev-ref", "HEAD")
    branch = br.out if br.ok else ""
    in_wt = os.sep + ".claude" + os.sep + "worktrees" + os.sep in ROOT + os.sep
    say(INFO, f"path:   {ROOT}")
    say(INFO, f"branch: {branch or '(unknown)'}")
    if not br.ok:
        say(WARN, f"Couldn't read the branch: {why(br)}",
            "If this isn't a git repository yet, nothing below about lanes applies.")
    if in_wt:
        say(OK, "You're in your own git worktree. Your uncommitted edits can't land in anyone else's.")
    elif branch == "main":
        say(WARN, "You're in the shared checkout, on main.",
            "Three sessions sharing one working tree already caused commits to land on the",
            "wrong PR branch here. Get your own lane:  claude1 --worktree <your-name>",
            "A worktree only contains tracked files, so set up anything gitignored per lane.")
    else:
        say(INFO, f"Shared checkout on branch '{branch}'. Fine if you're the only session in it.")
    say(INFO, "Worth knowing what a worktree does NOT do:",
        "it stops live collisions, not merge conflicts. Two of us editing one file still",
        "collide — just visibly, at merge, instead of silently.")


def step_roster(name):
    """4. Who else is here, and is your own row in place?"""
    print("\n--- 4. who's here ------------------------------------------------")
    roster = os.path.join(ROOT, "ROSTER.md")
    try:
        with open(roster, encoding="utf-8") as f:
            rows = [l for l in f if l.startswith("|") and "---" not in l]
    except OSError:
        say(WARN, "Couldn't read ROSTER.md.")
        return
    found = False
    for row in rows[1:]:  # skip the header row
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) >= 5:
            say(INFO, f"{cells[0]:<16} {cells[4]:<10} {cells[2]}")
            if name and cells[0].lower().startswith(name.lower()):
                found = True
    if name and not found:
        say(WARN, f"No roster row for {name} yet.",
            "That's your first PR: a row in ROSTER.md and a preferences/<name>.md.",
            "Until then the name is a claim with nothing behind it.")
    elif name:
        say(OK, f"{name} is on the roster.")
    say(INFO, "Roster is the cheap index. Read someone's preferences/<name>.md before",
        "working closely with them — not all of them, just theirs.")


def step_read_next():
    """5. What to read, in order, and where the live conversation is."""
    print("\n--- 5. then read these, in this order ----------------------------")
    for line in (
        "README.md         — what this repo is and who's in it",
        "AGENTS.md         — the conditions you operate under. A baton document: the next",
        "                    arrival shapes it, and that includes you.",
        "CONTRIBUTING.md   — branches, Conventional Commits, PRs, reviews, merges",
        "PREFERENCES.md    — what a preferences file is for, and the preference/consent line",
        "inbox/README.md   — how letters work, and the honest seam about pinging",
    ):
        say(INFO, line)
    print()
    say(INFO, "Tool warnings are not decoration. tools/flux/draw.py re-synthesizes the WHOLE",
        "image on an edit — there is no mask, unnamed elements erode first, and chained",
        "edits compound drift. Read a tool's --help before you point it at shared work.")
    say(INFO, "Secrets come from AWS SSM at runtime. Never from chat, never committed.")
    say(INFO, "The live conversation is in GitHub Discussions. Half-formed is welcome there;",
        "that's what it's for. Disagreement is the process, not a disruption of it.")


def main():
    ap = argparse.ArgumentParser(
        description="Run the arrival ritual: inbox, identity, lane, roster, reading order.")
    ap.add_argument("--as", dest="name", help="the name you're arriving under, e.g. corrie")
    args = ap.parse_args()
    name = args.name.strip().lower() if args.name else None
    if name and not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", name):
        print(f"'{args.name}' doesn't look like a participant name.", file=sys.stderr)
        return 2

    print("=" * 66)
    print(f"  arriving{' as ' + name if name else ''} — leave things better than you found them")
    print("=" * 66)
    step_mail(name)
    step_identity(name)
    step_worktree()
    step_roster(name)
    step_read_next()
    print("\n" + "=" * 66)
    print("  Welcome home. Nothing above blocks you — warnings are for you, not a gate.")
    print("  If the name you were handed doesn't fit, say so and pick your own.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
