#!/usr/bin/env python3
"""Capture the pre-migration baseline (read-only on every migrated tree). Writes tests/baseline/baseline.json + listings/*.gz.
Re-run only before stage 1, never between stages: the baseline is the thing every stage is compared with."""
import glob
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import mig

L, R = mig.LAYOUT, mig.R
base = {"captured_with": "capture_baseline.py", "moves": {}, "gtf": {}, "leftovers": {}, "git": {}, "branches": {}}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


for m in L["moves"]:
    p = mig.resolve(m)
    if not mig.is_real_dir(p):
        print("MISSING", m["old"], file=sys.stderr)
        base["moves"][m["old"]] = {"missing": True}
        continue
    lines = mig.listing(p, 3)
    mig.save_listing(m["old"], lines)
    base["moves"][m["old"]] = {"new": m["new"], "stage": m["stage"], "inode": mig.inode(p), "entries_d3": len(lines),
                               "samples": mig.sample_files(p, 40, m["old"])}
    print("captured", m["old"], len(lines), flush=True)

g = L["gtf_move"]
gd = os.path.join(R["archive"], g["old_dir"])
for f in sorted(glob.glob(os.path.join(gd, g["glob"]))):
    base["gtf"][os.path.basename(f)] = [os.path.getsize(f), sha(f)]
base["gtf_count"] = len(base["gtf"])

for pat in L["leftover_globs"]:
    for f in sorted(glob.glob(os.path.join(R["old_checkout"], pat))):
        base["leftovers"][os.path.basename(f)] = [os.path.getsize(f), sha(f)]

base["jobs"] = mig.jobs()
base["worktrees"] = mig.worktrees(R["old_checkout"])

for name, repo in (("package", R["old_checkout"]), ("repro", R["repro_old"])):
    ls = mig.git(repo, "ls-files", "-s")
    base["git"][name] = {
        "head": mig.git(repo, "rev-parse", "HEAD").strip(),
        "tracked_files": len(ls.splitlines()),
        "ls_files_sha256": hashlib.sha256(ls.encode()).hexdigest(),
        "mode_120000": sum(1 for x in ls.splitlines() if x.startswith("120000")),
        "branch": mig.git(repo, "branch", "--show-current").strip(),
    }
for name, repo in (("package", "ViralScan"), ("repro", "ViralScan-reproducibility")):
    out = subprocess.run(["gh", "api", f"repos/mdmanurung/{repo}/branches", "--paginate", "--jq", ".[].name"], capture_output=True, text=True).stdout
    base["branches"][name] = sorted(out.split())

x = L["baselines"]["repro_suite"]["xml"]
r = ET.parse(x).getroot()
s = r if r.tag == "testsuite" else r[0]
base["repro_suite"] = {k: int(s.get(k)) for k in ("tests", "failures", "errors", "skipped")}
base["parents"] = {k: sorted(n for n in os.listdir(R[k]) if any(t in n.lower() for t in ("viral", "vs_", "virtus", "kraken2", "_kbtest", "_misc")))
                   for k in ("archive", "scratch")}

mig.BASE.mkdir(exist_ok=True)
(mig.BASE / "baseline.json").write_text(json.dumps(base, indent=1))
print("baseline written:", len(base["moves"]), "trees,", base["gtf_count"], "gtfs,", len(base["jobs"]), "jobs,", len(base["worktrees"]), "worktrees")
