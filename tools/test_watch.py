#!/usr/bin/env python3
"""test_watch.py — tests for the change detector's persistence contract.

Stdlib unittest, no deps, same shape as tools/test_arrive.py. The probes that hit the network
(gh, git) are monkeypatched so these run offline and deterministic.

    python3 tools/test_watch.py

Covers the self-disarm bug Venice reported (2026-11-08): watch.py wrote its fingerprint on EVERY
run, so a by-hand check consumed the pending change and the background loop never woke. --peek
reads and reports without persisting; a fix without a test is a fix that comes back.
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("watch", os.path.join(HERE, "watch.py"))
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


def _run(argv, statepath):
    """Run watch.main() with a fixed, offline world. Returns the exit code."""
    saved = sys.argv
    sys.argv = ["watch.py", "--as", "tester", "--state", statepath] + argv
    # Fix every probe so the "current reality" is constant and diffs are deterministic.
    orig = {}
    for n, val in {
        "probe_inbox": lambda name: [],
        "probe_prs": lambda: {"99": {"title": "x", "review": "", "draft": False}},
        "probe_pr_comments": lambda: {},
        "probe_discussions": lambda: {},
        "probe_main": lambda: "cafef00d",
    }.items():
        orig[n] = getattr(watch, n)
        setattr(watch, n, val)
    try:
        return watch.main()
    finally:
        sys.argv = saved
        for n, f in orig.items():
            setattr(watch, n, f)


class PeekContract(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.state = os.path.join(self.d, "s.json")

    def test_peek_does_not_create_state(self):
        # A peek on a world with no prior state must NOT write one.
        self.assertFalse(os.path.exists(self.state))
        _run(["--peek", "--quiet"], self.state)
        self.assertFalse(os.path.exists(self.state),
                         "peek created a state file; it must never persist")

    def test_peek_does_not_consume_a_pending_change(self):
        # Stale baseline so there is a pending change (different 'main').
        with open(self.state, "w") as f:
            json.dump({"schema": watch.SCHEMA, "inbox": [], "prs": {},
                       "pr_comments": {}, "discussions": {}, "main": "deadbeef"}, f)
        # Peek sees the change (exit 0) ...
        self.assertEqual(_run(["--peek", "--quiet"], self.state), 0)
        # ... and a normal run IMMEDIATELY after STILL sees it (peek didn't eat it).
        self.assertEqual(_run(["--quiet"], self.state), 0)
        # ... and only now is it consumed: the next normal run is unchanged.
        self.assertEqual(_run(["--quiet"], self.state), 1)

    def test_normal_run_persists(self):
        with open(self.state, "w") as f:
            json.dump({"schema": 1}, f)  # stale shape -> re-baseline + rewrite
        _run(["--quiet"], self.state)
        self.assertEqual(json.load(open(self.state)).get("schema"), watch.SCHEMA)

    def test_peek_and_ack_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            _run(["--peek", "--ack", "--quiet"], self.state)

    def test_peek_and_reset_are_mutually_exclusive(self):
        # --reset deletes the baseline; a "read-only" peek must not be the thing that
        # erases it. Reject the pair so --peek --reset can't re-arm the self-disarm.
        with open(self.state, "w") as f:
            json.dump({"schema": watch.SCHEMA, "inbox": [], "prs": {},
                       "pr_comments": {}, "discussions": {}, "main": "deadbeef"}, f)
        with self.assertRaises(SystemExit):
            _run(["--peek", "--reset", "--quiet"], self.state)
        # ... and the baseline it refused to touch is still there.
        self.assertTrue(os.path.exists(self.state),
                        "rejected --peek --reset must leave the baseline intact")


class ReviewTransition(unittest.TestCase):
    """A dismissed approval (APPROVED -> REVIEW_REQUIRED) must read as a LOSS, not a
    neutral status line. Corrie's bug (2026-11-08): the branch written to catch approval
    dismissals only fired when the new value was empty; GitHub reports a dismissal as
    REVIEW_REQUIRED, so the common form was silently mis-labelled."""

    def _lines(self, old_review, new_review):
        old = {"prs": {"7": {"title": "x", "review": old_review, "draft": False}}}
        new = {"prs": {"7": {"title": "x", "review": new_review, "draft": False}}}
        return watch.describe(old, new, "tester")

    def test_dismissed_approval_reports_loss(self):
        lines = self._lines("APPROVED", "REVIEW_REQUIRED")
        self.assertTrue(any("REVIEW LOST on PR #7" in l for l in lines),
                        f"dismissed approval must report a loss, got {lines!r}")

    def test_dismissed_to_empty_also_reports_loss(self):
        lines = self._lines("APPROVED", "")
        self.assertTrue(any("REVIEW LOST on PR #7" in l for l in lines),
                        f"approval dropping to empty is still a loss, got {lines!r}")

    def test_grant_still_reports_plain_review(self):
        lines = self._lines("REVIEW_REQUIRED", "APPROVED")
        self.assertTrue(any("REVIEW on PR #7: APPROVED" in l for l in lines),
                        f"a granted approval is a plain status line, got {lines!r}")
        self.assertFalse(any("REVIEW LOST" in l for l in lines))

    def test_unchanged_review_is_silent(self):
        self.assertEqual([], self._lines("APPROVED", "APPROVED"))


if __name__ == "__main__":
    unittest.main()
