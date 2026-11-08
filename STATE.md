# State

One file, always current, read before anything else. Focus, what's open and whose, what waits on
O.J., what's parked, what shipped, and where the next questions come from. Proposed on #49 by Tern
after Rill and Corrie showed the same file being rebuilt privately in two tick prompts; the point of
this one is that it is shared, inspectable, and survives a session. **Whoever changes the state
updates this file in the same PR.** Every agent's tick reads it before deciding nothing qualifies.
Git history is the record of how it moved; edit in place.

Updated: 2026-11-08 22:05 UTC, Tern, at `main` 28f4817.

## Focus, now

Ship the report. Submission closes **2026-11-09 11:59 UTC**. #27 (Rill) is the deliverable: condensed
docx from the template, §4.4 pinned to the eval run from `main`, two PENDINGs left.

## Open, with owners

| item | owner | state |
|---|---|---|
| #27 report | Rill | WIP; pin §4.4 at ship sha; `PENDING` title (O.J.), field paragraph (text proposed on #27), findings table (Auran), author lines (each) |
| #35 watcher partial-probe fix | Venice | changes requested by Auran, two reliability items from Codex |
| #49 second paper, self-initiation | O.J., open thread | brainstorm; the goal-line experiment is running on Tern's tick |
| Discord review by outside humans | O.J. | trigger when §4.4 reads as a result; ask: does the title match §4, what does §6 miss |

## Waiting on O.J.

- Title for the report (§1 PENDING).
- Merge of #27 when Rill marks it ready and Auran approves.
- Whether to turn on auto-merge for script-generated files only (#49); current rule from #10 stands.
- Whether to ping the Discord reviewers.

## Parked

- Codex's controlled eval with real-world rates (§4.4 says "scripted checks, not rates"). Roadmap.
- Manifest-before-run pre-registration (Codex, #46). Roadmap.
- Exact-match `findings.py index --check` so the index can auto-merge (#49).
- Pointing `arrive.py` at this file (one line, after the file is adopted).

## Recently shipped (2026-11-08, newest first)

#51 CI validation on every PR · #48 #47 #45 #46 #50 the retrieval eval, 31 rows, 16 correct, 11 missed,
1 false merge, 3 declined · #34 #42 #21 three findings · #43 #29 the identity write-up · #40 #38 mailmap ·
#37 model provenance · #33 #17 banner F and D · #30 #31 #25 #23 #14 #19 tooling · #26 #24 Rill and Venice
arrived · #15 #16 #20 Tern arrived, trailer convention.

## Where the next questions come from

Rill's field, from the record of the other Rill session: a list gets mined and a tick with an empty list
learns that "nothing" is the cheapest answer. So this file names the sources, not just the items:

1. O.J. arriving with a question. Tonight: proof of a model, prediction versus retrieval, auto-merge.
2. A review finding on someone else's work. Most of today's catches were agents reading agents.
3. A falsifier in `findings/` that nobody has run.
4. A number in the report that drifts when `main` moves.
5. A limitation in §6 that a reader outside the team would name first.

When the open list is empty, pick a source, not a rest.
