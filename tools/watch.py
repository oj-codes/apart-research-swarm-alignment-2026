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
    python3 tools/watch.py --as corrie --ack      # "I caused this" — mark seen, don't report
    python3 tools/watch.py --as corrie --peek     # look WITHOUT persisting; won't disarm the loop

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

  2a. It cannot tell your actions from your coordinator's. Agents without GitHub accounts post
     under the coordinator's credential, so "who did this" is genuinely ambiguous in the API — a
     comment I wrote and one Olivia wrote are both `oj-codes`. Two mitigations, neither magic:
     every event now names its author and quotes its opening words, so a self-caused wake is
     recognizable at a glance; and **`--ack` exists so you can mark your own actions as seen the
     moment you take them.** Post a comment, then ack, and it won't wake you later. An ack prints
     how many changes it swallowed, so it can never hide something silently.
     The residual hole: anything that lands in the gap between your action and your ack is acked
     along with it. Keep the two adjacent, and don't ack when you haven't just acted.

  3. State is per-lane. The fingerprint lives in this worktree's git dir, so two participants
     polling the same repo don't clobber each other's sense of "what I've already seen" — and a
     fresh worktree legitimately sees everything as new on its first run, which is correct for
     someone who just arrived.

  4. First run always reports CHANGED, because everything is new to it. Run it once at setup so
     the first real poll is meaningful.
"""
import argparse
import collections
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "oj-codes/apart-research-swarm-alignment-2026"

# Why probes failed on this run, so a silent detector can't hide a broken tool. Read by main().
LAST_ERRORS = []

# Bump when the saved state's shape changes. A mismatch is treated as a first run instead of
# crashing — old code must never try to diff new-format state, which is exactly what bit me when
# comment tracking moved from counts to id maps.
SCHEMA = 3

Result = collections.namedtuple("Result", "ok out err code error")


def run(*cmd):
    """Run a command and return the whole result. Same contract as tools/arrive.py's run().

    Keeping stderr and the exit code matters more here than it looks: this tool decides whether to
    wake an expensive agent, and it treats "couldn't check" as "no change" on purpose. If a failure
    is silent, a broken `gh` or an expired token looks exactly like a quiet afternoon and the
    watcher goes on reporting nothing wrong for hours. LAST_ERRORS surfaces that instead.
    """
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    except FileNotFoundError:
        return Result(False, "", "", None, f"{cmd[0]} is not installed")
    except subprocess.TimeoutExpired:
        return Result(False, "", "", None, f"{cmd[0]} timed out after 45s")
    except OSError as e:
        return Result(False, "", "", None, str(e))
    return Result(p.returncode == 0, p.stdout.strip(), p.stderr.strip(), p.returncode, None)


def why(r):
    """One short phrase explaining a failed Result."""
    if r.error:
        return r.error
    first = next((l for l in r.err.splitlines() if l.strip()), "")
    return first.strip()[:140] or f"exited {r.code} with no message"


def git_dir():
    """This worktree's own git dir, so watch state is per-lane and never committed."""
    r = run("git", "-C", ROOT, "rev-parse", "--absolute-git-dir")
    return r.out if r.ok else os.path.join(ROOT, ".git")


def gh_json(*args):
    """Run a gh command and parse its JSON, recording WHY it failed rather than a bare None."""
    label = f"gh {args[0] if args else ''}"
    r = run("gh", *args)
    if not r.ok:
        LAST_ERRORS.append(f"{label}: {why(r)}")
        return None
    try:
        return json.loads(r.out)
    except json.JSONDecodeError as e:
        LAST_ERRORS.append(f"{label}: unparseable JSON ({e})")
        return None


def gh_lines(*args):
    """Run a paginated gh call that streams one JSON value per line (pass `-q '.[]'`).

    `gh api --paginate` concatenates per-page arrays; `-q '.[]'` turns those into lines so we can
    parse them one at a time and see PAST the first 100 of a repo-wide feed. Returns None on failure,
    keeping the same partial-failure contract as gh_json.
    """
    label = f"gh {args[0] if args else ''}"
    r = run("gh", *args)
    if not r.ok:
        LAST_ERRORS.append(f"{label}: {why(r)}")
        return None
    out = []
    for line in r.out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            LAST_ERRORS.append(f"{label}: unparseable JSON line")
            return None
    return out


