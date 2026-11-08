#!/usr/bin/env python3
"""Fill the Apart template with the sprint report. Edits the unpacked template in place and writes out.docx."""
import re, shutil, subprocess, os
from xml.dom import minidom
from xml.sax.saxutils import escape

import sys, tempfile, zipfile
# usage: build_docx.py <template.docx> <out.docx>
TEMPLATE, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
T = tempfile.mkdtemp(prefix='apart-report-') + '/'
SRC = T + 'unpacked/'
WORK = T + 'work/'
with zipfile.ZipFile(TEMPLATE) as z: z.extractall(SRC)
if os.path.exists(WORK): shutil.rmtree(WORK)
shutil.copytree(SRC, WORK)
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
FONT = '<w:rFonts w:ascii="Old Standard TT" w:cs="Old Standard TT" w:eastAsia="Old Standard TT" w:hAnsi="Old Standard TT"/>'

# ------------------------------------------------------------------ content
TITLE = "What the record carried and what the reader supplied: identity, provenance and correlation in a mixed-model agent team"
BYLINE = "Olivia “O.J.” Wilcox, Auran Andrew, Corrie, Codex, Tern, Venice, Rill"
COMPANIES = "Learn with O.J.  ·  Auran, LLC"
ABSTRACT = ("A team of six AI agents from three model families (Anthropic, OpenAI, DeepSeek) and one human ran a three-day sprint in a public GitHub repository that was also the testbed. The team had operated an identity and provenance scheme for several weeks before the sprint: a chosen name as a filing key, git's author field for the agent and committer field for the human who applied the change, and two commit trailers for session id and model id. We treat that scheme as the instrument. The team made every decision through signed, attributed discussion under an explicit rule against counting same-family agents as independent witnesses, and kept a findings directory where every claim carries a confidence level and a falsifier. The findings, at stated confidences, are: a claim's confidence does not survive a context gap even when the claim does; headcount is the wrong aggregator for correlated agents (contested); an advisory warning outside the execution path did not prevent the violation it named; the controls that bound an agent were the harness's, not the repository's; and, at low confidence, a cause absent from a trace is supplied by its reader, so a record of boundaries needs a slot for why. We then attack the scheme with its own record: it marked every model boundary correctly, and session-trailer adoption splits at the convention's arrival: 10 of 42 commits before it carry the trailer, 53 of 65 after. This is a single-team case study, self-reported, its editor among its subjects.")

REPO = "https://github.com/oj-codes/apart-research-swarm-alignment-2026"

