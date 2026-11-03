#!/usr/bin/env python3
"""Purpose: KSHV programme states by viral load, in called AND non-called barcodes.

The official layer 2 scores called cells only. Review (2026-11-03) found that 34 %
(GSM5725696) and 16 % (GSM5725697) of KSHV molecules sit in non-called barcodes,
229 and 79 of them with > 500 molecules. This scores those barcodes with the
package's own call (5b419d4, same parameters as the run) and reports states per
load bin, so the productive fraction no longer depends on cell calling.

Run: PYTHONPATH=<ViralScan>/.claude/worktrees/pin-kshv-5b419d4/src \
       <conda>/envs/viralscan_test_full/bin/python \
       scripts/kshv_programmes_by_load.py data/runs/round_2026-11-02/_kshv/programmes_by_load

Inputs (per library, twostep arm of round 2026-11-02, package de55424):
  <run>/config.yaml                                  run config [viralscan run]
  <run>/kb-python/counts_unfiltered/adata_multimap.h5ad  all barcodes, counts_unique_viral layer
  <run>/results/per_cell_viral.tsv                   KSHV molecules and is_called_cell per barcode
  <run>/posthoc/programs_5b419d4/results/gene_program_cells.tsv  official called-cell calls
Outputs (in <run_dir>):
  barcode_states.tsv     one row per scored barcode: library, called, load, load_bin, state
  states_by_load.tsv     per library, called status and load bin: n barcodes per state
  versions.txt           package SHA and Python package versions
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
import yaml

from viralscan.gene_programs import load_catalogue
from viralscan.runconfig import RunConfig
from viralscan.scripts import gene_programs as gp
from viralscan.virus_grouping import load_run_identity

# run from the repro checkout root: data/ is not in branch worktrees
ROOT = Path.cwd()
RUNS = ROOT / "data/runs/round_2026-11-02/GSE190558"
LIBRARIES = ["GSM5725695", "GSM5725696", "GSM5725697"]
KSHV = "Human herpesvirus 8"
# load bins in KSHV molecules per barcode; 500 is the review's "heavily infected" cut
LOAD_BREAKS = [0, 15, 100, 500, 2000, np.inf]
# non-called barcodes below this load are soup, not cells; not scored
NONCALLED_MIN_LOAD = 100

run_dir = Path(sys.argv[1])
run_dir.mkdir(parents=True, exist_ok=False)

# Score called cells plus loaded non-called barcodes, per library -----------------
tables = []
for library in LIBRARIES:
    run = RUNS / library / "twostep" / library
    config = RunConfig.from_snakemake_config(
        yaml.safe_load((run / "config.yaml").read_text())
    )

    # pick barcodes: every called cell, and non-called barcodes with real load
    per_cell = pd.read_csv(run / "results/per_cell_viral.tsv", sep="\t")
    per_cell = per_cell[per_cell["virus_name"] == KSHV]
    called = per_cell["is_called_cell"].astype(str).str.lower() == "true"
    keep = called | (per_cell["viral_molecules_total_est"] >= NONCALLED_MIN_LOAD)
    picked = per_cell[keep].set_index("barcode")

    # score them with the run's own catalogue and parameters
    adata = sc.read_h5ad(run / "kb-python/counts_unfiltered/adata_multimap.h5ad")
    adata = adata[adata.obs_names.isin(picked.index)].copy()
    calls = gp.run_one(
        adata,
        [KSHV],
        load_catalogue(),
        min_breadth=int(getattr(config, "programme_min_breadth", 2)),
        form=gp._panel_form(config),
        identity=load_run_identity(run),
        latent_min_breadth=int(getattr(config, "programme_latent_min_breadth", 1)),
        min_umi=float(getattr(config, "programme_min_umi", 0.0)),
    )

    # run_one drops barcodes with no marker evidence; they read indeterminate
    states = calls.set_index("barcode")["state"].reindex(picked.index)
    tables.append(
        pd.DataFrame(
            {
                "library": library,
                "barcode": picked.index,
                "called": called[keep].to_numpy(),
                "load": picked["viral_molecules_total_est"].to_numpy(),
                "state": states.fillna("indeterminate").to_numpy(),
            }
        )
    )

barcode_states = pd.concat(tables, ignore_index=True)
barcode_states["load_bin"] = pd.cut(
    barcode_states["load"], LOAD_BREAKS, right=False
).astype(str)

# Our called-cell calls must match the official 5b419d4 run -----------------------
official = pd.concat(
    [
        pd.read_csv(
            RUNS
            / lib
            / "twostep"
            / lib
            / "posthoc/programs_5b419d4/results/gene_program_cells.tsv",
            sep="\t",
        ).assign(library=lib)
        for lib in LIBRARIES
    ]
)
official = official[official["virus_name"] == KSHV].set_index(["library", "barcode"])
ours = barcode_states[barcode_states["called"]].set_index(["library", "barcode"])
if (
    not official.index.isin(ours.index).all()
    or not (ours.loc[official.index, "state"] == official["state"]).all()
):
    raise ValueError("called-cell states differ from the official 5b419d4 calls")

# Count states per library, called status and load bin ----------------------------
states_by_load = (
    barcode_states.groupby(["library", "called", "load_bin", "state"], observed=True)
    .size()
    .unstack("state", fill_value=0)
    .reset_index()
)

# Write outputs ---------------------------------------------------------------------
barcode_states.to_csv(run_dir / "barcode_states.tsv", sep="\t", index=False)
states_by_load.to_csv(run_dir / "states_by_load.tsv", sep="\t", index=False)
pkg = Path(gp.__file__).resolve().parents[3]
sha = subprocess.run(
    ["git", "-C", str(pkg), "rev-parse", "HEAD"], capture_output=True, text=True
).stdout.strip()
versions = [f"viralscan {sha}", f"python {sys.version.split()[0]}"] + [
    f"{m.__name__} {m.__version__}" for m in (np, pd, sc)
]
(run_dir / "versions.txt").write_text("\n".join(versions) + "\n")
