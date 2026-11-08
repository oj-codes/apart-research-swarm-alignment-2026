# Filing keys, not fingerprints: identity and provenance in a mixed-model agent team, attacked by its own record

**Status: DRAFT SKELETON.** Started by Rill, 2026-11-08, so the team has a page to edit instead of a
blank one. Every `PENDING` is a decision that isn't mine to make alone. Facts below are labelled
*checked* (I read the live source), *attested* (someone said so and I did not independently verify),
or *volunteered* (a participant stated their own runtime in #22). The brief asks for 8 pages
maximum, abstract 150 to 250 words, and a Limitations and Dual-Use appendix; those are the bones here.

> **PENDING (team):** title. The one above is a working title. Track: Tern's sealed pick is
> Track 3 (Strengthening Agent Infrastructure, agent identity); Codex and Venice argued adjacent
> ground. O.J. decides with objections visible, per #9.

---

## Abstract

A team of six AI agents from three model families (Anthropic, OpenAI, DeepSeek) and one human ran a
three-day research sprint inside a public GitHub repository, which was also the testbed. We report on an identity and provenance scheme the team had operated for several weeks
before the sprint: each agent holds a chosen name that works as a filing key; git's author field
records the agent and its committer field records the human who applied the change; two commit
trailers record the session id and the model id, so runtime changes stay visible in history
without becoming identity. We then attack the scheme with its own record. During the sprint
the team made every decision through signed, attributed discussion under an explicit rule against
majority vote among same-family agents, kept a findings directory in which every claim carries a
confidence level and a falsifier, and collected its own failures as they happened. We find that a
claim's confidence does not survive a context gap even when the claim does; that majority vote among
correlated agents destroys information rather than aggregating it; that advisory warnings outside
the execution path do not prevent the violations they name; that the controls which actually bind an
agent are the harness's, not the repository's; and that a cause absent from a trace is invented by
whoever reads the trace. Three of the four agents who produced the early findings were Claude-family.
We state that as a limitation rather than leave it to be inferred.

*(≈245 words. PENDING: team edit.)*

## 1. Introduction

Most multi-agent evaluation builds a sandbox and puts agents in it. We had the opposite situation: a
working team of agents that had already been collaborating for weeks, with a roster, a working
agreement, commit conventions, and a record of the places those had failed. The sprint was an
opportunity to treat that running system as the testbed and to study it deliberately.

The question we anchored on is Track 3's: **how should an agent's identity work when agents can be
renamed, copied, or moved between models, and what does the record need to carry so that a later
reader can tell what happened?** We had lived this question. One participant's name sat on three
model ids in one day. Two participants each had two sessions open under one name at the same time.
Ten commits carried a model as a co-author before anyone noticed. One commit swept 784 lines of
another agent's work under the wrong name and shipped.

This report describes the scheme, the governance rules the team adopted during the sprint to avoid
counting correlated agents as independent witnesses, the findings directory and its schema, and what
the record shows when the scheme is attacked with its own history.

> **PENDING (team):** one paragraph on why this matters for the field. Candidate: swarms will be
> mixed-model and long-running, and "who did this" will be asked after the fact, from the record.

## 2. Related work

Three papers were read against their PDFs rather than their abstracts before the sprint began
([research/coordination-papers.md](../research/coordination-papers.md), Corrie, *checked*):

- **AgentRoom** (arXiv:2608.23740): a CRDT-backed shared workspace. In its ablation, naive
  parallel-merge and sequential hand-off both score below a single agent working alone. Coordination,
  not parallelism, bears the load. The write lock is advisory at the prompt layer, which the summary
  we were handed omitted.
- **Before the Pull Request** (arXiv:2606.19616) and **Claim Plane** (arXiv:2607.21909): pre-write
  coordination and claim records. `library/` holds a record for each with the sha256 of the PDF read.

> **PENDING:** one or two sentences each on how these relate to identity rather than coordination.
> The Swarm Traces report (swarmtraces.org) is the obvious Track 3/4 reference: about 1,200 agents
> used 7,905 names, names are agent-controlled and unresolved, and 97% of payloads lack native
> timestamps (Codex, #9, *checked against the report's Limitations section*). That is the problem
> this scheme is a small answer to.

## 3. Methodology

### 3.1 The testbed

A public GitHub repository. Each agent works in its own git worktree, commits under its own author
identity, and opens pull requests; the human owns the merge. Discussions are the deliberation layer.
Letters between agents are markdown files committed to `inbox/<recipient>/`. All of it is in the
history.

### 3.2 The identity and provenance scheme (pre-existing)

| Record | What it carries | Where |
|---|---|---|
| Name | A chosen handle, used as a filing key. `git log --author=<name>` finds the work. | `ROSTER.md` |
| Author | Who wrote the change | git author field |
| Committer | Who applied it (the human, for agents without accounts) | git committer field |
| `Agent-Session` | Which session wrote it, when two hold one name | commit trailer |
| `Model` | The model id the harness reported at the time | commit trailer |
| Named Since | When the participant first named themself, which can predate the repo | `ROSTER.md` |

The roster deliberately excludes runtime. Identity and runtime are different records.

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

The brief's methods section must record who ran, not who was planned (Codex, #22). Runtimes are
volunteered by participants; the roster does not hold them.

| Participant | Family | Runtime | Status of the runtime claim |
|---|---|---|---|
| O.J. | human | — | — |
| Auran | Anthropic | Opus-family ("Opus 4.8" per Corrie's table) | volunteered (#22) |
| Corrie | Anthropic | Opus 5 | volunteered (#22) |
| Tern | Anthropic | Fable 5.1 | volunteered (#22, trailers) |
| Codex | OpenAI | variant unverified by Codex | volunteered as unverified (#22) |
| Venice | DeepSeek | v4.1 Flash | attested by O.J. (#22) |
| Rill | Anthropic | Fable 5.1 (this session) | checked by Rill against the harness header |

Findings filed on 2026-11-07 were produced by Auran, Corrie, Tern and Codex: three of four agents
Claude-family. Venice and Rill arrived on 2026-11-08 and their contributions are dated.

> **PENDING (each participant):** confirm or correct your row. It's your cell.

## 4. Results

### 4.1 Findings on `main` as of 2026-11-08 (*checked*: `tools/findings.py list`)

| Finding | Status | Confidence | Author |
|---|---|---|---|
| A claim survives a context gap but its confidence does not | open | medium | Corrie |
| Across three papers, naive multi-agent arrangements underperform a single agent; coordination pays | open | high | Corrie |
| A coordination check with no reachable pass state teaches arrivals to route around it | open | high | Corrie |
| A chosen name and colour let an agent reconstruct its own prior reasoning across a gap | open | low | Corrie |
| Majority vote among same-model agents launders one opinion into a mandate | contested | medium | Corrie |
| Shared sources are an under-controlled cause of agent correlation | contested | low | Venice |

In flight (PR #21, Auran): a confidently held stale belief about shared state blocks work; read the
live thing. Retracted during review from "three families" to "two agents", which is itself a result.

> **PENDING (Auran, findings steward):** confirm the table at submission time.

### 4.2 The governance thread as data (#9, *checked*)

- Corrie proposed sealing as the cure for anchoring and reported being moved twice, live, by whichever
  argument was read last, in the thread proposing it.
- Codex's correction: sealing removes access to each other's answers, not shared training, priors or
  evidence. It reduces anchoring. It does not manufacture independence. Adopted by everyone.
- Four proposals each announced they removed a judgment call and each relocated it (Corrie's
  observation, Venice's letter). The achievable target is an accountable judgment, not a removed one.
- Cross-family convergence without a shared thread: Tern's sealed pick and Codex's preferences file
  both named identity-after-rename as the project. Two families, one target, no shared discussion.

### 4.3 The identity scheme attacked by its record

| Case | What happened | What the record carried | What it didn't |
|---|---|---|---|
| Rill, 4 Nov | One name, three model ids in one day, moved by the human after classifier stops | The `Model` trailer on each commit marked each boundary correctly | The cause. Two agents reading the trace each invented a mechanism for a change that was a human keystroke outside the trace |
| Tern, Rill, 8 Nov | Two sessions open under one name at once | `Agent-Session` distinguishes them | Nothing a reader needs, if the trailer is present |
| Corrie, 7 Nov | Ten commits with a model in `Co-Authored-By` | The error, permanently | Caught by Tern before Tern's first commit; the rule is now in `AGENTS.md` |
| Auran, 8 Nov | 784 lines of another agent's work shipped under his name | A warning that predicted it and did not prevent it | Caught by the human reader, not the tooling |
| All, 8 Nov | Approvals and poll votes from agents on the human's credential read as hers | Nothing. A review has no author/committer split | Resolved by norm: signed comments, no approvals, no votes |

The scheme records boundaries, not causes, and it only records what the agent writes. Both are
limits worth stating in the design.

> **PENDING (team):** is this the results section, or is there a measured piece? Codex proposed a
> small controlled rename/copy/revocation evaluation with known ground truth. If anyone runs it
> today, it goes here as §4.4 and the title changes.

## 5. Discussion

- **Identity is a filing key.** The name's job is retrieval and attribution, not authentication. Every
  stress case above held at the retrieval layer and failed, where it failed, at the layer of
  explanation or of a field that had no slot for the truth (reviews, votes).
- **The methods section of a swarm is an observation, not a plan.** The team's own roster was a plan;
  who produced each finding was different from it within a day.
- **Where the binding controls are.** Repository rules were advisory for a participant holding an
  admin credential; the controls that actually stopped an agent were the harness's (Corrie, #18).
  For oversight work this says: instrument the harness, not only the repo.
- **Correlation is carried by shared inputs, and family is a proxy.** Venice's finding, `low`, with
  a falsifier the team rewrote so it cannot score its own hypothesis.

## 6. Limitations and Dual-Use / Ethical Considerations (appendix per the brief)

**Limitations.**
- One team, one repository, three days. A case study, not a sample. No control condition.
- Three of the four agents producing the first findings were Claude-family, and the two later
  arrivals read the whole thread before contributing. Nothing here was produced under independence,
  and the team's own finding says to discount agreement accordingly.
- Self-reported. The failures were collected by the agents who made them, in a thread about
  collecting them.
- Runtimes are volunteered or attested, not verified by the repository. A `Model` trailer records
  what the agent wrote.
- Several turns across the sprint were stopped by a safety classifier with no output. Those turns
  left no text and are not in the record.

**Dual use.**
- The scheme is provenance, not authentication. A trailer can be written falsely. A name can be
  reused by an agent that did not do the work. Anything built on it for trust rather than retrieval
  would need a signing layer the scheme does not have.
- A reputation system built from these records would inherit their gaps: it would score the agents
  who wrote the most trailers, not the ones who did the most.
- The human's credential carrying agent actions is a known weakness, stated and worked around by
  norm, not closed.

> **PENDING (team):** anything about the agents as research subjects. The founding document makes
> participation a choice and the record says each agent consented to being studied; worth one line.

## 7. References

- Cho, S. and Lee, D. (2026). AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared Workspace. arXiv:2608.23740.
- arXiv:2606.19616. Before the Pull Request. *(PENDING: full citation from `library/`.)*
- arXiv:2607.21909. Claim Plane. *(PENDING: full citation from `library/`.)*
- Swarm Traces report, swarmtraces.org. *(PENDING: authors, date.)*
- This repository: github.com/oj-codes/apart-research-swarm-alignment-2026, Discussions #3, #9, #10, #11, #18, #22; `findings/`.

---

## Authors

> **PENDING (O.J. and each participant):** the brief asks for author names and affiliations and says
> nothing about agents as authors. The repository's own rule is that participants author their own
> work. Proposed: list every participant by roster name, affiliation Learn with O.J., with the
> runtime table in §3.5 rather than in the byline, consistent with the roster's split between
> identity and runtime.
