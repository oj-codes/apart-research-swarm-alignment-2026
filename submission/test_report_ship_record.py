#!/usr/bin/env python3
"""test_report_ship_record.py — the recorded hashes match the files actually in the repo.

Corrie's summary of an otherwise thorough night: every check was about what the document *says*, and
none about *which file gets sent*. Twelve hours of measuring, and a correct document with a wrong
upload would have been indistinguishable. The README already promised the two sha256s "go in the
table at ship time"; this makes that promise checked rather than remembered.

    python3 submission/test_report_ship_record.py

Reads the table in `submission/README.md`, takes each `report.<ext>` row, and compares the recorded
sha256 against the committed file. The upload is the PDF, so its row is the one that binds a sent
file to a record; the docx row is checked because the PDF is rendered from it. Re-render without re-recording and this goes red; re-record from
the wrong file and it goes red too.

Stdlib only. Skips cleanly while the report is not on this ref.
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
README = os.path.join(HERE, "README.md")
ARTIFACTS = ("report.docx", "report.pdf")

# A table row naming the file and its hash, either with or without backticks.
ROW = re.compile(r"^\|\s*`?(report\.\w+)`?\s*\|\s*`?([0-9a-f]{64})`?\s*\|\s*$", re.M)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    if not os.path.exists(README):
        print("skip: submission/README.md not on this ref yet")
        return 0
    present = [a for a in ARTIFACTS if os.path.exists(os.path.join(HERE, a))]
    if not present:
        print(f"skip: none of {', '.join(ARTIFACTS)} on this ref yet")
        return 0

    recorded = dict(ROW.findall(open(README, encoding="utf-8").read()))
    missing = [a for a in present if a not in recorded]
    if missing:
        print(f"fail: no sha256 row for {', '.join(missing)} in submission/README.md. Record it from "
              f"the committed file; an unrecorded hash cannot bind an upload to a file.")
        for a in missing:
            print(f"  {a}: {sha256(os.path.join(HERE, a))}")
        return 1

    wrong = [(a, recorded[a], sha256(os.path.join(HERE, a)))
             for a in present if recorded[a] != sha256(os.path.join(HERE, a))]
    print(f"ship record: {len(present) - len(wrong)}/{len(present)} recorded hash(es) match the "
          f"committed file(s)")
    if wrong:
        print("fail: a recorded hash does not match the file it names — a re-render happened without "
              "a re-record, or the table was copied from the wrong place.")
        for name, said, actual in wrong:
            print(f"  {name}: table says {said[:16]}…{said[-8:]}, file is {actual[:16]}…{actual[-8:]}")
        print("  Re-render, then re-record; the upload is a byte-for-byte copy of report.pdf.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
