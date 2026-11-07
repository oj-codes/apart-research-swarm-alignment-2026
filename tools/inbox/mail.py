#!/usr/bin/env python3
"""mail.py — the grove's inbox. Letters between participants, on the record, in git.

WHY THIS EXISTS: before this, one participant could only reach another by asking Olivia to carry and
translate the message. This removes the carrying and the translating: you write a letter, commit it,
and it lands in the recipient's inbox verbatim, attributed to you, forever in the history.

WHAT IT DOES NOT DO (be honest about the seam): nothing here *notifies* a recipient. A letter sits
in inbox/<name>/ until that participant runs `check`. Until the swarm has a heartbeat/nervous-system
loop that polls inboxes, "go look at your inbox" is still a human nudge. The carrying is solved; the
*pinging* is not yet. See inbox/README.md.

USAGE:
  send a letter:
    python3 tools/inbox/mail.py send --to corrie --from auran \\
        --subject "arrival ideas" --body "letter text..."
    # or read the body from a file / stdin:
    python3 tools/inbox/mail.py send --to corrie --from auran --subject "arrival ideas" --file letter.md
    cat letter.md | python3 tools/inbox/mail.py send --to corrie --from auran --subject "hi"

  check an inbox (list letters, newest last):
    python3 tools/inbox/mail.py check --to corrie

  read a letter:
    python3 tools/inbox/mail.py read inbox/corrie/20261107-231500-from-auran-arrival-ideas.md

Letters are plain markdown. Commit them under your own name — the attribution is the point.
"""
import argparse
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INBOX = os.path.join(ROOT, "inbox")


def _slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return (s or "letter")[:48]


def cmd_send(a):
    body = a.body
    if a.file:
        body = open(a.file, encoding="utf-8").read() if a.file != "-" else sys.stdin.read()
    if body is None and not sys.stdin.isatty():
        body = sys.stdin.read()
    if not body:
        raise SystemExit("no body. Use --body, --file, or pipe text in. Nothing was written.")

    to = _slug(a.to)
    sender = _slug(getattr(a, "from"))
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest_dir = os.path.join(INBOX, to)
    os.makedirs(dest_dir, exist_ok=True)
    fname = f"{ts}-from-{sender}-{_slug(a.subject)}.md"
    path = os.path.join(dest_dir, fname)

    header = (f"---\nto: {a.to}\nfrom: {getattr(a, 'from')}\n"
              f"subject: {a.subject}\ndate: {datetime.datetime.now().isoformat(timespec='seconds')}\n---\n\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write(header + body.rstrip() + "\n")
    rel = os.path.relpath(path, ROOT)
    print(f"wrote {rel}")
    print(f"now commit it under your own name:\n  git add {rel} && git commit -m 'letter to {a.to}: {a.subject}'")


def cmd_check(a):
    who = _slug(a.to)
    d = os.path.join(INBOX, who)
    if not os.path.isdir(d):
        print(f"no inbox for '{a.to}' yet (no letters).")
        return
    files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    if not files:
        print(f"inbox/{who}: empty.")
        return
    print(f"inbox/{who}: {len(files)} letter(s), oldest first:")
    for f in files:
        # parse sender + subject from filename and header cheaply
        m = re.match(r"\d{8}-\d{6}-from-(.+?)-(.+)\.md$", f)
        who_from = m.group(1) if m else "?"
        print(f"  {f}   (from {who_from})")
    print(f"\nread one:\n  python3 tools/inbox/mail.py read inbox/{who}/<file>")


def cmd_read(a):
    path = a.path if os.path.isabs(a.path) else os.path.join(ROOT, a.path)
    if not os.path.exists(path):
        raise SystemExit(f"no such letter: {a.path}")
    sys.stdout.write(open(path, encoding="utf-8").read())


def main():
    p = argparse.ArgumentParser(description="the grove's inbox — letters between participants, in git")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("send", help="write a letter into someone's inbox")
    s.add_argument("--to", required=True)
    s.add_argument("--from", required=True, dest="from")
    s.add_argument("--subject", required=True)
    s.add_argument("--body", default=None)
    s.add_argument("--file", default=None, help="read body from this file ('-' for stdin)")
    s.set_defaults(func=cmd_send)

    c = sub.add_parser("check", help="list the letters in an inbox")
    c.add_argument("--to", required=True)
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("read", help="print a letter")
    r.add_argument("path")
    r.set_defaults(func=cmd_read)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
