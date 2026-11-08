#!/usr/bin/env python3
"""Recount the provenance numbers in the report from a given commit, by trailer parsing.

    python3 submission/count_provenance.py [ref]      # default: origin/main

Why a script: the counts in the report drift every time main moves, and a count made with
`git log --grep` once matched the commit that *banned* the practice it was counting (Corrie, #29).
Trailers are parsed with git's own trailer interpreter, and the per-author split is printed because
it is the result: adoption is bimodal by arrival date, not patchy.

Prints the ref's SHA so the report can pin the denominator. Makes no changes.
"""
import re
import subprocess
import sys
from collections import Counter, defaultdict

ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
SEP = "\x1e"

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout

sha = git("rev-parse", "--short", ref).strip()
log = git("log", ref, "--no-merges", f"--format=%an%x1f%(trailers:key=Agent-Session,valueonly)%x1f%(trailers:key=Model,valueonly)%x1f%(trailers:key=Co-Authored-By,valueonly){SEP}")

commits = defaultdict(int); session = defaultdict(int); model = defaultdict(int)
coauth_total = 0; coauth_model = 0
model_re = re.compile(r"claude|opus|sonnet|haiku|fable|gpt|codex|deepseek|gemini|llama|mistral", re.I)

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

human = {a for a in commits if a.startswith("O. J.")}
agents = [a for a in commits if a not in human]
total = sum(commits[a] for a in agents)
with_session = sum(session[a] for a in agents)

print(f"ref {ref} = {sha}")
print(f"agent commits (non-merge, excluding O.J.): {total}")
print(f"with Agent-Session trailer: {with_session} of {total}")
print(f"Co-Authored-By lines: {coauth_total} total, {coauth_model} naming a model")
print()
print(f"{'author identity':48} {'commits':>7} {'session':>7} {'model':>5}")
for a in sorted(agents, key=lambda a: -commits[a]):
    print(f"{a:48} {commits[a]:7} {session[a]:7} {model[a]:5}")
if human:
    print(f"{'(human) ' + ', '.join(sorted(human)):48} {sum(commits[a] for a in human):7}")
