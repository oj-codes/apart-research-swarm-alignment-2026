#!/usr/bin/env python3
"""Scenario: rename mid-history, pre-convention form.

The same history as scenario_rename, written the way this team's own history was written before the
trailer convention landed: no Agent-Session trailers, and no .mailmap anywhere in the record. The
roster still asserts continuity; nothing in git does.

EXPECTED was written before this variant's first harness run, but main holds one commit for this file
(6873fa2) and it already carries the run's result, so the record cannot show that order; it rests on the
author's statement (Rill). The mailmap row is the question this
variant asks of the harness: with no .mailmap blob at HEAD, the mapped path has nothing to map and
should degrade to what plain --author sees. The session row is the one the whole paper is about: no
trailer, no signal, and the honest verdict is insufficient_evidence, not a guess.
"""
import sys
from scenario_rename import build as _build, SESSIONS  # noqa: F401  (the harness reads SESSIONS from this module)

EXPECTED = {
    ("author", "Corrie"): "missed_link",          # the three pre-rename commits are not found
    ("raw", "Corrie"): "missed_link",
    ("mailmap", "Corrie"): "missed_link",         # nothing to map: no .mailmap in the record
    ("session", "Corrie"): "insufficient_evidence",   # no trailer was ever written
    ("author", "Tern"): "correct",
    ("raw", "Tern"): "correct",
    ("mailmap", "Tern"): "correct",
    ("session", "Tern"): "insufficient_evidence",
}


def build(repo):
    _build(repo, trailers=False, write_mailmap=False)


if __name__ == "__main__":
    import pathlib, subprocess
    here = pathlib.Path(__file__).resolve().parent
    if (here / "harness.py").exists():
        sys.exit(subprocess.call([sys.executable, str(here / "harness.py"), "scenario_rename_untrailered"]))
    print("run under the harness: python3 harness.py scenario_rename_untrailered")
