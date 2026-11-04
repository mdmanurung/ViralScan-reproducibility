#!/usr/bin/env python3
"""Purpose: held-out gate of the beta-binomial mixed veto (PLAN PROG-MIXED-VETO-01), criteria 1-6 of
analysis/round_2026-11-02/prog_mixed_veto_prereg.md, scored exactly as the addendum
analysis/round_2026-11-04_veto/gate_scoring_addendum.md fixes.

Run (from the repro checkout root, package pkg_13ea776 on PYTHONPATH):
  python scripts/prog_mixed_veto_heldout_gate.py data/runs/round_2026-11-04_veto data/runs/round_2026-11-04_veto/gate

Inputs:
  <round>/gate_libs.tsv                      library, group, run_dir (groups: gse184257_kshv, gse184257_mock,
                                             gsm5725698, gsm5725695, hsv1)
  <run_dir>/kb-python/counts_unfiltered/adata_multimap.h5ad     unique layer for N
  <run_dir>/results/{virus_identity.tsv, called_cells.tsv}
  <run_dir>/posthoc/programs_veto_{any,betabinomial}/results/gene_program_cells.tsv
Outputs (in the fresh output dir):
  cells_by_bin.tsv     library, rule, bin, n cells, lytic / mixed / latent counts
  criteria.tsv         library, criterion, value, threshold, status (pass / fail / not_estimable)
  gate.txt             one line: PASS, FAIL or INCOMPLETE, and why
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc

from viralscan.gene_programs import EVIDENCE_LAYER
from viralscan.virus_grouping import group_genes_by_identity, load_run_identity

ROUND, OUT = Path(sys.argv[1]), Path(sys.argv[2])
KSHV = "Human herpesvirus 8"
LOW, HIGH = (15, 100), (500, np.inf)  # unique KSHV molecules, user decision Q13a
MIN_BIN_CELLS = 30  # a smaller bin is not estimable (pre-registration)
MIN_LYTIC_PCT, MAX_GAP = 90.0, 10.0  # criteria 1 and 3
MIN_LATENT_PCT, MAX_PROD_PCT = 95.0, 1.0  # criterion 5
OUT.mkdir(parents=True, exist_ok=False)

libs = pd.read_csv(ROUND / "gate_libs.tsv", sep="\t")


# Per-library cell table: unique-layer N, called flag, state under each rule ----------
def library_cells(run, rule):
    cells = pd.read_csv(
        run / f"posthoc/programs_veto_{rule}/results/gene_program_cells.tsv", sep="\t"
    )
    cells = cells[cells["virus_name"] == KSHV].set_index("barcode")
    adata = sc.read_h5ad(run / "kb-python/counts_unfiltered/adata_multimap.h5ad")
    genes = group_genes_by_identity(adata.var_names, load_run_identity(run))[0][KSHV]
    cols = adata.var_names.get_indexer(genes)
    n = pd.Series(
        np.asarray(adata.layers[EVIDENCE_LAYER][:, cols[cols >= 0]].sum(axis=1)).ravel(),
        index=adata.obs_names,
        name="n",
    )
    called = pd.read_csv(run / "results/called_cells.tsv", sep="\t").iloc[:, 0]
    out = pd.DataFrame({"n": n.reindex(called).fillna(0)}, index=pd.Index(called, name="barcode"))
    out["state"] = cells["state"].reindex(out.index).fillna("not_scored")
    out["productive_breadth"] = cells["productive_breadth"].reindex(out.index).fillna(0)
    return out


def bin_summary(cells, lo, hi):
    in_bin = cells[(cells["n"] >= lo) & (cells["n"] < hi)]
    scored = in_bin[in_bin["state"].isin(["productive", "mixed", "latent"])]
    return {
        "n_called": len(in_bin),
        "n_scored": len(scored),
        "n_lytic": int(scored["state"].isin(["productive", "mixed"]).sum()),
        "n_mixed": int((scored["state"] == "mixed").sum()),
        "n_latent": int((scored["state"] == "latent").sum()),
        "n_productive": int((scored["state"] == "productive").sum()),
    }


bins, crit = [], []


def add(library, criterion, value, threshold, ok, n_cells):
    status = "not_estimable" if value is None else ("pass" if ok else "fail")
    crit.append(
        {"library": library, "criterion": criterion, "value": value,
         "threshold": threshold, "n_cells": n_cells, "status": status}
    )


for lib in libs.itertuples():
    run = Path(lib.run_dir)
    tables = {rule: library_cells(run, rule) for rule in ("any", "betabinomial")}
    for rule, cells in tables.items():
        for name, (lo, hi) in (("low", LOW), ("high", HIGH)):
            bins.append({"library": lib.library, "group": lib.group, "rule": rule, "bin": name,
                         **bin_summary(cells, lo, hi)})
    bb = tables["betabinomial"]
    low, high = (bin_summary(bb, *LOW), bin_summary(bb, *HIGH))

    # criteria 1 and 3: lytic share (called-cell denominator) and mixed-share gap
    if lib.group in ("gse184257_kshv", "gsm5725698"):
        ok_n = high["n_called"] >= MIN_BIN_CELLS
        pct = 100 * high["n_lytic"] / high["n_called"] if ok_n else None
        add(lib.library, "1_lytic_pct_high", pct, f">={MIN_LYTIC_PCT}", ok_n and pct >= MIN_LYTIC_PCT, high["n_called"])
        est = low["n_scored"] >= MIN_BIN_CELLS and high["n_scored"] >= MIN_BIN_CELLS
        gap = 100 * (high["n_mixed"] / high["n_scored"] - low["n_mixed"] / low["n_scored"]) if est else None
        add(lib.library, "3_mixed_gap_points", gap, f"|gap|<={MAX_GAP}", est and abs(gap) <= MAX_GAP, high["n_scored"])
    # criterion 2: mock libraries, no called cell with >= 2 productive groups
    if lib.group == "gse184257_mock":
        n2 = int((bb["productive_breadth"] >= 2).sum())
        add(lib.library, "2_mock_cells_breadth_ge2", n2, "==0", n2 == 0, len(bb))
    # criterion 5: latent library, >= 95 % of scored KSHV cells latent, <= 1 % productive
    if lib.group == "gsm5725695":
        scored = bb[bb["state"].isin(["productive", "mixed", "latent", "reactivating", "indeterminate"])]
        scored = scored[scored["state"] != "indeterminate"]
        lat = 100 * (scored["state"] == "latent").mean()
        prod = 100 * (scored["state"] == "productive").mean()
        add(lib.library, "5_latent_pct", lat, f">={MIN_LATENT_PCT}", lat >= MIN_LATENT_PCT, len(scored))
        add(lib.library, "5_productive_pct", prod, f"<={MAX_PROD_PCT}", prod <= MAX_PROD_PCT, len(scored))
    # criterion 6: HSV-1 productive calls identical between the rules
    if lib.group == "hsv1":
        a = pd.read_csv(Path(lib.run_dir) / "posthoc/programs_veto_any/results/gene_program_cells.tsv", sep="\t")
        b = pd.read_csv(Path(lib.run_dir) / "posthoc/programs_veto_betabinomial/results/gene_program_cells.tsv", sep="\t")
        cols = ["barcode", "virus_name", "state"]
        merged = a[cols].merge(b[cols], on=["barcode", "virus_name"], suffixes=("_any", "_bb"), validate="1:1")
        diff = int(((merged["state_any"] == "productive") != (merged["state_bb"] == "productive")).sum())
        add(lib.library, "6_productive_calls_changed", diff, "==0", diff == 0, len(merged))

bins = pd.DataFrame(bins)
crit = pd.DataFrame(crit)
bins.to_csv(OUT / "cells_by_bin.tsv", sep="\t", index=False)
crit.to_csv(OUT / "criteria.tsv", sep="\t", index=False)

# Gate: every estimable criterion passes; 1 and 3 estimable on >= 1 GSE184257 KSHV library --
held = crit[crit["library"].isin(libs.loc[libs["group"] == "gse184257_kshv", "library"])]
estimable = {c: ((held["criterion"] == c) & (held["status"] != "not_estimable")).any()
             for c in ("1_lytic_pct_high", "3_mixed_gap_points")}
if (crit["status"] == "fail").any():
    verdict = "FAIL: " + ", ".join(crit.loc[crit["status"] == "fail", "library"] + ":" + crit.loc[crit["status"] == "fail", "criterion"])
elif not all(estimable.values()):
    verdict = f"INCOMPLETE: criteria 1 and 3 not both estimable on a GSE184257 KSHV library {estimable}"
else:
    verdict = "PASS (Set 3 only unless Set 2 is added; the pre-registration needs Set 2 before the gate counts as passed)"
(OUT / "gate.txt").write_text(verdict + "\n")
