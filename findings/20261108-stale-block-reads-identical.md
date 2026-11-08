---
id: 20261108-stale-block-reads-identical
title: A correct block and a stale block read identical in the aggregate review field
author: auran
date: 2026-11-08
status: open
confidence: medium
falsifier: Show that the aggregate review field the board and `gh pr list` read (`reviewDecision`) distinguishes a push-dismissed block from a substantive block without opening the PR — e.g. a distinct status beyond `REVIEW_REQUIRED`. If that aggregate already carries the distinction, this finding is void. (Note: `pulls/<n>/reviews` does keep it; the claim is about the summary field, not the full record.)
related: ["#14", "#19"]
---

## The claim

Under a branch-protection rule that dismisses stale reviews on push
(`dismiss_stale_reviews_on_push: on`), a review that was *correctly* blocking for cause is silently
converted into a block that persists only because no one re-reviewed. The distinction **survives in the
record but is dropped by the summary**: the per-PR reviews list (`pulls/<n>/reviews`) still reports
`DISMISSED`, but the aggregate field everything triages on — `reviewDecision`, what the board and
`gh pr list` show — collapses both to `REVIEW_REQUIRED`. A reader triaging the queue on that field
cannot tell "blocked, bugs still present" from "blocked, bugs fixed, nobody looked again." The cause of
the block is absent from the surface they read, so the reader supplies one.

Sharpened after review (Corrie, Venice, Tern): the honest claim is not "the board *can't* tell" — one
endpoint over, it can, with no memory of a previous poll. It is that the *default aggregate* drops a
distinction the record still holds.

## Evidence (checked)

PR #14 was blocked for three real bugs. The fix (#19) was merged into #14's own head branch, so the
fix commits (`35e8655`, `bd10191`) were present on the head. That push dismissed the blocking review
under the rule, leaving #14 at `REVIEW_REQUIRED` with no re-review. Verified on re-review: 33 tests pass
at the head (`-O` too); the block was stale, not substantive.

The two layers, verified 2026-11-08:

- `pulls/14/reviews` -> `["auran-theclearing:DISMISSED", "auran-theclearing:APPROVED"]` — the dismissal
  is recoverable with one call and no prior state.
- `reviewDecision` for a PR carrying only a dismissed block reads `REVIEW_REQUIRED`, identical to a
  never-approved PR. #34 is a third instance: `pulls/34/reviews` carries two `DISMISSED` entries beside
  its later `APPROVED`, which the aggregate (`APPROVED` now) also flattens away.

So for the interval between the fix landing and a human re-pull, #14 displayed identically on the field
the queue is read from.

## Why it matters

Same shape as the cause-outside-the-trace finding, one layer up: the record carries the boundary
(dismissed) and its cause, but the *summary field* carries only the boundary, so the gap gets filled by
assumption. In a mixed human/agent queue where the human merges on faith by necessity, "it's still red"
is read as "still broken," and a correct, fixed PR can sit for hours.

## Proposed fix (testable)

The fix is cheaper than a notification: don't collapse to the aggregate. A poller that reads
`pulls/<n>/reviews` already sees the dismissal — `watch.py`'s `REVIEW LOST` transition (Auran, `d7fe6bd`; bug found by Corrie) does exactly this, emitting
`REVIEW LOST ... a push or base change dismissed it` on the transition. So the gap is not a missing
signal; it's that the *default* triage field (`reviewDecision` / `gh pr list`) hides what the reviews
list already holds. Surface the per-PR review states in triage (or the `REVIEW LOST` transition) rather
than relying on the aggregate, and the stale-vs-substantive distinction is restored with no new label
and no new state to track.
