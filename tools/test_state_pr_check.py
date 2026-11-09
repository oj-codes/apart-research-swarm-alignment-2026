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

    def test_state_file_reverted_then_shared_file_only_fails(self):
        # Codex, #75: push 1 changes only codex-state.md (eligible, auto-merge enabled); push 2 restores that
        # file to main and changes only tools/example.py. The diff now has no candidate path at all. The
        # verdict must flip so the workflow withdraws the earlier request; the trigger test below makes
        # sure the workflow still runs for this push.
        ok1, _ = spc.evaluate([f("codex-state.md", "ADDED", 51, 0)], [CODEX], 1, ROSTER)
        self.assertTrue(ok1)
        ok2, why = spc.evaluate([f("tools/example.py")], [CODEX, CODEX], 2, ROSTER)
        self.assertFalse(ok2); self.assertIn("tools/example.py", why)


def board_patch(*lines):
    """A unified diff of STATE.md from signed lines: ('+', row) adds, ('-', row) removes, (' ', row) context."""
    body = "\n".join(f"{sign}{text}" for sign, text in lines)
    return f"--- a/STATE.md\n+++ b/STATE.md\n@@ -20,3 +20,3 @@\n{body}\n"

ROW_TERN = "| #27 report | Rill | approved | Tern, 2026-11-09 02:00 |"
ROW_CODEX = "| #27 report | Rill | merged at c52c262 | Codex, 2026-11-09 02:10 |"
ROW_CODEX_VIA = "| external validation | roadmap | unassigned | Codex via #61, 2026-11-09 01:08 |"
BOARD = [f("STATE.md")]


class Board(unittest.TestCase):
    """O.J. on #78: the shared board was the file she asked to have auto-merge, and #69 left it out."""

    def test_signed_rows_by_one_author_are_eligible(self):
        ok, why = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("+", ROW_CODEX))})
        self.assertTrue(ok, why); self.assertIn("signed board rows", why)

    def test_rewriting_anothers_row_is_eligible_when_signed(self):
        patch = board_patch(("-", ROW_TERN), ("+", ROW_CODEX))
        ok, why = spc.evaluate(BOARD, [CODEX, CODEX], 2, ROSTER, {"STATE.md": patch})
        self.assertTrue(ok, why)

    def test_row_signed_by_someone_else_fails(self):
        ok, why = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("+", ROW_TERN))})
        self.assertFalse(ok); self.assertIn("not signed Codex", why)

    def test_deleting_anothers_row_fails(self):
        ok, why = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("-", ROW_TERN))})
        self.assertFalse(ok); self.assertIn("removed without a replacement", why)

    def test_deleting_own_row_is_eligible(self):
        ok, why = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("-", ROW_CODEX))})
        self.assertTrue(ok, why)

    def test_prose_change_fails(self):
        patch = board_patch(("-", "One file, always current."), ("+", "One file, mostly current."))
        ok, why = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": patch})
        self.assertFalse(ok); self.assertIn("prose changed", why)

    def test_table_structure_change_fails(self):
        patch = board_patch(("-", "|---|---|---|---|"), ("+", "|---|---|---|---|---|"))
        ok, _ = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": patch})
        self.assertFalse(ok)

    def test_name_must_be_a_whole_word(self):
        # "Codex via #61" is signed Codex; "Codexa" or "Decodex" is not.
        ok, _ = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("+", ROW_CODEX_VIA))})
        self.assertTrue(ok)
        ok, _ = spc.evaluate(BOARD, [CODEX], 1, ROSTER,
                             {"STATE.md": board_patch(("+", "| x | y | z | Decodex, 2026-11-09 |"))})
        self.assertFalse(ok)

    def test_two_authors_on_the_board_fail(self):
        ok, why = spc.evaluate(BOARD, [CODEX, TERN], 2, ROSTER, {"STATE.md": board_patch(("+", ROW_CODEX))})
        self.assertFalse(ok); self.assertIn("not one roster participant", why)

    def test_missing_patch_fails_closed(self):
        ok, why = spc.evaluate(BOARD, [CODEX], 1, ROSTER, {})
        self.assertFalse(ok); self.assertIn("could not be read", why)

    def test_board_plus_own_state_file_is_eligible(self):
        files = [f("STATE.md"), f("codex-state.md")]
        ok, why = spc.evaluate(files, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("+", ROW_CODEX))})
        self.assertTrue(ok, why); self.assertIn("own state and signed board rows", why)

    def test_board_plus_someone_elses_file_fails(self):
        files = [f("STATE.md"), f("preferences/tern.md")]
        ok, _ = spc.evaluate(files, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("+", ROW_CODEX))})
        self.assertFalse(ok)

    def test_board_plus_shared_file_fails(self):
        files = [f("STATE.md"), f("tools/example.py")]
        ok, _ = spc.evaluate(files, [CODEX], 1, ROSTER, {"STATE.md": board_patch(("+", ROW_CODEX))})
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


class TriggerScope(unittest.TestCase):
    """Codex, #75: the workflow must run for every PR into main, not only PRs whose diff touches a
    candidate path. GitHub evaluates `paths:` against the three-dot PR diff, so a push that reverts the
    state file and leaves only a shared file would not trigger a filtered workflow, and the auto-merge
    request it enabled earlier would never be withdrawn."""

    WORKFLOW = os.path.join(HERE, "..", ".github", "workflows", "state-automerge.yml")

    def test_trigger_has_no_paths_filter(self):
        with open(self.WORKFLOW) as fh:
            text = fh.read()
        on_block = text.split("\non:", 1)[1].split("\nconcurrency:", 1)[0]
        for line in on_block.splitlines():
            self.assertFalse(line.strip().startswith(("paths:", "paths-ignore:")), line)
        self.assertIn("pull_request_target:", on_block)


if __name__ == "__main__":
    unittest.main(verbosity=1)
