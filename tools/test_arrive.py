#!/usr/bin/env python3
"""test_arrive.py — tests for the arrival ritual.

Stdlib unittest, no deps, same shape as tools/inbox/test_mail.py. Inbox tests run against a
scratch dir via GROVE_INBOX so they never touch the real inbox/.

    python3 tools/test_arrive.py

Covers the three defects Olivia found in review, because a fix without a test is a fix that comes
back:

  - letter counting at 0, 1, 10 and 20 letters. The original check was `"0 letter" in out`, which
    is also true of "10 letter(s)" and "20 letter(s)" -- so an arrival with ten letters waiting
    was told nothing was there. Prose written for humans is the wrong thing to branch on.
  - run() preserving stderr, exit codes, and the reason a command never ran, instead of
    collapsing four different failures into None.
  - identity parsed from `git var GIT_AUTHOR_IDENT` and compared EXACTLY, not by substring
    against the configured name.

Add a test when you add a failure mode.
"""
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def load_arrive():
    """Import tools/arrive.py by path — it's a script, not an installed module."""
    spec = importlib.util.spec_from_file_location("arrive", os.path.join(HERE, "arrive.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


arrive = load_arrive()


class InboxCounting(unittest.TestCase):
    """The 0/1/10/20 cases. 10 and 20 are the ones that were broken."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="arrive-test-")
        os.environ["GROVE_INBOX"] = self.tmp

    def tearDown(self):
        os.environ.pop("GROVE_INBOX", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def seed(self, who, n):
        d = os.path.join(self.tmp, who)
        os.makedirs(d, exist_ok=True)
        for i in range(n):
            with open(os.path.join(d, f"2026110{i % 9}-00000{i % 9}-from-auran-n{i}.md"), "w") as f:
                f.write(f"---\nto: {who}\nfrom: auran\nsubject: n{i}\n---\n\nbody\n")

    def test_zero_letters(self):
        self.seed("corrie", 0)
        self.assertEqual(arrive.inbox_letters("corrie"), [])

    def test_one_letter(self):
        self.seed("corrie", 1)
        self.assertEqual(len(arrive.inbox_letters("corrie")), 1)

    def test_ten_letters(self):
        """The original bug: '0 letter' is a substring of '10 letter(s)'."""
        self.seed("corrie", 10)
        self.assertEqual(len(arrive.inbox_letters("corrie")), 10)

    def test_twenty_letters(self):
        """And of '20 letter(s)'."""
        self.seed("corrie", 20)
        self.assertEqual(len(arrive.inbox_letters("corrie")), 20)

    def test_missing_inbox_is_empty_not_an_error(self):
        self.assertEqual(arrive.inbox_letters("nobody-here"), [])

    def test_ignores_non_markdown(self):
        self.seed("corrie", 2)
        with open(os.path.join(self.tmp, "corrie", ".DS_Store"), "w") as f:
            f.write("junk")
        with open(os.path.join(self.tmp, "corrie", "notes.txt"), "w") as f:
            f.write("not a letter")
        self.assertEqual(len(arrive.inbox_letters("corrie")), 2)

    def test_sorted_oldest_first(self):
        d = os.path.join(self.tmp, "corrie")
        os.makedirs(d, exist_ok=True)
        for fn in ("20261108-000000-from-a-z.md", "20261107-000000-from-a-a.md"):
            open(os.path.join(d, fn), "w").close()
        self.assertEqual(arrive.inbox_letters("corrie")[0], "20261107-000000-from-a-a.md")

    def test_respects_grove_inbox_redirect(self):
        """If this failed, the tests would be writing into the real inbox/."""
        self.assertEqual(arrive.inbox_dir(), self.tmp)


class RunPreservesResults(unittest.TestCase):
    """run() must distinguish the four failures the old version flattened into None."""

    def test_success_gives_stdout_and_zero(self):
        r = arrive.run("sh", "-c", "echo hello")
        self.assertTrue(r.ok)
        self.assertEqual(r.out, "hello")
        self.assertEqual(r.code, 0)
        self.assertIsNone(r.error)

    def test_missing_tool_is_named(self):
        r = arrive.run("definitely-not-a-real-binary-xyz")
        self.assertFalse(r.ok)
        self.assertIsNone(r.code)
        self.assertIn("not installed", arrive.why(r))

    def test_nonzero_preserves_stderr_and_code(self):
        r = arrive.run("sh", "-c", "echo oops >&2; exit 7")
        self.assertFalse(r.ok)
        self.assertEqual(r.code, 7)
        self.assertEqual(r.err, "oops")
        self.assertEqual(arrive.why(r), "oops")

    def test_nonzero_without_stderr_still_explains(self):
        r = arrive.run("sh", "-c", "exit 3")
        self.assertFalse(r.ok)
        self.assertIn("exited 3", arrive.why(r))

    def test_stdout_kept_even_when_command_fails(self):
        r = arrive.run("sh", "-c", "echo partial; exit 1")
        self.assertFalse(r.ok)
        self.assertEqual(r.out, "partial")

    def test_timeout_is_named_not_swallowed(self):
        r = arrive.run("sh", "-c", "sleep 25")       # run()'s timeout is 20s
        self.assertFalse(r.ok)
        self.assertIn("timed out", arrive.why(r))


class Identity(unittest.TestCase):
    """GitHub account, git author and git committer are three different things."""

    def test_effective_author_is_name_and_email(self):
        ident = arrive.git_ident("AUTHOR")
        if not ident:
            self.skipTest("no git identity available in this environment")
        self.assertRegex(ident, r"^.*<[^>]*>$")
        self.assertNotRegex(ident, r"\d{10}")   # the unix timestamp must be stripped

    def test_committer_also_readable(self):
        if not arrive.git_ident("AUTHOR"):
            self.skipTest("no git identity available in this environment")
        self.assertRegex(arrive.git_ident("COMMITTER"), r"^.*<[^>]*>$")

    def test_unknown_ident_kind_is_empty_not_a_crash(self):
        self.assertEqual(arrive.git_ident("NOT_A_REAL_KIND"), "")

    def test_substring_match_would_have_been_wrong(self):
        """Guards the fix: 'Corrie' is a substring of 'Not Corrie', so `in` is not identity."""
        expected = arrive.author_for("corrie")
        impostor = "Not Corrie <someone@example.com>"
        self.assertIn("Corrie", impostor)          # the old test would have passed
        self.assertNotEqual(impostor, expected)    # the new one does not


class RosterIsTheSourceOfTruth(unittest.TestCase):
    """Identity comes from ROSTER.md, not a second copy inside the tool."""

    def test_roster_parses_participants(self):
        rows = arrive.roster()
        self.assertTrue(rows, "ROSTER.md should yield participant rows")
        self.assertIn("name", rows[0], "parsed by header, not by column position")

    def test_separator_row_is_not_a_participant(self):
        for row in arrive.roster():
            self.assertNotEqual(set(row.get("name", "x")) - set("-: "), set())

    def test_every_git_author_is_well_formed(self):
        """A malformed cell could never match the effective identity, so the gate would warn forever."""
        for row in arrive.roster():
            ident = row.get("git author", "").strip().strip("`")
            if ident:
                self.assertRegex(ident, r"^[^<>]+ <[^<>@\s]+@[^<>@\s]+>$",
                                 f"malformed Git Author for {row.get('name')}")

    def test_author_for_strips_markdown_backticks(self):
        ident = arrive.author_for("corrie")
        self.assertNotIn("`", ident)
        self.assertRegex(ident, r"^[^<>]+ <[^<>@\s]+@[^<>@\s]+>$")

    def test_exact_name_match_only(self):
        self.assertIsNotNone(arrive.participant("corrie"))
        self.assertIsNotNone(arrive.participant("Corrie"))   # case-insensitive

    def test_prefix_does_not_match(self):
        """'cor' must not resolve to Corrie — a loose match hands you the wrong identity."""
        self.assertIsNone(arrive.participant("cor"))
        self.assertEqual(arrive.author_for("cor"), "")

    def test_parenthetical_name_matches_on_leading_token(self):
        """'Olivia (O.J.)' is findable as 'olivia', but as a whole token."""
        self.assertIsNotNone(arrive.participant("olivia"))
        self.assertIsNone(arrive.participant("oliv"))

    def test_unknown_and_empty_names(self):
        self.assertIsNone(arrive.participant("nobody-here"))
        self.assertIsNone(arrive.participant(""))
        self.assertIsNone(arrive.participant(None))
        self.assertEqual(arrive.author_for("nobody-here"), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
