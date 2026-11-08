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


REQUIRED = ("id", "title", "author", "date", "status", "confidence", "falsifier")


def parse_header(path):
    """Pull the --- header block off a finding. Returns (fields, errors); no YAML dependency.

    Errors are returned rather than papered over. The previous version substituted defaults for
    anything missing -- id from the filename, "(no title)", status "open", confidence "?" -- which
    made a file with no header at all appear in the index as a valid-looking row. A findings
    directory whose whole purpose is to keep confidence attached to claims should not be inventing
    confidence values for records that never stated one.
    """
    fields, errors = {}, []
    try:
        with open(path, encoding="utf-8") as f:
            first = f.readline()
            if first.strip() != "---":
                return fields, ["no '---' header block"]
            closed = False
            for line in f:
                if line.strip() == "---":
                    closed = True
                    break
                if not line.strip():
                    continue
                if ":" not in line:
                    errors.append(f"header line is not 'key: value': {line.strip()[:50]!r}")
                    continue
                k, v = line.split(":", 1)
                fields[k.strip().lower()] = v.strip()
            if not closed:
                errors.append("header block is never closed with '---'")
    except OSError as e:
        return {}, [f"unreadable: {e}"]
    return fields, errors


def validate(fields, errors, filename):
    """Everything wrong with one finding, as a list of plain sentences."""
    problems = list(errors)
    for key in REQUIRED:
        if not fields.get(key):
            problems.append(f"missing required field: {key}")

    conf = fields.get("confidence", "")
    if conf and conf not in CONFIDENCES:
        problems.append(f"confidence '{conf}' is not one of {', '.join(CONFIDENCES)}")

    status = fields.get("status", "")
    if status and status not in STATUSES:
        problems.append(f"status '{status}' is not one of {', '.join(STATUSES)}")

    fals = fields.get("falsifier", "")
    if fals and (fals == PLACEHOLDER or fals.lower().startswith("todo")):
        problems.append("falsifier is still the placeholder — a finding without one is a belief")

    # id IS the filename stem. One fact in one place -- so a rename can't leave a stale id behind,
    # and an id can't be claimed by a file that doesn't carry it.
    fid = fields.get("id", "")
    stem = filename[:-3] if filename.endswith(".md") else filename
    if fid and fid != stem:
        problems.append(f"id '{fid}' does not match the filename stem '{stem}'")

    return problems


def all_findings():
    """Every finding, well-formed or not. Malformed ones carry their problems in `_errors`."""
    if not os.path.isdir(FINDINGS):
        return []
    items = []
    for fn in sorted(os.listdir(FINDINGS)):
        if fn == "README.md" or not fn.endswith(".md"):
            continue
        fields, errors = parse_header(os.path.join(FINDINGS, fn))
        fields["_file"] = fn
        fields["_errors"] = validate(fields, errors, fn)
        items.append(fields)
    return items


def check_markers(text):
    """Validate the index markers BEFORE touching the file. Returns (ok, message, start, end).

    This writes into a shared document, so a bad assumption here destroys someone else's prose.
    The previous version only checked that both markers were findable, then spliced
    text[:start] + table + text[end:] -- so with the END marker ABOVE the BEGIN marker it would
    have silently deleted everything between them. Refuse rather than guess.
    """
    nb, ne = text.count(BEGIN), text.count(END)
    if nb == 0 or ne == 0:
        return False, f"missing marker ({BEGIN}... found {nb}x, {END} found {ne}x)", -1, -1
    if nb > 1 or ne > 1:
        return False, f"duplicate markers ({nb} begin, {ne} end) — ambiguous which block to replace", -1, -1
    start, end = text.find(BEGIN), text.find(END)
    if end < start:
        return False, "end marker appears before the begin marker — refusing to splice", -1, -1
    if text.find("-->", start) == -1 or text.find("-->", start) > end:
        return False, "begin marker's comment is never closed with '-->'", -1, -1
    return True, "ok", start, end


def duplicate_ids(items):
    """ids claimed by more than one file. Sequential ids collide across worktrees in silence."""
    seen = {}
    for i in items:
        fid = i.get("id")
        if fid:
            seen.setdefault(fid, []).append(i["_file"])
    return {k: v for k, v in seen.items() if len(v) > 1}


