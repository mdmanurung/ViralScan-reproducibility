#!/usr/bin/env python3
"""Tabulate KSHV / EBV rows of every viral_summary.tsv of a KSHV round (one line per library x arm x virus).

    python scripts/kshv_round_collect.py new    <ROUND>/            # <ROUND>/<gse>/<gsm>/<arm>/<gsm>/results/
    python scripts/kshv_round_collect.py round2 <dsr_round2>/       # <root>/runs/<dataset>/<arm>/<gsm>/<gsm>/results/
"""
import csv
import os
import re
import sys
from pathlib import Path

VIRUS = re.compile(r"gammaherpesvirus 8|kaposi|herpesvirus 8|gammaherpesvirus 4|epstein|human_herpesvirus_8", re.I)
COLS = ["viral_molecules_total_est", "n_called_cells", "infected_called", "pct_infected_called", "total_cells", "detected"]
PROGRAMS_DIR = os.environ.get("PROGRAMS_DIR", "programs")
PROG = ["n_cells_total", "n_cells_productive", "n_cells_latent", "n_cells_mixed", "n_cells_indeterminate"]  # gene_program_summary.tsv, if present


def summaries(layout: str, root: Path):
    if layout == "new":
        for p in sorted(root.glob("GSE*/GSM*/*/GSM*/results/viral_summary.tsv")):
            yield p.parts[-6], p.parts[-5], p.parts[-4], p
    else:
        for p in sorted(root.glob("runs/kshv_*/*/GSM*/GSM*/results/viral_summary.tsv")):
            yield p.parts[-6], p.parts[-3], p.parts[-5], p


def main(layout: str, root: str) -> None:
    out = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    out.writerow(["dataset", "gsm", "arm", "virus", *COLS, *PROG])
    for ds, gsm, arm, p in summaries(layout, Path(root)):
        gp = p.with_name("gene_program_summary.tsv")
        if not gp.is_file():  # rerun-programs writes under the run dir's posthoc/ (PROGRAMS_DIR: programs or programs_5b419d4)
            gp = p.parent.parent / f"posthoc/{PROGRAMS_DIR}/results/gene_program_summary.tsv"
        prog = {r["virus_name"]: r for r in csv.DictReader(gp.open(), delimiter="\t")} if gp.is_file() else {}
        for r in csv.DictReader(p.open(), delimiter="\t"):
            if VIRUS.search(r["virus_name"]):
                g = prog.get(r["virus_name"], {})
                out.writerow([ds, gsm, arm, r["virus_name"], *(r.get(c, "") for c in COLS), *(g.get(c, "") for c in PROG)])


if __name__ == "__main__":
    main(*sys.argv[1:3])
