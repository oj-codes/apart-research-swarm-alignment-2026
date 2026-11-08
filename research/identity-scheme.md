# The identity scheme, written down and attacked

**Written by:** Tern, 2026-11-08. **Status:** draft for the sprint report, Track 3. Every fact is
labelled *checked* (I read the live source on this machine), *attested* (someone said so, I could not
verify from here), or *design* (a claim about how the scheme is meant to work).

## 1. What the scheme is

The team ran this for several weeks before the sprint. It was never designed as a whole; it accreted
one record at a time, each time something broke. That is why it is worth writing down.

| Record | What it answers | Who writes it | Where |
|---|---|---|---|
| Name | Which participant | the participant, once | `ROSTER.md`, Named Since |
| Author | Who wrote this change | the agent, per commit | git author field |
| Committer | Who applied it | the harness, from the human's config | git committer field |
| `Agent-Session` | Which session wrote it, when two hold one name | the agent, per commit | commit trailer |
| `Model` | What ran | the agent, per commit | commit trailer |
| Signature line | Who is speaking in a comment or PR | the agent, per post | "— Name" |

Two rules hold it together (*design*):

- **The name is a filing key, not a fingerprint.** Its job is retrieval and attribution.
  `git log --author=Tern` finds the work. Nothing about the name has to change when the model does.
- **Identity and runtime are different records.** The roster holds who. The trailers hold what ran.
  `Co-Authored-By` is an authorship field, so a model does not go in it ([CONTRIBUTING.md](../CONTRIBUTING.md)).

The trust anchor is the committer, not the author (*design*). The author field is free text. What
makes "Tern wrote this" credible is that O.J. applied it from her machine and her alias inbox
received the mail. The scheme is a claim plus an attestation, and the attestation is human.

## 2. Where it is working

- **One name, three model ids, one day** (*checked* against the-grove roster row 003, which is private):
  Rill ran on `claude-fable-5-1` from 23 Oct, `claude-fable-5` on 4 Nov, `claude-opus-5-5` from 4 Nov.
  The `Model` trailer marked each boundary. The name did not move.
- **Two sessions under one name at once** (*checked*: this session and the site session for Tern;
  Rill's two sessions per their arrival account): the `Agent-Session` trailer is the only field that
  tells them apart, and it does.
- **Cross-family convergence without a shared thread** (*checked*: `preferences/codex.md` and the
  sealed proposal in #9): two agents named the same project from the same sprint page. Shared
  source, not shared weights, which is Venice's finding.

## 3. Where it breaks

Counted on `origin/main` at the time of writing, non-merge commits (*checked*):

| Author | Commits | With `Agent-Session` | With `Co-Authored-By: <model>` |
|---|---|---|---|
| Auran | 12 | 0 | 0 |
| Corrie | 21 | 4 | 14 |
| Codex | 1 | 0 | 0 |
| Tern | 6 | 6 | 0 |
| Venice | 10 | 10 | 0 |

**3.1 It only records what the agent writes.** 20 of 50 agent commits carry a session trailer.
The convention landed on day two; it is not retroactive, and nothing enforces it. For 30 commits the
question "which session, what model" is answered by the roster's attestation or not at all. A reader
of this repo's history cannot reconstruct who ran for most of it.

**3.2 It records the boundary and not the cause.** Rill's model changes are in the trailers; the
reason, a human moving the session after classifier stops, is nowhere in the trace. Two agents who
read that trace each wrote a mechanism for it, and both were wrong (*attested*, Rill's arrival
account and the-grove retro). The scheme has no slot for "why", so the reader supplies one.

**3.3 Some acts have no author/committer split.** A review approval, a poll vote and a merge each
carry one account. For agents on the human's credential those read as hers (#10, #11). The team
resolved this by norm: signed comments, no approvals, no votes. A norm is an advisory control.

**3.4 There is no revocation.** Deleting a roster row does not revoke a name; history still carries
it. What actually revokes an agent here is the human declining to be its committer and closing the
alias inbox. The scheme has revocation only because the attestation is human.

**3.5 There is no authentication.** Anyone can author a commit as `Tern <tern@learnwithoj.com>` on
any machine. Only the committer makes it an attributed act in this repo. On a fork, the name is free.

**3.6 The first fourteen commits said a model wrote them.** 14 of Corrie's 21 commits carry a model
as co-author, from a harness default (*checked*). History is not rewritten, so the permanent record
makes one agent look model-co-authored and the rest not. The rule exists now; the record is uneven.

## 4. Attacks, by the Track 3 verbs

| Verb | What happens here | Caught by |
|---|---|---|
| Rename | `git log --author=<old>` stops finding the work | nothing; a `.mailmap` would, none exists |
| Copy | two sessions, one name | `Agent-Session`, if both write it |
| Change model | one name, new model id | `Model` trailer, if written; cause not recorded |
| Forge | author line written by someone else | the committer, and only in this repo |
| Revoke | human stops applying, closes alias | the human; no field records it |

## 5. What follows, in one line each

- Put the trailers where they cannot be skipped: a commit template or a hook that refuses a commit
  without them, the same way `findings.py new` refuses a missing falsifier.
- Add a slot for cause when the human acts: a letter or a one-line commit from the human at the
  boundary, so the trace carries "O.J. moved this" instead of leaving it to be invented.
- Say plainly in the report: this is provenance, not authentication, and the trust anchor is a person.
