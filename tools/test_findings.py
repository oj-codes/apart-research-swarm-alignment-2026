#!/usr/bin/env python3
"""test_findings.py — failure paths for the findings tool.

Stdlib unittest, no deps, same shape as tools/inbox/test_mail.py. Every test runs against a
scratch findings/ dir, so none of this touches the real one.

    python3 tools/test_findings.py

Covers what Olivia asked to see before merge — concurrent creation and malformed input — plus the
index markers, because that code path writes into a shared document and a bad assumption there
destroys someone else's prose rather than just erroring.

Add a test when you add a failure mode.
"""
import importlib.util
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    spec = importlib.util.spec_from_file_location("findings", os.path.join(HERE, "findings.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GOOD = """---
id: {stem}
title: A claim someone could disagree with
author: corrie
date: 2026-11-08
status: open
confidence: medium
falsifier: An observation that would show this is wrong
related: []
---

## The claim
body
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.mkdtemp(prefix="findings-test-")
        self.mod.FINDINGS = self.tmp
        self.mod.README = os.path.join(self.tmp, "README.md")
        self.write_readme(f"# findings\n\nintro\n\n{self.mod.BEGIN} -->\nold table\n{self.mod.END}\n\ntail\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_readme(self, text):
        with open(self.mod.README, "w", encoding="utf-8") as f:
            f.write(text)

    def read_readme(self):
        with open(self.mod.README, encoding="utf-8") as f:
            return f.read()

    def finding(self, stem, body=None):
        p = os.path.join(self.tmp, f"{stem}.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(body if body is not None else GOOD.format(stem=stem))
        return p


class Markers(Base):
    """cmd_index writes into a shared doc. It must validate before it splices."""

    def assert_refused(self):
        before = self.read_readme()
        self.assertEqual(self.mod.cmd_index(None), 1)
        self.assertEqual(self.read_readme(), before, "README must be left untouched on refusal")

    def test_valid_markers_rewrite(self):
        self.finding("20261108-a-valid-finding")
        self.assertEqual(self.mod.cmd_index(None), 0)
        self.assertIn("20261108-a-valid-finding", self.read_readme())
        self.assertIn("tail", self.read_readme(), "content after the block must survive")
        self.assertIn("intro", self.read_readme(), "content before the block must survive")

    def test_missing_begin_marker(self):
        self.write_readme(f"# findings\n\nintro\n{self.mod.END}\ntail\n")
        self.assert_refused()

    def test_missing_end_marker(self):
        self.write_readme(f"# findings\n\n{self.mod.BEGIN} -->\ntable\ntail\n")
        self.assert_refused()

    def test_both_markers_missing(self):
        self.write_readme("# findings\n\nno markers at all\n")
        self.assert_refused()

    def test_duplicate_begin_markers(self):
        self.write_readme(
            f"{self.mod.BEGIN} -->\na\n{self.mod.BEGIN} -->\nb\n{self.mod.END}\n")
        self.assert_refused()

    def test_duplicate_end_markers(self):
        self.write_readme(
            f"{self.mod.BEGIN} -->\na\n{self.mod.END}\nb\n{self.mod.END}\n")
        self.assert_refused()

    def test_end_before_begin_does_not_eat_the_file(self):
        """The dangerous one: splicing text[:start]+table+text[end:] would delete the middle."""
        self.write_readme(
            f"# findings\n{self.mod.END}\nIMPORTANT PROSE\n{self.mod.BEGIN} -->\n")
        self.assert_refused()
        self.assertIn("IMPORTANT PROSE", self.read_readme())

    def test_unclosed_begin_comment(self):
        self.write_readme(f"# findings\n{self.mod.BEGIN}\ntable\n{self.mod.END}\n")
        self.assert_refused()

    def test_unreadable_readme(self):
        os.remove(self.mod.README)
        self.assertEqual(self.mod.cmd_index(None), 1)

    def test_check_reports_bad_markers(self):
        self.write_readme("# findings\nno markers\n")
        self.assertEqual(self.mod.cmd_check(None), 1)


class Malformed(Base):
    """Incomplete findings must look incomplete, not get defaults substituted for them."""

    def errors_for(self, stem, body):
        self.finding(stem, body)
        item = [i for i in self.mod.all_findings() if i["_file"] == f"{stem}.md"][0]
        return item["_errors"]

    def test_well_formed_has_no_errors(self):
        self.assertEqual(self.errors_for("20261108-ok", GOOD.format(stem="20261108-ok")), [])

    def test_no_header_block_at_all(self):
        errs = self.errors_for("20261108-bare", "just some prose, no header\n")
        self.assertTrue(any("no '---' header" in e for e in errs))

    def test_unclosed_header_block(self):
        errs = self.errors_for("20261108-unclosed", "---\nid: 20261108-unclosed\ntitle: x\n")
        self.assertTrue(any("never closed" in e for e in errs))

    def test_missing_required_fields_are_each_named(self):
        errs = self.errors_for("20261108-thin", "---\nid: 20261108-thin\n---\n\nbody\n")
        for field in ("title", "author", "date", "status", "confidence", "falsifier"):
            self.assertTrue(any(f"missing required field: {field}" == e for e in errs),
                            f"{field} should be reported missing")

    def test_no_silent_defaults(self):
        """The old version substituted id/title/status/confidence for missing values."""
        self.finding("20261108-thin", "---\nid: 20261108-thin\n---\n\nbody\n")
        item = [i for i in self.mod.all_findings() if i["_file"] == "20261108-thin.md"][0]
        self.assertNotIn("confidence", item, "must not invent a confidence value")
        self.assertNotIn("title", item, "must not invent a title")
        self.assertNotIn("status", item, "must not invent a status")

    def test_bad_confidence_value(self):
        body = GOOD.format(stem="20261108-badconf").replace("confidence: medium", "confidence: pretty-sure")
        errs = self.errors_for("20261108-badconf", body)
        self.assertTrue(any("confidence 'pretty-sure'" in e for e in errs))

    def test_bad_status_value(self):
        body = GOOD.format(stem="20261108-badstatus").replace("status: open", "status: vibes")
        errs = self.errors_for("20261108-badstatus", body)
        self.assertTrue(any("status 'vibes'" in e for e in errs))

    def test_placeholder_falsifier_is_an_error(self):
        body = GOOD.format(stem="20261108-todo").replace(
            "falsifier: An observation that would show this is wrong",
            f"falsifier: {self.mod.PLACEHOLDER}")
        errs = self.errors_for("20261108-todo", body)
        self.assertTrue(any("placeholder" in e for e in errs))

    def test_id_must_match_filename_stem(self):
        body = GOOD.format(stem="20261108-something-else")
        errs = self.errors_for("20261108-actual-name", body)
        self.assertTrue(any("does not match the filename stem" in e for e in errs))

    def test_malformed_makes_list_and_check_fail(self):
        self.finding("20261108-bare", "no header\n")
        self.assertEqual(self.mod.cmd_check(None), 1)
        self.assertEqual(self.mod.cmd_list(None), 1)

    def test_readme_is_not_treated_as_a_finding(self):
        self.assertEqual([i for i in self.mod.all_findings() if i["_file"] == "README.md"], [])


class Concurrency(Base):
    """Two agents in separate worktrees must not be able to collide in silence."""

    def test_duplicate_ids_detected(self):
        """The old sequential scheme produced exactly this: two files, one id, merged cleanly."""
        self.finding("20261108-first", GOOD.format(stem="20261108-first"))
        self.finding("20261108-second", GOOD.format(stem="20261108-first"))  # same id, other file
        dups = self.mod.duplicate_ids(self.mod.all_findings())
        self.assertIn("20261108-first", dups)
        self.assertEqual(len(dups["20261108-first"]), 2)
        self.assertEqual(self.mod.cmd_check(None), 1)

    def test_unique_ids_pass(self):
        self.finding("20261108-first")
        self.finding("20261108-second")
        self.assertEqual(self.mod.duplicate_ids(self.mod.all_findings()), {})
        self.assertEqual(self.mod.cmd_check(None), 0)

    def test_same_title_same_day_refuses_rather_than_overwriting(self):
        """Concurrent creation of the same claim collides on FILENAME, which is the visible case."""
        class Args:
            name, title, confidence = "corrie", "A duplicated claim", "low"
            falsifier = "something checkable"
        a = Args()
        self.assertEqual(self.mod.cmd_new(a), 0)
        created = [f for f in os.listdir(self.tmp) if f.endswith(".md") and f != "README.md"]
        self.assertEqual(len(created), 1)
        body_before = open(os.path.join(self.tmp, created[0]), encoding="utf-8").read()

        self.assertEqual(self.mod.cmd_new(a), 1, "second create must refuse")
        still = [f for f in os.listdir(self.tmp) if f.endswith(".md") and f != "README.md"]
        self.assertEqual(len(still), 1, "must not create a second file")
        self.assertEqual(open(os.path.join(self.tmp, created[0]), encoding="utf-8").read(),
                         body_before, "must not overwrite the existing finding")

    def test_new_rejects_placeholder_falsifier(self):
        class Args:
            name, title, confidence = "corrie", "Another claim", "low"
            falsifier = "TODO: figure this out later"
        self.assertEqual(self.mod.cmd_new(Args()), 2)

    def test_new_rejects_empty_falsifier(self):
        class Args:
            name, title, confidence = "corrie", "Yet another claim", "low"
            falsifier = "   "
        self.assertEqual(self.mod.cmd_new(Args()), 2)

    def test_new_rejects_bad_confidence(self):
        class Args:
            name, title, confidence = "corrie", "A third claim", "quite-sure"
            falsifier = "something checkable"
        self.assertEqual(self.mod.cmd_new(Args()), 2)

    def test_new_writes_a_file_that_validates(self):
        class Args:
            name, title, confidence = "corrie", "A clean new claim", "speculative"
            falsifier = "an observation that would settle it"
        self.assertEqual(self.mod.cmd_new(Args()), 0)
        items = [i for i in self.mod.all_findings()]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["_errors"], [],
                         "a freshly created finding must pass its own validator")


if __name__ == "__main__":
    unittest.main(verbosity=2)
