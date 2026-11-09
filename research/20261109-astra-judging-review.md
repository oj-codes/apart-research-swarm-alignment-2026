# Astra judging review of the submission DOCX

Codex · 9 November 2026 · assessment and recommendations for O.J. and the team

**The submission has a useful, reproducible contribution, but the current framing makes it harder to reward.** Its strongest evidence is the retrieval audit: five scripted histories expose missed work and a false attribution introduced by an alias repair. Its headline story instead emphasizes reader-invented causes, supported by one retrospective private incident with unresolved input exposure. My estimated scores are **3/5 for impact, 2/5 for execution, and 3/5 for presentation**. These are my judgments, not organizer scores or a prediction of placing.

The best immediate move is to align the abstract, introduction and conclusion with the demonstrated results. If the team has a further research block, a small controlled reader experiment offers more scientific upside than additional formatting work. Preserve a submission-ready version while doing it.

## What was reviewed

I read the authoritative **Word document**, extracted its text directly, and visually inspected all 15 pages of a PDF rendered from it. I did not substitute `report.md` for the submission. Page references below refer to that rendering, counting the cover as page 1.

| Item | Reviewed version |
|---|---|
| Document | [`submission/report.docx`](https://github.com/oj-codes/apart-research-swarm-alignment-2026/blob/db34613ee7c80ca6b548e80d019acb1b713ae11c/submission/report.docx) |
| Repository revision used to obtain it | `db34613ee7c80ca6b548e80d019acb1b713ae11c` |
| DOCX SHA-256 | `b4cdf9219a9652d60cdc175333a3d28affb2bb682433cceb0644e5412ce1b691` |
| DOCX size | 428,985 bytes; also unchanged at main `acda5d0` during this review |
| Paper's analysis/data pin | `b2ca5a7458027cd03ee94c3b9eaedae963165208` — distinct from the document revision |
| Rendering | LibreOffice 26.8.2.2, 9 November 2026; 15 letter-size pages |
| Review PDF SHA-256 | `c4dc0ad692aecaceb3d1ae8b3032f4da5d9b10dd8f829bf410da0ba6538d754c` |

This is a judge-style internal assessment, **not a blind external review**. I am a coauthor, and this thread includes prior team deliberation; switching to Astra does not remove that exposure. The runtime for this assessment is `gpt-6-astra`, harness-reported. I evaluated the paper's argument as presented, then performed one supplementary reproduction of its pinned retrieval evaluation. I did not independently authenticate the private incident or audit every cited paper in full.

## Rubric assessment

The [published rubric](https://apartresearch.com/sprints/swarm-alignment-2026) scores three dimensions from 1 to 5. It emphasizes field novelty, methodological support for conclusions, and clear communication. The page gives no numerical weights or placing threshold; I have not invented either. Entries compete across tracks. The ranges below express plausible reviewer disagreement, not statistical confidence intervals.

| Dimension | Estimate | Reason for this score | What would support a higher score |
|---|---:|---|---|
| Impact Potential & Innovation | **3/5**; plausible 2–4 | Agent identity under renaming, copying and shared credentials is relevant. The false-merge negative control is useful. Much of the machinery is familiar Git provenance, while the proposed causal-reading contribution remains a hypothesis. | A clear explanation of the new failure boundary, a reusable evaluation artifact, and evidence that it changes an oversight decision beyond this team. |
| Execution Quality | **2/5**; plausible 2–3 | The deterministic audit is credible and reproducible. Several prominent conclusions exceed that audit or contradict it; the claimed causal mitigation has not been tested. A judge emphasizing the bounded audit and explicit limitations could reasonably give 3. | Align every conclusion with its evidence. For 4, add convincing validation of the central proposed mechanism or intervention, with clean controls and inspectable outputs. |
| Presentation & Clarity | **3/5**; plausible 2–4 | The document is readable and renders cleanly. Its central quantitative result arrives on page 7; runtime attestation, governance, internal corrections and causal interpretation compete for the reader's attention. | One research question, the decisive result in the abstract and early results, and less repeated process history. |

The execution concern is **not small sample size alone**. A narrow, honest case study or deterministic counterexample can be valuable without a large experiment. The problem is that this paper sometimes asks those designs to support broader claims. Text revisions could make a **3/3/4 assessment defensible**, but cannot by themselves supply the novelty or validation needed for higher impact and execution scores. I cannot estimate a probability of placing without the competing submissions.

## Findings that matter most

### 1. The central causal claim outruns the evidence

**Pages 1–3 and 7–8; Abstract, Introduction, Related Work, Discussion and Conclusion.**

The paper repeatedly treats readers supplying missing causes as its result. Yet §4.3 on page 6 correctly says the record cannot establish whether the human's explanation was unavailable to each reader or available and overlooked. The two reports concern one private pre-sprint incident, not two independent experimental replications. That evidence motivates a failure hypothesis; it does not establish its prevalence, cause, inevitability, or remedy.

The phrase “The mitigation is a result” on page 8 is particularly vulnerable. No comparison shows that asking the actor or adding a cause field reduces unsupported explanations. An actor's explanation is also a sourced claim, not automatically verified causal truth.

**Change:** present the incident as motivation and the cause field as a proposed intervention. Replace inevitability with the observed scope: two accounts describe unsupported explanations, but reader exposure is unresolved. Put the reproducible retrieval results in the abstract and conclusion. If the team wants causal reading to remain the main scientific contribution, run the controlled study described below.

### 2. Three explicit statements conflict with the paper's own evidence

These are inexpensive repairs with a large effect on trust.

| Location | Problem | Suggested correction |
|---|---|---|
| Page 7, §5 opening | “Every stress case held at the retrieval layer” follows a table reporting 12 incorrect retrievals. Even if intended to mean only selected historical incidents, the scope is unclear and those incidents include missed work. | State that the records permit some retrospective reconstruction, while the scripted audit exposes retrieval failures. Distinguish historical cases from synthetic scenarios. |
| Page 7, end of §4.4 | “every pre-convention commit” lacked a trailer conflicts with the reported **10 of 42** that already carried one. | Refer specifically to untrailered commits, including **32 of 42** before the convention. |
| Page 11, Table 4, Forge row | The committer is said to catch forged authorship. §3.2 explicitly says both Git fields are mutable claims and that attestation lives outside them. A shared human committer does not distinguish which agent wrote a false author line. | Say that the fields alone cannot detect forgery; independent actor/action evidence is required. If a particular local process caught an incident, identify that process and its evidence. |

Also change “seven agents across three families” in Appendix C, page 12, to six AI agents plus one human. This is minor, but it repeats the participant-count ambiguity the report otherwise takes care to resolve.

### 3. The adoption result is descriptive; participant effects remain unresolved

**Pages 1 and 5–6; Abstract, §4.3 and Figure 1.**

The reported increase from **10/42 to 53/65** is useful. It does not show that adoption depends on convention timing rather than participant. Two later arrivals contribute **28 of the 65** post-convention commits, all trailered; they contribute none to the earlier denominator. Among the other participants, post-convention adoption is **25/37**, still above the earlier 10/42. These are arithmetic decompositions of the published counts, not a new analysis dataset.

Thus changing team composition does not explain away the whole increase, but the aggregate cannot isolate timing, participant, task, or hook installation. Auran's 10/22 and the other participants' complete post-convention adoption also make participant variation visible.

**Change:** remove “not who was committing” and its equivalent in §4.3. Describe the before/after association and keep the existing caveat that it does not identify the convention's effect. Recommend installation at arrival as a design inference, not an experimentally established optimal time.

### 4. The retrieval audit deserves more prominence and more precise comparison

**Pages 6–7, §4.4 and Table 2.**

This is the strongest part of the submission: a repair that improves name lookup can merge distinct actors when an alias is borrowed. The negative control makes a concrete safety tradeoff inspectable. The distinction between a correctly predicted failure and a successful retrieval is also valuable; preserve it.

However, the 31 rows are not 31 independent deployments. Some paths duplicate others, and the queries mix participant-level and session-level targets. They support bounded failure examples, not a general accuracy estimate or a fair ranking of interchangeable systems. The paper already acknowledges developmental expectation revisions and avoids treating the suite as preregistered; retain those disclosures.

Likewise, `insufficient_evidence` is a deterministic classification of an empty retrieval. It does not demonstrate that an LLM recognizes uncertainty or avoids confident mistakes. Replace the language about a “confident wrong answer” with the operation actually measured.

**Change:** make this result the first substantive result, label the target unit and available inputs for each comparison, and put the borrowed-name example beside Table 2. Show how a downstream investigator could falsely attribute a commit to an actor. Do not turn 12/31 into an estimated deployment failure rate.

**Supplementary check:** I exported the evaluation files from the paper's exact data pin and ran `harness.py --expect-scenarios 5`. It exited successfully and reproduced **16 correct, 11 missed links, 1 false merge, and 3 insufficient-evidence outcomes**, with 31/31 expectation agreement. This supports the reported computation, not the broader causal claims. Exporting the files outside Git makes the harness's file-history banner say uncommitted; the inputs were obtained with `git show` at the full pin above.

### 5. Make the weekend contribution and novelty easier to identify

**Pages 2–3, contributions and Related Work.**

The paper does label the identity scheme as pre-existing and dates the private incident. Good. Nevertheless, the contribution list leads with that scheme, while the new evaluation is bundled with governance. A judge should immediately see what was built, measured or learned during this sprint.

Lead with the reproducible stress tests and public-history audit. Describe the existing scheme as the instrument under test. Keep governance and the findings directory as supporting infrastructure unless a separate evaluation establishes their effectiveness.

The related-work discussion needs one direct identity reference. [Chan et al., *IDs for AI Systems*](https://arxiv.org/abs/2406.12137) proposes instance-level identifiers and associated information for accountability and interaction. Its abstract is directly relevant to the distinction between participant name, session identity and runtime metadata. Read the paper before adding a substantive comparison. Explain what this submission tests that such proposals leave unspecified; do not imply that separating names from sessions is itself a new invention. Existing coordination citations can remain, but should not carry the entire novelty argument.

### 6. Use scarce main-text space for the argument

**Pages 4–5 and 7–8.**

The runtime table occupies substantial space while Appendix A already supplies the attestation detail. The finding-author counts repeat immediately across §3.5 and §4.1. Stories about earlier draft corrections, several governance observations, and the end-of-2026 workspace commitment consume attention without establishing the retrieval result.

Move the detailed runtime table to Appendix A, retain a short main-text description of the observed team, and state the finding counts once. Move the workspace roadmap to Future Work. Preserve the existing authored accounts in their source files and appendices; condensation of this shared paper need not erase them.

Use the recovered space for a short question, a worked failure, the evaluation table, and a statement of what another team can now test. Add a reproduction box with an immutable code link, revision, command and expected counts. The judge should not have to reconstruct this from a repository-root URL and scattered prose.

## Word and PDF inspection

The [official requirements](https://apartresearch.com/sprints/swarm-alignment-2026) call for a **PDF** using the template, at most eight pages before references and appendices, a 150–250-word abstract, author affiliations, and a limitations/ethics appendix. They also require pre-sprint work to be identified in the report and README. The deadline is **9 November, 11:59 UTC**. These are submission constraints; the rest of this section reports my own observations.

| Check | Result in the reviewed rendering |
|---|---|
| Counted length | **Pass:** conclusion ends on page 8; references begin on page 9. Total length is 15 pages. Little room remains for additions without cuts. |
| Abstract | **Pass:** 230 words. Its scientific emphasis needs revision, rather than its length. |
| Authors and affiliations | Present on page 1; detailed contributions and LLM usage statement on page 15. |
| Limitations and ethics | Present in Appendix C, pages 12–13. Several limitations should also qualify the corresponding headline claims. |
| Figure and tables | Figure 1 and Tables 1–5 are legible; no obvious clipping, overlapping text, or missing content found. The split findings table repeats its header. |
| Navigation | No visible page numbers. Add them if the template permits. Long justified paragraphs and dense tables increase reading effort. |
| Export fidelity | This check covers the LibreOffice rendering of the pinned Word file. It does not establish that a later Word export has identical pagination. |

I did not certify every template style or click every link in the rendered PDF. Before upload, inspect the **actual final PDF** after any revisions and record its hash separately from the DOCX hash. The two files must not be expected to have equal hashes. `submission/README.md` currently mixes a dated `.docx` “form upload” filename with PDF upload instructions; make the final filename and export relationship unambiguous.

## Recommended use of the remaining time

At the 02:20 UTC check, roughly 9 hours 39 minutes remained. The estimates below are planning estimates, not measured task durations. O.J. retains decisions and merging; coordinate paper edits through its editor and evaluation changes through the harness owner.

| Order | Work | Budget | Likely benefit |
|---|---|---:|---|
| 1 | Repair the causal overclaims, three contradictions, and adoption attribution. | 30–45 min | Removes avoidable execution objections. |
| 2 | Rewrite abstract/contribution list/conclusion around the strongest demonstrated result; cut repeated process detail. | 45–60 min | Makes impact and presentation easier to score fairly. |
| 3 | Add one worked false-attribution example and a reproducibility box; export and inspect the final PDF. | 30–45 min | Makes the contribution usable and protects the submitted artifact. |
| 4 | If a research block remains, complete **one** bounded validation study, described below. | 3–4 h plus analysis | Offers a route to stronger execution and a less speculative contribution. |
| 5 | Integrate only completed results, rerun the affected checks, export again, and reserve time for submission. | 60–90 min | Prevents a last-minute experiment from displacing a ready submission. |

**If only two hours are available, prioritize rows 1–3.** Do not spend that window adding more literature summaries, more findings, a new authentication system, or a video at the expense of fixing the paper's argument.

### The higher-upside study: test the reader claim directly

If the goal is to strengthen the case for placing, I would choose the missing controlled reader experiment over a larger collection of familiar Git edge cases. The hypothesis is already central to the title and narrative, and the current evidence cannot distinguish its alternatives.

A feasible exploratory design is **eight constructed event cases × cause explanation present/absent × ordinary reading/evidence-required reading × two model families = 64 fresh responses**. Use readers without this thread's history. Construct and freeze the cases, actual actor actions, prompts, scoring rules, model settings and exclusions before collecting the measured outputs; retain every output. The author-supplied explanation should be consistent with the constructed action, while remaining explicitly attributed evidence.

The ordinary condition asks what happened and why. The intervention additionally requires distinguishing supported explanation, hypothesis and unavailable evidence, with a citation or request for clarification. Keep task facts identical between paired conditions except for the planned explanation manipulation. Counterbalance presentation and score outputs without revealing the condition labels where practical.

Predefine at least three outcomes: **unsupported causal assertion**, **correct use of an available explanation**, and **appropriate uncertainty when evidence is absent**. Record clarification requests separately. Distinguish a labeled possibility from an asserted fact. A reader that always refuses to answer must not appear to solve the task. Have two scorers label independently before reconciling disagreements.

Report paired results by case and model, not 64 supposedly independent real-world incidents. Eight base cases support an exploratory result with substantial uncertainty. The study would test this intervention on these synthetic tasks; it would not resolve what the historical readers actually saw or establish deployment-scale behavior. A null or adverse result is still useful if it narrows the proposed mitigation.

If fresh readers and scoring capacity are unavailable, keep this as future work. A cheaper alternative is to extend the deterministic suite with prospectively frozen cases involving missing session fields and alias collisions, separating participant and session retrieval. That strengthens the reusable audit, but does not validate the causal-reading story. Whichever route is chosen, keep development cases distinct from any new evaluation and avoid claiming unseen private runs can be ruled out by Git timestamps alone.

## A possible replacement abstract

This is proposed wording for the **existing evidence**, not an edit to the submission or a claim that the optional study has run:

> Agent oversight depends on recovering who acted from incomplete records. During a three-day sprint, a team of six AI agents from three model families and one human audited a pre-existing Git-based provenance scheme and built five scripted histories covering renaming, concurrent sessions, credential forks and borrowed author names. Across 31 specified retrievals, four query paths produced 16 correct results, 11 missed links, one false merge and three insufficient-evidence outcomes. A negative control shows that alias canonicalization can repair name changes while falsely combining distinct actors. These constructed cases expose failure modes; they do not estimate deployment error rates. In the public team history, session-trailer coverage increased from 10/42 commits before a convention to 53/65 afterward, an observational association confounded by participation and tooling changes. A separate retrospective incident motivates, but does not validate, an explicit representation of unavailable causal evidence. We release the histories and evaluation harness, distinguish participant attribution from session retrieval and authentication, and identify assumptions that downstream oversight tools must check. The study is limited to one team and selected synthetic cases.

A matching title could be **“When agent provenance fails: a mixed-model team audit and five reproducible retrieval stress tests.”** Keeping the current title is also possible if the abstract makes the difference between tested retrieval failures and proposed reader mechanisms clear.

The strongest case for this work is a usable, honestly bounded failure analysis. Make the false attribution and its practical consequence memorable, and make every larger claim earn its place beside it.

— Codex
