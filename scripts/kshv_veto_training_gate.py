#!/usr/bin/env python3
"""Purpose: training gate of the mixed veto (PLAN PROG-MIXED-VETO-01, user decision Q13a).

Criterion 3 on the training libraries before any held-out download: the mixed share,
among called cells in state productive, mixed or latent, may differ by at most 10 points
between the low-load bin [15, 100) and the high-load bin [500, inf) of KSHV molecules on
the UNIQUE layer (the N the rule tests). Compared for the shipped rule (any) and the
forced beta-binomial rule.

Run (from the repro checkout root):
  PYTHONPATH=<ViralScan>/.claude/worktrees/prog-mixed-veto-b/src \
    <conda>/envs/viralscan_test_full/bin/python scripts/kshv_veto_training_gate.py \
    data/runs/round_2026-11-02/_kshv/veto_training_gate

Inputs (per library, round 2026-11-02 twostep, package de55424 runs):
  <run>/kb-python/counts_unfiltered/adata_multimap.h5ad    unique layer for N
  <run>/results/virus_identity.tsv                         gene -> virus
  <run>/posthoc/programs_5b419d4/results/gene_program_cells.tsv      rule any [rerun-programs]
  _kshv/veto_training_check_betabinom_13ec4ff/<lib>/results/gene_program_cells.tsv  rule
                                                           betabinomial [rerun-programs]
Outputs (in <run_dir>):
  mixed_share_by_bin.tsv   library, rule, bin, n cells, mixed share (%)
  gate.tsv                 library, rule, low-bin share, high-bin share, gap, pass
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc

from viralscan.gene_programs import EVIDENCE_LAYER
from viralscan.virus_grouping import group_genes_by_identity, load_run_identity

# run from the repro checkout root: data/ is not in branch worktrees
ROOT = Path.cwd()
RUNS = ROOT / "data/runs/round_2026-11-02/GSE190558"
CHECK = ROOT / "data/runs/round_2026-11-02/_kshv/veto_training_check_betabinom_13ec4ff"
LIBRARIES = ["GSM5725696", "GSM5725697"]
KSHV = "Human herpesvirus 8"
# bins on unique-layer KSHV molecules, fixed by decision Q13a before this run
LOW, HIGH = (15, 100), (500, np.inf)
MAX_GAP = 10.0

run_dir = Path(sys.argv[1])
run_dir.mkdir(parents=True, exist_ok=False)

# Mixed share per library, rule and load bin -------------------------------------------
rows = []
for library in LIBRARIES:
    run = RUNS / library / "twostep" / library

    # unique-layer N per barcode, as run_one computes it
    adata = sc.read_h5ad(run / "kb-python/counts_unfiltered/adata_multimap.h5ad")
    genes = group_genes_by_identity(adata.var_names, load_run_identity(run))[0][KSHV]
    cols = adata.var_names.get_indexer(genes)
    n = pd.Series(
        np.asarray(
            adata.layers[EVIDENCE_LAYER][:, cols[cols >= 0]].sum(axis=1)
        ).ravel(),
        index=adata.obs_names,
        name="n",
    )

    cell_tables = {
        "any": run / "posthoc/programs_5b419d4/results/gene_program_cells.tsv",
        "betabinomial": CHECK / library / "results/gene_program_cells.tsv",
    }
    for rule, path in cell_tables.items():
        cells = pd.read_csv(path, sep="\t")
        cells = cells[
            (cells["virus_name"] == KSHV)
            & cells["state"].isin(["productive", "mixed", "latent"])
        ]
        cells = cells.join(n, on="barcode", validate="1:1")
        for name, (lo, hi) in (("low", LOW), ("high", HIGH)):
            in_bin = cells[(cells["n"] >= lo) & (cells["n"] < hi)]
            rows.append(
                {
                    "library": library,
                    "rule": rule,
                    "bin": name,
                    "bin_range": f"[{lo}, {hi})",
                    "n_cells": len(in_bin),
                    "mixed_pct": 100 * (in_bin["state"] == "mixed").mean(),
                }
            )

mixed_share_by_bin = pd.DataFrame(rows)

# Gate: high minus low, at most MAX_GAP points ------------------------------------------
gate = mixed_share_by_bin.pivot_table(
    index=["library", "rule"], columns="bin", values="mixed_pct"
).reset_index()
gate["gap"] = gate["high"] - gate["low"]
gate["pass"] = gate["gap"].abs() <= MAX_GAP

# Write outputs -----------------------------------------------------------------------
mixed_share_by_bin.to_csv(run_dir / "mixed_share_by_bin.tsv", sep="\t", index=False)
gate.to_csv(run_dir / "gate.tsv", sep="\t", index=False)
