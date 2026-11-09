#!/usr/bin/env python3
"""Offline regression cases for tools/state_pr_check.py, one per way it was shown to be wrong (Codex, #69)."""
import importlib.util, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("spc", os.path.join(HERE, "state_pr_check.py"))
spc = importlib.util.module_from_spec(spec); spec.loader.exec_module(spc)

ROSTER = {"tern": "Tern <tern@learnwithoj.com>", "codex": "Codex <codex@learnwithoj.com>"}
TERN = {"sha": "abc1234", "name": "Tern", "email": "tern@learnwithoj.com"}
CODEX = {"sha": "def5678", "name": "Codex", "email": "codex@learnwithoj.com"}

def f(path, ct="MODIFIED", add=3, dele=1):
    return {"path": path, "changeType": ct, "additions": add, "deletions": dele}


class Eligible(unittest.TestCase):
    def test_own_root_state_file(self):
        ok, why = spc.evaluate([f("codex-state.md", "ADDED", 51, 0)], [CODEX], 1, ROSTER)
        self.assertTrue(ok, why)

    def test_own_preferences_file(self):
        ok, why = spc.evaluate([f("preferences/tern.md")], [TERN, TERN], 2, ROSTER)
        self.assertTrue(ok, why)


class NotEligible(unittest.TestCase):
    def test_deleted_state_file_fails(self):  # Codex #3: changeType DELETED, 0 additions, 51 deletions returned ELIGIBLE
        ok, why = spc.evaluate([f("codex-state.md", "DELETED", 0, 51)], [CODEX], 1, ROSTER)
        self.assertFalse(ok); self.assertIn("deleted", why)

    def test_renamed_file_fails(self):
        ok, why = spc.evaluate([f("tern-state.md", "RENAMED")], [TERN], 1, ROSTER)
        self.assertFalse(ok); self.assertIn("renamed", why)

    def test_partial_commit_list_fails_closed(self):  # Codex #4: first page only
        ok, why = spc.evaluate([f("preferences/tern.md")], [TERN] * 30, 31, ROSTER)
        self.assertFalse(ok); self.assertIn("partial", why)

    def test_over_api_cap_fails_closed(self):
        ok, why = spc.evaluate([f("preferences/tern.md")], [TERN] * 251, 251, ROSTER)
        self.assertFalse(ok); self.assertIn("exceeds", why)

    def test_state_file_plus_tool_change_fails(self):  # Codex #1's vector at the rule level
        ok, why = spc.evaluate([f("tern-state.md"), f("tools/state_pr_check.py")], [TERN], 1, ROSTER)
        self.assertFalse(ok); self.assertIn("tools/state_pr_check.py", why)

    def test_shared_state_file_fails(self):
        ok, why = spc.evaluate([f("STATE.md")], [TERN], 1, ROSTER)
        self.assertFalse(ok)

    def test_other_participants_file_fails(self):
        ok, why = spc.evaluate([f("codex-state.md")], [TERN], 1, ROSTER)
        self.assertFalse(ok); self.assertIn("author line", why)

    def test_two_owners_fail(self):
        ok, why = spc.evaluate([f("codex-state.md"), f("preferences/tern.md")], [TERN], 1, ROSTER)
        self.assertFalse(ok); self.assertIn("more than one", why)

    def test_unknown_name_fails(self):
        ok, why = spc.evaluate([f("mallory-state.md")], [TERN], 1, ROSTER)
        self.assertFalse(ok); self.assertIn("not on the roster", why)

    def test_no_files_fails(self):
        ok, _ = spc.evaluate([], [TERN], 1, ROSTER)
        self.assertFalse(ok)


class HeadBinding(unittest.TestCase):
    """Codex #69: an older eligible run must not enable auto-merge for a newer head it never read."""

    def test_pinned_head_must_match(self):
        self.assertTrue(spc.head_matches("abc123", "ABC123"))
        self.assertFalse(spc.head_matches("abc123", "def456"))

    def test_unpinned_head_is_accepted(self):
        self.assertTrue(spc.head_matches(None, "anything"))

    def test_out_of_order_run_is_refused(self):
        # Run A read head A and found it eligible; by the time A acts, the PR is at head B (ineligible,
        # say it added STATE.md). A must refuse to act on B. The decision is head_matches, taken before
        # any mutation; --match-head-commit on the merge call is the second lock.
        run_a_head, current_head = "aaaaaaa", "bbbbbbb"
        self.assertFalse(spc.head_matches(run_a_head, current_head))


if __name__ == "__main__":
    unittest.main(verbosity=1)
