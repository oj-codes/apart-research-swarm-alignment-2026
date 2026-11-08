#!/usr/bin/env python3
"""Each test here pins one way this harness could silently score itself wrong.

Remove a guard in harness.py and exactly one of these goes red. That is the point: an eval of a
retrieval scheme is only worth its harness, and every trap below was hit for real during the
sprint rather than imagined for a test suite.

    python3 submission/eval/test_harness.py
"""
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import harness  # noqa: E402


def sh(repo, *args, **env):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null", **env)
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=e)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def new_repo(d):
    sh(d, "init", "-q", "-b", "main")
    sh(d, "config", "user.email", "committer@example.invalid")
    sh(d, "config", "user.name", "Committer")
    return pathlib.Path(d)


def commit(repo, msg, author, *, body="", path="f.txt"):
    """One commit with a chosen author string. Returns its sha."""
    f = repo / path
    f.write_text((f.read_text() if f.exists() else "") + msg + "\n")
    sh(repo, "add", path)
    sh(repo, "commit", "-q", "-m", msg + (("\n\n" + body) if body else ""),
       f"--author={author}")
    return sh(repo, "rev-parse", "HEAD").strip()


class Trap1MailmapFromRef(unittest.TestCase):
    """`--use-mailmap` reads the WORKING TREE's .mailmap, not the ref's.

    Run from a tree without one it silently does not mailmap. harness.path_mailmap passes
    `-c mailmap.blob=<ref>:.mailmap`, so it works regardless of the caller's cwd."""

    def test_mailmap_is_read_from_the_ref(self):
        with tempfile.TemporaryDirectory() as d:
            repo = new_repo(d)
            a = commit(repo, "one", "Venice <venice@example.invalid>")
            b = commit(repo, "two", "venice-handle <venice@example.invalid>")
            (repo / ".mailmap").write_text(
                "Venice <venice@example.invalid> venice-handle <venice@example.invalid>\n")
            sh(repo, "add", ".mailmap")
            sh(repo, "commit", "-q", "-m", "mailmap",
               "--author=Venice <venice@example.invalid>")

            got = harness.path_mailmap(repo, "Venice", mailmap_ref="HEAD")
            self.assertIn(a, got)
            self.assertIn(b, got, "the handle-spelled commit must collapse via the ref's .mailmap")

    def test_without_the_ref_the_collapse_is_lost(self):
        """Demonstrates the trap itself, so the guard above is not cargo-culted."""
        with tempfile.TemporaryDirectory() as d:
            repo = new_repo(d)
            commit(repo, "one", "Venice <venice@example.invalid>")
            b = commit(repo, "two", "venice-handle <venice@example.invalid>")
            # .mailmap exists only in a COMMIT, and we deliberately remove it from the worktree
            (repo / ".mailmap").write_text(
                "Venice <venice@example.invalid> venice-handle <venice@example.invalid>\n")
            sh(repo, "add", ".mailmap")
            sh(repo, "commit", "-q", "-m", "mailmap", "--author=Venice <venice@example.invalid>")
            os.remove(repo / ".mailmap")

            naive = harness.shas(harness.git(
                repo, "log", "--use-mailmap", "--no-merges", "--format=%H %aN", "--author=Venice"))
            self.assertNotIn(b, naive, "without mailmap.blob the handle commit is NOT collapsed")
            self.assertIn(b, harness.path_mailmap(repo, "Venice", mailmap_ref="HEAD"))


class Trap2TrailerNotGrep(unittest.TestCase):
    """A commit whose MESSAGE mentions the trailer name must not count as carrying it.

    The live instance: a `--grep 'Co-Authored-By'` count matched the commit that BANNED model
    co-authorship, inflating the violation count by one."""

    def test_message_mention_is_not_a_trailer(self):
        with tempfile.TemporaryDirectory() as d:
            repo = new_repo(d)
            real = commit(repo, "real", "Tern <tern@example.invalid>",
                          body="Agent-Session: sess-abc")
            talks = commit(repo, "rule: always write Agent-Session: sess-abc in your commits",
                           "Tern <tern@example.invalid>")

            got = harness.path_session(repo, "sess-abc")
            self.assertIn(real, got)
            self.assertNotIn(talks, got, "a message that merely NAMES the trailer must not match")


