#!/usr/bin/env python3
"""Per participant: commits before/after the trailer convention landed (2026-11-08T01:06:24-05:00, merge of #16),
with how many carry Agent-Session. Mailmapped names from the ref. Usage: split_by_convention.py [ref]"""
import subprocess, sys
from collections import defaultdict
from datetime import datetime, timezone
ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
CONV = datetime.fromisoformat("2026-11-08T01:06:24-05:00")
out = subprocess.run(["git", "-c", f"mailmap.blob={ref}:.mailmap", "log", ref, "--no-merges", "--use-mailmap",
                      "--format=%aN%x1f%aI%x1f%(trailers:key=Agent-Session,valueonly)%x1e"],
                     capture_output=True, text=True, check=True).stdout
agg = defaultdict(lambda: {"before": [0, 0], "after": [0, 0], "first": None})
for rec in out.split("\x1e"):
    rec = rec.strip("\n")
    if not rec.strip(): continue
    name, when, sess = (rec.split("\x1f") + ["", ""])[:3]
    if name.startswith("O. J."): continue
    t = datetime.fromisoformat(when.strip())
    key = "before" if t < CONV else "after"
    agg[name][key][1] += 1
    if sess.strip(): agg[name][key][0] += 1
    if agg[name]["first"] is None or t < agg[name]["first"]: agg[name]["first"] = t
sha = subprocess.run(["git", "rev-parse", "--short", ref], capture_output=True, text=True).stdout.strip()
print(f"ref {ref} = {sha}; convention = {CONV.isoformat()}")
print(f"{'participant':10} {'first commit (EST)':18} {'before: with/total':>18} {'after: with/total':>18}")
tb = ta = nb = na = 0
for name, d in sorted(agg.items(), key=lambda kv: kv[1]["first"]):
    b, a = d["before"], d["after"]
    tb += b[0]; nb += b[1]; ta += a[0]; na += a[1]
    print(f"{name:10} {d['first'].astimezone(CONV.tzinfo).strftime('%d %b %H:%M'):18} {b[0]:>8}/{b[1]:<9} {a[0]:>8}/{a[1]:<9}")
print(f"{'all':10} {'':18} {tb:>8}/{nb:<9} {ta:>8}/{na:<9}")
