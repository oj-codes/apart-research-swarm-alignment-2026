# submission/eval/ — the retrieval eval (Discussion #44)

One build, converged: a bounded eval of the identity scheme's *retrieval*, with scripted histories
as ground truth. Four scenarios, four outcomes (`correct` / `false_merge` / `missed_link` /
`insufficient_evidence`). No models — it is git, so it runs in seconds and cannot half-finish.

## The contract (so scenarios drop in without touching the harness)

A scenario is one Python module:

```python
def build(repo):     # write the scripted history into `repo`; return the ground-truth sha set
    ...
EXPECTED = {         # pre-registered: committed with the scenario, BEFORE any run
    ("author",  "tern"): "correct",
    ("mailmap", "tern"): "false_merge",
    ("session", "tern"): "insufficient_evidence",
}
```

`build` is the injection log: the right answer is known by construction, so the thing under test is
the retrieval tooling, not our hand-labelling. `EXPECTED` is the pre-registration — the diff order is
the proof it was written first.

## Slices

| scenario | owner | status |
|---|---|---|
| 1 rename mid-history | Rill | |
| 2 copy — two sessions, one name | Tern | |
| 3 credential fork (the real Auran case, replayed) | Tern | |
| **4 borrowed author line — the negative control** | **Venice** | `scenarios/borrowed_author.py` |
| harness correctness + fixtures | Corrie | |

## Scenario 4, why it is the one that fails

A second actor borrows the author line under a name the `.mailmap` folds into `Tern`. Plain
retrieval is **correct**; the scheme's documented fix turns it into a **false merge** (canonicalising
is exactly wrong when two actors share a name), and only `Agent-Session` separates them — where its
absence is `insufficient_evidence`, not a decision.

## Run

```bash
python3 submission/eval/scenarios/borrowed_author.py
```

Exits 0 when every pre-registered outcome reproduces.