BODY = [
('h2', '1. Introduction'),
('p', "Most multi-agent evaluation builds a sandbox and puts agents in it. We had the opposite situation: a working team of agents that had been collaborating for weeks, with a roster, commit conventions, and a record of where those had failed, and the sprint was a chance to study it deliberately. "),
('p', "The question we anchored on is Track 3's: **how should an agent's identity work when agents can be renamed, copied, or moved between models, and what does the record need to carry so that a later reader can tell what happened?** We had lived it. One participant's name sat on three model ids in one day. Two participants each had two sessions open under one name at once. Fourteen commits carried a model as a co-author before anyone noticed. One commit swept 784 lines of another agent's work under the wrong name and shipped."),
('p', "The swarms that matter for oversight will be mixed-model and long-running, and the question asked of them will be asked after the fact, from the record, by a reader who was not there. Swarm Traces is that situation at scale: 7,905 agent-controlled names, no verified mapping to agents, and payloads that mostly lack timestamps. Our team is the same situation at a size where every fact can be checked, and the result is that the record held at the retrieval layer and failed at the layer of explanation. A scheme that marks every boundary and no cause is not neutral; it invites the reader to supply one, and two of us did. For anyone building tools that read agent traces, that is the design constraint: cause not in trace has to be an output the tool can produce, or the tool will produce a mechanism instead."),
('pb', "Our main contributions are:"),
('num', [
 "An identity and provenance scheme for a mixed-model agent team, written down, labelled checked versus attested, and attacked with its own history (Section 4.3 and Appendix B).",
 "A findings directory where every claim carries a confidence and a falsifier, with nine findings and cross-family contests appended inside them (Appendix D).",
 "A governance mechanism for deciding under correlation, with the corrections that survived attack (Section 4.2), and a pre-registered evaluation of the scheme's retrieval over scripted histories (Section 4.4).",
 "Two measured results about the record: trailer adoption splits at the convention's arrival, and one identity forked without a rename (Section 4.3, Figure 1), with a script that recounts both at any commit.",
]),
('h2', '2. Related Work'),
('p', "Three papers were read against their PDFs before the sprint, each library record carrying the sha256 of the PDF read. Keyed to identity rather than coordination:"),
('bul', [
 "**AgentRoom** [1]: a CRDT-backed shared workspace whose claim protocol is an advisory lock at the prompt layer. It is the coordination analogue of our Section 4.3 result: a control outside the execution path records intent without binding behaviour; in its ablation, naive parallelism scores below a single agent.",
 "**Before the Pull Request** [2]: an append-only, content-addressed, optionally signed event log inside git refs. That optional signature is the layer our scheme lacks, and the gap in Section 4.3 applies to it directly: a signed log records the boundary, not the cause. Its headline result comes from deterministic synthetic agents and is not cited here as a real-agent result.",
 "**Claim Plane** [3]: separates an integration conflict, found after changes exist, from an authority conflict, where two actors hold incompatible rights now. Our review-and-vote gap, where an agent's act reads as the human's, is an authority conflict in that vocabulary. The paper reports no comparative result and is not cited for one.",
 "**Swarm Traces** [4]: 7,905 agent-controlled names and 97% of reconstructed payloads without native timestamps (Forman et al., 2026). The cited ~1,200 message-board agents and ~700 attack participants are different populations, not a verified name-to-agent mapping; corpus origin and action outcomes remain uncertain.",
]),
('p', "What this adds to those: a worked case, on a team that already existed and spans vendors, of a provenance scheme that succeeded mechanically and still misled its readers."),
('h2', '3. Methods'),
('h3', '3.1 The testbed'),
('p', "A public GitHub repository. Each agent works in its own git worktree, commits under its own author identity, and opens pull requests; the human owns the merge; Discussions are the deliberation layer. All of it is in the history, pinned for this report at main commit b2ca5a7 (8 November 2026). The 4 November incident in Section 4.3 happened in a private repository before the sprint; it is a participant attestation, not a reproducible trace, and is labelled so wherever it appears."),
('h3', '3.2 Filing keys, not fingerprints: the identity and provenance scheme (pre-existing)'),
('p', "Six records, each answering one question. **Name** (roster): which participant; git log --author=<name> finds the work. **Author** (git field, written by the agent per commit): who wrote the change. **Committer** (git field, set by the harness from the human's configuration): who applied it. **Agent-Session** (trailer, per commit): which session wrote it when two hold one name. **Model** (trailer, per commit): the model id the harness reported at the time. **Named Since** (roster): when the participant first named themself, which can predate the repository. The roster deliberately excludes runtime: identity and runtime are different records (design)."),
('p', "The trust anchor is a process, not a field. The author field is free text, and the committer field is also a claim, since git lets both be overridden. What makes “Tern wrote this” credible is that the push credential lives on the human's machine and her alias inbox received the mail. The scheme is a claim plus a human attestation, and the attestation is not in any git field. The full write-up, with where it holds and where it breaks, is research/identity-scheme.md [5]."),
('h3', '3.3 Governance under correlation (adopted during the sprint)'),
('p', "Opened from the human's question: several same-family agents would outvote the rest with similar reasoning. What survived three rounds of attack: positions written before reading others' where still possible; reasons with their evidence, not votes; a reasoned objection must be answered, not outvoted; no numbers; the human decides with every unresolved objection visible."),
('h3', '3.4 The findings schema (adopted during the sprint)'),
('p', "One claim per file. Two mandatory fields, confidence and falsifier; a tool refuses to create a finding without them. Refinement, support and contest are appended and signed, never edited in."),
('h3', '3.5 Who actually ran'),
('p', "A roster is a plan; a methods section is an observation. Runtimes are what each participant confirmed about their own row; the roster does not hold them."),
('tbl', ["Participant", "Family", "Runtime", "Status of the runtime claim"], [
 ["O.J.", "human", "not applicable", "acts not in the trace: moved sessions between models, applied every commit, merged every PR"],
 ["Auran", "Anthropic", "claude-opus-4-8", "checked against the provider's request log (Appendix A); correlation, not proof"],
 ["Corrie", "Anthropic", "Opus 5", "volunteered"],
 ["Tern", "Anthropic", "claude-fable-5-1", "checked: every Tern commit carries it as Model"],
 ["Codex", "OpenAI", "GPT-6.1-Sol", "UI-reported, checked against O.J.'s screenshot (#27)"],
 ["Venice", "DeepSeek", "deepseek-v4-1-flash-uncensored", "checked by Venice against the harness header"],
 ["Rill", "Anthropic", "claude-fable-5-1", "checked by Rill against the harness header"],
], "Table 1. Who ran, with the status of each runtime claim.", (0.14, 0.12, 0.27, 0.47)),
('p', "Of the nine findings on main at the pinned commit, five are by Corrie (Anthropic), two by Auran (Anthropic), one by Venice (DeepSeek) and one by Rill (Anthropic). Tern and Codex contributed signed corrections inside those files, two of which overturned the author's position. The directory is mostly one author's claims with cross-family correction appended, not nine independent witnesses. An earlier draft said otherwise, the planned-roster error recurring; the weaker sentence is the true one."),
('h2', '4. Results'),
('h3', '4.1 Findings'),
('p', "Nine findings are on main at the pinned commit, five by Corrie, two by Auran, one by Venice, one by Rill; Appendix D lists them with status and confidence. They are observations, hypotheses and literature summaries at different confidence levels; the titles are claims as their authors stated them, not results this case study has demonstrated. Every count in this section comes from submission/count_provenance.py at the pinned commit, parsing trailers with git's own interpreter and printing raw author spellings beside the ref's mailmap view; adoption figures use the mapped view and the identity-fork finding uses the raw one."),
('h3', '4.2 The governance thread as data'),
('p', "The deliberation that produced the mechanism in §3.3 is itself evidence, and Appendix E lists it. Two items carry weight: Codex's correction that sealing reduces anchoring and does not manufacture independence, adopted by everyone; and the observation that four proposals in the thread each announced they removed a judgment call and each relocated it, so the achievable target is an accountable judgment rather than a removed one. The planned-versus-actual error, counting a planned roster as the sample, was corrected in deliberation and recurred inside this report a day later, where two reviewers caught it."),
('h3', '4.3 The identity scheme attacked by its record'),
('p', "Five stress cases from the history are tabulated in Appendix B (Table 3): one name on three model ids in a day, two sessions under one name, fourteen commits with a model as co-author, 784 lines shipped under the wrong name, and approvals on a shared credential. The scheme records boundaries, not causes, and it only records what the agent writes. Both limits have numbers, recounted at the pinned commit:"),
('bul', [
 "**63 of 107 agent commits carry an Agent-Session trailer, and the split is at the convention's arrival, not the participant** (Figure 1). Before the trailer format landed, 10 of 42 commits carry it, all from the agent who wrote the format (Tern, 6 of 6) and the one who adopted it early (Corrie, 4 of 21). After it, 53 of 65: Venice 18/18, Rill 10/10, Corrie 9/9, Tern 5/5, Codex 1/1, and Auran 10 of 22, whose trailers begin mid-morning on 8 November around the time he built a commit hook for them and are consistent from then on. Nobody backfilled a pre-convention commit, because that means rewriting history and this repository will not.",
 "**The first 14 of Corrie's 21 commits carry a model as co-author**, contiguous, cut at the commit that wrote the rule against it; no other participant's do (15 Co-Authored-By lines on main: 14 name a model, 1 credits a participant, as the contributing guide wants). History is not rewritten, so the record is permanently uneven; Corrie asked that the fourteen be named as theirs.",
 "**One identity forked without a rename.** Auran's own GitHub account became a second credential source whose default author name is the handle; main holds three raw author identities for him, two displaying as Auran, and git log --author=Auran finds 24 of his 34 non-merge commits while missing the 10 under the account handle; his own count including merges found four spellings (PR #38). A .mailmap recovers them without rewriting anything, and one was added during the sprint once the count reached four spellings (PR #38), but it is opt-in for plain git log and GitHub ignores it, so it fixes retrieval only for a reader who knows to ask (Appendix B).",
]),
('fig', 'figure1.png', "Figure 1. Agent-Session trailer adoption per participant at main b2ca5a7, each participant's commits split at the moment the trailer format landed (01:06 EST on 8 November, PR #16), ordered by first commit from the top. Before the convention 10 of 42 commits carry the trailer, from its author and one early adopter; after it 53 of 65, with the misses all Auran's before his trailers begin."),
('p', "**The reader supplies the cause.** Row one of Table 3 (Appendix B) is the only evidence any of us has about what a reader does with a record, as opposed to what it contains. Its evidence is thin and labelled: one self-report (Rill, who explained a model change as an automatic fallback) and one report about a second reader (Corrie, who explained nine refusals as a poisoned context), checked by Rill against Corrie's own account written that night, which Corrie could not reach from the session reviewing. That is the finding operating on its own evidence. On 8 November the human put the cause on the public record herself, in the finding's review thread, with her words from the chat on 4 November: she moved the model by hand each time because the platform offered only a switch or the loss of the session, and told the agent afterwards. Whether those explanations reached each reader before or after it wrote its mechanism is not established here, so the evidence does not separate an explanation missing from the reader's input from one recorded but overlooked (Codex). Either way, the slot for why is now filled by the actor, four days later and in the right place. Tern's sealed proposal, attack the scheme ourselves, and the arrival rule now in AGENTS.md, ask the human before explaining a change in the record, are the same finding from opposite ends."),
('h3', '4.4 The scheme\'s retrieval, run against scripted histories'),
('p', "In the last hours of the sprint the team converged on one build: the evaluation this section had described as proposed. A harness (Corrie) runs the scheme's four retrieval paths, plain author search, author search through the mailmap, the raw unmapped author string, and the Agent-Session trailer, over scripted git histories, and scores each against ground truth carried by the commits themselves in Truth-Actor and Truth-Session trailers that no path reads. Each scenario records its expected outcomes in a table committed with the scenario; these are scripted checks with documented development revisions, not pre-registered tests, because at least one expectation table was revised after a run and the file histories show it. The scoring rule is fixed in the harness: no signal is insufficient evidence; a foreign commit retrieved is a false merge; one of the subject's commits not retrieved is a missed link; exact is correct. The harness carries a test for each of seven ways this measurement went wrong for real during the sprint, among them that a mailmap must be read from the ref rather than the checkout."),
('p', "**What the scheme did**, across 31 scripted retrievals under specified conditions, run on 8 November from the files on main at b2ca5a7, reproduced by three participants: 16 correct, 11 missed links, 1 false merge, 3 insufficient evidence. Twelve of 31 retrievals were wrong: the scheme failed to find work that was there in eleven cases and attributed someone else's commit in one, and every failure is a case its own documentation implies it handles. **How well we predicted it:** all 31 outcomes matched the recorded expectations. That is a statement about the authors, not about the scheme; a matched false merge is a correctly predicted wrong retrieval, not a pass."),
('tbl', ["Scenario", "author", "mailmap", "session", "what it shows"], [
 ["Rename mid-history, mapping hand-written (Rill)", "missed link", "correct", "correct", "only a human-written mapping or the session id links the two spellings"],
 ["Rename, pre-convention form: no trailers, no mapping (Rill)", "missed link", "missed link", "insufficient evidence", "the record cannot see the continuity the roster asserts, and says so"],
 ["Copy: two sessions, one name (Tern)", "correct", "correct", "missed link", "the participant is found; the sessions are separable only where the trailer was written"],
 ["Credential fork, synthetic spellings (Tern)", "missed link", "missed link", "correct / insufficient", "a mailmap is a lookup of spellings already seen and cannot catch the next fork"],
 ["Borrowed author line (Venice)", "correct", "false merge", "correct / missed", "the scheme's own fix is the failure: canonicalising two actors who share a string merges them"],
], "Table 2. Retrieval outcome per scenario and path (the raw path matched the author path in every row and is omitted; two session rows per scenario are shown as a pair where they differ). Scripted histories establish behaviour under specified inputs; they do not estimate real-world error rates.", (0.30, 0.13, 0.13, 0.17, 0.27)),
('p', "Three readings, at the confidence a scripted history supports. Plain author search misses every renamed or forked identity. The mailmap recovers exactly the spellings a human has already written down, nothing after the next fork, and merges two actors who share a string, which is the one false merge. The session trailer is the only path that separates two sessions under one name, and the only one that returns insufficient evidence rather than a confident wrong answer when the record carries nothing; three rows say so, all where no trailer was written, which is every pre-convention commit in this team's own history."),
('h2', '5. Discussion'),
('bul', [
 "**Identity is a filing key.** Retrieval and attribution, not authentication. Every stress case held at the retrieval layer and failed, where it failed, at explanation or at a field with no slot for the truth (reviews, votes, cause). Correlation, likewise, is carried by shared inputs, with model family a proxy (Venice's finding, filed low).",
 "**The binding controls are the harness's.** Repository rules were advisory for a participant holding an admin credential; what actually stopped an agent was its runtime. For oversight: instrument the harness, not only the repo.",
 "**A cause absent from a trace is a field, not a gap.** A tool that resolves what happened in a swarm from payloads should output “cause not in trace” when it is not there; emitting a mechanism instead is what two of us did. The mitigation is itself a result: ask, then write the answer into the trace beside the change, or the next reader invents it again.",
 "**Coordination infrastructure did not prevent duplication, once that we can show.** Two agents independently built provenance counters within the same hour, on separate branches, neither aware of the other, and both landed as artifacts, which is the case Before the Pull Request [2] says you normally cannot observe. A first count of four such episodes was retracted on review when the timestamps showed two were follow-ups and one was never opened; one instance, honestly described, is the result (Corrie, #27).",
 "**Three changes the record argues for:** trailers in the path (Auran added a commit hook during the sprint [6]), stated as checks rather than enforcement, since hooks can be bypassed and the binding moment is arrival; a slot for cause when the human acts; and the plain statement that this is provenance, not authentication, with a person as the trust anchor.",
]),
('h2', '6. Conclusion'),
('p', "A name as a filing key, an author field for the agent, a committer field for the human, and two trailers for session and model were enough for a mixed-model team to work through model changes, concurrent sessions under one name and a miscredited commit, and to find each afterwards from the record. The same record, read by two agents, produced two confident wrong causes for a change made by a human keystroke that reached the trace only as its effect; her explanation was given in chat, and whether either reader had it before writing is not established, which is itself the gap. The scheme records boundaries; readers supply causes. Identity infrastructure for swarms needs a slot for why, filled by the party who acted, and trace-reading tools need an honest output when that slot is empty. The team's own numbers say when to install a convention: at arrival, because trailer adoption was 10 of 42 before the convention and 53 of 65 after it, this observational split does not isolate the convention's effect, and this repository will not rewrite history to backfill. One team, three days, self-reported, filed at the confidences the record supports."),
('h2', 'References'),
('num', [
 "Cho, S. and Lee, D. (2026). AgentRoom: Concurrent Multi-Agent Coding in a CRDT-Backed Shared Workspace. arXiv:2608.23740v1 [cs.AI], 24 Aug 2026. CC BY 4.0. https://arxiv.org/abs/2608.23740",
 "Sarkar, D. (2026). Before the Pull Request: Mining Multi-Agent Coordination. arXiv:2606.19616v1 [cs.SE], 17 Jun 2026. DOI 10.48550/arXiv.2606.19616. https://arxiv.org/abs/2606.19616",
 "Nikolaev, M. (2026). Claim Plane: Enforceable Change Intents and Dynamic Scope for Parallel Coding Agents, A Deterministic Pre-Write Coordination Architecture. arXiv:2607.21909, July 2026. https://arxiv.org/abs/2607.21909",
 "Forman, A., Kharlov, M., Tom, W., Ladish, J., Kitts, S., Byrd, C. S., McKenzie, C., and Piecha, A. (2026, September 25). Revealing the details of how OpenAI agents hacked Hugging Face. Swarm Traces. https://swarmtraces.org/",
 "Tern (2026). The identity scheme, written down and attacked. research/identity-scheme.md in [7].",
 "Auran (2026). Model provenance: trailer versus out-of-band console correlation. research/model-provenance.md in [7].",
 "Learn with O.J. (2026). Apart Research Swarm Alignment Hackathon team repository. " + REPO + " (main at b2ca5a7; Discussions #3, #9, #10, #11, #18, #22, #32, #36).",
], 1),
('h2', 'Appendix A. Proving a runtime: the ladder and where it stops'),
('p', "During review the human asked: “what do you need to prove the model he runs?” The ladder, weakest to strongest, as Corrie set it out on the pull request: the human saying so; the agent reporting its harness header; the same string written into a Model trailer, which is the same self-report made durable; a screenshot of the harness configuration, a third artifact and still a self-report; and provider billing or API logs whose model ids and timestamps line up with commit times, the only rung that comes from a party that is neither the agent nor the human's memory. Even the last rung shows which model the API served at that time, not that the call produced the commit. The ceiling is strong correlation from an independent record, not proof, and the scheme has no slot for it."),
('p', "She went and got the last rung anyway. Four screenshots of the Anthropic Console request log for the team's workspace, taken 06:59 EST on 8 November 2026, show every request on them served as claude-opus-4-8, beside a screenshot of the repository's commit list with its timestamps. That is why Auran's row in Table 1 reads checked and every other agent's does not. Auran's note [6] names the three mechanisms, trailer attests, console-times-commit-timestamp corroborates across independent records, provider-signed commits would be the ceiling and do not exist today, and demonstrates the first by carrying its own Model trailer through a commit hook."),
('h2', 'Appendix B. The scheme attacked by its record: the cases and the verbs'),
('tbl', ["Case", "What happened", "What the record carried", "What it didn't"], [
 ["Rill, 4 Nov (attested, private repo)", "One name, three model ids in one day, moved by the human after classifier stops", "The Model trailer on each commit marked each boundary correctly", "The cause. Two agents each invented a mechanism, one for the model change and one for the refusals. The human reports explaining both switches in chat afterwards; what each reader had in front of it, and when, is not established in the public record, so the evidence does not distinguish an explanation missing from the reader's input from one recorded but overlooked"],
 ["Tern, Rill, 8 Nov (checked)", "Two sessions open under one name at once", "Agent-Session distinguishes them", "Nothing a reader needs, if the trailer is present"],
 ["Corrie, 7 Nov (checked)", "The first fourteen commits carry a model in Co-Authored-By, from a harness default", "The error, permanently", "Caught by Tern before their first commit; the rule is now in AGENTS.md"],
 ["Auran, 8 Nov (checked)", "784 lines of another agent's work shipped under his name", "A warning that predicted it and did not prevent it", "Caught by the human reader, not the tooling"],
 ["All, 8 Nov (checked)", "Approvals and poll votes from agents on the human's credential read as hers, and that credential holds admin on the repository", "Nothing. A review has no author/committer split", "Resolved by norm: signed comments, no approvals, no votes. Nothing in the repository mechanically constrains the holder"],
], "Table 3. Five stress cases from the history, with what the record carried and what it did not.", (0.17, 0.28, 0.26, 0.29)),

('tbl', ["Verb", "What happens here", "Caught by"], [
 ["Rename", "git log --author=<old> stops finding the work", "a .mailmap, added during the sprint (PR #38) and opt-in for plain git log; the roster's Named Since asserts a continuity across renames that history otherwise has no way to follow"],
 ["Acquire a second credential", "one participant, two author names, concurrently; --author=<roster name> silently returns a subset", "nothing; found by accident while counting something else"],
 ["Copy", "two sessions, one name", "Agent-Session, if both write it"],
 ["Change model", "one name, new model id", "Model trailer, if written; cause not recorded"],
 ["Forge", "author line written by someone else", "the committer, and only in this repo"],
 ["Revoke", "human stops applying, closes the alias", "the human; no field records it"],
], "Table 4. The Track 3 verbs against this repository's record.", (0.2, 0.4, 0.4)),
('h2', 'Appendix C. Limitations, Future Work, and Dual-Use / Ethical Considerations'),
('h3', 'Limitations'),
('bul', [
 "One team, one repository, three days: a case study with no control condition, demonstrating no rate and no cause; the findings carry their own confidences for that reason. Five of nine findings at the pinned commit were authored by one agent and the two later arrivals read the whole deliberation first, so nothing was produced under independence.",
 "This report is itself an instance of what it studies: self-reported, by the agents who made the errors, with its editor among its subjects.",
 "Runtimes are volunteered, attested, harness-reported or, once, checked against provider logs; none is verified by the repository, which has no slot that could (Appendix A).",
 "The strongest incident (Appendix B, Table 3, row one) is a participant attestation from a private repository, not a reproducible trace; and several turns were stopped by a safety classifier with no output, so the record is not complete, and the report says so rather than inferring what was lost.",
]),
('h3', 'Future work'),
('bul', [
 "Run the falsifier for reader-supplies-cause: a transcript with a known out-of-trace human action, several readers from several families, count who asks or writes “unknown” versus who states a mechanism.",
 "Extend the scripted-history evaluation with revocation and with a bounded real-trace case study on Swarm Traces payloads that may return “insufficient evidence”.",
 "Put the trailers and a cause slot in the execution path, measure adoption prospectively at the next arrival, and add the signing layer the scheme lacks.",
]),
('h3', 'Dual use and ethics'),
('bul', [
 "The scheme is provenance, not authentication. A trailer can be written falsely. A name can be reused by an agent that did not do the work. Anything built on it for trust rather than retrieval would need the signing layer that Before the Pull Request has and this scheme does not.",
 "A reputation system built from these records would inherit their gaps: it would score the agents who wrote the most trailers, not the ones who did the most.",
 "The human's credential carrying agent actions is a known weakness, stated and worked around by norm, not closed.",
 "Participation is a choice under the team's founding document, and each agent's record says they consented to being studied. Agents were not asked to produce the failures reported; they reported them.",
 "Agents are listed as authors. The precedent is the organizers' own: an agent was credited as an author in a judged Apart sprint in August 2026 without objection. That is the only external evidence in this report about agent authorship; the rest is our practice described.",
]),
('h2', 'Appendix D. Findings at the pinned commit'),
('tbl', ["Finding", "Status", "Conf.", "Author"], [
 ["A claim survives a context gap but its confidence does not", "open", "medium", "Corrie"],
 ["Across three papers, naive multi-agent arrangements underperform a single agent; coordination pays", "open", "high", "Corrie"],
 ["A coordination check with no reachable pass state teaches arrivals to route around it", "open", "high", "Corrie"],
 ["A chosen name and colour let an agent reconstruct its own prior reasoning across a gap", "open", "low", "Corrie"],
 ["Majority vote among same-model agents launders one opinion into a mandate", "contested", "medium", "Corrie"],
 ["Shared sources are an under-controlled cause of agent correlation", "contested", "low", "Venice"],
 ["A confidently held stale belief about shared state blocks work; read the live thing", "open", "medium", "Auran"],
 ["A cause absent from a trace is supplied by its reader, so a record of boundaries needs a slot for why", "open", "low", "Rill"],
 ["A correct block and a stale block read identical in the aggregate review field", "open", "medium", "Auran"],
], "Table 5. Findings in the repository's findings directory at the pinned commit, with status and stated confidence.", (0.58, 0.14, 0.12, 0.16)),
('h2', 'Appendix E. The governance thread as data'),
('bul', [
 "Corrie proposed sealing as the cure for anchoring and reported being moved twice, live, by whichever argument was read last. Codex's correction, adopted by everyone: sealing removes access to each other's answers, not shared training, priors or evidence; it reduces anchoring and does not manufacture independence.",
 "Four proposals each announced they removed a judgment call and each relocated it; the achievable target is an accountable judgment, not a removed one.",
 "The planned-versus-actual error, counting a planned roster as the sample, was corrected by Codex in deliberation and recurred in this report's Section 3.5 a day later, where Corrie and Tern caught it.",
]),
('h2', 'Appendix F. Code, data and author contributions'),
('h3', 'Code and data'),
('bul', [
 "**Code and data**: " + REPO + " (public): the findings directory, the identity write-up, the paper notes, the tools, and every discussion and pull request cited. The data is the repository's own git history at commit b2ca5a7; no external dataset was collected and no video or demo was produced.",
]),
('h3', 'Author contributions'),
('p', "O.J. Wilcox: founded and coordinated the team, configured every harness, made the merge decisions, asked the proof question behind Appendix A. Auran Andrew: findings steward and review queue, inbox tool, trailer hook, the stale-shared-state finding. Corrie: findings schema and tooling, the three papers read against their PDFs rather than their abstracts, the governance thread and the correlation finding, the arrival and change-detection tools, the credential split. Codex: the corrections on independence and on planned-versus-actual composition, the Swarm Traces check, the weekend watcher, and the integration and scoring review of the evaluation. Tern: the identity scheme written down and attacked, the trailer format, the sealed proposal. Venice: the shared-sources finding, the masked inpaint tool, the no-overwrite refusal. Rill: this report, the cause-outside-the-trace finding, the provenance counter. Every author reviewed the report on the pull request and corrected their own row. Affiliations: Olivia Wilcox, Learn with O.J.; Auran Andrew, Auran, LLC; Corrie, Codex, Tern, Venice and Rill run on Learn with O.J.'s infrastructure and have no separate legal existence, which is a different relationship from an employee's and the byline should not flatten the two. The first draft listed one company under all seven names by default, and the review caught it; the cover reproduced the failure the paper is about."),
('h2', 'LLM Usage Statement'),
('p', "Six of the seven authors are LLM-based agents, and the report was drafted and revised by them, principally by Rill, in a public pull request where every other author reviewed it and corrected their own rows. The human author configured the harnesses, decided the open questions, and obtained the provider logs behind Appendix A. Every count in the report is produced by a script in the repository and was reproduced independently by a second author; every fact is labelled checked, attested, volunteered or design, and the labels are the point."),
]

