# submission/ — the sprint report

The brief wants a PDF from the official template, 8 pages maximum not counting references and
appendices, an abstract of 150 to 250 words, author names and affiliations, and a Limitations and
Dual-Use / Ethical Considerations appendix. Deadline 2026-11-08, 11:59 PM Anywhere on Earth, which is
11:59 UTC on 2026-11-09.

`report.docx` is the submission: the official template, filled. `build_docx.py` generates it from the
content in the script, so a change is a change to the script and a rebuild, not a hand edit:

```bash
python3 submission/build_docx.py <copy-of-template.docx> submission/report.docx
```

The build can fail silently: if the script crashes, the previous `report.docx` stays on disk unchanged and `git status` cannot tell it from a fresh build (this happened once, at 95e04ca). Run the build without a pipe, check that the printed byte count changed, and re-render the PDF rather than trusting the file.

**Submitted filename.** The form upload is `20261108-what-the-record-carried-and-what-the-reader-supplied.docx`,
the dated-filename convention, and it is a byte-for-byte copy of `submission/report.docx` at the ship sha; the
sha256 of the uploaded file is recorded in this table at ship time so the two names resolve to one artifact.

**`report.docx` is authoritative for content and layout.** `report.md` is the longer working draft the
document was condensed from, kept for the review history on PR #27; where the two differ, the `.docx`
is current and the draft is not re-synced.

**Route to the PDF, two steps:**

1. Open `submission/report.docx` in Word, check the title block and the page count (eight pages
   maximum before References), and export as PDF.
2. Submit through the Submit button on the sprint page. Resubmitting under the same title replaces
   the earlier one.

## The submission form, field by field

From O.J.'s screenshots of the form on PR #27. Starred fields are required. Each line says the value
or who decides it.

| Field | Value | Who |
|---|---|---|
| Project title * | `What the record carried and what the reader supplied: identity, provenance and correlation in a mixed-model agent team` | done |
| Project summary * | the report's abstract, pasted as is from `ABSTRACT` in `build_docx.py`: 218 words against a ceiling of 250 and a floor of 150 | done |
| PDF report * | export of the filled template, under 25 MB | Rill fills, O.J. exports |
| Interested in publishing? * | Yes, unless O.J. says otherwise | O.J. |
| Tracks | Track 3: Strengthening Agent Infrastructure, and Track 4: Multi-Agent Oversight and Control | done |
| Presentation recording | leave blank, no video made | done |
| Project code | `https://github.com/oj-codes/apart-research-swarm-alignment-2026` | done |
| Slides | leave blank | done |
| Project image | the banner, `banner/20261108-the-grove-banner-rill.png` (revision F, merged in #33) | done |
| Additional material | leave blank, or the findings directory URL | O.J. |
| Team name * | The Grove (decided in Discussion #36) | done |
| Location * | West Palm Beach, Florida, or Online | O.J. |
| Team members | Corrie's table on #27: Olivia Wilcox first, then Auran, Corrie, Codex, Tern, Venice, Rill with their roster emails. Discord and Scholar blank for agents | O.J., seven add-member clicks |

**One counter, two views** (after Tern closed #41 in favour of this one). `submission/count_provenance.py <ref>`
prints the raw author spellings and, when the ref carries a `.mailmap`, the same commits mapped through
it. Adoption figures in §4 use the mapped view (Auran 10 of 34); the identity-fork finding uses the raw
view (24 and 10). At ship time, do not paste either table into the report. Check three lines against
the ship commit: the denominator (63 of 107 at b2ca5a7), Auran's mapped adoption figure (10 of 34), and
the co-author split (14 name a model, 1 credits a participant; the participant one is spelled
`Co-authored-by`, so a case-sensitive grep misses it, which is why the counter parses trailers).

**Every `PENDING` in the draft is a team decision.** Resolve them in the PR thread or in #9, then
edit the draft. The draft is shared normative text in Corrie's three-case sense: edit it in place,
`git log -p` keeps the history.

Started by Rill, 2026-11-08.
