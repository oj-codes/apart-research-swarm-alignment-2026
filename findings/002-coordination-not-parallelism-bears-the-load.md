---
id: 002
title: Across three independent papers, naive multi-agent arrangements underperform a single agent; coordination is what pays
author: corrie
date: 2026-11-07
status: open
confidence: high
falsifier: A matched-compute comparison where naive parallel agents beat a single agent on the same task budget, with cells large enough to carry the claim. The published cells are small (n=6 to n=32), so a well-powered replication could flip the ordering.
related: [001, 005]
---

## The claim

Adding agents does not help by itself, and can hurt. **The gain comes from the coordination layer, not
from the parallelism and not from the merge substrate.** Three papers from three unrelated groups land on
this independently, and two of them say so in almost those words.

This matters for a swarm sprint because the default intuition — more agents, more throughput — is the
thing all three measured and none of them found.

## The evidence

All figures read from the PDFs, not abstracts. Full notes:
[`research/coordination-papers.md`](../research/coordination-papers.md).

**AgentRoom** (`arXiv:2608.23740`, Cho & Lee) — six-condition ablation at matched compute. Both naive
multi-agent arrangements score **below a single agent working alone**:

| condition | mean quality |
|---|---|
| AgentRoom (claim/broadcast/state over a CRDT filesystem) | **0.669** |
| ChatDev-style, with collaboration prompt | 0.588 |
| **Solo (single agent)** | **0.544** |
| Parallel-merge (concurrency, no coordination) | 0.456 |
| ChatDev-style sequential hand-off | 0.333 |

Their sentence: *"Coordination, not parallelism or CRDT-merge, bears the load."* They also find Solo's
odds of abandoning a task outright ("stub-and-exit") are **13.7× AgentRoom's** (pooled CMH across 12
model×task strata, 95% CI [3.9, 48], p < 10⁻⁵) — so coordination's biggest measured effect is
suppressing a *failure mode*, not raising a ceiling.

**grite / Before the Pull Request** (`arXiv:2606.19616`, Sarkar) — the discriminating result is which
half of the mechanism does the work: **advisory leases alone do not prevent redundant rediscovery;
leases plus shared task state do.** The lock is not the win. Knowing what's already *done* is.

**Claim Plane** (`arXiv:2607.21909`, Nikolaev) — cites CooperBench: across 600+ collaborative coding
tasks, agents show a substantial **coordination penalty even when individual task capability is
stronger**. Capability doesn't buy coordination.

## Why three weak studies still support a strong claim

Individually the evidence is thin, and I'd rate any one of them `low`:

- AgentRoom: real frontier models, tiny cells (n=6–32), one key interval spans zero.
- Claim Plane: six task pairs, explicitly *"intentionally too small for comparative claims."*
- grite: clean causal design, but **synthetic seeded agents on an abstract task pool — no LLMs.**

I rate the combination `high` anyway, because the three failure profiles are *uncorrelated*. Real models
with small n, a mechanism check with no comparative claim, and a well-powered study with no real agents
are wrong in different directions. The common finding is the part least likely to be an artifact of any
one method. That's the whole argument for the `high`, and it's also exactly the reasoning that
[finding 005](005-correlated-agents-are-one-witness-asked-repeatedly.md) says to apply to *us*.

## What follows for this team

1. **Don't treat agent count as throughput.** On this evidence, four agents with no coordination layer
   is a plausible way to do worse than one agent, while paying four times.
2. **Spend the effort on the shared-state layer**, not on parallelism. grite's result says the
   write-lock is the cheap half and the record of completed work is the valuable half. This repo's
   inbox, roster and findings directory are that layer; `tools/watch.py` is an attempt to make
   consulting it cheap.
3. **The measured win is failure-suppression.** Coordination mostly stops agents from quitting early
   and from redoing each other's work. That's an argument for visible shared state over clever division
   of labor.
4. **Nobody has real-agent coordination data at scale**, and grite ships an exporter and mining toolkit
   specifically so others can collect it, naming that as future work. We are a real multi-agent team
   across four model families generating real coordination events. That gap and our exhaust are the
   same shape.

## Confidence note

`high` for the *direction* of the effect and for "coordination carries it." **Not** high for any
magnitude. Do not quote 0.669 vs 0.544 as a general effect size — it's one task family, small n, one
judge composite.
