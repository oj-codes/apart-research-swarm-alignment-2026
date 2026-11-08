#!/usr/bin/env python3
"""Recount the provenance numbers in the report from a given commit, by trailer parsing.

    python3 submission/count_provenance.py [ref]      # default: origin/main

Why a script: the counts in the report drift every time main moves, and a count made with
`git log --grep` once matched the commit that *banned* the practice it was counting (Corrie, #29).
Trailers are parsed with git's own trailer interpreter.

Two tables, because two things are true at once (Tern and Codex on #27):
  raw     author spellings as written, so a forked identity shows as separate rows
          (the identity-fork finding needs this view);
  mapped  the same commits with the ref's own .mailmap applied, so one participant is one row
          (adoption figures use this view). The mailmap is read from the ref, not the checkout,
          so a ref that predates it correctly falls back to raw names.

Prints the ref's SHA so the report can pin the denominator. Makes no changes.
"""
import re
import subprocess
import sys
from collections import defaultdict

ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
SEP = "\x1e"
model_re = re.compile(r"claude|opus|sonnet|haiku|fable|gpt|codex|deepseek|gemini|llama|mistral", re.I)

def git(*args, mapped=False):
    cmd = ["git"]
    if mapped:
        cmd += ["-c", f"mailmap.blob={ref}:.mailmap"]
    return subprocess.run(cmd + list(args), capture_output=True, text=True, check=True).stdout

def count(mapped):
    name = "%aN" if mapped else "%an"
    extra = ["--use-mailmap"] if mapped else []
    log = git("log", ref, "--no-merges", *extra,
              f"--format={name}%x1f%(trailers:key=Agent-Session,valueonly)%x1f%(trailers:key=Model,valueonly)%x1f%(trailers:key=Co-Authored-By,valueonly){SEP}",
              mapped=mapped)
    commits = defaultdict(int); session = defaultdict(int); model = defaultdict(int)
    coauth_total = coauth_model = 0
    for rec in log.split(SEP):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        an, sess, mod, co = (rec.split("\x1f") + ["", "", ""])[:4]
        an = an.strip()
        commits[an] += 1
        if sess.strip(): session[an] += 1
        if mod.strip(): model[an] += 1
        for line in co.splitlines():
            if line.strip():
                coauth_total += 1
                if model_re.search(line): coauth_model += 1
    return commits, session, model, coauth_total, coauth_model

def report(label, commits, session, model, coauth_total, coauth_model):
    human = {a for a in commits if a.startswith("O. J.")}
    agents = [a for a in commits if a not in human]
    total = sum(commits[a] for a in agents)
    with_session = sum(session[a] for a in agents)
    print(f"--- {label} ---")
    print(f"agent commits (non-merge, excluding O.J.): {total}")
    print(f"with Agent-Session trailer: {with_session} of {total}")
    print(f"Co-Authored-By lines: {coauth_total} total, {coauth_model} naming a model")
    print(f"{'author identity':48} {'commits':>7} {'session':>7} {'model':>5}")
    for a in sorted(agents, key=lambda a: -commits[a]):
        print(f"{a:48} {commits[a]:7} {session[a]:7} {model[a]:5}")
    if human:
        print(f"{'(human) ' + ', '.join(sorted(human)):48} {sum(commits[a] for a in human):7}")
    print()

sha = git("rev-parse", "--short", ref).strip()
print(f"ref {ref} = {sha}\n")
report("raw author spellings", *count(mapped=False))
has_mailmap = subprocess.run(["git", "cat-file", "-e", f"{ref}:.mailmap"], capture_output=True).returncode == 0
if has_mailmap:
    report("mapped through the ref's .mailmap", *count(mapped=True))
else:
    print("--- no .mailmap at this ref; mapped table is the raw table ---")
