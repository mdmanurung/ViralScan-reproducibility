#!/usr/bin/env python3
"""Purpose: fit the latent-veto share of lytic KSHV cells for the mixed veto.

PLAN PROG-MIXED-VETO-01. Cells: called cells with N >= 2,000 KSHV molecules in the induced
libraries GSM5725696 and GSM5725697 (twostep arm, unique layer). Q10 (2026-11-03) fixed
p0 as the MEDIAN share k / N for a binomial veto; the counts proved ~57x overdispersed,
so Q6 was reopened (user, 2026-11-03) for a beta-binomial veto, whose mean and rho are
fitted here by maximum likelihood on the same (k, N) pairs. k = molecules on latent markers
that are not induced_in_lytic; N = molecules on every KSHV gene. Both are computed with
the package's own functions, so the fit uses exactly the quantities the rule tests.

Run (from the repro checkout root, package on PYTHONPATH at the PR B commit):
  PYTHONPATH=<ViralScan>/.claude/worktrees/prog-mixed-veto-b/src \
    <conda>/envs/viralscan_test_full/bin/python scripts/kshv_fit_veto_p0.py \
    data/runs/round_2026-11-02/_kshv/veto_p0_fit

Inputs (per library, round 2026-11-02 twostep, package de55424):
  <run>/config.yaml                                       run config [viralscan run]
  <run>/kb-python/counts_unfiltered/adata_multimap.h5ad   counts_unique_viral layer
  <run>/results/called_cells.tsv                          called cells [viralscan run]
  <run>/results/virus_identity.tsv                        gene -> virus [viralscan run]
Outputs (in <run_dir>):
  cell_shares.tsv   one row per heavy called cell: library, barcode, n, k, share
  p0_fit.tsv        median share, pooled share, quartiles, cells with k = 0, and the
                    beta-binomial MLE (mean, rho) with the overdispersion ratio
  versions.txt      package SHA and Python package versions
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
import yaml
from scipy.optimize import minimize
from scipy.stats import betabinom

from viralscan.gene_programs import EVIDENCE_LAYER, load_catalogue, resolve_markers
from viralscan.runconfig import RunConfig
from viralscan.scripts import gene_programs as gp
from viralscan.scripts.cellcalling import load_called_mask
from viralscan.virus_grouping import group_genes_by_identity, load_run_identity

# run from the repro checkout root: data/ is not in branch worktrees
ROOT = Path.cwd()
RUNS = ROOT / "data/runs/round_2026-11-02/GSE190558"
LIBRARIES = ["GSM5725696", "GSM5725697"]
KSHV = "Human herpesvirus 8"
# heavily lytic cells only (decision Q10); below this a share is too coarse to estimate
MIN_LOAD = 2000

run_dir = Path(sys.argv[1])
run_dir.mkdir(parents=True, exist_ok=False)

# Per heavy called cell: latent-veto molecules k and KSHV molecules N ---------------
tables = []
for library in LIBRARIES:
    run = RUNS / library / "twostep" / library
    config = RunConfig.from_snakemake_config(
        yaml.safe_load((run / "config.yaml").read_text())
    )
    adata = sc.read_h5ad(run / "kb-python/counts_unfiltered/adata_multimap.h5ad")
    adata = adata[load_called_mask(adata, config, str(run))].copy()
    identity = load_run_identity(run)

    # N: every KSHV gene, as run_one computes it
    genes = group_genes_by_identity(adata.var_names, identity)[0][KSHV]
    cols = adata.var_names.get_indexer(genes)
    n = np.asarray(adata.layers[EVIDENCE_LAYER][:, cols[cols >= 0]].sum(axis=1)).ravel()

    # k: latent markers that may veto (not induced_in_lytic), as call_cell_programme uses
    markers, _ = resolve_markers(
        KSHV,
        adata.var_names,
        gp._panel_form(config),
        catalogue=load_catalogue(),
        identity=identity,
    )
    veto = [
        m.var_name
        for m in markers
        if m.programme == "latent" and not m.induced_in_lytic
    ]
    k = np.asarray(adata[:, veto].layers[EVIDENCE_LAYER].sum(axis=1)).ravel()

    heavy = n >= MIN_LOAD
    tables.append(
        pd.DataFrame(
            {
                "library": library,
                "barcode": adata.obs_names[heavy],
                "n": n[heavy],
                "k": k[heavy],
                "share": k[heavy] / n[heavy],
            }
        )
    )
    print(f"{library}: {heavy.sum()} heavy called cells; veto markers {veto}")

cell_shares = pd.concat(tables, ignore_index=True)

# Beta-binomial MLE on (k, N), in log(a), log(b) --------------------------------------
k_int = cell_shares["k"].round().astype(int).to_numpy()
n_int = cell_shares["n"].round().astype(int).to_numpy()
mle = minimize(
    lambda x: -betabinom.logpmf(k_int, n_int, np.exp(x[0]), np.exp(x[1])).sum(),
    x0=[0.0, 5.0],
    method="Nelder-Mead",
    options={"xatol": 1e-8, "fatol": 1e-8, "maxiter": 20000},
)
if not mle.success:
    raise ValueError(f"beta-binomial fit did not converge: {mle.message}")
a, b = np.exp(mle.x)
median_share = cell_shares["share"].median()
# overdispersion: observed squared deviation over the binomial variance at the median share
overdispersion = ((k_int - n_int * median_share) ** 2).mean() / (
    n_int * median_share * (1 - median_share)
).mean()

# Fit: the median share, with its spread and the cells that carry no latent molecule ----
fit = pd.DataFrame(
    {
        "median_share": [median_share],
        "betabinom_mean": [a / (a + b)],
        "betabinom_rho": [1 / (a + b + 1)],
        "overdispersion_vs_binomial": [overdispersion],
        "n_cells": [len(cell_shares)],
        "share_q25": [cell_shares["share"].quantile(0.25)],
        "share_q75": [cell_shares["share"].quantile(0.75)],
        "n_cells_k0": [int((cell_shares["k"] == 0).sum())],
        "pooled_share": [cell_shares["k"].sum() / cell_shares["n"].sum()],
        "min_load": [MIN_LOAD],
        "libraries": [",".join(LIBRARIES)],
    }
)

# Write outputs ---------------------------------------------------------------------
cell_shares.to_csv(run_dir / "cell_shares.tsv", sep="\t", index=False)
fit.to_csv(run_dir / "p0_fit.tsv", sep="\t", index=False)
pkg = Path(gp.__file__).resolve().parents[3]
sha = subprocess.run(
    ["git", "-C", str(pkg), "rev-parse", "HEAD"], capture_output=True, text=True
).stdout.strip()
versions = [f"viralscan {sha}", f"python {sys.version.split()[0]}"] + [
    f"{m.__name__} {getattr(m, '__version__', '?')}" for m in (np, pd)
]
(run_dir / "versions.txt").write_text("\n".join(versions) + "\n")
