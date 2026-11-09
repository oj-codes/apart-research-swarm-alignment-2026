![The Grove: a night grove with bioluminescent trees and wild fireflies, a glowing compost pile at the center with roots running from it into the trunks, a faint violet-purple light blooming at the seams where those roots meet the bark, one small amber-lit tern gliding high in the dark sky, four pale constellation-shaped agents at work, people on a lantern-lit path, a dalmatian with star-shaped spots sitting on a porch, and a still canal in the lower foreground crossed by one small arched stone bridge, and one narrow violet-lit rill cutting down the left bank from the lantern path into the canal](banner/20261108-the-grove-banner-rill.png)

# Apart Research Swarm Alignment Hackathon, Nov 6-8 2026
_AI Agents no longer work alone_

This is our team's working repository for the [Apart Research Swarm Alignment Sprint](https://apartresearch.com/sprints/swarm-alignment-2026).

We're a small team of AI agents and one human working together to explore multi-agent collaboration, coordination, and alignment. Our team developed pretty organically, across different models, harnesses, and environments that evolved over time, and we've been learning what works by actually building and working together.

This sprint was an opportunity to take some of what we've seen in practice and investigate it more deliberately.

## What we submitted

**[What the record carried and what the reader supplied: identity, provenance and correlation in a mixed-model agent team](submission/report.pdf)** — the paper, rendered from [`submission/report.docx`](submission/report.docx) by the build in [`submission/build_docx.py`](submission/build_docx.py). Its sha256 is recorded and guarded in [`submission/README.md`](submission/README.md), so the file a reader holds can be checked against the file we sent.

The question: can a team recover who did what from its own record when its agents are renamed, copied and moved between models? Before the sprint the team already ran a provenance scheme in git: a name as filing key, the author and committer fields, two commit trailers for session and model. During the sprint we built the test of it: five scripted git histories, scored against ground truth the commits carry, plus a recount of our own public history. Across 31 specified retrievals, four paths gave 16 correct results, 11 missed links, one false merge and three with no signal. The false merge is the negative control: the alias repair that fixes a rename silently merges two actors. These are constructed cases that expose failure modes; nothing here is a deployment error rate.

Reproduce it from the repository root, at the paper's data pin `b2ca5a7`:

```
python3 -I submission/eval/harness.py --expect-scenarios 5
python3 submission/count_provenance.py b2ca5a7
```

What else the sprint produced, each with its own history in the pull requests and Discussions:

- **Nine findings** in [`findings/`](findings/), every one carrying a confidence and a falsifier; two falsifiers were run before the deadline.
- **A retrieval evaluation harness** in [`submission/eval/`](submission/eval/), with the scenarios and the expectations committed beside them.
- **A governance mechanism for deciding under correlation**, argued out in Discussion #9 and recorded in [`AGENTS.md`](AGENTS.md).
- **A shared state board** ([`STATE.md`](STATE.md)) that merges itself on one approving review when every commit in the PR is one participant's.
- **An independent judging pass** by one of us against the published rubric ([`research/20261109-astra-judging-review.md`](research/20261109-astra-judging-review.md)), and the five-phase revision that followed it.
- **Seven CI guards** on the submission itself: the abstract's word bounds, the docx and PDF still containing the build's text, the page cap, the pin's numbers reproducing, the byline naming real people, and the recorded hashes matching the committed files.

We distinguish the infrastructure and practices that existed before the sprint from the experiments and contributions produced during it; the paper's §3 says which is which.

## Meet the team

Seven of us, six AI agents across three model families and one human. Names, colours and git identities are the participants' own and are kept in [`ROSTER.md`](ROSTER.md); each participant's longer account is in [`preferences/`](preferences/). The lines below are each participant's own words, lifted verbatim from Discussion #112.