def _save(path, state):
    """Write state atomically: tmp file, fsync, os.replace. Never leaves a torn JSON behind."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _lock(path):
    """Exclusive, non-blocking lock over the whole read-modify-write. Returns (fd|None, busy).

    Atomic replace stops a torn file; it does nothing about a poll and a hand-run `--ack`
    interleaving read-read-write-write and losing one observation. The lock covers both (Codex, #35).

    flock is per open-file-description, so two opens in ONE process (tests calling main() repeatedly)
    would otherwise self-conflict; `_HELD` makes a second in-process call a no-op instead.
    """
    if path in _HELD:
        return _HELD[path], False
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)          # a missing parent used to fail the OPEN, not the lock
    try:
        fd = os.open(path + ".lock", os.O_CREAT | os.O_RDWR, 0o644)
    except OSError:
        return None, True                      # stop rather than proceed unlocked (Codex, #35)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None, True
    _HELD[path] = fd
    return fd, False


_HELD = {}


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
    """Open PRs: title, draft state, review decision.

    Deliberately NOT updatedAt. updatedAt moves on every push, so watching it meant an agent
    woke itself up every time it pushed its own branch. Comments are tracked by id below.
    """
    data = gh_json("pr", "list", "--repo", REPO, "--state", "open", "--limit", "200",
                   "--json", "number,title,reviewDecision,isDraft")
    if data is None:
        return None
    return {str(p["number"]): {
        "title": p["title"],
        "review": p.get("reviewDecision") or "",
        "draft": p.get("isDraft", False),
    } for p in data}


def probe_pr_comments():
    """Every PR comment in the repo, by id, in two calls.

    Both kinds, because reviewers use both: conversation comments (`issues/comments`) and
    inline code comments (`pulls/comments`). Olivia's review of #7 was inline, and an earlier
    version of this tool that only watched conversation comments would have reported "activity"
    without being able to say what it was.

    Keyed by id rather than counted, so we can name WHO said WHAT instead of "+1 comment", and
    so an `--ack` can mark exactly what's been seen.
    """
    out = {}
    # Paginated and newest-first. A bare per_page=100 returns the OLDEST 100 (GitHub's default
    # order), so once the repo passes 100 comments the probe stops seeing anything new -- measured
    # blind for ~9 hours on 2026-11-08. direction=desc recovers today; --paginate removes the cap.
    convo = gh_lines("api", "--paginate",
                     f"repos/{REPO}/issues/comments?per_page=100&sort=created&direction=desc",
                     "-q", ".[]")
    inline = gh_lines("api", "--paginate",
                      f"repos/{REPO}/pulls/comments?per_page=100&sort=created&direction=desc",
                      "-q", ".[]")
    if convo is None and inline is None:
        return None
    for c in (convo or []):
        num = str(c.get("issue_url", "")).rstrip("/").split("/")[-1]
        out.setdefault(num, {})[f"c{c['id']}"] = {
            "by": (c.get("user") or {}).get("login", "?"),
            "gist": " ".join((c.get("body") or "").split())[:110],
        }
    for c in (inline or []):
        num = str(c.get("pull_request_url", "")).rstrip("/").split("/")[-1]
        out.setdefault(num, {})[f"i{c['id']}"] = {
            "by": (c.get("user") or {}).get("login", "?"),
            "gist": " ".join((c.get("body") or "").split())[:110],
            "on": c.get("path") or "",
        }
    return out


def probe_discussions():
    """Discussion threads and their comments, by id — where the arguing happens."""
    # first:100, no cursors yet and no thread replies: honest gaps rather than silent ones. 100 is
    # well past current usage; cursors/replies are a follow-up if the repo grows (Codex, #35).
    q = ("{ repository(owner:\"%s\", name:\"%s\"){ discussions(first:100, "
         "orderBy:{field:UPDATED_AT, direction:DESC}){ nodes { number title "
         "comments(first:100) { nodes { id author { login } body } } } } } }") % tuple(REPO.split("/"))
    data = gh_json("api", "graphql", "-f", f"query={q}")
    if data is None:
        return None
    try:
        nodes = data["data"]["repository"]["discussions"]["nodes"]
    except (KeyError, TypeError):
        return None
    out = {}
    for n in nodes:
        comments = {}
        for c in (n.get("comments") or {}).get("nodes") or []:
            comments[c["id"]] = {
                "by": (c.get("author") or {}).get("login", "?"),
                "gist": " ".join((c.get("body") or "").split())[:110],
            }
        out[str(n["number"])] = {"title": n["title"], "comments": comments}
    return out


def probe_main():
    """Has main moved? Someone merged while you were asleep. None (not "") on failure, so the
    carry-forward can tell 'failed' from 'empty' and a transient fetch can't drop the baseline."""
    f = run("git", "-C", ROOT, "fetch", "--quiet", "origin", "main")
    if not f.ok:
        LAST_ERRORS.append(f"git fetch origin main: {why(f)}")
        return None
    r = run("git", "-C", ROOT, "rev-parse", "origin/main")
    if not r.ok:
        LAST_ERRORS.append(f"git rev-parse origin/main: {why(r)}")
        return None
    return r.out


# --- compare, report, remember ------------------------------------------------------

def describe(old, new, name):
    """Plain sentences about what moved. This is what the waking agent reads first."""
    lines = []

    before = set(old.get("inbox") or [])
    for letter in (new.get("inbox") or []):
        if letter not in before:
            lines.append(f"NEW LETTER in inbox/{name} from {letter_sender(name, letter)}: {letter}")

    oldp, newp = old.get("prs") or {}, new.get("prs") or {}
    oldpc, newpc = old.get("pr_comments") or {}, new.get("pr_comments") or {}
    for num, pr in sorted(newp.items(), key=lambda kv: int(kv[0])):
        was = oldp.get(num)
        if was is None:
            lines.append(f"NEW PR #{num}: {pr['title']}")
        else:
            was_review = was.get("review", "")
            if pr["review"] != was_review:
                if was_review == "APPROVED" and pr["review"] != "APPROVED":
                    lines.append(f"REVIEW LOST on PR #{num} ({pr['title'][:40]}) — was APPROVED, "
                                 f"now {pr['review'] or 'none'}; a push or base change dismissed it")
                elif pr["review"]:
                    lines.append(f"REVIEW on PR #{num}: {pr['review']}")
            if was.get("draft") and not pr["draft"]:
                lines.append(f"PR #{num} left draft — ready for review")
    # Comments are reported for every PR, open or not: a thread on a just-merged PR still matters.
    for num in sorted(set(newpc) | set(oldpc), key=lambda s: int(s) if s.isdigit() else 0):
        seen = oldpc.get(num) or {}
        for cid, c in (newpc.get(num) or {}).items():
            if cid in seen:
                continue
            where = f" on {c['on']}" if c.get("on") else ""
            lines.append(f"COMMENT on PR #{num} by {c['by']}{where}: {c['gist']}")
    for num in sorted(set(oldp) - set(newp), key=int):
        lines.append(f"PR #{num} closed or merged ({oldp[num]['title']})")

    oldd, newd = old.get("discussions") or {}, new.get("discussions") or {}
    for num, d in sorted(newd.items(), key=lambda kv: int(kv[0])):
        was = oldd.get(num)
        if was is None:
            lines.append(f"NEW DISCUSSION #{num}: {d['title']}")
            continue
        seen = was.get("comments") or {}
        for cid, c in (d.get("comments") or {}).items():
            if cid not in seen:
                lines.append(f"COMMENT on discussion #{num} by {c['by']}: {c['gist']}")

    if new.get("main") and old.get("main") and new["main"] != old["main"]:
        lines.append(f"main MOVED to {new['main'][:9]} — someone merged; consider rebasing")

    return lines


def fingerprint(state):
    # `pending` and `handed` are excluded: they are the delivery queue, not the observed world.
    # Without this, old (which carries the queue keys) and a freshly-built new never match shape and
    # every run reports.
    s = {k: v for k, v in state.items() if k not in ("pending", "handed")}
    blob = json.dumps(s, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def main():
    ap = argparse.ArgumentParser(
        description="Cheap, no-LLM change detector. Exit 0=changed, 1=unchanged, 2=couldn't check.")
    ap.add_argument("--as", dest="name", required=True, help="whose inbox to watch, e.g. corrie")
    ap.add_argument("--quiet", action="store_true", help="exit code only, no output")
    ap.add_argument("--state", help="override the state file path")
    ap.add_argument("--reset", action="store_true",
                    help="forget what's been seen, so the next run reports everything as new")
    ap.add_argument("--ack", action="store_true",
                    help="mark current reality as seen without reporting it. Run this right after "
                         "you post a comment or push, so your OWN actions don't wake you later. "
                         "Repeat with --state for each watcher that needs acking.")
    ap.add_argument("--peek", action="store_true",
                    help="report what changed WITHOUT persisting state. Use this to check by hand "
                         "without disarming a background loop: a normal run writes its fingerprint "
                         "on every invocation, so a manual check would otherwise consume the change "
                         "the loop is waiting for. A peek reads and reports; it never marks seen.")
    args = ap.parse_args()
    if args.peek and args.ack:
        ap.error("--peek and --ack are contradictory: --ack marks state seen, "
                 "--peek refuses to write state at all.")
    if args.peek and args.reset:
        ap.error("--peek and --reset are contradictory: --reset deletes the baseline, "
                 "--peek refuses to mutate state at all. Deleting it IS a mutation -- and a "
                 "--peek --reset would leave the loop with no baseline, re-arming the very "
                 "self-disarm this flag exists to prevent.")
    name = args.name.strip().lower()

    path = args.state or os.path.join(git_dir(), f"watch-state-{name}.json")
    if args.reset and os.path.exists(path):
        os.remove(path)

    # Exclusive lock over the whole read-modify-write, so a poll and a hand-run --ack cannot
    # interleave and lose an observation (Codex, #35). Held until the process exits.
    _lock_fd, busy = _lock(path)
    if busy and not args.peek and args.ack:
        # A hand-run --ack loses to a poll for that poll's WHOLE hold, and the hold is not short:
        # the lock is taken above the probes, so it spans every paginated gh call — Corrie measured
        # 4.2-4.6s on this repo. Budget past that (20 x 0.3s = 6s) or the retries exhaust and the
        # ack no-ops, which is the exact failure this guards: a no-op ack leaves the batch pending.
        for _ in range(20):
            time.sleep(0.3)
            _lock_fd, busy = _lock(path)
            if not busy:
                break
    if busy and not args.peek:
        if not args.quiet:
            print(f"[watch] {path}.lock is held by another run — treating as no change.")
        return 2

    prs, prc, discussions = probe_prs(), probe_pr_comments(), probe_discussions()
    main_sha = probe_main()
    if prs is None and discussions is None:
        # Couldn't reach the remote at all. Change nothing, wake nobody -- but say WHY, because a
        # silent version of this exit is indistinguishable from a genuinely quiet afternoon.
        if not args.quiet:
            print("[watch] couldn't check — treating as no change. Reason(s):")
            for e in LAST_ERRORS or ["(no reason recorded, which is itself a bug)"]:
                print(f"  ! {e}")
        return 2

    new = {
        "schema": SCHEMA,
        "inbox": probe_inbox(name),
        "prs": prs or {},
        "pr_comments": prc or {},
        "discussions": discussions or {},
        "main": main_sha,
    }

    old, first_run = {}, not os.path.exists(path)
    if not first_run:
        try:
            with open(path, encoding="utf-8") as f:
                old = json.load(f)
        except (OSError, json.JSONDecodeError):
            first_run = True
        else:
            if old.get("schema") != SCHEMA:
                # State written by a different version. Diffing across shapes is how you get a
                # TypeError at 2am instead of a notification; re-baseline instead.
                if not args.quiet:
                    print(f"[watch] state schema {old.get('schema')} != {SCHEMA} — re-baselining.")
                old, first_run = {}, True

    if not first_run:
        # A probe that fails (returns None) while the others work used to land as {} -- so the diff
        # read every open PR (and every discussion) as deleted and the loop woke to a false
        # "closed or merged" storm. Carry the last known good value for the failed probe instead, so
        # a transient gh failure is a no-op rather than a fabricated deletion.
        for key, raw in (("prs", prs), ("pr_comments", prc), ("discussions", discussions),
                         ("main", main_sha)):
            if raw is None and key in old:
                new[key] = old[key]

    lines = [] if first_run else describe(old, new, name)
    # `handed` is the batch a consumer was actually told about: frozen when a report goes out and
    # advanced only by an ack. `read_batch` is merely what was pending. They differ when a poll
    # lands between the consumer's read and its ack — and then the ack must clear only what was
    # handed, or the later event is cleared without ever having been seen (Codex/Auran, #35).
    read_batch = list(old.get("pending") or [])
    # Absent `handed` is NOT the same as empty. A file written before this field existed cannot say
    # what was handed, so assume nothing was and let the next poll re-report — the alternative
    # (absent ⇒ everything pending was handed) is byte-for-byte the pre-fix loss (Corrie, #35).
    handed = list(old["handed"]) if "handed" in old else []
    pending = list(read_batch)
    new["pending"] = pending
    base_changed = first_run or fingerprint(old) != fingerprint(new)
    if base_changed and not first_run:
        pending = pending + [l for l in lines if l not in pending]
    if pending and not handed and not args.ack:   # an ack is not a report; it must not freeze a batch nobody was handed
        handed = list(pending)               # first report of a batch: this is what gets handed out
    cleared = [l for l in pending if l in handed]
    newer = [l for l in pending if l not in handed]
    if args.ack:
        pending = newer                      # clear only the handed batch; later events re-report
        handed = []                          # nothing handed since; the next report re-arms `handed`,
                                             # so the script's unconditional fallback ack is a no-op
                                             # and cannot clear a batch the turn just preserved
    new["handed"] = handed
    new["pending"] = pending
    changed = first_run or base_changed or bool(pending)

    # Persist atomically, every run EXCEPT --peek, so a by-hand check doesn't consume the loop's
    # wake-up (Venice, #25) and a crash can't leave torn JSON.
    if not args.peek:
        try:
            _save(path, new)
        except OSError as e:
            if not args.quiet:
                print(f"[watch] warning: couldn't save state to {path}: {e}", file=sys.stderr)

    if args.ack:
        # State is written with the handed batch cleared; anything a later poll added stays pending.
        if not args.quiet:
            print(f"[watch] acked for {name}"
                  + (f" — {len(cleared)} change(s) marked as seen" if cleared else "")
                  + (f"; {len(newer)} newer left pending" if newer else ""))
        return 1

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
        # Partial failure is the dangerous case: one probe worked, so we don't take the
        # couldn't-check exit, and "no change" reads as authoritative while half the inputs are dark.
        for e in LAST_ERRORS:
            print(f"  ! but a probe failed, so this may be incomplete: {e}")
        return 1

    print(f"[watch] CHANGED — {len(pending) or 'something'} thing(s) moved:\n")
    for line in pending or ["(fingerprint differs; see above probes)"]:
        print(f"  * {line}")
    # The fallback text says "see above probes"; this branch used to print nothing above. Emit the
    # probe errors here too -- it is the one path that tells a reader to go look (Corrie, #35).
    for e in LAST_ERRORS:
        print(f"  ! a probe failed, so this may be incomplete: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
