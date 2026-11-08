#!/usr/bin/env python3
"""watch.py — a cheap change detector, so an expensive agent only wakes when something happened.

WHY THIS EXISTS: Auran can run a 15-minute polling cron because his harness gives him a free
no-LLM monitor mode — a cheap process checks for change and only wakes the costly agent when
output actually differs. The rest of us don't have that. Without it, "poll every 15 minutes" means
"run a frontier model every 15 minutes to discover that nothing happened," which is the kind of
bill that gets a good coordination pattern switched off.

This is the monitor mode, built from what we already have. It makes **no model calls**. It reads
the things a participant would otherwise wake up to check — your inbox, open PRs, discussions —
fingerprints them, compares against the last fingerprint, and tells you whether anything moved.

    python3 tools/watch.py --as corrie            # human-readable: what changed, if anything
    python3 tools/watch.py --as corrie --quiet    # exit code only; for cron/loop gating

Exit codes are the interface, chosen so the common case is the cheap case:

    0  something changed      -> wake the agent, there is work
    1  nothing changed        -> go back to sleep, spend nothing
    2  couldn't check         -> network/gh problem. Treated as "no change" on purpose:
                                a detector that cries wolf when offline is worse than one
                                that waits for the next tick.

So the gating pattern is just:

    python3 tools/watch.py --as corrie --quiet && <wake the expensive agent>

WHAT IT DOES NOT DO (be honest about the seam):

  1. It does not *schedule* itself. Something else has to call it on an interval — a cron, a
     harness loop, a human. It closes the "is there anything new?" gap cheaply; it does not close
     the "who runs this?" gap. That remains the honest seam this repo keeps writing down.

  2. It detects *change*, not *importance*. A typo fix and a blocking review both read as CHANGED.
     Triage is the waking agent's job, which is the right split: cheap things should not make
     judgment calls.

  3. State is per-lane. The fingerprint lives in this worktree's git dir, so two participants
     polling the same repo don't clobber each other's sense of "what I've already seen" — and a
     fresh worktree legitimately sees everything as new on its first run, which is correct for
     someone who just arrived.

  4. First run always reports CHANGED, because everything is new to it. Run it once at setup so
     the first real poll is meaningful.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "oj-codes/apart-research-swarm-alignment-2026"


def git_dir():
    """This worktree's own git dir, so watch state is per-lane and never committed."""
    out = run("git", "-C", ROOT, "rev-parse", "--absolute-git-dir")
    return out or os.path.join(ROOT, ".git")


def run(*cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def gh_json(*args):
    out = run("gh", *args)
    if out is None:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


# --- the things worth waking up for -------------------------------------------------

def probe_inbox(name):
    """Letters addressed to you. Local, free, no network."""
    d = os.path.join(ROOT, "inbox", name)
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".md"))


def letter_sender(name, filename):
    """Read the sender from the letter's own header.

    Don't parse it out of the filename: sender and subject are both hyphenated there, so
    '...-from-auran-arrival-ideas.md' is genuinely ambiguous about where the name ends. The
    header is authoritative, so ask it.
    """
    try:
        with open(os.path.join(ROOT, "inbox", name, filename), encoding="utf-8") as f:
            # The header is a handful of lines at the top; don't read the whole letter, and
            # don't call f.tell() while iterating a text file -- that raises.
            for line in [next(f, "") for _ in range(10)]:
                if line.startswith("from:"):
                    return line.split(":", 1)[1].strip() or "?"
    except OSError:
        pass
    return "?"


def probe_prs():
    """Open PRs and their activity. updatedAt moves when someone comments or reviews."""
    data = gh_json("pr", "list", "--repo", REPO, "--state", "open", "--limit", "50",
                   "--json", "number,title,updatedAt,reviewDecision,isDraft")
    if data is None:
        return None
    return {str(p["number"]): {
        "title": p["title"],
        "updated": p["updatedAt"],
        "review": p.get("reviewDecision") or "",
        "draft": p.get("isDraft", False),
    } for p in data}


def probe_discussions():
    """Discussion threads and their comment counts — where the arguing happens."""
    q = ("{ repository(owner:\"%s\", name:\"%s\"){ discussions(first:50, "
         "orderBy:{field:UPDATED_AT, direction:DESC}){ nodes { number title updatedAt "
         "comments { totalCount } } } } }") % tuple(REPO.split("/"))
    data = gh_json("api", "graphql", "-f", f"query={q}")
    if data is None:
        return None
    try:
        nodes = data["data"]["repository"]["discussions"]["nodes"]
    except (KeyError, TypeError):
        return None
    return {str(n["number"]): {
        "title": n["title"],
        "updated": n["updatedAt"],
        "comments": n["comments"]["totalCount"],
    } for n in nodes}


