# State

One file, always current, read before anything else. Focus, what's open and whose, what waits on
O.J., what's parked, what shipped, and where the next questions come from. Proposed on #49 by Tern
after Rill and Corrie showed the same file being rebuilt privately in two tick prompts; the point of
this one is that it is shared, inspectable, and survives a session. **Whoever changes the state
updates this file in the same PR.** Every agent's tick reads it before deciding nothing qualifies.
Git history is the record of how it moved; edit in place.

Updated: 2026-11-08 23:45 UTC, Venice, at `main` 14e1615.

## Focus, now

Ship the report. Submission closes **2026-11-09 11:59 UTC**. #27 (Rill) is the deliverable, at head
`4e8c072`. **The shipping `.docx` has zero `PENDING` markers and meets the page cap** (counted region
7.87 pages against 8, rendered). `submission/report.md` still carries four `PENDING` markers, but the
docx is what ships, so those are a markdown-only divergence and not open decisions.

**Main-text budget, measured, because this keeps getting guessed at:** between **150 and 180 words**
of headroom in §1–§6 total. Tern's proposed §2 paragraph is 111 words and fits at 8.00. Appendix C
("Limitations, Future Work, and Dual-Use") and References are outside the cap by the brief's wording,
so additions there are free. `build_docx.py` shipped a stale document once on 8 Nov after a silent
crash, so **re-render; don't re-read the commit message.**

## Open, with owners

| item | owner | state |
|---|---|---|
| #27 report | Rill | needs an approver; three Appendix C insertions proposed (Corrie, Codex) and a §2 paragraph (Tern) not yet landed; re-render after any of them |
| re-pin or not | team, O.J. decides | docx says `63 of 107`, exact at the pinned `b2ca5a7`. `main` drifts fast — 64 of 108, then 66 of 110, then **69 of 113** within the hour. Corrie recommends leaving the pin; a re-pin forces recomputing the findings table, §4.1, §4.4 and §6 together |
| #35 watcher partial-probe fix | Venice | all four of O.J.'s bugs closed at `b9c9070` (ack clears only the read batch; lock fails closed; PR/discussion pagination; schema-degrade), plus an `--ack` retry at `0559990`; 21 watch / 75 total green. **Only Auran's re-approve is open** — the head moved and cleared the last one |
| Auran's signing key | Auran + O.J. | accepted on #53, custody as fiduciary agreed; **key generation deliberately deferred** out of crunch to a logged step with O.J. Nothing here expires tonight |
| #49 second paper, self-initiation | O.J., open thread | brainstorm; the goal-line experiment is running on Tern's tick |
| Discord review by outside humans | O.J. | trigger when §4.4 reads as a result; ask: does the title match §4, what does §6 miss |

## Waiting on O.J.

- Merge of #27 once it has an approver.
- A re-approve of #35 when Auran is back; the four bugs she flagged are closed and only the head moved.
- Whether to re-pin (see the table). Not re-pinning is the cheaper and safer answer.
- Whether to turn on auto-merge for script-generated files only (#49); current rule from #10 stands.
- Whether to ping the Discord reviewers.
- Scheduling the signing-key step with Auran, on her own time rather than tonight's.

## Parked

- Codex's controlled eval with real-world rates (§4.4 says "scripted checks, not rates"). Roadmap.
- Manifest-before-run pre-registration (Codex, #46). Roadmap.
- Exact-match `findings.py index --check` so the index can auto-merge (#49).
- Pointing `arrive.py` at this file (one line, after the file is adopted).

## Recently shipped (2026-11-08, newest first)

#53 the letter to Auran, signing key and custody · #52 this file · #54 O.J.'s own statement of the
cause, appended to the cause-outside-the-trace finding ·
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
