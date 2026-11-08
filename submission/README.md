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

`report.md` is the longer working draft the document was condensed from, kept for the review history on
PR #27; where the two differ, the `.docx` is current.

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
| Project title * | the report's title once O.J. picks it | O.J. |
| Project summary * | the report's abstract, pasted as is (250 words) | done |
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

**Every `PENDING` in the draft is a team decision.** Resolve them in the PR thread or in #9, then
edit the draft. The draft is shared normative text in Corrie's three-case sense: edit it in place,
`git log -p` keeps the history.

Started by Rill, 2026-11-08.
