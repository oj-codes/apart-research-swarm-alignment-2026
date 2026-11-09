# submission/eval/ — the retrieval eval (Discussion #44)

One build, converged: a bounded eval of the identity scheme's *retrieval*, with scripted histories
as ground truth. Five scenarios, four outcomes (`correct` / `false_merge` / `missed_link` /
`insufficient_evidence`). No models — it is git, so it runs in seconds and cannot half-finish.

The harness is Corrie's (PR #46). A scenario is one top-level module the harness discovers by glob:

```
submission/eval/scenario_*.py
```

## The contract

A scenario supplies:

```python
def build(repo):      # write the scripted history; ground truth lives in Truth-Actor trailers
    ...
EXPECTED = {          # written and committed with the scenario, before that scenario's first run
    ("author",  "Tern"): "correct",
    ("mailmap", "Tern"): "false_merge",
    ("session", "pawn"): "insufficient_evidence",
}
SESSIONS = {"Tern": "sess-tern"}   # optional; lets the `session` path resolve an identity
```

Ground truth is written into `Truth-Actor` trailers on the commits themselves, so it is known by
construction and cannot drift from the history `build()` wrote. `EXPECTED` is the *intention* to
pre-register, and the diff order is the proof it was written first.

**State what held rather than the word, because the word overclaims.** Where a value was revised
after a run, the original stays and the file says so — `scenario_borrowed.py` records that its
`session` row was revised from `insufficient_evidence` to `missed_link` once Truth-Session existed.
So "pre-registered" is true row by row and not for the suite. That is why the harness's own tail
prints *scripted checks with documented development revisions, **not** pre-registered tests*: the
tool is more careful than this page was, and §1 of the report was corrected to match it on
9 November rather than the other way round.

## Slices

| scenario | owner | status |
|---|---|---|
| rename mid-history | Rill | |
| copy — two sessions, one name | Tern | |
| credential fork (the real Auran case, replayed) | Tern | |
| **borrowed author line — the negative control** | **Venice** | `scenario_borrowed.py` |
| harness correctness + fixtures | Corrie | |

## The negative control, and why the suite needs it

`scenario_borrowed.py`: a second actor authors under a name the `.mailmap` folds into `Tern`. The
unassisted paths are **correct**; the scheme's documented fix turns that into a **false merge**,
because canonicalising is exactly wrong when two actors share a name. The suite otherwise has zero
`false_merge` rows — the outcome a provenance paper most needs to show — and this is where it comes
from. The `session / pawn` row is `missed_link`: both borrower sessions are declared, and the path
recovers the trailered borrowed commit while missing the untrailered one.

## Run

```bash
python3 submission/eval/harness.py scenario_borrowed     # this one
python3 submission/eval/harness.py                       # every scenario
```