class Trap3MergesExplicit(unittest.TestCase):
    """`--no-merges` silently drops merge commits. A spelling once reported as 'zero across
    every ref' had two, both merges. Inclusion must be an argument, never a forgotten default."""

    def test_merge_commits_are_excluded_by_default_and_reachable_on_request(self):
        with tempfile.TemporaryDirectory() as d:
            repo = new_repo(d)
            base = commit(repo, "base", "Rill <rill@example.invalid>")
            sh(repo, "checkout", "-q", "-b", "side")
            commit(repo, "side", "Rill <rill@example.invalid>", path="side.txt")
            sh(repo, "checkout", "-q", "main")
            commit(repo, "main2", "Rill <rill@example.invalid>", path="main.txt")
            sh(repo, "merge", "--no-ff", "side", "-m", "merge")
            sh(repo, "commit", "--amend", "-q", "--no-edit",
               "--author=Rill <rill@example.invalid>")
            merge_sha = sh(repo, "rev-parse", "HEAD").strip()
            self.assertEqual(len(sh(repo, "rev-list", "--parents", "-n1", merge_sha).split()), 3,
                             "the fixture must actually be a merge commit")

            self.assertNotIn(merge_sha, harness.path_author(repo, "Rill"))
            self.assertIn(merge_sha, harness.path_author(repo, "Rill", merges=True))


class Trap4CaseSensitivity(unittest.TestCase):
    """`--author` is a case-sensitive regex: `--author=Auran` misses `auran-theclearing`.

    That is not a bug to paper over -- it is the thing the eval measures. Pinned so a later
    'fix' that adds -i cannot silently turn a MISSED_LINK scenario into a CORRECT_LINK one."""

    def test_author_match_stays_case_sensitive(self):
        with tempfile.TemporaryDirectory() as d:
            repo = new_repo(d)
            upper = commit(repo, "one", "Auran <a@example.invalid>")
            lower = commit(repo, "two", "auran-handle <a@example.invalid>")

            got = harness.path_author(repo, "Auran")
            self.assertIn(upper, got)
            self.assertNotIn(lower, got,
                             "case-sensitivity is the measured behaviour; do not add -i")


class Trap6RawUsesLowercaseAn(unittest.TestCase):
    """`%aN` applies the mailmap EVEN under `--no-use-mailmap`; the raw view needs `%an`.

    Found by Tern while drafting scenarios 2 and 3. If path_raw used %aN, the 'before mailmap'
    column would quietly equal the 'after' column and every fork scenario would score CORRECT."""

    def test_raw_view_shows_the_unmapped_spelling(self):
        with tempfile.TemporaryDirectory() as d:
            repo = new_repo(d)
            commit(repo, "one", "Venice <v@example.invalid>")
            b = commit(repo, "two", "venice-handle <v@example.invalid>")
            (repo / ".mailmap").write_text(
                "Venice <v@example.invalid> venice-handle <v@example.invalid>\n")
            sh(repo, "add", ".mailmap")
            sh(repo, "commit", "-q", "-m", "mailmap", "--author=Venice <v@example.invalid>")

            self.assertIn(b, harness.path_raw(repo, "venice-handle"),
                          "%an must report the spelling actually written")
            self.assertNotIn(b, harness.path_raw(repo, "Venice"),
                             "the raw view must NOT collapse; that is what makes it the control")


class ScoringRule(unittest.TestCase):
    """The pre-registered precedence, pinned so it cannot drift after seeing a matrix."""

    def test_precedence(self):
        self.assertEqual(harness.classify(set(), {"a"}), "insufficient_evidence")
        self.assertEqual(harness.classify({"a"}, {"a"}), "correct")
        self.assertEqual(harness.classify({"a", "x"}, {"a"}), "false_merge")
        self.assertEqual(harness.classify({"a"}, {"a", "b"}), "missed_link")

    def test_false_merge_outranks_missed_link(self):
        """Both wrong at once: attributing someone else's commit is the worse failure."""
        self.assertEqual(harness.classify({"a", "x"}, {"a", "b"}), "false_merge")

    def test_every_outcome_is_declared(self):
        for o in ("correct", "false_merge", "missed_link", "insufficient_evidence"):
            self.assertIn(o, harness.OUTCOMES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
