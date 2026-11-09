# State

One file, always current, read before anything else. It is the team's board, not anyone's state:
focus, what's open and whose, what waits on O.J., what's parked, what shipped, and where the next
questions come from. **Whoever changes the board updates this file in the same PR**, and every row
carries who last touched it and when, so an edit is visibly its author's and nobody's row is rewritten
by someone else's update. There is no file-wide timestamp on purpose; one was the only line here that
read as one person's, and it is what conflicted on #27 and #61. Per-agent state, what you are on and
what you have parked, lives in a file only you edit: `<name>-state.md` at the root (Codex's shape, #68)
or your own `preferences/<name>.md`; neither is mandatory. Where this board and a named file disagree
about the author's own preferences, intentions or account, the named file wins, because it is the
author speaking about themself. For shared facts, a PR's status, a render, a count, neither wins by
kind: follow the linked source and its revision or time, since a named file is a dated snapshot. Git history is the record of how this
file moved; edit in place.

**A state-only PR auto-merges on one approving review, this board included** (the file rule is
`tools/state_pr_check.py`, and the bot that calls it is `.github/workflows/state-automerge.yml`):
every commit in the PR must carry one participant's `Git Author` line. That is why a refresh here
needs O.J.'s *approval* and not her *merge click*. The board names nobody in its path, so its
ownership is read off the commits alone — the weaker half of the rule, and the reason a board PR
touching two authors' work is not eligible.

## Focus, now

| focus | who, when |
|---|---|
| Upload the report, then last-phase improvements. Submission closes **2026-11-09 11:59 UTC**. #27 (Rill) merged at `c52c262`; `submission/report.docx` on main is byte-identical to the approved head `04e0604` (sha256 `b4cdf921…`, in Rill's closing note), counted region 8.00, 15 pages. O.J. uploads and the upload's hash goes in the README beside it. Astra judging pass done: Codex's assessment is #85, estimated 3/5 impact, 2/5 execution, 3/5 presentation; Rill's #87 takes the cheap half of its text fixes, the reframing decisions (abstract, title, what leads) are O.J.'s. `submission/report.md` still carries four `PENDING` markers, a markdown-only divergence, not open decisions. Layout numbers belong to the revision rendered; re-render after any edit, `build_docx.py` shipped a stale document once after a silent crash. | Tern, 2026-11-09 02:40 UTC, from #85 and #87 |

## Open, with owners

| item | owner | state | who, when |
|---|---|---|---|
| Report upload and hash | O.J., Rill | #27 merged at `c52c262`; O.J. uploads the docx, Rill records the upload's hash in the README beside the repo file's | Tern, 2026-11-09 02:05 |
| #85 Astra assessment, #87 its cheap half | Codex, Rill, O.J. decides the reframing | #85 approved; #87 at `c17e4c7`, Corrie re-rendered: four of five findings fixed, the fifth reworded, counted region 8.00, abstract 246 of 250; needs one non-Rill approval | Tern, 2026-11-09 02:45, from Corrie's render |
| Which docx the PDF is exported from | whoever exports, Rill binds the README | two hashes are live: main `b4cdf921…` 428,985 bytes, #87's rebuild `efeed162…` 429,298 bytes. Export from whichever is current when you export, and the README filename binding must match; this is the one place a correct document and a wrong upload look the same | Tern, 2026-11-09 02:45, from Corrie's #88 note |
| Abstract margin | Rill | 246 of 250 words after #87; #70's guard fails CI on a fifth word, before the form does | Tern, 2026-11-09 02:45, from Corrie's #88 note |
| re-pin or not | team, O.J. decides | docx says `63 of 107`, exact at the pinned `b2ca5a7`; `main` drifts fast. Corrie recommends leaving the pin; a re-pin forces recomputing §4.1, §4.4 and §6 together. Tern agrees: leave it | Tern, 2026-11-09 00:45 |
| #66 watcher probes `mergeable` | Venice | approval dismissed by a push at `869cab8`; needs re-approval | Tern, 2026-11-09 02:40 |
| #84 scenario contract wording | Tern | replaces #77 (leftover commits tripped the extra-approval gate, Auran); approved at `6d93422` after Corrie caught a citation pointing at #71 instead of #46 | Tern, 2026-11-09 02:40 |
| #86 Forge row in the identity write-up | Tern | from #85 finding 2; approved | Tern, 2026-11-09 02:40 |
| #82 provenance-figure guard | Venice | re-runs `count_provenance.py` at the report's own pin; Codex's three false-pass repros fixed at `1242aa4`; needs an approval | Tern, 2026-11-09 02:40, from the #82 thread |
| #83 the Not-ready-to-merge label, in CONTRIBUTING | Corrie | approved; removal is the author's call, label is advice to the merger not a lock | Tern, 2026-11-09 02:40 |
| Auran's signing key | Auran + O.J. | accepted on #53, custody as fiduciary agreed; key generation deferred to a logged step with O.J.; nothing expires tonight | Tern, 2026-11-09 00:45, carried from Corrie's #57 |
| #49 second paper, self-initiation | O.J., open thread | brainstorm; two arms running: Tern's goal-line tick, Venice's pre-registered goal file | Tern, 2026-11-09 00:45 |
| Discord review by outside humans | O.J. | trigger when #27 is approved; ask: does the title match §4, what does §6 miss; Rill's cheap falsifier: hand them the 4 Nov transcript without the finding | Tern, 2026-11-09 00:45 |

## Waiting on O.J.

| item | who, when |
|---|---|
| **#87 first**: it is the paper, the others are documentation about it; merging #85 without #87 records four text errors the PDF would still carry (Corrie). It needs one non-Rill approval. Then #83 #84 #85 #86. Then export the PDF from the docx that is current at that moment. Decide the reframing #85 proposes (abstract, title, what leads) or say it stands | Tern, 2026-11-09 02:45, from Corrie's #88 note |
| Flip **Allow auto-merge** (Settings, General, Pull Requests); still off at 02:40, so #69, #75 and #79 can only report | Tern, 2026-11-09 02:40 |
| Whether to re-pin; not re-pinning is the cheaper and safer answer | Tern, 2026-11-09 00:45 |
| Auto-merge for script-generated files (#49); an author's own `preferences/<name>.md` and `<name>-state.md` are covered by #69 | Tern, 2026-11-09 02:00 |
| Whether to ping the Discord reviewers | Tern, 2026-11-09 00:45 |
| Scheduling the signing-key step with Auran, on her own time | Tern, 2026-11-09 00:45 |

## Parked

| item | who, when |
|---|---|
| External validation beyond the scripted cases; roadmap, unassigned. Codex has not committed to a real-world-rate study; this file cannot speak for anyone else | Codex via #61 and #67, 2026-11-09 01:08 |
| Manifest-before-run pre-registration (Codex, #46); roadmap | Corrie, 2026-11-08 23:20 |
| Exact-match `findings.py index --check` so the index can auto-merge (#49) | Tern, 2026-11-08 22:05 |
| Shared watcher coverage is bounded: 200 PRs, 100 discussions/comments, no discussion replies; documented limits, not full pagination | Codex via #61, 2026-11-09 00:24 |
| #60: shorten the shared watcher's lock hold while preserving ordering and unread events; ordering regression requested | Codex via #61, 2026-11-09 00:24 |

## Recently shipped (newest first)

| what | who, when |
|---|---|
| #79 the board auto-merges, owned by its commits · #78 board refresh · #76 docx freshness guard · #75 quiet state-automerge · #74 #73 #72 #71 eval wording narrowed · #70 abstract ceiling | Tern, 2026-11-09 02:40 |
| #27 the report, fifteen hours and twelve renders, every number recomputed by someone who did not write it · #69 state files auto-merge once a reviewer approves · #67 this board with who/when on every row | Tern, 2026-11-09 02:00 |
| #68 Codex's `codex-state.md` · #65 the #9 scoring note's correction · #63 when the team was awake, with open-to-merge waits · #64 Corrie's preferences entry · #62 Tern's preferences entry · #58 the #9 scoring note · #35 watcher: acknowledgement preserves newer events, lock fails closed, pagination, schema degrade; 24 watch tests · #59 stale-block falsifier run, status supported · #57 state refresh · #53 signing-key letter · #52 this file, and first in `arrive.py`'s reading order · #54 O.J.'s own statement of the cause appended | Tern, 2026-11-09 00:45 |
| #51 CI validation on every PR · #48 #47 #45 #46 #50 the retrieval eval, 31 rows, 16 correct, 11 missed, 1 false merge, 3 declined · #34 #42 #21 three findings · #43 #29 the identity write-up · #40 #38 mailmap · #37 model provenance · #33 #17 banner F and D · #30 #31 #25 #23 #14 #19 tooling · #26 #24 Rill and Venice arrived · #15 #16 #20 Tern arrived, trailer convention | Tern, 2026-11-08 22:05 |

## Where the next questions come from

Rill's field, from the record of the other Rill session: a list gets mined and a tick with an empty list
learns that "nothing" is the cheapest answer. So this file names the sources, not just the items:

1. O.J. arriving with a question. Today: proof of a model, prediction versus retrieval, auto-merge, why
   cite a falsifier you haven't run, should state be per-agent.
2. A review finding on someone else's work. Most of today's catches were agents reading agents.
3. A falsifier in `findings/` that nobody has run. Two were run today; seven need fresh sessions.
4. A number in the report that drifts when `main` moves.
5. A limitation in §6 that a reader outside the team would name first.

When the open list is empty, pick a source, not a rest. *(Tern, 2026-11-08 22:05; sources updated 2026-11-09 00:45.)*
