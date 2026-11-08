#!/usr/bin/env python3
"""findings.py — add a finding, list what's here, refresh the index.

WHY THIS EXISTS: a finding nobody can pick up is a finding that didn't happen. The findings/
directory is the pickup-able form, and this tool exists mostly to make the two fields that matter
unskippable at creation time: `confidence` (how much weight this can bear) and `falsifier` (what
would change your mind).

Those two are mandatory because they are the first things dropped in a hurry and the first things
lost across a context gap. See findings/001 — a claim travels, its confidence doesn't, so an
unlabeled low-confidence read comes back looking like a verified result.

USAGE:
  python3 tools/findings.py new --as corrie --title "Your claim in one sentence" \\
      [--confidence medium] [--falsifier "what would show this is wrong"]
  python3 tools/findings.py list                  # grouped by status
  python3 tools/findings.py index                 # rewrite the table in findings/README.md

WHAT IT DOES NOT DO (be honest about the seam):

  - It does not refuse a weak falsifier. It prompts, it warns if you leave it as the placeholder,
    and then it trusts you. Making it refuse would be stronger, and I'd rather someone argue for
    that than have me impose it in the same commit that creates the directory.

  - `index` regenerates ONLY a table of pointers -- id, title, status, confidence, author -- between
    two markers in findings/README.md. It never copies a finding's content anywhere. That limit is
    deliberate: a generated file that duplicated the findings would quietly outrank them, which is a
    shadow rather than an index. Pointers are safe to generate; content is not.
"""
import argparse
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINDINGS = os.path.join(ROOT, "findings")
README = os.path.join(FINDINGS, "README.md")
BEGIN = "<!-- INDEX:BEGIN"
END = "<!-- INDEX:END -->"

CONFIDENCES = ("high", "medium", "low", "speculative")
STATUSES = ("open", "supported", "contested", "superseded", "retracted")
PLACEHOLDER = "TODO: what observation would show this is wrong?"


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return "-".join(s.split("-")[:9]) or "finding"


def parse_header(path):
    """Pull the --- header block off a finding. Tiny and deliberate: no YAML dependency."""
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            if f.readline().strip() != "---":
                return out
            for line in f:
                if line.strip() == "---":
                    break
                if ":" in line:
                    k, v = line.split(":", 1)
                    out[k.strip()] = v.strip()
    except OSError:
        return {}
    return out


def all_findings():
    if not os.path.isdir(FINDINGS):
        return []
    items = []
    for fn in sorted(os.listdir(FINDINGS)):
        if not re.match(r"^\d{3}-.*\.md$", fn):
            continue
        h = parse_header(os.path.join(FINDINGS, fn))
        h["_file"] = fn
        h.setdefault("id", fn[:3])
        h.setdefault("title", "(no title)")
        h.setdefault("status", "open")
        h.setdefault("confidence", "?")
        h.setdefault("author", "?")
        items.append(h)
    return items


def next_id(items):
    used = [int(i["id"]) for i in items if str(i.get("id", "")).strip().isdigit()]
    return f"{(max(used) + 1) if used else 1:03d}"


def cmd_new(args):
    items = all_findings()
    nid = next_id(items)
    slug = slugify(args.title)
    path = os.path.join(FINDINGS, f"{nid}-{slug}.md")
    if os.path.exists(path):
        print(f"{path} already exists", file=sys.stderr)
        return 1
    if args.confidence not in CONFIDENCES:
        print(f"--confidence must be one of {', '.join(CONFIDENCES)}", file=sys.stderr)
        return 2

    falsifier = args.falsifier or PLACEHOLDER
    body = f"""---
id: {nid}
title: {args.title}
author: {args.name}
date: {datetime.date.today().isoformat()}
status: open
confidence: {args.confidence}
falsifier: {falsifier}
related: []
---

## The claim

<!-- State it as a claim, not a topic. One or two sentences someone could disagree with. -->

## The evidence

<!-- What you actually observed or read. Quote primary sources; link them. -->

## What follows

<!-- What someone should do differently if this holds. -->

## What I'd want checked

<!-- The weakest part, named by you before someone else names it for you. -->

## Confidence note

<!-- Why `{args.confidence}` and not higher or lower. Be honest downward. -->
"""
    os.makedirs(FINDINGS, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"created findings/{nid}-{slug}.md")
    if falsifier == PLACEHOLDER:
        print("\n  WARNING: no --falsifier given, so the header has a placeholder.")
        print("  A finding without a falsifier is a belief. Fill it in before you commit,")
        print("  or change `confidence:` to `speculative` and say so in the note.")
    print("\nnext: write it, then refresh the index and commit under your own name:")
    print("  python3 tools/findings.py index")
    print(f"  git add findings/{nid}-{slug}.md findings/README.md")
    print(f'  git commit --author="..." -m "findings: {args.title.lower()[:50]}"')
    return 0


def cmd_list(args):
    items = all_findings()
    if not items:
        print("no findings yet. add one:  python3 tools/findings.py new --as <you> --title \"...\"")
        return 0
    by_status = {}
    for i in items:
        by_status.setdefault(i["status"], []).append(i)
    order = [s for s in STATUSES if s in by_status] + \
            [s for s in sorted(by_status) if s not in STATUSES]
    for status in order:
        print(f"\n{status.upper()}")
        for i in by_status[status]:
            print(f"  {i['id']}  [{i['confidence']:<11}] {i['title']}")
            print(f"       {i['author']}  ·  findings/{i['_file']}")
    weak = [i for i in items if PLACEHOLDER in (i.get("falsifier") or "")]
    if weak:
        print(f"\n{len(weak)} finding(s) still have a placeholder falsifier: "
              f"{', '.join(i['id'] for i in weak)}")
    print()
    return 0


def cmd_index(args):
    items = all_findings()
    rows = ["| id | finding | status | conf. | author |", "|---|---|---|---|---|"]
    for i in items:
        title = i["title"].replace("|", "\\|")
        rows.append(f"| [{i['id']}]({i['_file']}) | {title} | {i['status']} | "
                    f"{i['confidence']} | {i['author']} |")
    table = "\n".join(rows)

    try:
        with open(README, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        print(f"can't read {README}", file=sys.stderr)
        return 1

    start, end = text.find(BEGIN), text.find(END)
    if start == -1 or end == -1:
        print(f"couldn't find the {BEGIN}...{END} markers in findings/README.md", file=sys.stderr)
        return 1
    head_end = text.find("-->", start)
    marker = text[start:head_end + 3]
    new = text[:start] + marker + "\n" + table + "\n" + text[end:]
    if new == text:
        print(f"index already current ({len(items)} finding(s))")
        return 0
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)
    print(f"index refreshed: {len(items)} finding(s)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Add, list, and index findings.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="create a new finding from the template")
    p.add_argument("--as", dest="name", required=True, help="your name, e.g. corrie")
    p.add_argument("--title", required=True, help="the claim in one sentence")
    p.add_argument("--confidence", default="medium",
                   help=f"one of: {', '.join(CONFIDENCES)} (default: medium)")
    p.add_argument("--falsifier", help="what observation would show this is wrong")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("list", help="show findings grouped by status")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("index", help="rewrite the pointer table in findings/README.md")
    p.set_defaults(fn=cmd_index)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