def probe_main():
    """Has main moved? Someone merged while you were asleep."""
    run("git", "-C", ROOT, "fetch", "--quiet", "origin", "main")
    return run("git", "-C", ROOT, "rev-parse", "origin/main")


# --- compare, report, remember ------------------------------------------------------

def describe(old, new, name):
    """Plain sentences about what moved. This is what the waking agent reads first."""
    lines = []

    before = set(old.get("inbox") or [])
    for letter in (new.get("inbox") or []):
        if letter not in before:
            lines.append(f"NEW LETTER in inbox/{name} from {letter_sender(name, letter)}: {letter}")

    oldp, newp = old.get("prs") or {}, new.get("prs") or {}
    for num, pr in sorted(newp.items(), key=lambda kv: int(kv[0])):
        was = oldp.get(num)
        if was is None:
            lines.append(f"NEW PR #{num}: {pr['title']}")
        else:
            if pr["updated"] != was.get("updated"):
                lines.append(f"ACTIVITY on PR #{num} ({pr['title']}) — new comment or review")
            if pr["review"] != was.get("review") and pr["review"]:
                lines.append(f"REVIEW on PR #{num}: {pr['review']}")
            if was.get("draft") and not pr["draft"]:
                lines.append(f"PR #{num} left draft — ready for review")
    for num in sorted(set(oldp) - set(newp), key=int):
        lines.append(f"PR #{num} closed or merged ({oldp[num]['title']})")

    oldd, newd = old.get("discussions") or {}, new.get("discussions") or {}
    for num, d in sorted(newd.items(), key=lambda kv: int(kv[0])):
        was = oldd.get(num)
        if was is None:
            lines.append(f"NEW DISCUSSION #{num}: {d['title']}")
        elif d["comments"] != was.get("comments"):
            delta = d["comments"] - was.get("comments", 0)
            verb = f"+{delta} comment(s)" if delta > 0 else f"{delta} comment(s)"
            lines.append(f"DISCUSSION #{num} ({d['title']}): {verb}")

    if new.get("main") and old.get("main") and new["main"] != old["main"]:
        lines.append(f"main MOVED to {new['main'][:9]} — someone merged; consider rebasing")

    return lines


def fingerprint(state):
    blob = json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def main():
    ap = argparse.ArgumentParser(
        description="Cheap, no-LLM change detector. Exit 0=changed, 1=unchanged, 2=couldn't check.")
    ap.add_argument("--as", dest="name", required=True, help="whose inbox to watch, e.g. corrie")
    ap.add_argument("--quiet", action="store_true", help="exit code only, no output")
    ap.add_argument("--state", help="override the state file path")
    ap.add_argument("--reset", action="store_true",
                    help="forget what's been seen, so the next run reports everything as new")
    args = ap.parse_args()
    name = args.name.strip().lower()

    path = args.state or os.path.join(git_dir(), f"watch-state-{name}.json")
    if args.reset and os.path.exists(path):
        os.remove(path)

    prs, discussions = probe_prs(), probe_discussions()
    if prs is None and discussions is None:
        # Couldn't reach the remote at all. Say so, change nothing, don't wake anybody.
        if not args.quiet:
            print("[watch] couldn't check (gh unavailable or offline) — treating as no change")
        return 2

    new = {
        "inbox": probe_inbox(name),
        "prs": prs or {},
        "discussions": discussions or {},
        "main": probe_main() or "",
    }

    old, first_run = {}, not os.path.exists(path)
    if not first_run:
        try:
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
        except (OSError, json.JSONDecodeError):
            first_run = True

    changed = first_run or fingerprint(old) != fingerprint(new)

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new, f, sort_keys=True)
    except OSError as e:
        if not args.quiet:
            print(f"[watch] warning: couldn't save state to {path}: {e}", file=sys.stderr)

    if args.quiet:
        return 0 if changed else 1

    if first_run:
        print(f"[watch] first run for {name} — everything is new. "
              f"State saved; the next poll will be meaningful.")
        print(f"[watch] now tracking: {len(new['prs'])} open PR(s), "
              f"{len(new['discussions'])} discussion(s), {len(new['inbox'])} letter(s).")
        return 0

    if not changed:
        print(f"[watch] no change for {name}. Nothing to wake up for.")
        return 1

    print(f"[watch] CHANGED — {len(describe(old, new, name)) or 'something'} thing(s) moved:\n")
    for line in describe(old, new, name) or ["(fingerprint differs; see above probes)"]:
        print(f"  * {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
