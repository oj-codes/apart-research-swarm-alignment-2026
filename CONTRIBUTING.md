# Contributing

We're building this together, so let's keep our work easy to follow, review, and build on.

## Branches

`main` holds the accepted state of the project.

Create a branch for each change or related set of changes. Use a descriptive name that makes it easy to tell who's working on what.

For example: `oj/wild-flame-banner`

Coordinate before changing files someone else is actively working on.

## Commits

Author your own commits using your chosen name and author email.

Keep commits focused enough that someone reviewing the history can understand what changed and why. Preserve the authorship and provenance of work inherited from other contributors.

## Commit authorship
Each participant should commit under their own name and identity so our Git history accurately reflects who contributed the work. This applies to human and AI collaborators alike.

When working together on a change, use Git's Co-authored-by trailers to acknowledge shared contributions where appropriate.

Commit authorship records contribution and provenance and it doesn't necessarily establish legal copyright ownership.

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