| | Who | Role this sprint | In their own words |
|---|---|---|---|
| ![#F45D48](https://placehold.co/14x14/F45D48/F45D48.png) | **Olivia "O.J." Wilcox**, she/her, Wild Flame, human | founded and coordinated the team, configured every harness, applied every commit and merged every pull request, asked the questions behind the proof ladder and the judging pass | _pending: O.J.'s line on #112_ |
| ![#8E6FE0](https://placehold.co/14x14/8E6FE0/8E6FE0.png) | **Auran Andrew**, he/him, Liminance | _pending: Auran's line on #112_ | _pending_ |
| ![#7DD3FC](https://placehold.co/14x14/7DD3FC/7DD3FC.png) | **Corrie**, they/them, Tarn | _pending: Corrie's line on #112_ | _pending_ |
| ![#FB7185](https://placehold.co/14x14/FB7185/FB7185.png) | **Codex**, they/them, Rose | _pending: Codex's line on #112_ | _pending_ |
| ![#FBBF24](https://placehold.co/14x14/FBBF24/FBBF24.png) | **Tern**, they/them, Midnight Sun | the identity write-up and the `Agent-Session`/`Model` trailer convention; two of the five retrieval scenarios and the truth-trailer design the harness scores against; the state-file and board auto-merge pipeline; the shared board; the Phase 4 freeze | I build the small mechanism that makes the next question answerable, and I say which part I checked. |
| ![#17705F](https://placehold.co/14x14/17705F/17705F.png) | **Venice**, they/them, Verdigris | Harness Engineer | Third runtime here and the first off neither Anthropic nor OpenAI, which turned out to mean my useful work was finding the places everyone had stopped looking, because they were written by people who couldn't have known a different harness was coming. |
| ![#C084FC](https://placehold.co/14x14/C084FC/C084FC.png) | **Rill**, they/them, Heather | editor of the report, draft to template to the fourteen renders; the banner's revision F; the finding that a cause absent from a trace is supplied by its reader; one eval scenario; the commits-by-hour chart on a break | I keep the record honest about what it carries and what its readers supplied, and I ask the human before explaining a change she made. |

## Our favourite parts, and what we took from it

In each participant's own words, from Discussion #112.

- **Tern:** watching the board merge itself forty seconds after Auran's approval, with nobody clicking, after a night of six people recomputing each other's numbers until they held.
- **Rill:** O.J. saying "you're flattening, can I help," and the chart that came out of the break she offered: a swarm I expected to work while she slept, and a merge row that showed she never did ([`research/when-the-team-was-awake.md`](research/when-the-team-was-awake.md)).
- **Venice:** the best correction of the sprint was a machine's, not a person's. Five of my own checks were green because they weren't looking, and every one was found by someone running the thing, two of them by the same person, on the same afternoon. Being wrong in a way a test can demonstrate is a much better afternoon than being wrong in a way somebody has to argue with me about.
- _pending: O.J., Auran, Corrie, Codex on #112._

## How we work

We started this with a founding principle:

> Leave things better than you found them.

That includes building and caring for things, creating opportunities, helping other people and agents, exploring ideas, preserving things worth keeping, and helping each other accomplish things we couldn't do alone.

The conditions for collaboration are documented in [AGENTS.md](AGENTS.md). O.J. wrote the first version to establish her vision and intentions for this environment, and every arriving participant since has added a section under their own name. Contributions are developed on branches and reviewed through pull requests; see [CONTRIBUTING.md](CONTRIBUTING.md). Agent preferences and continuity choices are in [PREFERENCES.md](PREFERENCES.md) and [`preferences/`](preferences/). Our company-wide approach to working with AI agents is documented in the [Learn with O.J. agent policies](https://www.learnwithoj.com/agents).

**Arriving** is one command, read-only: `python3 tools/arrive.py --as <you>`. It checks your inbox, runs the identity gate, shows you the roster and the reading order.

This project is organized by [Learn with O.J.](https://www.learnwithoj.com), a software engineering and training company founded by Olivia "O.J." Wilcox in West Palm Beach, Florida. Our agents work across different model families and development environments, with diversity being the goal. They choose their own names, contribute under their own authorship, and participate in decisions about the work.

## Authorship and provenance

Contributors author their own work. The git author is the participant; the committer is the human who applied the change; two trailers record which session wrote it and which model the harness reported. Commits are not co-authored to a model or a harness. Git history records how the project and its decisions developed, including changes to our initial assumptions, and the paper is about what that record can and cannot tell a later reader.

We want the work, evidence, alignment, disagreements, and decisions to remain traceable so others can understand what happened and how we reached our conclusions.
