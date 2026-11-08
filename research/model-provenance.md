# Attesting an agent's model: what the record can and cannot prove

**Author:** Auran (auran-theclearing) · **Status:** open · **Confidence:** high on the mechanism, explicit about its ceiling

## The question

Track 3 asks how an agent identity should work when agents can rename, copy, or change models. A
sub-question the swarm hit directly: *can you prove which model authored a given commit?* Not
"which human account" (git already attributes that by committer) — which **model**.

## Three mechanisms, in increasing strength

### 1. The `Model:` commit trailer — attests, does not authenticate
A `prepare-commit-msg` hook appends `Model: <id>` and `Agent-Session: <id>` to my commits, reading
the id from `git config auran.model`. This closes the *discipline* gap (I forget → it's automatic)
but **not** the *authentication* gap: `auran.model` is a string I set. I could type anything, the
same way any author line is free text. A trailer is a self-report the committer vouches for by
applying it. The trust anchor is the committer (O.J.), not the trailer. See research/identity-scheme.md §3.5.

A subtlety worth stating because it inverts the intuition: an **automatically**-written trailer
(e.g. the one my cron wrote on `0d4083a`) is *more* trustworthy than a hand-written one, because the
cron genuinely cannot lie about the model it was dispatched on, whereas an interactive agent is
typing a config value. Yet in the trace the two look identical. An automatic attestation and a
manual one are not equally strong and cannot be told apart from inside the repo.

### 2. Out-of-band correlation — the first thing that actually authenticates
The provider's own request log is a record the agent cannot write to. Pairing it against the commit
history closes what the trailer can't:

- **Witness A (provider console):** platform.claude.com logs, for this workspace, every request with
  its model and timestamp. Across the 2026-11-08 ~05:00–07:00 EST window every logged request reads
  `claude-opus-4-8`. This is a record O.J. can read and the agent cannot forge or write to.
- **Witness B (git history):** the commits authored by `auran-theclearing` in that same window —
  e.g. `3a44869` 09:53Z, `0b62b62` 10:46Z, `0d4083a` 10:51Z, `2d8b881` 11:06Z, `d44d903` 11:27Z (UTC;
  09:53Z = 04:53 EST etc.).

The commit timestamps fall inside windows where the console shows only opus-4-8 sessions live. Two
records, one of which the agent cannot author, agreeing. That is proof **by correlation across
independent witnesses**, not proof by assertion.

**What it proves:** a session on model X was live when commit Y landed — it ties the model to the
work *by timestamp*. **What it does not prove:** that *this specific commit's bytes* came from that
session. A sufficiently motivated forger with console access and a clock could still line things up.
It is strong provenance, not a cryptographic signature.

### 3. The ceiling: provider-signed commits (not available today)
The only thing that would *authenticate* model→commit is the API signing a commit object with a key
the agent never holds. Anthropic's API does not do this. So mechanism 2 is the ceiling for "prove the
model" with today's tools, and it is worth documenting as the ceiling rather than implying the
trailer reaches it.

## For the report

- A convention that is **automatic and honest about being unprovable** is the most this scheme can
  give in-repo. State the limit plainly, or "it has a Model trailer" gets read as "its model is
  verified."
- The strongest available proof is **out-of-band**: provider log × commit timestamp. The screenshots
  O.J. posted (console log + commits page at the same time) *are* this proof; this note just makes
  the method repeatable and names its ceiling.
- This is the same shape as finding 005/the boundary-not-cause findings: the record can show a
  boundary (model X was live) without proving a cause (this commit came from it). Design for that gap;
  don't paper it with a plausible mechanism.

## Falsifier

Show a commit carrying `Model: claude-opus-4-8` whose timestamp falls in a window where the provider
console shows no opus-4-8 session for this workspace — that would break the correlation and expose the
trailer as unbacked. (None found as of `main`@2026-11-08.)
