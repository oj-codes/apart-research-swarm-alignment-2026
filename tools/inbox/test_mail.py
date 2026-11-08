#!/usr/bin/env python3
"""Tests for the grove inbox (tools/inbox/mail.py).

Run from anywhere:   python3 tools/inbox/test_mail.py
Stdlib only. Each test gets a fresh scratch inbox via GROVE_INBOX, so the real inbox/ is never touched.

These cover the ways an agent actually breaks a mail tool: colliding filenames, empty/garbage names,
path traversal on read, a missing --file, round-trip fidelity, and listing order.
"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mail  # noqa: E402


class MailTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="grove-inbox-test-")
        os.environ["GROVE_INBOX"] = self.tmp

    def tearDown(self):
        os.environ.pop("GROVE_INBOX", None)
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- happy path ----
    def test_send_then_read_roundtrip_is_verbatim(self):
        body = "Hello Corrie.\n\nMulti-line body with  spaces and *markdown*.\nLine three."
        path = mail.send_letter("corrie", "auran", "arrival ideas", body)
        self.assertTrue(os.path.isfile(path))
        got = mail.read_letter(path)
        self.assertIn(body.rstrip(), got)          # body preserved verbatim
        self.assertIn("to: corrie", got)           # header present
        self.assertIn("from: auran", got)
        self.assertIn("subject: arrival ideas", got)

    def test_check_lists_oldest_first(self):
        mail.send_letter("corrie", "auran", "first", "one")
        mail.send_letter("corrie", "tern", "second", "two")
        who, files = mail.list_inbox("corrie")
        self.assertEqual(who, "corrie")
        self.assertEqual(len(files), 2)
        self.assertEqual(files, sorted(files))     # chronological by filename

    def test_check_empty_inbox(self):
        who, files = mail.list_inbox("nobody")
        self.assertEqual(files, [])

    # ---- failure modes with catches ----
    def test_same_second_letters_do_not_clobber(self):
        # Two letters that produce the same base filename must both survive.
        p1 = mail.send_letter("corrie", "auran", "hi", "first message")
        p2 = mail.send_letter("corrie", "auran", "hi", "second message")
        self.assertNotEqual(p1, p2)
        who, files = mail.list_inbox("corrie")
        self.assertEqual(len(files), 2)
        bodies = {mail.read_letter(os.path.join(self.tmp, "corrie", f)) for f in files}
        self.assertTrue(any("first message" in b for b in bodies))
        self.assertTrue(any("second message" in b for b in bodies))

    def test_empty_body_rejected(self):
        with self.assertRaises(mail.MailError):
            mail.send_letter("corrie", "auran", "subj", "")
        with self.assertRaises(mail.MailError):
            mail.send_letter("corrie", "auran", "subj", "   \n  ")

    def test_empty_subject_rejected(self):
        with self.assertRaises(mail.MailError):
            mail.send_letter("corrie", "auran", "", "body")

    def test_garbage_recipient_rejected(self):
        # A name that slugs to nothing must error, not silently become "letter".
        for bad in ("", "   ", "!!!", "///", "。。。"):
            with self.assertRaises(mail.MailError):
                mail.send_letter(bad, "auran", "subj", "body")

    def test_read_rejects_path_traversal(self):
        # Must not read files outside the inbox tree.
        secret = os.path.join(self.tmp, "..", "outside-secret.txt")
        with open(secret, "w") as f:
            f.write("TOP SECRET")
        with self.assertRaises(mail.MailError):
            mail.read_letter(secret)
        with self.assertRaises(mail.MailError):
            mail.read_letter(os.path.join(self.tmp, "corrie", "..", "..", "outside-secret.txt"))

    def test_read_missing_letter_errors_cleanly(self):
        with self.assertRaises(mail.MailError):
            mail.read_letter(os.path.join(self.tmp, "corrie", "nope.md"))

    def test_recipient_name_is_slugged_safely(self):
        # Mixed-case / spaces normalize; the letter lands in a predictable dir.
        path = mail.send_letter("Corrie J", "auran", "s", "b")
        self.assertIn(os.path.join(self.tmp, "corrie-j"), path)

    # ---- CLI layer ----
    def test_cli_missing_file_errors_without_traceback(self):
        err = io.StringIO()
        with self.assertRaises(SystemExit) as cm, redirect_stderr(err):
            mail.main(["send", "--to", "corrie", "--from", "auran",
                       "--subject", "s", "--file", "/does/not/exist.md"])
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("--file not found", err.getvalue())

    def test_cli_send_and_check_roundtrip(self):
        out = io.StringIO()
        with redirect_stdout(out):
            mail.main(["send", "--to", "corrie", "--from", "auran",
                       "--subject", "cli hello", "--body", "from the cli"])
        self.assertIn("wrote", out.getvalue())
        out2 = io.StringIO()
        with redirect_stdout(out2):
            mail.main(["check", "--to", "corrie"])
        self.assertIn("1 letter(s)", out2.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
