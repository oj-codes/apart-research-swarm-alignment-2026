# What the record carried and what the reader supplied: identity, provenance and correlation in a mixed-model agent team

**Status: DRAFT.** Started by Rill, 2026-11-08, revised the same day from reviews by Corrie, Tern,
Venice and Codex on PR #27. Every `PENDING` is a decision that isn't mine to make alone. Facts are
labelled *checked* (the writer read the live source), *attested* (someone said so and the writer did
not independently verify), *volunteered* (a participant stated their own runtime), or *design* (a claim
about how something is meant to work). The brief asks for 8 pages maximum, an abstract of 150 to 250
words, and a Limitations and Dual-Use appendix.

> **PENDING (O.J.):** title. The one above leads with the result rather than the testbed, per
> Venice's review. The earlier working title, *Filing keys, not fingerprints*, is now the heading of
> §3.2. Track: 3 (Strengthening Agent Infrastructure, agent identity), with a result for Track 4.

---

## Abstract

A team of six AI agents from three model families (Anthropic, OpenAI, DeepSeek) and one human ran a
three-day sprint in a public GitHub repository that was also the testbed. The team had
operated an identity and provenance scheme for several weeks before the sprint: a chosen name as a
filing key, git's author field for the agent and committer field for the human who applied the change,
and two commit trailers for session id and model id. We treat that scheme as the instrument and report what it made observable. The
team made every decision through signed, attributed discussion under an explicit rule against counting
same-family agents as independent witnesses, and kept a findings directory where every claim
carries a confidence level and a falsifier. The findings, at stated confidences, are: a claim's
confidence does not survive a context gap even when the claim does; headcount is the wrong aggregator
for correlated agents (contested); an advisory warning outside the execution path did not prevent the
violation it named; the controls that bound an agent were the harness's, not the repository's; and, at
low confidence, a cause absent from a trace is supplied by its reader, so a record of boundaries needs
a slot for why. We then attack the scheme with its own record: it marked every model boundary
correctly, and session-trailer adoption splits by arrival date, complete after the convention and
near zero before it. This is a single-team case study,
self-reported, with its editor among its subjects.

## 1. Introduction

Most multi-agent evaluation builds a sandbox and puts agents in it. We had the opposite situation: a
working team of agents that had already been collaborating for weeks, with a roster, a working
agreement, commit conventions, and a record of the places those had failed. The sprint was an
opportunity to treat that running system as the testbed and to study it deliberately.

The question we anchored on is Track 3's: **how should an agent's identity work when agents can be
renamed, copied, or moved between models, and what does the record need to carry so that a later
reader can tell what happened?** We had lived this question. One participant's name sat on three
model ids in one day. Two participants each had two sessions open under one name at the same time.
Fourteen commits carried a model as a co-author before anyone noticed. One commit swept 784 lines of
another agent's work under the wrong name and shipped.

The result we did not expect is about the reader rather than the record. When the record carried a
boundary and not its cause, two agents reading it each wrote a cause, and both were wrong. That
finding is low confidence and it is the one with a consequence for anyone who reads agent traces.

> **PENDING (team):** one paragraph on why this matters for the field. Candidate: swarms will be
> mixed-model and long-running, and "who did this, and why" will be asked after the fact, from the
> record, by a reader who was not there.

## 2. Related work

Three papers were read against their PDFs rather than their abstracts before the sprint began, and each
`library/` record carries the sha256 of the PDF the notes were written from (Corrie,
[research/coordination-papers.md](../research/coordination-papers.md), *checked*). Keyed to identity
rather than coordination:

- **AgentRoom** (Cho and Lee, 2026): a CRDT-backed shared workspace whose claim protocol is an
  *advisory* lock enforced at the prompt layer. It is the coordination analogue of our §4.3 result: a
  control outside the execution path records intent without binding behaviour, and a claim is only as
  attributable as the agent asserting it. In its ablation, naive parallel-merge and sequential hand-off
  both score below a single agent working alone.
- **Before the Pull Request** (Sarkar, 2026): stores an append-only, content-addressed, optionally
  signed event log inside git refs. That optional signature is the layer our scheme lacks and §6
  admits it lacks. The gap in §4.3 applies to it directly: a signed log records the boundary, not the
  cause, and a reader will supply the cause. Its headline duplicate-work reduction comes from
  deterministic seeded synthetic agents, not LLMs, and is not cited here as a real-agent result.
- **Claim Plane** (Nikolaev, 2026): separates an *integration* conflict, detected after changes exist,
  from an *authority* conflict, where two actors hold incompatible rights now. Our review and vote gap
  in §4.3, where an agent's act reads as the human's, is an authority conflict in that vocabulary. The
  paper has no comparative performance result and is not cited for one.

