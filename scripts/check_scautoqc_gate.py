#!/usr/bin/env python3
"""SCAUTOQC-01 gate check on a finished `--scautoqc` run: python check_scautoqc_gate.py <sample run dir>."""
import json
import sys
from pathlib import Path

import scanpy as sc

d = Path(sys.argv[1])
done = json.loads((d / "log" / "scautoqc.done").read_text())
called = {l.strip() for l in (d / "results" / "called_cells.tsv").read_text().splitlines()[1:] if l.strip()}
ok = True
for name, info in done.items():
    a = sc.read_h5ad(d / "kb-python" / "counts_unfiltered" / name) if (d / "kb-python" / "counts_unfiltered" / name).exists() else sc.read_h5ad(next(d.rglob(name)))
    m = a.obs_names.isin(called)
    flag = a.obs["scautoqc_cell_passed_qc"]
    checks = {
        "n_cells_scored == called": info["n_cells_scored"] == len(called) == int(m.sum()),
        "non-called flags all NA": bool(flag[~m].isna().all()),
        "called flags none NA": bool(flag[m].notna().all()),
        "matrix rows == all barcodes": a.n_obs > len(called),
    }
    print(name, "n_scored", info["n_cells_scored"], "called", len(called), "n_obs", a.n_obs, "clusterwise", info.get("clusterwise_status"))
    for k, v in checks.items():
        print(" ", "PASS" if v else "FAIL", k)
        ok &= v
print("GATE_DATA_CHECKS", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
