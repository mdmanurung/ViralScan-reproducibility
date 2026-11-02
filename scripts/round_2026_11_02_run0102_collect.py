#!/usr/bin/env python3
"""Print job states and the top viral_summary rows per arm for RUN-01/RUN-02 (round 2026-11-02).
Usage: python scripts/round_2026_11_02_run0102_collect.py [data_dir]"""
import csv, json, sys
from pathlib import Path

data = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
root = data / "runs" / "round_2026-11-02"
for d in sorted(root.glob("*_SRR*")):
    acc = d.name.split("_")[-1]
    print(f"== {d.name}")
    chem = d / "_meta" / "chem.json"
    if chem.is_file():
        j = json.loads(chem.read_text())
        print("chem:", (j.get("chemistry") or {}).get("chemistry"), "strand:", (j.get("strand_pilot") or {}).get("choice"))
    for arm in ("combined_off", "combined_artefact", "twostep"):
        s = d / arm / acc / "results" / "viral_summary.tsv"
        if not s.is_file():
            print(f"{arm}: no viral_summary.tsv")
            continue
        rows = list(csv.DictReader(s.open(), delimiter="\t"))
        rows.sort(key=lambda r: -float(r["viral_molecules_total_est"] or 0))
        print(f"{arm}: {len(rows)} viruses; top 8 (name, molecules, infected_called, n_called_cells)")
        for r in rows[:8]:
            print("  ", r["virus_name"], r["viral_molecules_total_est"], r["infected_called"], r["n_called_cells"])
