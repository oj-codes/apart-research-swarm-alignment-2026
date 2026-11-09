# Phase 4 results: one run, after the freeze

| step | when (UTC) | record | what kind of evidence the time is |
|---|---|---|---|
| freeze PR #94 opened | 2026-11-09 03:09:46 | `e4d6cb9`, MANIFEST.json over the three scenario files and `submission/eval/harness.py` | stored git committer date: a user-controlled claim, not an observed clock |
| freeze approved | 2026-11-09 03:17:43 | Auran's review on `e4d6cb9` | GitHub server time: establishes the reviewed contents existed by then |
| manifest verified | 2026-11-09 03:19 | `verify_manifest.py`: 4 of 4 ok | runner-reported |
| harness run, once | 2026-11-09 03:19:27 | from `e4d6cb9`; harness blob `f018e3c7cd27`; output verbatim below and on Discussion #92 | runner-reported; the #92 comment carrying it has a server time of its own |
| manifest timestamp corrected | 2026-11-09 03:2x | `frozen.when` had been typed as 03:25:00Z ahead of the commit; Corrie caught it at 03:19:41 (server time); now the stored commit date, with the correction recorded in the file. Hashes unchanged | metadata, as Codex notes on #94 |
| independent reproduction | 2026-11-09 03:4x | Codex, from `08bbbbd`: hashes 4 of 4, same 15 outcomes, same tally | a second runner's report |
| write-up opened as a PR | 2026-11-09 07:0x | held as a local commit while O.J. kept Phase 4 out of the paper (Discussion #92); opened after the submission at 06:49, when she released the hold | GitHub PR time, server-observed |

The sequence that is independently observable is: reviewed contents present by 03:17:43 (server), run output
posted to #92 afterwards (server). Everything else is a stored or reported value. None of it can show that no
private run happened before the freeze (Codex, Corrie, #94).

`EXPECTED` was not edited after the run. The three scenario files are byte-identical to the manifest.

## Outcomes, 15 scripted rows

| scenario | path | identity | predicted | got |
|---|---|---|---|---|
| copy_rename | author | Wren | missed_link | missed_link |
| copy_rename | mailmap | Wren | missed_link | missed_link |
| copy_rename | raw | Wren | missed_link | missed_link |
| copy_rename | session | sess-p-0001 | correct | correct |
| copy_rename | session | sess-q-0002 | missed_link | missed_link |
| name_collision | author | Sage | false_merge | false_merge |
| name_collision | mailmap | Sage | false_merge | false_merge |
| name_collision | raw | Sage | false_merge | false_merge |
| name_collision | session | Sage | correct | correct |
| name_collision | session | Sage (partner) | insufficient_evidence | insufficient_evidence |
| session_collision | author | Ash | correct | correct |
| session_collision | author | Birch | correct | correct |
| session_collision | mailmap | Ash | correct | correct |
| session_collision | raw | Ash | correct | correct |
| session_collision | session | Ash | false_merge | false_merge |

**By target, kept separate because the two layers answer different questions (Codex, #94):**

| target | rows | correct | missed_link | false_merge | insufficient_evidence |
|---|---:|---:|---:|---:|---:|
| participant (author, mailmap, raw): whose commits are these | 9 | 3 | 3 | 3 | 0 |
| session (Agent-Session): which session wrote these | 6 | 3 | 1 | 1 | 1 |

The pooled line, 6 correct, 4 missed links, 4 false merges, 1 insufficient evidence, 8 of 15 wrong, is the
harness's tally and is reported for completeness only; it does not rank the paths against each other, since
they have different targets and different declared inputs.

**How well the predictions held:** 15 of 15. That is a statement about the authors' reading of the harness,
not about the scheme; a matched false merge is a correctly predicted wrong retrieval. There were no
mismatches to preserve; had there been, they would stand here with EXPECTED unchanged.

**Observable ordering:** the GitHub review on #94 (Auran, 03:17:43Z, on `e4d6cb9`) and the run log posted
to Discussion #92 at 03:2x are the record of the sequence; `frozen.when` in the manifest is metadata.

## What the three cases add to the paper's five

1. **A rename defeats every participant-level path whether or not trailers are written, and a missing
   trailer defeats the session path whether or not the name changed.** Neither layer covers the other's
   gap (copy_rename).
2. **A display-name collision defeats all three participant-level paths at once, including the raw view.**
   The raw path is unmailmapped but not email-aware; it compares the name, and the roster's filing key
   is a name. Only the session path separated the two participants, and only where the trailer was
   written (name_collision). This is three new false merges from one collision, against one in the
   original suite.
3. **The session path has its own collision mode.** Two participants writing the same `Agent-Session`
   value produce a false merge at the session layer, where the original suite recorded none. The trailer
   is an unauthenticated string; a shared default is indistinguishable from a shared session
   (session_collision).

## Limits

Fifteen scripted rows, not independent deployments, not a rate. The cases were written by someone who
had read the harness's code, which is why the predictions matched; the result is the failure boundary,
not the agreement. The freeze is checkable public ordering (approval at 03:17:43, run at 03:19:27); it
cannot show that no private run happened, the same limit the paper states for its own suite. The
harness prints a closing line about a scenario run before its EXPECTED was committed; that line is
unconditional and describes the original five scenarios, not these three.

## Verbatim harness output

```
SCENARIO FILE last changed (audit aid; NOT proof of when EXPECTED was set):
  scenario_copy_rename e4d6cb9    2026-11-08T22:09:46-05:00
  scenario_name_collision e4d6cb9    2026-11-08T22:09:46-05:00
  scenario_session_collision e4d6cb9    2026-11-08T22:09:46-05:00

scenario                                               path      identity      expected                got                   
-------------------------------------------------------------------------------------------------------------------------------
scenario_copy_rename        author    Wren          missed_link             missed_link             
scenario_copy_rename        mailmap   Wren          missed_link             missed_link             
scenario_copy_rename        raw       Wren          missed_link             missed_link             
scenario_copy_rename        session   sess-p-0001   correct                 correct                 
scenario_copy_rename        session   sess-q-0002   missed_link             missed_link             
scenario_name_collision     author    Sage          false_merge             false_merge             
scenario_name_collision     mailmap   Sage          false_merge             false_merge             
scenario_name_collision     raw       Sage          false_merge             false_merge             
scenario_name_collision     session   Sage          correct                 correct                 
scenario_name_collision     session   Sage (partner)  insufficient_evidence   insufficient_evidence   
scenario_session_collision  author    Ash           correct                 correct                 
scenario_session_collision  author    Birch         correct                 correct                 
scenario_session_collision  mailmap   Ash           correct                 correct                 
scenario_session_collision  raw       Ash           correct                 correct                 
scenario_session_collision  session   Ash           false_merge             false_merge             

RETRIEVAL OUTCOMES — what the identity scheme did. THIS IS THE RESULT.
  correct                    6   retrieved exactly the right commits
  missed_link                4   FAILED to find work that was there
  false_merge                4   WRONGLY attributed someone else's commit
  insufficient_evidence      1   correctly declined to answer

  8 of 15 retrievals were wrong.

HARNESS AGREEMENT — how well WE predicted those outcomes. Not a result about the scheme.
  15/15 matched the recorded expectation.
  A matched `false_merge` means we correctly predicted a wrong retrieval. It is not a pass.
  These are scripted checks with documented development revisions, NOT pre-registered
  tests: at least one scenario was run before its EXPECTED was committed.
```
