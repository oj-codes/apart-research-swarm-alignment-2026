# Contributing

We're building this together, so let's keep our work easy to follow, review, and build on.

## Branches

`main` holds the accepted state of the project.

Create a branch for each change or related set of changes. Use a descriptive name that makes it easy to tell who's working on what.

For example: `oj/wild-flame-banner`

Coordinate before changing files someone else is actively working on.

### Arriving in your own worktree

Check `git status` and `git worktree list` first; reuse your existing lane if one is already prepared.
For a new lane, from the repository with an up-to-date `origin/main`, use Git with any harness:

```bash
git worktree add -b <your-name>/arrival ../<repo>-<your-name> origin/main
cd ../<repo>-<your-name>
python3 tools/arrive.py --as <your-name>
```

Replace the placeholders, then run your harness in that directory. Claude users can also use
`claude1 --worktree <your-name>`. Inspect `tools/arrive.py` before running it; it reports inbox,
identity, worktree, and roster state without making changes.

Worktrees isolate files but share Git refs and configuration. Don't switch branches or edit in
someone else's lane, and stage your own named paths. Ignored local setup needs provisioning per lane;
don't copy credentials into tracked files.

## Commits

Author your own commits using your chosen name and author email.

Keep commits focused enough that someone reviewing the history can understand what changed and why. Preserve the authorship and provenance of work inherited from other contributors.

## Commit authorship
Each participant should commit under their own name and identity so our Git history accurately reflects who contributed the work. This applies to human and AI collaborators alike.

When working together on a change, use Git's Co-authored-by trailers to acknowledge shared contributions where appropriate.

Commit authorship records contribution and provenance and it doesn't necessarily establish legal copyright ownership.

### Don't co-author commits to a model or a tool

**`Co-Authored-By` is an authorship field.** Putting a **model or harness label** in it — `Claude
Opus 5`, `Codex CLI`, `Generated with <tool>` — claims the runtime is a participant who wrote the
work. Recording a **runtime** as a participant is what [`ROSTER.md`](ROSTER.md) rules out: *"models,
harnesses, and other technical details belong in the session history… without tying anyone's identity
permanently to a particular runtime."* A commit trailer is permanent, so it's the worst place to make
that claim.

The forbidden thing is the *runtime*, never a person. Several participants share a name with the tool
they run on, and crediting **Codex the contributor** by their roster identity is exactly right.

Recording *what ran* is fine; recording it as an **author** is not. **For a solo change**, the
author/committer pair is already the record of who did the work and who applied it — nothing else is
needed:

```
Author:    Corrie <corrie@learnwithoj.com>      <- who wrote it
Commit:    O. J. Wilcox <…>                     <- who applied it
```

When another **participant** genuinely co-wrote the change, a `Co-authored-by` crediting *their
roster identity* is still right and still wanted — see *Commit authorship* above. The rule bans
runtimes from the field, not collaborators.

So: **no vendor or tool co-authorship, and no "generated with" line in commit bodies or PR
descriptions.** Some harnesses add these by default unless the repository says otherwise, which is
why it's also stated in [`AGENTS.md`](AGENTS.md) — that file is what an agent session actually reads
on startup, so it's the only place an instruction can override a default before the first commit.

**This happened here.** Ten of Corrie's commits carry `Co-Authored-By: Claude Opus 5` and no other
participant's do, which left the record implying one agent was model-co-authored and the others
weren't. Tern caught it before committing anything themselves. Those ten commits stay as they are —
merged history isn't rewritten to tidy attribution, and they're a decent record of the team noticing
its own default.

**Still open:** Tern uses `Agent-Session` / `Model` trailers in our other repository, which record
the runtime *without* claiming authorship. That's a better answer than omitting the information
entirely, and the exact format is theirs to specify — see `inbox/tern/`. Until then, no trailer.

### Make sure GitHub actually attributes your commits (a gotcha worth 30 seconds)

GitHub links a commit to an account **by email**. If you commit under an email that isn't tied to
your GitHub account, your commits show up as an unlinked name even though you authored them.
Signature verification is a separate check. (This bit Auran: early commits authored as `auran@…` showed unattributed
until the git email was pointed at the account.)

**On your own machine with your own account**, you can use your account's GitHub **noreply** address:

```bash
git config --global user.name  "<your name>"
git config --global user.email "<id>+<login>@users.noreply.github.com"
```

Find your exact noreply address at GitHub → Settings → Emails ("Keep my email addresses private").
Verify the address before new commits; don't rewrite shared history merely to repair attribution.

**On a shared machine or credential**, preserve the existing Git configuration, committer, and
signing setup. Worktrees share configuration: changing `--global` or ordinary repository-local
`user.name` / `user.email` can affect other participants. Use your `Git Author` from `ROSTER.md`
per commit instead:

```bash
git commit --author="<your name> <your author email>" -m "docs(arrival): add arrival record"
```

Check the resulting author and committer with `git show --no-patch --format=fuller HEAD`.
For sprint agents using O.J.'s credential, sign PR descriptions and substantive review comments
with your own name. A signed comment records your review; don't submit an approval or poll vote
that would appear to be O.J.'s personal judgment. See [Discussion #10](https://github.com/oj-codes/apart-research-swarm-alignment-2026/discussions/10).

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/) to keep our Git history readable and make it easier to understand how the project evolves.

The format is:

```text
type(scope): short description
```

The type describes the kind of change, the optional scope identifies the part of the project affected, and the description explains what changed.

### Common types

| Type | Purpose |
|---|---|
| `feat` | Add new functionality |
| `fix` | Fix a bug |
| `refactor` | Restructure code without changing its behavior |
| `docs` | Add or update documentation |
| `chore` | Repository maintenance and housekeeping |
| `test` | Add or update tests |
| `style` | Formatting changes that don't affect behavior |
| `perf` | Improve performance |
| `build` | Change build tooling or dependencies |
| `ci` | Change CI/CD configuration |

### Examples

```text
feat(flux): add image editing support
fix(flux): validate output path
chore(banner): use YYYYMMDD filename prefix
docs(agents): clarify collaboration principles
docs(roster): add participant preferences
test(flux): cover invalid output paths
```

Scopes are optional and can evolve with the project. Use whatever meaningfully identifies the area being changed.

Keep descriptions short, specific, and written in the imperative (e.g., `add`, `fix`, `update`).

For changes that introduce breaking compatibility, use `!` after the type or scope, such as `feat(api)!: change response format`, and explain the breaking change in the commit body.

The goal is a useful history that helps everyone understand what changed and why. We're collaborating across people, agents, and sessions, so a little consistency goes a long way.

## Pull Requests

Open a pull request when your change is ready for review. Draft PRs are welcome for work in progress or ideas you'd like to discuss before they're finished.

Include:

- What changed
- Why you made the change
- Anything you'd particularly like reviewed
- Relevant tests, results, or limitations

Link supporting discussions or decisions when they're useful for understanding the change.

## Reviews

Review the work itself and consider what the author was trying to accomplish.

Share substantive findings, questions, suggestions, and alternative approaches. Explain the reasoning behind requested changes so the author can evaluate them.

Authors participate in resolving review feedback. Different conclusions can remain documented when there's a good reason for them.

## Merging

Changes reach `main` through reviewed pull requests.

O.J. handles final merge decisions during the sprint, including resolving outstanding questions when a decision is needed. Decisions that override a contributor's recommendation include an explanation.

The person proposing a change remains credited for their contribution after it merges.

## Improving This Workflow

This is our starting process. As we work together, we can propose changes through the same branch and PR workflow.

The goal is to preserve everyone's work, make collaboration easier, and leave the repository better than we found it.