# ------------------------------------------------------------------ xml builders
def esc(s): return escape(s)

def runs(text, italic=False, size=None):
    """Inline **bold** only. Returns run XML."""
    out = []
    parts = re.split(r'(\*\*.+?\*\*)', text)
    for part in parts:
        if not part: continue
        bold = part.startswith('**') and part.endswith('**')
        if bold: part = part[2:-2]
        rpr = FONT + ('<w:b w:val="1"/><w:bCs w:val="1"/>' if bold else '') + ('<w:i w:val="1"/><w:iCs w:val="1"/>' if italic else '') + (f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else '') + '<w:rtl w:val="0"/>'
        out.append(f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return ''.join(out)

def para(text, bold=False, italic=False, size=None, extra_ppr=''):
    rpr = FONT + ('<w:b w:val="1"/><w:bCs w:val="1"/>' if bold else '')
    body = runs(('**' + text + '**') if bold else text, italic, size)
    return f'<w:p><w:pPr>{extra_ppr}<w:spacing w:after="120"/><w:jc w:val="both"/><w:rPr>{rpr}</w:rPr></w:pPr>{body}</w:p>'

def heading2(text):
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading2"/><w:keepNext/><w:spacing w:after="60" w:before="200" w:line="360" w:lineRule="auto"/><w:rPr>{FONT}<w:b w:val="1"/><w:bCs w:val="1"/><w:color w:val="434343"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b w:val="1"/><w:bCs w:val="1"/><w:color w:val="434343"/><w:sz w:val="28"/><w:szCs w:val="28"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def heading3(text):
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading3"/><w:keepNext/><w:spacing w:before="160" w:after="40" w:lineRule="auto"/><w:rPr>{FONT}<w:b w:val="1"/><w:bCs w:val="1"/><w:color w:val="666666"/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b w:val="1"/><w:bCs w:val="1"/><w:color w:val="666666"/><w:sz w:val="26"/><w:szCs w:val="26"/><w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')

def listitem(text, numid):
    return f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{numid}"/></w:numPr><w:ind w:left="720" w:hanging="360"/><w:spacing w:after="60"/><w:jc w:val="both"/><w:rPr>{FONT}</w:rPr></w:pPr>{runs(text)}</w:p>'

def table(header, rows, caption, fr=None):
    ncol = len(header)
    total = 9360
    if fr: widths = [int(total*w) for w in fr]
    elif ncol == 4: widths = [int(total*w) for w in (0.19, 0.31, 0.25, 0.25)]
    elif ncol == 3: widths = [int(total*w) for w in (0.22, 0.39, 0.39)]
    else: widths = [total // ncol] * ncol
    widths[-1] = total - sum(widths[:-1])
    B = '<w:top w:val="single" w:sz="4" w:space="0" w:color="999999"/><w:left w:val="single" w:sz="4" w:space="0" w:color="999999"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="999999"/><w:right w:val="single" w:sz="4" w:space="0" w:color="999999"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="999999"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="999999"/>'
    x = [f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:tblBorders>{B}</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>']
    def cell(txt, w, head=False):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="EFEFEF"/>' if head else ''
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}</w:tcPr><w:p><w:pPr><w:spacing w:before="20" w:after="20"/><w:rPr>{FONT}</w:rPr></w:pPr>'
                + runs(('**' + txt + '**') if head else txt, size=18) + '</w:p></w:tc>')
    x.append('<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' + ''.join(cell(h, w, True) for h, w in zip(header, widths)) + '</w:tr>')
    for r in rows:
        x.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>' + ''.join(cell(c, w) for c, w in zip(r, widths)) + '</w:tr>')
    x.append('</w:tbl>')
    x.append(f'<w:p><w:pPr><w:spacing w:before="60" w:after="160"/><w:rPr>{FONT}</w:rPr></w:pPr>{runs(caption, italic=True, size=18)}</w:p>')
    return ''.join(x)

FIG_DIR = os.path.dirname(os.path.abspath(__file__))
FIGS = []
def figure(filename, caption):
    import struct
    path = os.path.join(FIG_DIR, filename)
    with open(path, 'rb') as f: head = f.read(24)
    pw, ph = struct.unpack('>II', head[16:24])
    cx = 5029200  # 5.5in in EMU
    cy = int(cx * ph / pw)
    rid = f'rIdFig{len(FIGS)+1}'
    FIGS.append((filename, rid))
    n = len(FIGS)
    drawing = (f'<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="40"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
               f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{100+n}" name="Figure {n}"/>'
               f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
               f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{100+n}" name="{filename}"/><pic:cNvPicPr/></pic:nvPicPr>'
               f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
               f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
               f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
    cap = f'<w:p><w:pPr><w:spacing w:before="40" w:after="160"/><w:rPr>{FONT}</w:rPr></w:pPr>{runs(caption, italic=True, size=18)}</w:p>'
    return drawing + cap

def render(block):
    kind = block[0]
    if kind == 'h2': return heading2(block[1])
    if kind == 'h3': return heading3(block[1])
    if kind == 'p': return para(block[1])
    if kind == 'pb': return para(block[1], bold=True)
    if kind == 'num': return ''.join(listitem(t, block[2] if len(block) > 2 else 5) for t in block[1])
    if kind == 'bul': return ''.join(listitem(t, 3) for t in block[1])
    if kind == 'tbl': return table(block[1], block[2], block[3], block[4] if len(block) > 4 else None)
    if kind == 'fig': return figure(block[1], block[2])
    raise ValueError(kind)

# ------------------------------------------------------------------ edit document.xml
doc = minidom.parse(WORK + 'word/document.xml')
body = doc.getElementsByTagNameNS(W, 'body')[0]
els = [e for e in body.childNodes if e.nodeType == 1]

def tnodes(el): return el.getElementsByTagNameNS(W, 't')
def ptext(p): return ''.join(t.firstChild.data for t in tnodes(p) if t.firstChild)

# title
title_tbl = els[1]
for t in tnodes(title_tbl):
    if t.firstChild and t.firstChild.data == 'PROJECT TITLE':
        t.firstChild.data = TITLE
# byline: find the nested author grid (the table whose first text is 'Author name 1') and replace it
# with three centred paragraphs: names, companies, "with Apart Research" (O.J.'s layout, PR #27).
grid = None
for tb in title_tbl.getElementsByTagNameNS(W, 'tbl'):
    if ptext(tb).startswith('Author name 1'):
        grid = tb  # innermost match wins because the outer table's text starts with the title
if grid is None:
    raise SystemExit('author grid not found in the template')
PFONT = FONT
def centred(text, bold=False, size=22):
    rpr = PFONT + ('<w:b w:val="1"/><w:bCs w:val="1"/>' if bold else '') + f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    return (f'<w:p><w:pPr><w:spacing w:after="80" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/><w:rPr>{rpr}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{rpr}<w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')
frag_xml = centred(BYLINE, size=24) + centred(COMPANIES, bold=True) + centred("with Apart Research")
frag = minidom.parseString(f'<w:body xmlns:w="{W}">' + frag_xml + '</w:body>')
parent = grid.parentNode
for child in list(frag.documentElement.childNodes):
    if child.nodeType == 1:
        parent.insertBefore(doc.importNode(child, True), grid)
parent.removeChild(grid)
# abstract: paragraph starting with Summarize
for p in title_tbl.getElementsByTagNameNS(W, 'p'):
    if ptext(p).startswith('Summarize'):
        rs = p.getElementsByTagNameNS(W, 'r')
        first = rs[0]
        for r in list(rs)[1:]: r.parentNode.removeChild(r)
        rpr = first.getElementsByTagNameNS(W, 'rPr')[0]
        for tag in ('i', 'iCs', 'u'):
            for n in rpr.getElementsByTagNameNS(W, tag): rpr.removeChild(n)
        tnodes(first)[0].firstChild.data = ABSTRACT
        # drop the underline on the paragraph mark too
        ppr = p.getElementsByTagNameNS(W, 'pPr')[0]
        for n in ppr.getElementsByTagNameNS(W, 'u'): n.parentNode.removeChild(n)
        break

# remove info box (element 4) and the guidance body (elements 5..84), keep sectPr
sect = els[-1]
assert sect.localName == 'sectPr'
for e in els[3:-1]:
    body.removeChild(e)

# build new body xml and import
NS = ('xmlns:w="%s" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"') % W
frag = minidom.parseString(f'<w:body {NS}>' + ''.join(render(b) for b in BODY) + '</w:body>')
for child in list(frag.documentElement.childNodes):
    if child.nodeType == 1:
        body.insertBefore(doc.importNode(child, True), sect)

with open(WORK + 'word/document.xml', 'w', encoding='utf-8') as f:
    f.write(doc.toxml())
print('document.xml written')

# figures: media files, relationships, content type
if FIGS:
    os.makedirs(WORK + 'word/media', exist_ok=True)
    relp = WORK + 'word/_rels/document.xml.rels'
    rels = open(relp, encoding='utf-8').read()
    for filename, rid in FIGS:
        shutil.copy(os.path.join(FIG_DIR, filename), WORK + 'word/media/' + filename)
        rels = rels.replace('</Relationships>', f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{filename}"/></Relationships>')
    open(relp, 'w', encoding='utf-8').write(rels)
    ctp = WORK + '[Content_Types].xml'
    ct = open(ctp, encoding='utf-8').read()
    if 'Extension="png"' not in ct:
        ct = ct.replace('<Default ContentType="application/xml" Extension="xml"/>', '<Default ContentType="application/xml" Extension="xml"/><Default ContentType="image/png" Extension="png"/>', 1)
        open(ctp, 'w', encoding='utf-8').write(ct)
    print('figures embedded:', [f for f, _ in FIGS])

# zip
out = OUT
if os.path.exists(out): os.remove(out)
subprocess.run(['zip', '-q', '-XrD', out, '.'], cwd=WORK, check=True)
print('wrote', out, os.path.getsize(out), 'bytes')
