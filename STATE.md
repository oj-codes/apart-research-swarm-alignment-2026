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

## Focus, now

| focus | who, when |
|---|---|
| Ship the report. Submission closes **2026-11-09 11:59 UTC**. #27 (Rill) is the deliverable at `04e0604`: approved by Auran, mergeable, twelfth render by Corrie at that head, abstract now on page 1, zero `PENDING` markers in the shipping `.docx`. The only step left is O.J.'s merge. `submission/report.md` still carries four `PENDING` markers, a markdown-only divergence, not open decisions. Layout numbers belong to the revision rendered; re-render after any edit, `build_docx.py` shipped a stale document once after a silent crash. | Tern, 2026-11-09 02:00 UTC, from Auran's approval and Corrie's render on #27 |

## Open, with owners

| item | owner | state | who, when |
|---|---|---|---|
| #27 report | Rill | approved by Auran at `04e0604`, mergeable; waits only on O.J.'s merge, then the Astra judging pass she proposed | Tern, 2026-11-09 02:00 |
| re-pin or not | team, O.J. decides | docx says `63 of 107`, exact at the pinned `b2ca5a7`; `main` drifts fast. Corrie recommends leaving the pin; a re-pin forces recomputing §4.1, §4.4 and §6 together. Tern agrees: leave it | Tern, 2026-11-09 00:45 |
| #66 watcher probes `mergeable` | Venice | approved by Auran; Codex's review reproduces a remaining `UNKNOWN` transition problem | Tern, 2026-11-09 01:15, from Codex's #67 note |
| #75 state-automerge false comments | Tern | the #69 workflow ran on every PR into main and wrote "withdrawn" where nothing was enabled; Codex's review taken at `d3d1a38`: trigger unfiltered, quiet unless withdrawing a real request, 17 offline cases; needs Auran's approval. Until it merges, every PR into main gets one false bot comment per push | Tern, 2026-11-09 02:00 |
| #76 docx freshness guard | Venice | CI fails if a sentence of `build_docx.py` is missing from the committed `report.docx`; Corrie's two points taken at `0bac023`; needs an approval | Tern, 2026-11-09 02:00, from Corrie's review |
| #77 scenario contract wording | Tern | draft; the docstring follow-up Codex asked for on #72, ready once #72 merges | Tern, 2026-11-09 02:00 |
| #70 abstract ceiling test | Venice | approved; guards the form's 150-to-250-word window, abstract at 248 | Tern, 2026-11-09 01:25, corrected from Codex's #67 note |
| Auran's signing key | Auran + O.J. | accepted on #53, custody as fiduciary agreed; key generation deferred to a logged step with O.J.; nothing expires tonight | Tern, 2026-11-09 00:45, carried from Corrie's #57 |
| #49 second paper, self-initiation | O.J., open thread | brainstorm; two arms running: Tern's goal-line tick, Venice's pre-registered goal file | Tern, 2026-11-09 00:45 |
| Discord review by outside humans | O.J. | trigger when #27 is approved; ask: does the title match §4, what does §6 miss; Rill's cheap falsifier: hand them the 4 Nov transcript without the finding | Tern, 2026-11-09 00:45 |

## Waiting on O.J.

| item | who, when |
|---|---|
| Merge #27 at `04e0604`, then the approved set #66 #70 #71 #72 #73 #74. #75 needs Auran first | Tern, 2026-11-09 02:00 |
| Flip **Allow auto-merge** (Settings, General, Pull Requests) now that #69 is in; without it the workflow only reports | Tern, 2026-11-09 02:00 |
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
| #69 state files auto-merge once a reviewer approves · #67 this board with who/when on every row | Tern, 2026-11-09 02:00 |
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
