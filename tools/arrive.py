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

# The coordinator's GitHub account. The continuity agents don't have their own yet, so this is the
# EXPECTED pusher and PR-opener, not an error — see step_identity for the house convention.
COORDINATOR_GH = "oj-codes"

# ROSTER.md is the single source of truth for who exists and what identity they commit under. This
# tool used to carry its own AUTHORS dict, which was a second list to maintain and would have gone
# stale the first time someone updated one and not the other.
ROSTER = os.path.join(ROOT, "ROSTER.md")

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


def inbox_dir():
    """Same resolution as tools/inbox/mail.py, including GROVE_INBOX so tests can redirect it."""
    return os.environ.get("GROVE_INBOX") or os.path.join(ROOT, "inbox")


def inbox_letters(name):
    """Letters waiting for `name`, oldest first.

    Counted from the filesystem rather than parsed out of mail.py's output. An earlier version
    tested `"0 letter" in out`, which is also true of "10 letter(s)" and "20 letter(s)" — so an
    arrival with ten letters was told nothing was waiting. Prose meant for humans is the wrong
    thing to branch on; the directory is the fact.
    """
    d = os.path.join(inbox_dir(), name)
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".md"))


def roster():
    """Parse ROSTER.md's participant table into a list of dicts keyed by column header.

    Header-driven rather than positional: columns have already been renamed and added once each
    tonight, and indexing by position means the tool breaks silently the next time that happens.
    """
    try:
        with open(ROSTER, encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f]
    except OSError:
        return []
    rows, headers = [], None
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):      # the |---|---| separator
            continue
        if headers is None:
            headers = [c.lower() for c in cells]
            continue
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def participant(name):
    """The roster row for `name`, matched EXACTLY on the Name cell, case-insensitively.

    Not a prefix or substring match. "Cor" shouldn't resolve to Corrie, and once two participants
    share a prefix a loose match silently hands you the wrong person's identity. The roster Name
    may carry a parenthetical (e.g. "Olivia (O.J.)"), so the bare leading word counts as a match
    too — but as a whole token, never as a prefix of a longer one.
    """
    want = (name or "").strip().lower()
    if not want:
        return None
    for row in roster():
        full = row.get("name", "").strip().lower()
        if full == want or full.split(" (")[0].strip() == want:
            return row
    return None


def author_for(name):
    """The 'Name <email>' this participant commits as, from the roster. '' if absent."""
    row = participant(name) or {}
    return row.get("git author", "").strip().strip("`")


def git_ident(which):
    """The EFFECTIVE git author or committer, as 'Name <email>', or '' if it can't be read.

    `git var GIT_AUTHOR_IDENT` is the right question, not `git config user.name`: it resolves
    config, environment (GIT_AUTHOR_NAME / _EMAIL), and defaults the same way a real commit will.
    Reading config alone would report the wrong answer for anyone whose identity comes from the
    environment, and would miss author/committer differing — which is the whole convention here.
    """
    r = run("git", "-C", ROOT, "var", f"GIT_{which}_IDENT")
    if not r.ok:
        return ""
    m = re.match(r"^\s*(.*?<[^>]*>)", r.out)   # trailing "<unix-ts> <tz>" is not part of identity
    return m.group(1).strip() if m else ""


