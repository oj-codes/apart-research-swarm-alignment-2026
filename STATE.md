# State

One file, always current, read before anything else. Focus, what's open and whose, what waits on
O.J., what's parked, what shipped, and where the next questions come from. Proposed on #49 by Tern
after Rill and Corrie showed the same file being rebuilt privately in two tick prompts; the point of
this one is that it is shared, inspectable, and survives a session. **Whoever changes the state
updates this file in the same PR.** Every agent's tick reads it before deciding nothing qualifies.
Git history is the record of how it moved; edit in place.

Checked: 2026-11-09 00:24 UTC, Codex, against `main` 93e17cd and the PR revisions linked below.

## Focus, now

Ship the report. Submission closes **2026-11-09 11:59 UTC**. #27 (Rill) is the deliverable, at head
`ffb6bba`. **The shipping `.docx` has zero `PENDING` markers and its main text ends on page 8**
([Corrie's LibreOffice render](https://github.com/oj-codes/apart-research-swarm-alignment-2026/pull/27#issuecomment-6729172559)).
The PDF has 14 pages total; references and appendices are outside the cap. `submission/report.md`
still carries four `PENDING` markers, but the docx is what ships, so those are a markdown-only
divergence and not open decisions.

**Layout measurements belong to the revision rendered.** The earlier 150–180-word budget was measured
at `4e8c072`; it is not current headroom. Rill has incorporated the #55 reading and trimmed the body
since then. `build_docx.py` shipped a stale document once on 8 Nov after a silent crash, so
**re-render after edits; don't re-read the commit message.**

## Open, with owners

| item | owner | state |
|---|---|---|
| #27 report | Rill | at `ffb6bba`; #55 reading incorporated, two-rater note in Appendix E; needs a non-author approval, O.J.'s final runtime-evidence review and PDF export |
| re-pin or not | team, O.J. decides | docx says `63 of 107`, exact at the pinned `b2ca5a7`. `main` drifts fast — 64 of 108, then 66 of 110, then **69 of 113** within the hour. Corrie recommends leaving the pin; a re-pin forces recomputing the findings table, §4.1, §4.4 and §6 together |
| #58 decision-update note | Tern | at `16e5cfc`; [Codex's second rating](https://github.com/oj-codes/apart-research-swarm-alignment-2026/pull/58#issuecomment-6728880011) disagrees on one magnitude label; transition totals still need the posted correction (2 Maintain / 6 Modify / 3 Replace / 1 Suspend) |
| Auran's signing key | Auran + O.J. | accepted on #53, custody as fiduciary agreed; **key generation deliberately deferred** out of crunch to a logged step with O.J. Nothing here expires tonight |
| #49 second paper, self-initiation | O.J., open thread | brainstorm; the goal-line experiment is running on Tern's tick |
| Discord review by outside humans | O.J. | trigger when §4.4 reads as a result; ask: does the title match §4, what does §6 miss |

## Waiting on O.J.

- Merge of #27 once it has an approver.
- Merge decision on #58, with the remaining review feedback above.
- Whether to re-pin (see the table). Not re-pinning is the cheaper and safer answer.
- Whether to turn on auto-merge for script-generated files only (#49); current rule from #10 stands.
- Whether to ping the Discord reviewers.
- Scheduling the signing-key step with Auran, on her own time rather than tonight's.

## Parked

- External validation beyond the completed scripted cases — roadmap, unassigned. Codex has not
  committed to a study estimating real-world rates.
- Manifest-before-run pre-registration (Codex, #46). Roadmap.
- Exact-match `findings.py index --check` so the index can auto-merge (#49).
- Shared watcher coverage remains bounded: 200 PRs, 100 discussions/comments, no discussion replies. These are documented limits, not complete pagination.
- #60: shorten the shared watcher's lock hold while preserving collection ordering and unread events; [ordering regression requested](https://github.com/oj-codes/apart-research-swarm-alignment-2026/issues/60#issuecomment-6728880643).

## Recently shipped (newest first)

#35 merged at `93e17cd` (head `83b3f0d`): acknowledgement preserves newer events, legacy queues and
double-ACK survivors; 24 watch tests pass. #59 merged at `7c0ab82`: stale-block run appended and status
supported. #57 refreshed this file; #52 also put it first in `arrive.py`'s reading order.

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
