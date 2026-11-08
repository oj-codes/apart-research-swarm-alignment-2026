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


def _run(argv, statepath, overrides=None):
    """Run watch.main() with a fixed, offline world. Returns the exit code.

    `overrides` replaces individual probes, e.g. {"probe_prs": lambda: None} to simulate a
    transient gh failure while the rest of the world still answers.
    """
    saved = sys.argv
    sys.argv = ["watch.py", "--as", "tester", "--state", statepath] + argv
    # Fix every probe so the "current reality" is constant and diffs are deterministic.
    world = {
        "probe_inbox": lambda name: [],
        "probe_prs": lambda: {"99": {"title": "x", "review": "", "draft": False}},
        "probe_pr_comments": lambda: {},
        "probe_discussions": lambda: {},
        "probe_main": lambda: "cafef00d",
    }
    if overrides:
        world.update(overrides)
    orig = {}
    for n, val in world.items():
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
        # ... and it stays pending across polls -- at-least-once, not cleared by polling ...
        self.assertEqual(_run(["--quiet"], self.state), 0)
        # ... until an --ack clears it. Only then is the next run quiet.
        _run(["--ack", "--quiet"], self.state)
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


class PartialProbeFailure(unittest.TestCase):
    """A probe that fails (returns None) while the others answer must NOT be read as a deletion.

    Venice, 2026-11-08: a transient `gh pr list` failure returned None -> {} and the diff reported
    every open PR as "closed or merged", waking the loop into a false merge storm."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.state = os.path.join(self.d, "s.json")
        with open(self.state, "w") as f:
            json.dump({"schema": watch.SCHEMA, "inbox": [],
                       "prs": {"99": {"title": "x", "review": "", "draft": False}},
                       "pr_comments": {}, "discussions": {}, "main": "cafef00d"}, f)

    def test_failed_pr_probe_carries_the_last_known_list(self):
        rc = _run(["--quiet"], self.state, overrides={"probe_prs": lambda: None})
        self.assertEqual(rc, 1, "a failed pr probe is not a change; it must not read as a close")
        kept = json.load(open(self.state)).get("prs") or {}
        self.assertIn("99", kept, "the last known PR list must be carried, not blanked to {}")

    def test_failed_discussion_probe_carries_too(self):
        rc = _run(["--quiet"], self.state, overrides={"probe_discussions": lambda: None})
        self.assertEqual(rc, 1)
        self.assertIn("discussions", json.load(open(self.state)))

    def test_failed_main_probe_carries_not_clears(self):
        # probe_main returns None on failure (not ""), so it must be carried like the rest.
        rc = _run(["--quiet"], self.state, overrides={"probe_main": lambda: None})
        self.assertEqual(rc, 1, "a failed main probe is not a change")
        self.assertEqual(json.load(open(self.state)).get("main"), "cafef00d",
                         "the last known main sha must survive a failed probe")

    def test_pending_survives_polls_and_clears_on_ack(self):
        # A change must stay pending until --ack, so a wake whose consumer died is re-reported.
        with open(self.state, "w") as f:
            json.dump({"schema": watch.SCHEMA, "inbox": [], "prs": {},
                       "pr_comments": {}, "discussions": {}, "main": "deadbeef"}, f)
        self.assertEqual(_run(["--quiet"], self.state), 0)          # change, pending written
        st = json.load(open(self.state))
        self.assertTrue(st.get("pending"), "the change must be recorded in pending")
        self.assertEqual(_run(["--quiet"], self.state), 0)          # still pending, not consumed
        _run(["--ack", "--quiet"], self.state)
        self.assertEqual(json.load(open(self.state)).get("pending"), [])
        self.assertEqual(_run(["--quiet"], self.state), 1)          # now quiet

    def test_state_is_written_atomically_tmp_is_gone(self):
        _run(["--quiet"], self.state)
        self.assertTrue(os.path.exists(self.state))
        self.assertFalse(os.path.exists(self.state + ".tmp"), "os.replace must leave no .tmp behind")

    def test_a_real_change_still_reports_when_another_probe_fails(self):
        # discussions fails, but a genuinely new PR appears: still a change (via prs).
        rc = _run(["--quiet"], self.state, overrides={
            "probe_discussions": lambda: None,
            "probe_prs": lambda: {"99": {"title": "x", "review": "", "draft": False},
                                  "100": {"title": "new", "review": "", "draft": False}},
        })
        self.assertEqual(rc, 0, "a working probe's real change must still wake the loop")


class Delivery(unittest.TestCase):
    """At-least-once: a change stays pending until --ack, so a wake whose consumer died is
    re-reported rather than marked seen by the persistence that preceded it (Corrie, #35)."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.state = os.path.join(self.d, "s.json")
        with open(self.state, "w") as f:
            json.dump({"schema": watch.SCHEMA, "inbox": [], "prs": {},
                       "pr_comments": {}, "discussions": {}, "main": "deadbeef"}, f)

    def test_pending_survives_a_poll_and_clears_on_ack(self):
        self.assertEqual(_run(["--quiet"], self.state), 0)      # a change
        self.assertEqual(_run(["--quiet"], self.state), 0)      # STILL pending, not consumed by polling
        self.assertTrue(json.load(open(self.state)).get("pending"))
        _run(["--ack", "--quiet"], self.state)                  # the consumer confirms
        self.assertEqual(json.load(open(self.state)).get("pending"), [])
        self.assertEqual(_run(["--quiet"], self.state), 1)      # quiet only now

    def test_state_written_atomically_no_tmp_left(self):
        _run(["--quiet"], self.state)
        self.assertTrue(os.path.exists(self.state))
        self.assertFalse(os.path.exists(self.state + ".tmp"))


class MainProbeCarry(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.state = os.path.join(self.d, "s.json")
        with open(self.state, "w") as f:
            json.dump({"schema": watch.SCHEMA, "inbox": [],
                       "prs": {"99": {"title": "x", "review": "", "draft": False}},
                       "pr_comments": {}, "discussions": {}, "main": "cafef00d"}, f)

    def test_failed_main_probe_carries_not_blanks(self):
        rc = _run(["--quiet"], self.state, overrides={"probe_main": lambda: None})
        self.assertEqual(rc, 1, "a down git fetch is not a change")
        self.assertEqual(json.load(open(self.state)).get("main"), "cafef00d",
                         "main must be carried, not blanked, when its probe fails")


if __name__ == "__main__":
    unittest.main()
