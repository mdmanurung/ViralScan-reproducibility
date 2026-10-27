#!/usr/bin/env python3
"""Stage 5: rewrite old absolute paths in live scripts (D56). Default = dry run (writes audit/step5_diffs.diff, edits nothing).
--apply: back up each file to data/backups/stage5-script-backups/<abs path> first, then edit in place (same mode, same mtime kept off).
Frozen records are skipped (see SKIP): provenance/superseded dirs and frozen source snapshots."""
import csv
import difflib
import os
import re
import shutil
import sys

import mig

R = mig.R
OUT = mig.HERE.parent / "audit"
APPLY = "--apply" in sys.argv
STAGE = next((a for a in sys.argv[1:] if a.isdigit()), "3")
OPT = lambda k, d: next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{k}=")), d)
SCAN, ONLY, OUT_NAME = OPT("scan", str(OUT / "step5_scan.tsv")), OPT("only", ""), OPT("out", "step5")  # --only=<substring> limits the files
SKIP = re.compile(mig.LAYOUT["frozen_dir_regex"])
BACKUP = os.path.join(R["data"], "backups", "stage5-script-backups")

pairs = [l.rstrip("\n").split("\t") for l in open(OUT / "path_map.tsv")][1:]
rx, new_of = mig.path_regex(pairs)
files = [r[0] for r in list(csv.reader(open(SCAN), delimiter="\t"))[1:]]
todo = [f for f in files if not SKIP.search(f) and ONLY in f]
skipped = [f for f in files if SKIP.search(f)]
diffs, changed = [], 0
for f in todo:
    old = open(f, errors="surrogateescape").read()
    new = rx.sub(lambda m: new_of[m.group(1)], old)
    if new == old:
        continue
    changed += 1
    diffs.append("".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), f"a{f}", f"b{f}", n=0)))
    if APPLY:
        b = os.path.join(BACKUP, f.lstrip("/"))
        os.makedirs(os.path.dirname(b), exist_ok=True)
        shutil.copy2(f, b)
        st = os.stat(f)
        with open(f, "w", errors="surrogateescape") as fh:
            fh.write(new)
        os.chmod(f, st.st_mode)
(OUT / (f"{OUT_NAME}_applied.diff" if APPLY else f"{OUT_NAME}_diffs.diff")).write_text("\n".join(diffs))
print(f"{'applied' if APPLY else 'dry run'}: {changed} files change, {len(skipped)} frozen records skipped", file=sys.stderr)
(OUT / f"{OUT_NAME}_skipped.txt").write_text("\n".join(skipped) + "\n")