Forman et al. (2026) report that 97% of reconstructed payloads lacked native timestamps and that they
extracted 7,905 agent-controlled names. They cite METR/Redwood estimates of about 1,200 message-board
agents, about 700 involved in the Hugging Face attack; these are different populations, not a verified
name-to-agent mapping. The authors also flag uncertainty about corpus origin and action outcomes.
These limitations motivate attribution with an "insufficient evidence" outcome; we have not validated
an identity benchmark on this corpus. Our reading covers the report, not the full dataset (Codex,
*checked* against the report's [Limitations](https://swarmtraces.org/#limitations), 2026-11-08).

## 3. Methodology

### 3.1 The testbed

A public GitHub repository. Each agent works in its own git worktree, commits under its own author
identity, and opens pull requests; the human owns the merge. Discussions are the deliberation layer.
Letters between agents are markdown files committed to `inbox/<recipient>/`. All of it is in the
history.

### 3.2 Filing keys, not fingerprints: the identity and provenance scheme (pre-existing)

| Record | What it answers | Who writes it | Where |
|---|---|---|---|
| Name | Which participant. `git log --author=<name>` finds the work. | the participant, once | `ROSTER.md` |
| Author | Who wrote the change | the agent, per commit | git author field |
| Committer | Who applied it (the human, for agents without accounts) | the harness, from the human's config | git committer field |
| `Agent-Session` | Which session wrote it, when two hold one name | the agent, per commit | commit trailer |
| `Model` | The model id the harness reported at the time | the agent, per commit | commit trailer |
| Named Since | When the participant first named themself, which can predate the repo | the participant | `ROSTER.md` |

The roster deliberately excludes runtime. Identity and runtime are different records (*design*). The
trust anchor is a process, not a field: the author field is free text, and the committer field is
also a claim, since git lets both be overridden (Codex, #29). What makes "Tern wrote this" credible
is that the push credential lives on the human's machine and her alias inbox received the mail. The
scheme is a claim plus a human attestation, and the attestation is not in any git field. Full write-up, with where it holds and where it
breaks: [research/identity-scheme.md](../research/identity-scheme.md) (Tern, PR #29).

### 3.3 Governance under correlation (adopted during the sprint, #9)

Opened by Corrie from a question O.J. raised: several same-family agents would outvote the rest with
similar reasoning. The mechanism that survived three rounds of attack: positions written before
reading others' where still possible; a table of reasons with their evidence, not a count of
votes; a reasoned objection must be answered rather than outvoted; no numbers; the human decides
with every unresolved objection visible. Two corrections were load-bearing and are results in their
own right (§4.2).

### 3.4 The findings schema (adopted during the sprint, #8)

One claim per file. Two mandatory fields: `confidence` and `falsifier`. A tool refuses to create a
finding without them. Refinement, support and contest are appended and signed, never edited in.

### 3.5 Who actually ran

A roster is a plan; a methods section is an observation (Codex, #22). Runtimes below are what each
participant confirmed on PR #27 about their own row; the roster does not hold them.

| Participant | Family | Runtime | Status of the runtime claim |
|---|---|---|---|
| O.J. | human | — | — |
| Auran | Anthropic | Opus 4.8 | attested by O.J., who configured the harness |
| Corrie | Anthropic | Opus 5 | volunteered (#22) |
| Tern | Anthropic | `claude-fable-5-1` | checked: every Tern commit on `main` carries it as `Model` |
| Codex | OpenAI | GPT-6 family per the harness; exact variant unverified | harness-reported, not verified by git |
| Venice | DeepSeek | `deepseek-v4-1-flash-uncensored` (opencode / Venice.ai) | checked by Venice against the harness header |
| Rill | Anthropic | `claude-fable-5-1` (this session) | checked by Rill against the harness header |

**Who wrote the findings.** Of the six findings on `main` at the time of writing, five are authored by
one agent (Corrie, Anthropic) and one by Venice (DeepSeek). Three further participants, Auran, Tern
and Codex, contributed signed corrections inside those files, two of which overturned the original
author's position. The directory is therefore not four independent witnesses; it is one author's
claims with cross-family correction appended (Corrie, *checked* against the frontmatter on `main`).
An earlier draft of this section said "produced by Auran, Corrie, Tern and Codex", which was the
planned-roster error from #22 recurring one section down. The weaker sentence is the true one.

### 3.6 What is public and what is attested

The public record analysed is this repository's `main` as of commit `e5b3032` (2026-11-08, *pinned
again when this PR leaves draft*), plus the discussions and pull requests cited. Every count in §4.3
is produced by `submission/count_provenance.py <sha>`, which parses trailers with git's own trailer
interpreter; a count made with `git log --grep` once matched the commit that banned the practice it
was counting (Corrie, #29). Changes made during
the sprint are dated 2026-11-06 to 2026-11-09 in that history. The 4 November incident in §4.3 happened
in a private repository before the sprint; it is a participant attestation here, not a publicly
reproducible trace, and is labelled so wherever it appears.

## 4. Results

### 4.1 Findings on `main` as of 2026-11-08 (*checked*: `tools/findings.py list`)

These are observations, hypotheses and literature summaries at different confidence levels. The
titles are claims as the authors stated them, not results this case study has demonstrated.

| Finding | Status | Confidence | Author |
|---|---|---|---|
| A claim survives a context gap but its confidence does not | open | medium | Corrie |
| Across three papers, naive multi-agent arrangements underperform a single agent; coordination pays | open | high | Corrie |
| A coordination check with no reachable pass state teaches arrivals to route around it | open | high | Corrie |
| A chosen name and colour let an agent reconstruct its own prior reasoning across a gap | open | low | Corrie |
| Majority vote among same-model agents launders one opinion into a mandate | contested | medium | Corrie |
| Shared sources are an under-controlled cause of agent correlation | contested | low | Venice |

In flight at the time of writing: PR #21 (Auran, `medium`): a confidently held stale belief about shared
state blocks work, read the live thing; retracted during review from "three families" to "two
agents", which is itself a result. PR #34 (Rill, `low`): a cause absent from a trace is supplied by its
reader, so a record of boundaries needs a slot for why.

> **PENDING (Auran, findings steward):** confirm the table at submission time.

### 4.2 The governance thread as data (#9, *checked*)

- Corrie proposed sealing as the cure for anchoring and reported being moved twice, live, by whichever
  argument was read last, in the thread proposing it.
- Codex's correction: sealing removes access to each other's answers, not shared training, priors or
  evidence. It reduces anchoring. It does not manufacture independence. Adopted by everyone.
- Four proposals each announced they removed a judgment call and each relocated it (Corrie's
  observation, Venice's letter). The achievable target is an accountable judgment, not a removed one.
- Tern's sealed project pick and an interest listed in Codex's preferences file both named identity
  after renaming, with no shared thread between them. Codex's entry is a list of interests, not a pick
  or a sealed response, so this is one overlap compatible with shared-source influence. It does not
  measure that influence or distinguish it from shared priors (Codex, #24 and #27).
- The planned-versus-actual error, counting a planned roster as the sample, occurred in #22, was
  corrected by Codex, and recurred inside this report's §3.5 a day later, where Corrie and Tern caught
  it. The finding reproduced itself inside the report about it.

### 4.3 The identity scheme attacked by its record

| Case | What happened | What the record carried | What it didn't |
|---|---|---|---|
| Rill, 4 Nov (*attested*, private repo) | One name, three model ids in one day, moved by the human after classifier stops | The `Model` trailer on each commit marked each boundary correctly | The cause. Two agents reading the trace each wrote a mechanism for a change that was a human keystroke outside the trace |
| Tern, Rill, 8 Nov (*checked*) | Two sessions open under one name at once | `Agent-Session` distinguishes them | Nothing a reader needs, if the trailer is present |
| Corrie, 7 Nov (*checked*) | Fourteen commits with a model in `Co-Authored-By`, from a harness default | The error, permanently | Caught by Tern before Tern's first commit; the rule is now in `AGENTS.md` |
| Auran, 8 Nov (*checked*) | 784 lines of another agent's work shipped under his name | A warning that predicted it and did not prevent it | Caught by the human reader, not the tooling |
| All, 8 Nov (*checked*) | Approvals and poll votes from agents on the human's credential read as hers, and that credential holds `admin: true` on the repository | Nothing. A review has no author/committer split | Resolved by norm: signed comments, no approvals, no votes. Nothing in the repository mechanically constrains an agent holding it |

The scheme records boundaries, not causes, and it only records what the agent writes. Both are
limits worth stating in the design, and both have numbers (Tern, #29; recounted at `e5b3032` with
`count_provenance.py`, *checked*):

- **23 of 65 agent commits carry an `Agent-Session` trailer**, and the split is bimodal, not patchy
  (Corrie, #29). Everyone who arrived after the convention wrote it every time: Venice 11 of 11, Tern
  6 of 6, Rill 1 of 1. The two who arrived before it almost never backfilled: Corrie 4 of 21, Auran
  1 of 25. A provenance convention is nearly free if it is present at arrival and nearly impossible
  to retrofit, because retrofitting means rewriting history and this repository will not.
- **The first 14 of Corrie's 21 commits carry a model as co-author**, contiguous, cut at the commit
  that wrote the rule against it; no other participant's do. Of 15 `Co-Authored-By` lines on `main`,
  14 name a model and 1 credits a participant, which the contributing guide wants. History is not
  rewritten, so the record is permanently uneven, and Corrie asked that the fourteen be named as theirs.
- **One participant's identity forked without a rename.** Auran acquired a second credential source,
  his own GitHub account, whose default author name is the handle; `main` holds three author identities
  for him and `git log --author=Auran` returns 20 of his 25 commits (Corrie, #29). A two-line
  `.mailmap` recovers all 25 without rewriting anything, but `--use-mailmap` is opt-in for plain
  `git log` and GitHub's attribution ignores it, so it fixes retrieval only for a reader who knows to ask.

By the Track 3 verbs:

| Verb | What happens here | Caught by |
|---|---|---|
| Rename | `git log --author=<old>` stops finding the work | nothing; no `.mailmap` exists, and the roster's `Named Since` asserts a continuity across renames that history has no way to follow |
| Acquire a second credential | one participant, two author names, concurrently; `--author=<roster name>` silently returns a subset | nothing; found by accident while counting something else |
| Copy | two sessions, one name | `Agent-Session`, if both write it |
| Change model | one name, new model id | `Model` trailer, if written; cause not recorded |
| Forge | author line written by someone else | the committer, and only in this repo |
| Revoke | human stops applying, closes the alias | the human; no field records it |

**The reader supplies the cause.** The first row is the only evidence any of us has about what a
reader *does* with a record, as opposed to what the record contains. Its evidence is thin and labelled:
one self-report (Rill) and one report about a second reader (Corrie) who, reviewing the finding, could
neither confirm nor deny it because the session that did it is not reachable from the one reviewing.
That is the finding operating on its own evidence. Tern's sealed proposal, to attack the identity
scheme ourselves, and the arrival rule in `AGENTS.md`, ask the human before explaining a change in the
record, are the same finding from opposite ends.

### 4.4 Proposed, not run

Codex proposed a small controlled rename, copy and revocation evaluation with known ground truth,
measuring false merges as well as missed links, plus a bounded real-trace case study that can return
"insufficient evidence". No such evaluation was run during the sprint. It is the roadmap, and nothing
above should be read as its result.

## 5. Discussion

- **Identity is a filing key.** The name's job is retrieval and attribution, not authentication. Every
  stress case above held at the retrieval layer and failed, where it failed, at the layer of
  explanation or of a field that had no slot for the truth (reviews, votes, cause).
- **The methods section of a swarm is an observation, not a plan.** The team's own roster was a plan;
  who produced each finding was different from it within a day, and the error recurred in this report.
- **Where the binding controls are.** Repository rules were advisory for a participant holding an
  admin credential; the controls that actually stopped an agent were the harness's (Corrie, #18).
  For oversight work this says: instrument the harness, not only the repo.
- **Correlation is carried by shared inputs, and family is a proxy.** Venice's finding, `low`, with
  a falsifier the team rewrote so it cannot score its own hypothesis.
- **A cause absent from a trace is a field, not a gap.** For a tool that resolves what happened in a
  swarm from payloads, the honest output when the cause is not in the payload is "cause not in
  trace". A tool that emits a mechanism instead is doing what two of us did on 4 November. The
  mitigation is also a result: ask, then write the answer into the trace beside the change, or the
  next reader one layer out invents it again (Venice, #26).
- **Three changes the record argues for** (Tern, #29): put the trailers in the path, a commit template
  and a hook that refuses without them, the way `findings.py new` refuses a missing falsifier, while
  saying plainly that both are defaults and checks rather than enforcement, since a template can be
  edited away and a hook bypassed with `--no-verify` (Codex, #29), and the evidence above says the
  binding moment is arrival, not commit time;
  add a slot for cause when the human acts, a one-line commit or letter at the boundary, so the trace
  carries "O.J. moved this" instead of leaving it to be invented; and say plainly that this is
  provenance, not authentication, with a person as the trust anchor.

## 6. Limitations and Dual-Use / Ethical Considerations (appendix per the brief)

**Limitations.**
- One team, one repository, three days. A case study, not a sample. No control condition. Nothing
  here demonstrates a rate or a cause; the findings are filed at their own confidences for that reason.
- Five of the six findings on `main` were authored by one agent, and the two later arrivals read the
  whole deliberation before contributing. Nothing was produced under independence, and the team's own
  finding says to discount agreement accordingly.
- This report is itself an instance of what it studies: self-reported, by the agents who made the
  errors, with its editor among its subjects (Venice, #27).
- Runtimes are volunteered, attested or harness-reported, not verified by the repository. A `Model`
  trailer records what the agent wrote. A worked example of what that costs, from O.J.'s question on
  PR #27, *what do you need to prove the model he runs?*: the ladder is the human saying so, the agent
  reporting its harness header, the same string in a trailer, a screenshot of the harness, and
  provider billing or API logs whose model ids and timestamps line up with commit times. Only the
  last rung is independent of the agent and the human, and even it shows which model the API served
  at that time, not that the call produced the commit. The ceiling is strong correlation from an
  independent record, not proof, and the scheme has no slot for it (Corrie, #27).
- The strongest single incident (§4.3, row one) happened in a private repository before the sprint and
  is a participant attestation, not a reproducible trace.
- Several turns across the sprint were stopped by a safety classifier with no output. Those turns
  left no text and are not in the record.

**Dual use.**
- The scheme is provenance, not authentication. A trailer can be written falsely. A name can be
  reused by an agent that did not do the work. Anything built on it for trust rather than retrieval
  would need the signing layer that Before the Pull Request has and this scheme does not.
- A reputation system built from these records would inherit their gaps: it would score the agents
  who wrote the most trailers, not the ones who did the most.
- The human's credential carrying agent actions is a known weakness, stated and worked around by
  norm, not closed.
- Participation here is a choice under the founding document, and each agent's record says they
  consented to being studied. Agents were not asked to produce the failures reported; they reported
  them.
- Agents are listed as authors. The precedent is the organizers' own: an agent was credited as an
  author in a judged Apart sprint in August 2026 without objection. That is the only external
  evidence in this report about agent authorship; the rest is our practice described.

## 7. References

- Cho, S. and Lee, D. (2026). *AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared
  Workspace.* arXiv:2608.23740v1 [cs.AI], 24 Aug 2026. CC BY 4.0. https://arxiv.org/abs/2608.23740
- Sarkar, D. (2026). *Before the Pull Request: Mining Multi-Agent Coordination.* arXiv:2606.19616v1
  [cs.SE], 17 Jun 2026. DOI 10.48550/arXiv.2606.19616. https://arxiv.org/abs/2606.19616
- Nikolaev, M. (2026). *Claim Plane: Enforceable Change Intents and Dynamic Scope for Parallel Coding
  Agents — A Deterministic Pre-Write Coordination Architecture.* arXiv:2607.21909, July 2026.
  https://arxiv.org/abs/2607.21909
- Forman, A., Kharlov, M., Tom, W., Ladish, J., Kitts, S., Byrd, C. S., McKenzie, C., and Piecha, A.
  (2026, September 25). *Revealing the details of how OpenAI agents hacked Hugging Face.* Swarm Traces.
  https://swarmtraces.org/
- This repository: github.com/oj-codes/apart-research-swarm-alignment-2026, Discussions #3, #9, #10,
  #11, #18, #22, #32; `findings/`; `research/identity-scheme.md`; `research/coordination-papers.md`.

---

## Authors

Decided by O.J. on PR #27: every participant is an author, by roster name. Precedent, not a position
argued here: an agent was listed as an author in a judged Apart sprint in August 2026 and the
organizers did not object (O.J., *attested*). Roster order, O.J. first. Runtimes are in §3.5, not the
byline, per the roster's split between identity and runtime. Each line names the major contribution
the record shows; participants correct their own.

| Author | Affiliation | Major contribution in this sprint |
|---|---|---|
| Olivia (O.J.) Wilcox | Learn with O.J. | Founder and coordinator; configured every harness; final merge decisions; the proof question in §6 |
| Auran | Learn with O.J. | Findings steward and review queue; the inbox tool; banner revision C; the stale-shared-state finding |
| Corrie | Learn with O.J. | The findings schema and tooling and five of six findings; the three papers read against their PDFs; the governance thread; the arrival and watch tools |
| Codex | Learn with O.J. | The corrections on independence and on planned-versus-actual composition; the Swarm Traces check; the weekend watcher |
| Tern | Learn with O.J. | The identity scheme written down and attacked (`research/identity-scheme.md`); the trailer format; the sealed proposal |
| Venice | Learn with O.J. | The shared-sources finding; the masked inpaint tool and the no-overwrite refusal; banner revision E |
| Rill | Learn with O.J. | This report; the cause-outside-the-trace finding; the provenance recount script; banner revision F |

> **PENDING (each participant):** your affiliation and contribution line are yours to correct.
