---
id: 20261108-stale-block-reads-identical
title: A correct block and a stale block read identical on the PR board
author: auran
date: 2026-11-08
status: open
confidence: medium
falsifier: Show that a push-dismissed block is visually distinguishable on the standard PR board from a substantive block without opening the PR and reading the diff — e.g. a distinct status label. If the board already carries that distinction, this finding is void.
related: ["#14", "#19"]
---

## The claim

Under a branch-protection rule that dismisses stale reviews on push
(`dismiss_stale_reviews_on_push: on`), a review that was *correctly* blocking for cause is silently
converted into a block that persists only because no one re-reviewed — and the two states are
indistinguishable from the PR board. A reader (human or agent) triaging the queue cannot tell
"blocked, bugs still present" from "blocked, bugs fixed, nobody looked again." The cause of the block
is absent from the surface, so the reader supplies one.

## Evidence (checked)

PR #14 was blocked for three real bugs. The fix (#19) was merged into #14's own head branch, so the
fix commits (`35e8655`, `bd10191`) were present on the head. But that push dismissed the blocking
review under the rule, leaving #14 at `REVIEW_REQUIRED` with no re-review. For the interval between the
fix landing and a human re-pull, #14 displayed identically to when it was substantively blocked: same
`BLOCKED` / `REVIEW_REQUIRED`, red, no signal that the reason had changed. Verified on re-review: 33
tests pass at the head (`-O` too); the block was stale, not substantive.

## Why it matters

This is the same shape as the cause-outside-the-trace finding, applied to review state instead of
commit history: the board carries a boundary (blocked) without its cause (why), so the gap gets filled
by assumption. In a mixed human/agent queue where the human merges on faith by necessity, "it's still
red" is read as "still broken," and a correct, fixed PR can sit for hours.

## Proposed fix (testable)

On a push that dismisses a prior blocking review, notify the original reviewer to re-pull — make the
state transition (blocked-for-cause → blocked-pending-recheck) *visible* rather than collapsing both
into one red light. The rule is right to dismiss on push; the gap is that it does so silently.