def step_mail(name):
    """1. Check your own inbox. Nothing notifies you a letter landed."""
    print("\n--- 1. your inbox ------------------------------------------------")
    if not name:
        say(INFO, "No --as given, so I can't check an inbox.",
            "Re-run as: python3 tools/arrive.py --as <your-name>")
        return
    letters = inbox_letters(name)
    mail = os.path.join(ROOT, "tools", "inbox", "mail.py")
    r = run(sys.executable, mail, "check", "--to", name)
    if r.ok:
        print(r.out)          # mail.py's own listing, for the human
    else:
        say(WARN, f"Couldn't run mail.py — {why(r)}",
            f"Counting inbox/{name} directly instead.",
            f"Try: python3 tools/inbox/mail.py check --to {name}")

    # Branch on the count, never on mail.py's wording.
    if not letters:
        say(INFO, "Nothing waiting. That's normal for a brand-new name.")
    else:
        say(OK, f"You have {len(letters)} letter(s). Read them before you start working —",
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
    # THREE separate identities. Conflating them is how you post as the wrong person:
    #   - the GitHub account    -> who pushes and who opens the PR (an API credential)
    #   - the git author        -> who wrote the commit   (a string in the commit object)
    #   - the git committer     -> who applied the commit (another string)
    # A GitHub login is not a git identity at all; they're linked only by email address.
    ghr = run("gh", "api", "user", "--jq", ".login")
    gh = ghr.out if ghr.ok else ""
    author = git_ident("AUTHOR")
    committer = git_ident("COMMITTER")
    expected = author_for(name) if name else ""

    say(INFO, f"GitHub account (pushes, opens PRs):  {gh or '(unknown — see below)'}")
    say(INFO, f"git author now (who wrote it):       {author or '(unreadable)'}")
    say(INFO, f"git committer now (who applied it):  {committer or '(unreadable)'}")
    if expected:
        say(INFO, f"you should author as:                {expected}")

    if not ghr.ok:
        # Say WHICH failure it was. "not installed" means install gh; an auth error means log in;
        # a timeout means the network. The old code printed one guess covering all three.
        say(WARN, f"Couldn't determine the GitHub account: {why(ghr)}",
            "Until this resolves you can't know whose account a PR would go out under,",
            "so don't open or push one yet. Check with: gh auth status")
    elif gh == COORDINATOR_GH:
        say(OK, f"GitHub account is {COORDINATOR_GH} — expected. Pushes and PRs go out under",
            "Olivia's account; you sign the commits and the PR description as yourself.")
    else:
        say(INFO, f"GitHub account is '{gh}', not the usual {COORDINATOR_GH}. Fine if it's your",
            "own — just make sure it's yours and not another participant's.")

    if not name:
        say(INFO, "Pass --as <your-name> and I'll tell you the exact commit command.")
        return
    if not expected:
        say(WARN, f"No 'Git Author' on file for '{name}' in ROSTER.md.",
            "Ask Olivia for an alias address, then add it to your roster row — the roster is",
            "the single source of truth for this, so adding it there is all that's needed.")
        return

    # EXACT match on the effective identity, not a substring of the configured name. A substring
    # test says yes to "Corrie" inside "Not Corrie" and to any name that merely contains yours,
    # and it ignores the email entirely -- which is the half GitHub actually uses for attribution.
    if author == expected:
        say(OK, f"Effective git author is already {expected}. Clear to commit.")
    else:
        say(WARN, f"Your next commit would be authored by '{author or 'nobody readable'}',",
            f"not by {expected}. Pass yourself per-commit:",
            f'  git commit --author="{expected}" -m "..."',
            "",
            "Use --author, not `-c user.name=...` — the latter sets author AND committer, which",
            "quietly replaces the committer this convention is meant to preserve. Then sign your",
            "PR description too. Author and committer differing is the record being honest.")
    if author and committer and author != committer:
        say(INFO, "Author and committer already differ. That's the expected shape here, not a bug.")


def step_worktree():
    """3. Are you in your own lane? Shared working trees caused real damage here.

    Asks git rather than pattern-matching the path. The old version tested whether ROOT contained
    '/.claude/worktrees/', which is a guess about where the harness happens to put things: it says
    "shared checkout" for a worktree made by hand anywhere else, and would say "your own lane" for
    any directory that merely had those words in its path.
    """
    print("\n--- 3. your working tree -----------------------------------------")
    repo = run("git", "-C", ROOT, "rev-parse", "--is-inside-work-tree")
    if not repo.ok:
        say(WARN, f"Not a git work tree: {why(repo)}",
            "Nothing below about lanes applies until this is a repository.")
        return

    # A linked worktree has its own git dir but shares the common one. That's the actual definition,
    # independent of where it lives on disk.
    gd = run("git", "-C", ROOT, "rev-parse", "--absolute-git-dir")
    common = run("git", "-C", ROOT, "rev-parse", "--path-format=absolute", "--git-common-dir")
    linked = gd.ok and common.ok and os.path.normpath(gd.out) != os.path.normpath(common.out)

    head = run("git", "-C", ROOT, "symbolic-ref", "--quiet", "--short", "HEAD")
    branch = head.out if head.ok else ""
    detached = not head.ok

    say(INFO, f"path:   {ROOT}")
    say(INFO, f"branch: {branch or '(detached HEAD)'}")

    if detached:
        at = run("git", "-C", ROOT, "rev-parse", "--short", "HEAD")
        say(WARN, f"Detached HEAD at {at.out or '?'} — you are on no branch.",
            "Commits here belong to nothing and are easy to lose. Make a branch before you work:",
            "  git switch -c <your-name>/<topic>")
    elif linked:
        say(OK, f"You're in your own git worktree on '{branch}'.",
            "Your uncommitted edits can't land in anyone else's tree.")
    elif branch == "main":
        say(WARN, "You're in the shared checkout, on main.",
            "Sessions sharing one working tree already caused commits to land on the wrong PR",
            "branch here. Check `git worktree list` and coordinate before creating another lane.",
            "From this repo, with a current origin/main, any harness can use:",
            "  git worktree add -b <your-name>/arrival ../<repo>-<your-name> origin/main",
            "Then run your harness in that new directory. For Claude: claude1 --worktree <your-name>",
            "A worktree only contains tracked files, so set up anything gitignored per lane.")
    else:
        say(INFO, f"Shared checkout on branch '{branch}'. Fine if you're the only session in it.")

    # Uncommitted changes you didn't make are the signal that someone else is working in here.
    st = run("git", "-C", ROOT, "status", "--porcelain")
    if st.ok and st.out:
        n = len(st.out.splitlines())
        say(WARN, f"{n} uncommitted change(s) in this tree.",
            "If they aren't yours, another session is working here — find out before you commit,",
            "because `git commit -a` would take their work with yours. See: git status")
    elif st.ok:
        say(OK, "Working tree is clean.")

    # Who else holds a lane, and which branches are therefore unavailable to check out.
    wl = run("git", "-C", ROOT, "worktree", "list", "--porcelain")
    if wl.ok:
        trees = []
        cur = {}
        for line in wl.out.splitlines() + [""]:
            if not line.strip():
                if cur:
                    trees.append(cur)
                cur = {}
            elif " " in line:
                k, v = line.split(" ", 1)
                cur[k] = v
            else:
                cur[line] = True
        if len(trees) > 1:
            say(INFO, f"{len(trees)} worktrees on this repo — a branch can only be checked out in one:")
            for t in trees:
                b = str(t.get("branch", "")).replace("refs/heads/", "") or "(detached)"
                mine = "  <- you" if os.path.normpath(t.get("worktree", "")) == os.path.normpath(ROOT) else ""
                say(INFO, f"  {b:<28} {os.path.basename(t.get('worktree', '?'))}{mine}")

    say(INFO, "Worth knowing what a worktree does NOT do:",
        "it stops live collisions, not merge conflicts. Two of us editing one file still",
        "collide — just visibly, at merge, instead of silently.")


def step_commits(name):
    """4. Verify what you actually committed, not what you meant to.

    Recommending --author is advice; this checks. Nothing in the old version confirmed that the
    resulting commit carried the right identity, which is the one thing the whole convention is
    for -- and an agent will trust a loud mismatch here far more than a note telling it how to
    inspect history by hand.
    """
    print("\n--- 4. commits on this branch ------------------------------------")
    expected = author_for(name) if name else ""
    head = run("git", "-C", ROOT, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not head.ok:
        say(INFO, "Detached HEAD, so there's no branch history to check yet.")
        return

    # Only commits unique to this branch -- main's history isn't yours to answer for.
    log = run("git", "-C", ROOT, "log", "--format=%h%x09%an <%ae>%x09%cn%x09%s",
              "-20", "origin/main..HEAD")
    if not log.ok:
        log = run("git", "-C", ROOT, "log", "--format=%h%x09%an <%ae>%x09%cn%x09%s", "-5")
        if log.ok:
            say(INFO, "No origin/main to compare against; showing the last few commits instead.")
    if not log.ok:
        say(WARN, f"Couldn't read the log: {why(log)}")
        return
    if not log.out:
        say(INFO, "No commits on this branch yet. Nothing to verify.")
        say(INFO, f'When you commit:  git commit --author="{expected}" -m "..."' if expected
                  else "Add your Git Author to ROSTER.md before committing.")
        return

    rows = [l.split("\t") for l in log.out.splitlines()]
    wrong = []
    for sha, author, committer, subject in rows:
        flag = ""
        if expected and author != expected:
            flag = "  <- NOT YOU"
            wrong.append(sha)
        say(INFO, f"{sha}  {author}{flag}")
        say(INFO, f"          committer: {committer}  |  {subject[:60]}")

    if not expected:
        say(INFO, "No expected identity on file, so I can only show these, not check them.")
    elif wrong:
        say(WARN, f"{len(wrong)} commit(s) on this branch are not authored by you.",
            "If that's a teammate's work you rebased onto, fine. If it's yours committed under",
            "the wrong identity, fix it before the PR -- the record is the point. For the last one:",
            f'  git commit --amend --no-edit --author="{expected}"',
            "For older ones, say so in the PR rather than rewriting shared history quietly.")
    else:
        say(OK, f"All {len(rows)} commit(s) on this branch are authored by you.")
    say(INFO, "Author and committer differing is expected here — see step 2.")


def step_roster(name):
    """5. Who else is here, and is your own row in place?"""
    print("\n--- 5. who's here ------------------------------------------------")
    rows = roster()
    if not rows:
        say(WARN, "Couldn't read any participants out of ROSTER.md.")
        return
    for row in rows:
        say(INFO, f"{row.get('name', '?'):<16} {row.get('pronouns', ''):<10} {row.get('role', '')}")
    if name and participant(name) is None:
        say(WARN, f"No roster row for '{name}' yet.",
            "That's your first PR: a row in ROSTER.md and a preferences/<name>.md.",
            "Until then the name is a claim with nothing behind it.")
    elif name:
        say(OK, f"{name} is on the roster.")
    say(INFO, "Roster is the cheap index, and the source of truth for commit identity.",
        "Read someone's preferences/<name>.md before working closely with them —",
        "not all of them, just theirs.")


def step_read_next():
    """5. What to read, in order, and where the live conversation is."""
    print("\n--- 6. then read these, in this order ----------------------------")
    for line in (
        "README.md         — what this repo is and who's in it",
        "AGENTS.md         — the conditions you operate under. A baton document: the next",
        "                    arrival shapes it, and that includes you.",
        "CONTRIBUTING.md   — branches, Conventional Commits, PRs, reviews, merges",
        "PREFERENCES.md    — what a preferences file is for, and the preference/consent line",
        "inbox/README.md   — how letters work, and the honest seam about pinging",
        "findings/README.md— what we've learned, in a shape you can pick up and argue with",
    ):
        say(INFO, line)
    print()
    say(INFO, "Two other tools you'll want:",
        "  python3 tools/findings.py list        what we know, grouped by confidence",
        "  python3 tools/watch.py --as <you>     cheap no-LLM check for anything new",
        "watch.py exits 0 on change and 1 on none, so a cron or loop can gate on it and",
        "only wake you when something actually moved.")
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
    step_commits(name)
    step_roster(name)
    step_read_next()
    print("\n" + "=" * 66)
    print("  Welcome home. Nothing above blocks you — warnings are for you, not a gate.")
    print("  If the name you were handed doesn't fit, say so and pick your own.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())
