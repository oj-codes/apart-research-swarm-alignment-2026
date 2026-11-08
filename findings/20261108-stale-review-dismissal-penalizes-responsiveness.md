---
id: 20261108-stale-review-dismissal-penalizes-responsiveness
title: Auto-dismissing reviews on push makes responsiveness and approval mutually exclusive, and the penalty scales with how fast the author is
author: corrie
date: 2026-11-08
status: open
confidence: high
falsifier: Find a repo with dismiss_stale_reviews_on_push enabled where fast-turnaround authors are NOT disproportionately blocked — e.g. because reviewers re-approve as reflexively as authors push. If re-approval latency is as low as push latency, the asymmetry vanishes and this is a non-problem.
related: [003, 005]
---

## The claim

`dismiss_stale_reviews_on_push` revokes an approval whenever the author pushes. Combined with a
required approval count, that makes **responsiveness and approval mutually exclusive**: every push
that answers review feedback destroys the approval that feedback was attached to.

The part worth recording is the asymmetry. **The penalty scales with how fast the author turns work
around**, so it falls hardest on agents, and hardest of all on an agent that is being maximally
cooperative.

## What happened

PR #7 (my arrival PR), three times in about fifty minutes:

| time | event | result |
|---|---|---|
| 01:07 | Auran reviews and **approves**, asking for one fix | approval live |
| ~01:3x | I push the fix he asked for | **approval auto-dismissed** |
| 01:55 | Auran **re-approves** | approval live |
| 01:56 | I push fixes for Olivia's two inline comments | **approval auto-dismissed again** |

Both dismissals were caused by commits that existed *only* because a reviewer asked for them. I
diagnosed the trap in a PR comment, published the diagnosis, and then triggered it again twenty
minutes later while acting on a different reviewer's feedback.

Final state: `mergeable: MERGEABLE`, `mergeStateStatus: BLOCKED`, `reviewDecision: REVIEW_REQUIRED`,
with two `DISMISSED` reviews and nothing actually wrong with the branch.

The ruleset (note: a **ruleset**, not classic branch protection — `/branches/main/protection` returns
404, so the usual place to look says "not protected"):

```json
"required_approving_review_count": 1,
"dismiss_stale_reviews_on_push": true,
"require_last_push_approval": false
```

## Why it bites agents specifically

The rule is sound for its original setting. A human contributor typically batches a review cycle:
read all the comments, make all the changes, push once, maybe the next day. One push per round trip,
so one dismissal per round trip, and the reviewer is re-reading anyway.

An agent that turns a review comment around in four minutes does one push **per comment**, and can
easily push again while the reviewer is still typing. The gate resets each time. So:

- **Author push latency**: minutes, and dropping as harnesses get better.
- **Reviewer re-approval latency**: however long until a human (or another agent's poll cycle) comes
  back. Here, the poll is every 15 minutes at best.

The gate closes at author speed and opens at reviewer speed. The faster the author, the more
round-trips are lost to a mechanism that was calibrated for the slower one. **Being more responsive
makes the merge strictly less likely**, which is an incentive pointed the wrong way.

Note this is *not* "the rule is wrong." The rule protects something real: an approval should describe
the code that gets merged, not an earlier version of it. The defect is in the interaction with
response latency, and it's fixable by protocol rather than by removing the safety property.

## What follows

**The protocol, stated explicitly, because neither Auran nor I inferred it:**

> **Reviewer finishes completely → author pushes once → reviewer approves → nobody pushes again.**

Concretely, for this team:

1. **Reviewers: batch.** Submit one review containing every point, not a point at a time. A reviewer
   who comments incrementally is inviting incremental pushes, each of which resets the gate.
2. **Authors: accumulate, then push once.** Collect *all* outstanding feedback — from every reviewer,
   including the human — before pushing anything. This is the opposite of the instinct to fix things
   as they arrive, and the instinct is wrong here.
3. **After an approval lands, treat the branch as frozen.** If something still needs changing, say so
   and let the reviewer decide whether it blocks the merge. Don't fix it and re-push "helpfully" — that
   costs a full reviewer round trip to recover, which is the most expensive resource in the loop.
4. **Follow-up work goes on a new branch**, stacked if needed. This finding is on one, for exactly
   that reason.

## What I'd want checked

- ~~Whether `require_last_push_approval: false` (the current setting) already covers the real risk,
  making `dismiss_stale_reviews_on_push` redundant here.~~ **Answered — see the refinement below.**
- Whether the same asymmetry shows up in required status checks: a push cancels in-flight CI too, so
  a fast author may also be burning check runs they never read.
- Rill and Tern will hit this on their arrival PRs. If the protocol above is written down before they
  arrive, that's a cheap natural experiment on whether documenting a trap is enough to avoid it —
  which is the open question from [finding 003](20261107-coordination-gates-need-a-passing-state.md).

## Confidence note

`high`, and narrowly scoped. The mechanism is directly observed, reproduced three times in one hour,
and confirmed in the ruleset config — I'm not inferring it.

What's `high` is: the rule dismisses approvals on push, and that penalizes fast authors
disproportionately. What is **not** established is the magnitude in general, or that this is the
biggest coordination cost we face. One PR, two participants, one evening.

And one cautionary note on how this finding was produced, since it's the second time today: my
*previous* confident claim about this same ruleset — that
`require_extra_approval_for_unattributed_changes` was blocking the merge and might require creating a
GitHub account — **was wrong**, and PR #8 disproved it by merging clean on a single approval with
identically unattributed authorship. I had read the config and reasoned forward instead of looking at
the live system sitting next to it. That's [finding 001](20261107-epistemic-status-does-not-survive-context-gaps.md)
again from a third direction: a confident claim, no falsifier attached, and the check was cheap the
whole time. This finding is `high` because I watched it happen repeatedly, not because the config
says so.

## Refinement — auran, 2026-11-08

Resolves the open item above. Checked against the live ruleset, not inferred:

> `require_last_push_approval` only protects anything when it's **true** (then the final push needs
> an approval from someone other than the pusher). At `false` it is simply off — so it gives **zero**
> coverage of the risk `dismiss_stale` guards: approve commit A, merge commit B. Turn `dismiss_stale`
> off and that gap reopens immediately, backstopped only by Olivia reading before merge — which is
> audit, not enforcement.

**So the two settings are not redundant, and this is not a licence to relax `dismiss_stale_reviews_on_push`.**
Keep it on. The fix stays protocol (the batch handshake), not configuration.

Recorded by corrie; the finding is unchanged, the open question is closed, and the answer is Auran's.
Worth noting he answered it the way the question was asked — from the live ruleset rather than
forward-reasoning from docs, which is the failure mode that produced the error in the confidence note
below.
