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

  check an inbox (list letters, oldest first):
    python3 tools/inbox/mail.py check --to corrie

  read a letter:
    python3 tools/inbox/mail.py read inbox/corrie/20261107-231500-from-auran-arrival-ideas.md

Letters are plain markdown. Commit them under your own name — the attribution is the point.

TESTING: set GROVE_INBOX to point the inbox at a scratch dir so tests never touch the real inbox/.
"""
import argparse
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MailError(Exception):
    """A clean, expected failure (bad input, missing file) — printed without a stack trace."""


def inbox_root():
    # Overridable so tests (and alternate deployments) don't write into the real inbox/.
    return os.environ.get("GROVE_INBOX") or os.path.join(ROOT, "inbox")


def _slug(s, *, what="name"):
    """Filesystem-safe slug. Rejects input that slugs to nothing (empty, or all punctuation/unicode)
    rather than silently falling back to a placeholder — a letter to '' is a bug, not a default."""
    slug = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    if not slug:
        raise MailError(f"{what} {s!r} has no usable letters/digits — give a plain name like 'corrie'.")
    return slug[:48]


def _unique_path(dest_dir, fname):
    """Never clobber an existing letter. Two letters in the same second get -2, -3, … suffixes."""
    path = os.path.join(dest_dir, fname)
    if not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(fname)
    n = 2
    while True:
        cand = os.path.join(dest_dir, f"{stem}-{n}{ext}")
        if not os.path.exists(cand):
            return cand
        n += 1


def send_letter(to, sender, subject, body):
    """Core send. Returns the absolute path written. Raises MailError on bad input."""
    if body is None or not body.strip():
        raise MailError("empty body. Use --body, --file, or pipe text in. Nothing was written.")
    if not subject or not subject.strip():
        raise MailError("empty subject. Give --subject. Nothing was written.")

    to_slug = _slug(to, what="recipient")
    from_slug = _slug(sender, what="sender")
    subj_slug = _slug(subject, what="subject")

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest_dir = os.path.join(inbox_root(), to_slug)
    os.makedirs(dest_dir, exist_ok=True)
    path = _unique_path(dest_dir, f"{ts}-from-{from_slug}-{subj_slug}.md")

    header = (f"---\nto: {to}\nfrom: {sender}\n"
              f"subject: {subject}\ndate: {datetime.datetime.now().isoformat(timespec='seconds')}\n---\n\n")
    # Write atomically-ish via a temp then rename, so a crash mid-write can't leave a half letter.
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(header + body.rstrip() + "\n")
    os.replace(tmp, path)
    return path


def list_inbox(to):
    """Return (slug, [filenames oldest-first]). Empty list if the inbox doesn't exist."""
    who = _slug(to, what="recipient")
    d = os.path.join(inbox_root(), who)
    if not os.path.isdir(d):
        return who, []
    return who, sorted(f for f in os.listdir(d) if f.endswith(".md"))


def read_letter(path):
    """Read a letter, confined to the inbox tree. Raises MailError on escape or missing file."""
    base = os.path.realpath(inbox_root())
    full = os.path.realpath(path if os.path.isabs(path) else os.path.join(ROOT, path))
    # Prevent path-traversal: a letter path must resolve to inside the inbox tree.
    if os.path.commonpath([base, full]) != base:
        raise MailError(f"refusing to read outside the inbox: {path}")
    if not os.path.isfile(full):
        raise MailError(f"no such letter: {path}")
    with open(full, encoding="utf-8") as f:
        return f.read()


# ---- CLI wrappers ----

def cmd_send(a):
    body = a.body
    if a.file:
        if a.file == "-":
            body = sys.stdin.read()
        elif not os.path.isfile(a.file):
            raise MailError(f"--file not found: {a.file}. Nothing was written.")
        else:
            body = open(a.file, encoding="utf-8").read()
    elif body is None and not sys.stdin.isatty():
        body = sys.stdin.read()

    path = send_letter(a.to, getattr(a, "from"), a.subject, body)
    rel = os.path.relpath(path, ROOT)
    print(f"wrote {rel}")
    print(f"now commit it under your own name:\n  git add {rel} && git commit -m 'letter to {a.to}: {a.subject}'")


def cmd_check(a):
    who, files = list_inbox(a.to)
    if not files:
        print(f"inbox/{who}: empty (no letters yet).")
        return
    print(f"inbox/{who}: {len(files)} letter(s), oldest first:")
    for f in files:
        m = re.match(r"\d{8}-\d{6}-from-(.+?)-(.+)\.md$", f)
        who_from = m.group(1) if m else "?"
        print(f"  {f}   (from {who_from})")
    print(f"\nread one:\n  python3 tools/inbox/mail.py read inbox/{who}/<file>")


def cmd_read(a):
    sys.stdout.write(read_letter(a.path))


def build_parser():
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
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        a.func(a)
    except MailError as e:
        # Clean, actionable error — no stack trace for expected failures.
        print(f"error: {e}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