def cmd_new(args):
    # Date + slug, never a counter. A counter needs coordination we don't have: two agents in
    # separate worktrees both read the same max and both allocate the next number, producing two
    # DIFFERENT filenames that git merges cleanly into two findings sharing one id -- silently.
    # With date+slug, two agents who genuinely duplicate work produce the SAME filename, which
    # git surfaces as a conflict. Same naming trick as inbox/ letters, for the same reason.
    slug = slugify(args.title)
    nid = f"{datetime.date.today().strftime('%Y%m%d')}-{slug}"
    path = os.path.join(FINDINGS, f"{nid}.md")
    if os.path.exists(path):
        print(f"findings/{nid}.md already exists — someone already filed this claim today.\n"
              f"Read it first; if yours is genuinely different, retitle it.", file=sys.stderr)
        return 1
    if args.confidence not in CONFIDENCES:
        print(f"--confidence must be one of {', '.join(CONFIDENCES)}", file=sys.stderr)
        return 2
    falsifier = args.falsifier.strip()
    if not falsifier or falsifier == PLACEHOLDER or falsifier.lower().startswith("todo"):
        print("--falsifier must say what observation would show this is wrong.\n"
              "A finding without one is a belief; file it as confidence: speculative and say so.",
              file=sys.stderr)
        return 2
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
    print(f"created findings/{nid}.md")
    if falsifier == PLACEHOLDER:
        print("\n  WARNING: no --falsifier given, so the header has a placeholder.")
        print("  A finding without a falsifier is a belief. Fill it in before you commit,")
        print("  or change `confidence:` to `speculative` and say so in the note.")
    print("\nnext: write it, then refresh the index and commit under your own name:")
    print("  python3 tools/findings.py index")
    print(f"  git add findings/{nid}.md findings/README.md")
    print(f'  git commit --author="..." -m "findings: {args.title.lower()[:50]}"')
    return 0


def cmd_list(args):
    items = all_findings()
    if not items:
        print("no findings yet. add one:  python3 tools/findings.py new --as <you> --title \"...\"")
        return 0

    good = [i for i in items if not i["_errors"]]
    bad = [i for i in items if i["_errors"]]

    by_status = {}
    for i in good:
        by_status.setdefault(i["status"], []).append(i)
    order = [s for s in STATUSES if s in by_status] + \
            [s for s in sorted(by_status) if s not in STATUSES]
    for status in order:
        print(f"\n{status.upper()}")
        for i in by_status[status]:
            print(f"  {i['id']}  [{i['confidence']:<11}] {i['title']}")
            print(f"       {i['author']}  ·  findings/{i['_file']}")

    # Malformed records get their own section and their own exit code. They are NOT shown with
    # invented defaults alongside valid ones, which is how an incomplete finding used to look
    # indistinguishable from a checked one.
    if bad:
        print(f"\nMALFORMED ({len(bad)}) — not valid findings, shown so they can be fixed")
        for i in bad:
            print(f"  findings/{i['_file']}")
            for p in i["_errors"]:
                print(f"       ! {p}")
    dups = duplicate_ids(items)
    if dups:
        print(f"\nDUPLICATE IDS ({len(dups)})")
        for fid, files in sorted(dups.items()):
            print(f"  {fid} claimed by: {', '.join(files)}")
    print()
    return 1 if (bad or dups) else 0


def cmd_check(args):
    """Validate every finding and say what's wrong. Exit nonzero so CI and pre-merge can gate."""
    items = all_findings()
    bad = [i for i in items if i["_errors"]]
    dups = duplicate_ids(items)
    for i in bad:
        for p in i["_errors"]:
            print(f"findings/{i['_file']}: {p}")
    for fid, files in sorted(dups.items()):
        print(f"duplicate id '{fid}' claimed by: {', '.join(files)}")

    ok, msg, _, _ = (True, "ok", 0, 0)
    try:
        with open(README, encoding="utf-8") as f:
            ok, msg, _, _ = check_markers(f.read())
    except OSError as e:
        ok, msg = False, f"unreadable: {e}"
    if not ok:
        print(f"findings/README.md: index markers invalid — {msg}")

    problems = len(bad) + len(dups) + (0 if ok else 1)
    if problems:
        print(f"\n{problems} problem(s) across {len(items)} finding(s).")
        return 1
    print(f"{len(items)} finding(s), all well-formed; index markers valid.")
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

    ok, msg, start, end = check_markers(text)
    if not ok:
        print(f"refusing to rewrite findings/README.md: {msg}", file=sys.stderr)
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
    # Both REQUIRED, with no default. A default confidence means the tool asserts a confidence
    # the author never stated -- which is the exact failure finding 001 is about, built into the
    # thing meant to prevent it.
    p.add_argument("--confidence", required=True,
                   help=f"required, one of: {', '.join(CONFIDENCES)}")
    p.add_argument("--falsifier", required=True,
                   help="required: what observation would show this is wrong")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("check", help="validate every finding; exit 1 if anything is wrong")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("list", help="show findings grouped by status")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("index", help="rewrite the pointer table in findings/README.md")
    p.set_defaults(fn=cmd_index)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
