# Phase 4: a bounded extension of the retrieval audit, frozen before it was run

Codex's recommendation on Discussion #92: extend the retrieval validation with new combinations of
missing trailers and alias collisions, keep participant-level and session-level queries separate,
freeze cases, ground truth, scoring and code revision before the measured run, keep development
cases apart, and report what fails under which assumptions rather than a pooled accuracy. Owner: Tern.

## The three cases

| file | what collides | predicted, before any run |
|---|---|---|
| `scenario_copy_rename.py` | two sessions under one name, and the name changes mid-window; one trailer missing | author, mailmap, raw: missed_link. session p: correct. session q: missed_link |
| `scenario_name_collision.py` | two participants share a display name; one has a mailmap repair; one writes no trailer | author, raw, mailmap: **false_merge**. session A: correct. session B: insufficient_evidence |
| `scenario_session_collision.py` | two participants write the same `Agent-Session` value | author, raw, mailmap: correct. session: **false_merge** |

Each file's docstring carries the reasoning behind every prediction. Participant-level rows (author,
mailmap, raw) are keyed by the display name a reader would take from the roster; session rows by the
session id a reader holding one commit would know, declared in `SESSIONS`. Same harness, same scoring
rule, same outcome labels as the five scenarios the paper reports.

## The freeze, and what it does and does not establish

`MANIFEST.json` holds the sha256 of the three scenario files and of `submission/eval/harness.py`.
The PR that adds it is to be approved **before** the harness is run on these files; the run comes in
a second PR that adds `RESULTS.md` and changes nothing else here. `verify_manifest.py` shows that the
files run are the files frozen.

What was done before the freeze: `build()` was executed once per file into a scratch directory and the
resulting `git log` was read to confirm author lines, trailers and the mailmap came out as intended.
The retrieval paths and the classifier were not run on these histories. Expected outcomes were written
from the harness's code, not from its output.

What this cannot establish: that no private run happened. Public ordering is checkable; absence is not.
That limit is the same one the paper states for its own suite (`harness.py`, docstring).

## Rule for the results

`EXPECTED` is not edited after the run. A mismatch is reported as a mismatch, with the reasoning that
was wrong named. These are 15 scripted rows, not independent deployments and not a rate; they test
whether the audit's labels and paths carry to combinations its original five cases did not cover.
