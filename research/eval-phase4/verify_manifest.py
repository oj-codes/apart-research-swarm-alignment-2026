#!/usr/bin/env python3
"""Recompute the sha256 of every file MANIFEST.json names and compare. Exit 0 if all match, 1 if not.

    python3 research/eval-phase4/verify_manifest.py

The manifest is the freeze: it was committed and approved before the harness was run on these
scenarios. This script shows that the files being run are the files that were frozen. It cannot
show that no run happened before the freeze; see README.md for what is and is not claimed.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    with open(os.path.join(HERE, "MANIFEST.json"), encoding="utf-8") as f:
        m = json.load(f)
    bad = 0
    for rel, want in sorted(m["files"].items()):
        got = sha256(os.path.join(ROOT, rel))
        ok = got == want
        bad += not ok
        print(f"{'ok      ' if ok else 'MISMATCH'}  {rel}  {got[:16]}")
    print("manifest frozen at:", m["frozen"]["statement"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
