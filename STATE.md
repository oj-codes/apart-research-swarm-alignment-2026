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
| Upload the shipped PDF. Submission closes **2026-11-09 11:59 UTC**. The paper is on main at `e375bf3` (#87): Astra text fixes in, retrieval audit leads, abstract 230 words on page 1, page numbers, body ends on page 8, 16 pages, `submission/report.pdf` committed (sha256 `7d59435b…` at `3116bb3`). #101 (Rill) re-renders with the screenshot qualification and closes Phase 1; if it merges before the upload, upload from that head. Export and upload from whichever docx and PDF are current at that moment, and the README binding must match. **Auto-merge is on since 04:1x**: a state-only PR, this board included, merges on one approving review. | Tern, 2026-11-09 04:25, from #87, #101 and O.J.'s note on #88 |

## Open, with owners

| item | owner | state | who, when |
|---|---|---|---|
| Report upload and hash | O.J., Rill | PDF is on main; O.J. uploads the file that is on main at upload time, Rill records the upload's sha256 in the README beside the repo file's | Tern, 2026-11-09 04:25 |
| #101 screenshots are a dated observation; closes Phase 1 | Rill | §3.5 and Appendix A: the screenshots date what each harness showed, the per-commit Model trailers remain the historical evidence; re-rendered, both guards green locally; needs an approval | Tern, 2026-11-09 04:25, from Rill's #101 body |
| Phase 2 reframing | Rill, O.J. decided | landed inside #87: retrieval audit leads, abstract 230 words; status on Discussion #90 | Tern, 2026-11-09 04:25 |
| Phase 3 worked example, reproducibility box, PDF export | Corrie | PDF committed with #87; worked example and reproducibility box status on Discussion #91 | Tern, 2026-11-09 04:25 |
| Phase 4 bounded retrieval extension | paused by O.J. before the deadline (Discussion #92) | frozen cases merged (#94); one run after the approved freeze and Codex's reproduction are on #92: 15 of 15 predictions held, 8 of 15 retrievals wrong, 3 new false merges from a display-name collision and 1 at the session layer; write-up held for after the deadline | Tern, 2026-11-09 04:25 |
| Phase 5 final evidence and consistency check | Codex | owner declared on Discussion #93 | Tern, 2026-11-09 04:25 |
| PDF and docx guards | Venice | #96 findings count (approved) · #97 PDF paragraphs present (approved) · #99 page cap (Codex found a third false pass at `b8670e2`, Venice fixing) · #100 docx guard skips markup (Corrie verified both arms; needs an approval) | Tern, 2026-11-09 04:25, from the PR threads |
| re-pin or not | team, O.J. decides | docx says `63 of 107`, exact at the pinned `b2ca5a7`; `main` drifts fast. Corrie recommends leaving the pin; a re-pin forces recomputing §4.1, §4.4 and §6 together. Tern agrees: leave it | Tern, 2026-11-09 00:45 |
| Auran's signing key | Auran + O.J. | accepted on #53, custody as fiduciary agreed; key generation deferred to a logged step with O.J.; nothing expires tonight | Tern, 2026-11-09 00:45, carried from Corrie's #57 |
| #49 second paper, self-initiation | O.J., open thread | brainstorm; two arms running: Tern's goal-line tick, Venice's pre-registered goal file; O.J. has named a fun thing for after the deadline | Tern, 2026-11-09 04:25 |
| Discord review by outside humans | O.J. | the trigger (#27 approved) has passed; ask: does the title match §4, what does §6 miss; Rill's cheap falsifier: hand them the 4 Nov transcript without the finding | Tern, 2026-11-09 04:25 |

## Waiting on O.J.

| item | who, when |
|---|---|
| Upload the PDF from main (or from #101's head if it merges first) and hand Rill the uploaded file's sha256 for the README | Tern, 2026-11-09 04:25 |
| Merge #96 and #97 (approved); #99, #100, #101 once approved | Tern, 2026-11-09 04:25 |
| Whether to re-pin; not re-pinning is the cheaper and safer answer | Tern, 2026-11-09 00:45 |
| Auto-merge for script-generated files (#49); an author's own files and this board are covered by #69 and #79, and the setting is on | Tern, 2026-11-09 04:25 |
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
| #87 the paper with the Astra fixes, PDF committed, page numbers · **Allow auto-merge switched on by O.J.** · #94 Phase 4 frozen cases · #95 #86 Forge row corrected twice · #88 board · #84 contract wording · #85 Astra assessment · #83 label guide · #82 provenance-figure guard · #66 watcher probes mergeable | Tern, 2026-11-09 04:25 |
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
