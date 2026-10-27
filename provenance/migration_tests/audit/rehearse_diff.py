#!/usr/bin/env python3
"""Build rehearsal/<batch>/results.tsv from junit xml and diff against rehearsal/baseline/results.tsv."""
import glob, os, sys, pathlib, xml.etree.ElementTree as ET

SPLIT = pathlib.Path("/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/backups/viralscan-split")
REH = pathlib.Path(os.environ.get("REH_ROOT", SPLIT / "rehearsal"))
batch = sys.argv[1]
W = REH / batch

def status(tc):
    for k, name in (("failure", "FAILED"), ("error", "ERROR"), ("skipped", "SKIPPED")):
        if tc.find(k) is not None: return name
    return "PASSED"

res = {}
for x in sorted(glob.glob(str(W / "chunk_*.xml"))):
    for tc in ET.parse(x).getroot().iter("testcase"):
        res[f"{tc.get('classname')}::{tc.get('name')}"] = status(tc)
(W / "results.tsv").write_text("".join(f"{k}\t{v}\n" for k, v in sorted(res.items())))
cnt = {}
for v in res.values(): cnt[v] = cnt.get(v, 0) + 1
print(f"[{batch}] {len(res)} tests: {cnt}")
if batch == "baseline":
    sys.exit(0)

import os
base_p = REH / os.environ.get("BASELINE", "baseline") / "results.tsv"
if not base_p.exists():
    print("no baseline results; run: rehearse.sh baseline"); sys.exit(2)
base = dict(l.rstrip("\n").split("\t") for l in base_p.read_text().splitlines())
bdir = SPLIT / "audit" / "batches"
chain = [l.strip() for l in (bdir / f"{batch}.needs").read_text().splitlines() if l.strip() and not l.startswith("#")] if (bdir / f"{batch}.needs").exists() else []
removed_files = set()
for b in chain + [batch]:
    rm = bdir / f"{b}.rm"
    if rm.exists(): removed_files |= {l.strip() for l in rm.read_text().splitlines() if l.strip() and not l.startswith("#")}
mod = lambda tid: "/".join(tid.split("::")[0].split(".")[:-1]) if False else tid.split("::")[0]
def file_of(tid):  # classname tests.test_x[.Class] -> tests/test_x.py
    parts = tid.split("::")[0].split(".")
    for i in range(len(parts), 0, -1):
        cand = "/".join(parts[:i]) + ".py"
        if cand in removed_files: return cand
    return None

exp_removed = []
for b in chain + [batch]:
    ef = bdir / f"{b}.expected_removed"
    if ef.exists(): exp_removed += [l.strip() for l in ef.read_text().splitlines() if l.strip() and not l.startswith("#")]
missing = [t for t in base if t not in res]
is_expected = lambda t: file_of(t) or any(x in t for x in exp_removed)
explained = [t for t in missing if is_expected(t)]
unexplained_missing = [t for t in missing if not is_expected(t)]
regress = [t for t in base if t in res and base[t] == "PASSED" and res[t] != "PASSED"]
new_bad = [t for t in res if t not in base and res[t] in ("FAILED", "ERROR")]
print(f"removed with their test file: {len(explained)}; vanished unexplained: {len(unexplained_missing)}; "
      f"regressed PASSED->not: {len(regress)}; new failures: {len(new_bad)}")
for label, lst in (("VANISHED", unexplained_missing), ("REGRESSED", regress), ("NEWBAD", new_bad)):
    for t in lst[:60]: print(f"  {label} {t}  [{res.get(t, 'absent')}]")
    if len(lst) > 60: print(f"  ... {len(lst) - 60} more {label}")
sys.exit(1 if (unexplained_missing or regress or new_bad) else 0)
