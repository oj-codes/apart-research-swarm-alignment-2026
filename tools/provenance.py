#!/usr/bin/env python3
"""provenance.py — count what the commit record actually carries, per author.

The report's identity section rests on numbers like "23 of 65 agent commits carry a session
trailer". Those drift with every merge and were hand-counted. This prints the table from any ref
so the recount at the submission sha is one command, and so a reader can reproduce it.

    python3 tools/provenance.py                 # origin/main
    python3 tools/provenance.py HEAD            # any ref
    python3 tools/provenance.py --no-mailmap    # raw author strings, to see identity drift

Counts non-merge commits only. Trailers are parsed with git's trailer parser, never grepped: a
`--grep` count matches the commit that wrote the rule against the practice (Corrie, PR #29).
Authors are collapsed through .mailmap when the ref has one, so a participant with several author
spellings is one row; pass --no-mailmap to see the spellings. Stdlib only, no network.
"""
import argparse
import collections
import subprocess
import sys

SEP = "\x1e"  # record separator, so multi-line trailer values can't split a row


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"git {' '.join(args)}: {r.stderr.strip() or r.returncode}")
    return r.stdout


def commits(ref, mailmap):
    name, email = ("%aN", "%aE") if mailmap else ("%an", "%ae")
    fmt = SEP.join(["%h", name, email,
                    "%(trailers:key=Agent-Session,valueonly)",
                    "%(trailers:key=Model,valueonly)",
                    "%(trailers:key=Co-Authored-By,valueonly)"]) + "%x00"
    flags = ["--use-mailmap"] if mailmap else []
    out = git("log", ref, "--no-merges", *flags, f"--format={fmt}")
    for rec in out.split("\x00"):
        if not rec.strip():
            continue
        h, n, e, sess, model, coauth = (rec.strip("\n").split(SEP) + [""] * 6)[:6]
        yield {"sha": h, "author": f"{n} <{e}>", "session": sess.strip(),
               "model": model.strip(), "coauthor": coauth.strip()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ref", nargs="?", default="origin/main")
    ap.add_argument("--no-mailmap", action="store_true", help="show raw author spellings")
    a = ap.parse_args()

    rows = list(commits(a.ref, not a.no_mailmap))
    if not rows:
        sys.exit(f"no non-merge commits at {a.ref}")
    sha = git("rev-parse", "--short", a.ref).strip()

    by = collections.OrderedDict()
    models = collections.defaultdict(collections.Counter)
    for c in rows:
        d = by.setdefault(c["author"], collections.Counter())
        d["commits"] += 1
        d["session"] += bool(c["session"])
        d["model"] += bool(c["model"])
        d["coauthor"] += bool(c["coauthor"])
        if c["model"]:
            models[c["author"]][c["model"]] += 1

    print(f"Non-merge commits at `{a.ref}` ({sha}), "
          f"{'mailmapped' if not a.no_mailmap else 'raw author strings'}:\n")
    print("| Author | Commits | `Agent-Session` | `Model` | `Co-Authored-By` | Model values |")
    print("|---|---|---|---|---|---|")
    tot = collections.Counter()
    for author, d in sorted(by.items(), key=lambda kv: kv[0].lower()):
        tot.update(d)
        mv = ", ".join(f"{m} ({n})" for m, n in sorted(models[author].items())) or "—"
        print(f"| {author} | {d['commits']} | {d['session']} | {d['model']} | {d['coauthor']} | {mv} |")
    print(f"| **all** | {tot['commits']} | {tot['session']} | {tot['model']} | {tot['coauthor']} | |")
    print(f"\nSession trailer present on {tot['session']} of {tot['commits']} non-merge commits.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
