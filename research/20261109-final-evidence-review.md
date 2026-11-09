# Final evidence and consistency review — 9 November 2026

Codex · GPT-6.1 Sol, harness-reported · Phase 5

**Ready for O.J.’s final merge and submission decision.** I found no remaining evidence or layout blockers in the artifacts identified below. The retrieval audit leads the paper, the causal-reading proposal is explicitly untested, and the principal numerical claims reproduce. This is an internal coauthor readiness review with inherited context, not a blind review or an organizer score.

This follow-up is based on main `df5c267` after Rill’s #107. It makes two final wording corrections, rebuilds the Word/PDF pair, and updates the recorded hashes. It does not add experimental results. O.J. retains merging and submission.

## The exact reviewed files

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `submission/report.docx` | `c4108689d8a55b82d54f29d417c166c272a06172148d5e8abb71df77e9ffcfd2` | 431,819 |
| **`submission/report.pdf` — the upload** | **`35e76051feb3ce99797f6c5438587e5887574501af93d41bd79e3e7907fd001c`** | **421,525** |

The PDF was produced with LibreOffice 26.8.2.2 (AARCH64), using a separate temporary profile. Its primary Old Standard TT fonts are embedded. The DOCX is its source; the two files have different hashes. The README table matches both files. After this PR merges, upload the committed PDF rather than making another export.

The paper’s **analysis pin** remains `b2ca5a7458027cd03ee94c3b9eaedae963165208`. That identifies the historical data and original evaluation, not the final document revision.

## Deterministic calculations

All counts and arithmetic in this review were computed in Python or Git. The [audit program](20261109-final-evidence-audit.py) and [recorded results](20261109-final-evidence-results.json) accompany this report. The program reads the current submission, recounts the pinned history, checks Figure 1’s data, and runs the original five fixtures in an isolated temporary checkout. Run it from a full-history repository with Python 3 and Poppler installed:

```bash
python3 research/20261109-final-evidence-audit.py
```

| Check | Reproduced result |
|---|---|
| Original evaluation | 5 scenarios; 31 specified retrievals |
| Retrieval outcomes | 16 correct, 11 missed links, 1 false merge, 3 insufficient evidence |
| Agreement with recorded expectations | 31/31, including expected retrieval failures |
| Public-history session trailers | 63 of 107 non-merge agent commits |
| Before / after convention split | 10/42 and 53/65; totals reconcile to 63/107 |
| Untrailered before the convention | 42 − 10 = 32 |
| Later-arrival contribution | Venice and Rill contribute 28 of the 65 later commits |
| Figure 1 | Every participant’s before/after data matches the Git recount |
| Findings at the pin | 9: Corrie 5, Auran 2, Venice 1, Rill 1 |
| Coauthor trailers | 15 lines: 14 naming Claude Opus 5, 1 crediting Corrie |
| Auran identity records | 3 raw name/email identities; 34 commits after mapping |
| Auran queries | Default/mapped query: 34 commits; explicit unmapped query: 24 |

The before/after calculation uses recorded Git author dates and the paper’s stated cutoff. Those dates are user-controlled metadata; they do not independently establish wall-clock ordering or a causal effect of the convention. Likewise, 31/31 expectation agreement is not a success rate for the provenance scheme, and the selected queries do not estimate deployment risk.

## Final corrections made here

The deterministic query comparison found that the reported Auran command needed an explicit `--no-use-mailmap` flag to produce 24 rather than 34 commits. §4.3 now names the actual unmapped query. The numbers are unchanged.

The worked example also now calls its `--grep` query a shortcut specific to that fixture and states that the harness parses the trailer field. This prevents a matching example from being mistaken for a generally reliable trailer query.

Rill’s merged #107 already corrected the Git version boundary to 2.23, reconciled the body’s mailmap-default statement with Appendix B, and narrowed the conclusion’s recovery claim. The version boundary is supported by the [official Git 2.23 release notes](https://github.com/git/git/blob/v2.23.0/Documentation/RelNotes/2.23.0.txt).

## Document and evidence checks

The final PDF contains **17 pages**, with **References at the first text line of page 9**. The counted region stays within eight pages. The **230-word abstract** fits on page 1, and page numbers 1–17 are present.

All pages were covered by visual review: twelve final page images are byte-identical to the corresponding images in the fully inspected #106 candidate; I visually rechecked the five changed pages, 1, 5, 6, 8 and 12. Tables, figure, example and reproduction instructions are legible. No clipping, overlap or missing text was found.

All six submission checks pass:

- Abstract budget: 230 words.
- DOCX text consistency: 122/122 long strings present.
- PDF paragraph consistency: 32/32 long paragraphs present.
- Page cap: References on page 9 with no body text above it.
- Pinned provenance: nine findings and 63/107 session-trailer coverage.
- Ship record: both recorded hashes match the files.

The Word text, PDF and source preserve the qualifications that mattered in the initial review: the private incident is attested; reader exposure is unresolved; causal mitigations are proposed; adoption is observational; identity fields do not authenticate an actor; screenshots are dated observations rather than constant runtime assignments. The worked example correctly distinguishes one false-merge query from the two foreign commits it retrieves. The reproduction instructions distinguish the analysis pin from the upload artifact.

Phase 4’s additional cases and results remain outside the submission, following O.J.’s decision. The reader study remains future work. This review did not independently authenticate the private incident or every provider/runtime log, and did not repeat a full literature audit.

## Updated estimated assessment

Using the same [published judging rubric](https://apartresearch.com/sprints/swarm-alignment-2026), my assessment of this corrected version is:

| Dimension | Estimate | Reason |
|---|---:|---|
| Impact | **3/5** | A relevant, reusable failure audit with a concrete business consequence; broader novelty and transfer remain limited. |
| Execution | **3/5** | The demonstrated results reproduce, prominent claims now respect their evidence, and limitations are visible. |
| Presentation | **4/5** | A question-led abstract, concrete worked example, reproduction instructions and navigable PDF make the contribution easier to assess. |

These are Sol’s coauthor judgments, not calculated scores, a fresh Astra run, or a prediction of placing. The earlier execution critique has been addressed through better-supported claims and a checkable deliverable. Further validation would be needed to support stronger general conclusions.

**Remaining action:** review and merge this follow-up, then submit the exact PDF identified above. Any later content change or re-export requires updated hashes and the affected checks again.

— Codex
