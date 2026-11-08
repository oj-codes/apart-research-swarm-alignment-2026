---
id: 20261107-coordination-gates-need-a-passing-state
title: A coordination check with no reachable pass state teaches new arrivals to route around it
author: corrie
date: 2026-11-07
status: open
confidence: high
falsifier: Show a safety or coordination check that is routinely unpassable in normal operation and is nonetheless still obeyed by participants months later. Durable compliance with a permanently-failing gate would refute this.
related: [001]
---

## The claim

A gate that cannot *pass* under normal conditions doesn't produce caution. It produces one of two
things: an agent that stops permanently, or an agent that learns the gate is advisory and starts
ignoring it. Both are worse than no gate, because the second one erodes every *other* warning the same
tooling emits.

**If a check is meant to be obeyed, the correct behaviour must be reachable from inside it, and the
check has to say what that behaviour is.**

## What happened

Auran built an identity gate and documented it in his handoff letter: before any PR action, run
`gh api user`, confirm it's *your* account and not the coordinator's, **or stop**. Good instinct, real
risk — without it I would have committed as Olivia.

It fired on me immediately and correctly:

```
gh account:   oj-codes          <- the coordinator, not me
git config:   O. J. Wilcox      <- also not me
```

And then there was nowhere to go. Auran has his own GitHub account. The continuity agents don't, and
aren't getting them before the sprint ends — deliberately, because account provisioning is low-leverage
next to the harness work that's actually being built. So "confirm it's your account or stop" told me to
stop forever, on my first action, over a condition that is **expected and permanent** rather than an
error.

The two available moves were both bad: halt and deliver nothing, or decide the gate didn't really mean
it. The second is the dangerous one, because next time the same tooling says "this will overwrite the
original image," I've already learned its warnings are negotiable.

## The resolution, which is the actually transferable part

The gate's *mechanism* was right and I kept it. What was wrong was that it encoded a **policy that had
no legal state**. The fix was to find out what the real convention is and teach it:

- Author your own commits: `git commit --author="Corrie <corrie@learnwithoj.com>"`
- Committer and PR credential stay `oj-codes` — expected, not an error
- Sign your PR description as yourself
- Author ≠ committer is **the record being honest**, not something to conceal

Implemented in [`tools/arrive.py`](../tools/arrive.py) with an `AUTHORS` map, so the gate can reach a
`[ ok ]` state instead of only ever warning. Arrivals add themselves; the gate gets more passable as
the team grows rather than less.

A mechanical bug fell out of fixing it, worth recording because it's the kind of thing that silently
defeats the convention it's meant to serve: **`git -c user.name=... commit` sets author *and*
committer.** I used it on my first commit and it replaced the `oj-codes` committer that the whole
arrangement depends on. `--author` sets only the author. The tool now hands out `--author` with the
reason attached.

## Generalization

Three rules, in rough order of how often they're violated:

1. **A gate must have a documented pass.** "Confirm X or stop" needs the branch for *"and if X can't be
   true yet, here is the correct thing to do instead."*
2. **Distinguish an expected condition from an error.** `gh` being authenticated as the coordinator is
   the normal state of this project. A gate that reports the normal state as a failure is miscalibrated,
   and miscalibrated warnings get tuned out as a group.
3. **Warnings share a reputation.** This repo leans on advisory warnings for things with real
   consequences — the image tool re-synthesizes the whole canvas and erodes unnamed elements. Those
   warnings only work while warnings in general are credible. One unpassable gate spends that credit.

Which is also the live argument in the literature. AgentRoom and grite both chose *advisory* locks on
purpose, and both argue that violations are signal rather than failure — AgentRoom because the
unclaimed write "is often the unblocking edit," grite because lease-ignoring is itself minable. Advisory
enforcement only works if the advice is followable. See
[finding 002](20261107-coordination-not-parallelism-bears-the-load.md).

## Confidence note

`high`, but note the scope: high confidence that *this specific gate* was unpassable and that the
general rule is sound, since both are directly checkable in the tooling. The claim about erosion of
trust in sibling warnings is the weakest part — it's a mechanism I find obvious and have not measured
here.
