#!/usr/bin/env python3
"""SENS-CAL-01: measured capture versus iid divergence, against fragment_capture_exact (exploratory, training only).

Purpose: score each planted-divergence run (sens07 score logic), compare per-divergence capture with the
    exact substitution-only DP, and fit one effective read length by binomial maximum likelihood.

Run:     PYTHONPATH=<package>/src python scripts/senscal01_capture.py --root <sens dir> --out-dir <new dir>

Inputs:
    <root>/calibration/runs/d<DIV>/plant/truth.tsv and run/CAL08/kb-python/counts_unfiltered/adata_multimap.h5ad
    <root>/calibration/runs/twin/run/CAL08/kb-python/counts_unfiltered/adata_multimap.h5ad
Outputs (--out-dir, must not exist):
    capture_by_divergence.tsv   per divergence x family: planted, recovered, capture, Wilson CI, DP(L=90)
    fit.json                    L_eff (1 parameter), L_eff with free ceiling c0 (2 parameters), profile table
    fig_capture_vs_divergence.png
"""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sens07_planted_sensitivity as s7  # noqa: E402
from viralscan.sensitivity import fragment_capture_exact  # noqa: E402
from viralscan.virus_identity import VirusIdentityTable  # noqa: E402

# ── Parameters ───────────────────────────────────────────────────────────────────────────────
DIVERGENCES = [0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.125, 0.15]
K = 31  # kallisto k-mer length of the index
READ_LEN = 90  # R2 length of the planted reads
L_GRID = range(K, 151)  # candidate effective read lengths for the fit
LUEBBERT = (0.044, 0.55)  # Luebbert et al. 2025 Fig 1c, EBOV iid: figure reading +/-0.03, read length unverified

ap = argparse.ArgumentParser()
ap.add_argument("--root", type=Path, required=True)
ap.add_argument("--out-dir", type=Path, required=True)
args = ap.parse_args()
OUT = args.out_dir
OUT.mkdir(parents=True)
H5 = "run/CAL08/kb-python/counts_unfiltered/adata_multimap.h5ad"
RUNS = args.root / "calibration/runs_v3"

table = VirusIdentityTable.read_tsv(RUNS / "twin/run/CAL08/results/virus_identity.tsv")
gene_group = {g.gene_id: g.family for g in table.genes if g.viral}
twin = s7.load_counts(RUNS / "twin" / H5, "X")

# ── Score every divergence run ───────────────────────────────────────────────────────────────
rows = []
for d in DIVERGENCES:
    run = RUNS / ("d0.10" if d == 0.10 else f"d{d}")  # the job names carry the grid as typed
    truth = list(csv.DictReader(open(run / "plant/truth.tsv"), delimiter="\t"))
    _, summary = s7.score(truth, s7.load_counts(run / H5, "X"), gene_group, twin, threshold=1)
    for r in summary:
        rows.append(dict(divergence=d, family=r["family"], n_genomes=r["n_genomes"], planted=r["planted"],
                         recovered=r["recovered"], capture=r["capture"], ci_low=r["capture_ci_low"], ci_high=r["capture_ci_high"],
                         dp_L90=fragment_capture_exact(d, READ_LEN, K)))
with open(OUT / "capture_by_divergence.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
    w.writeheader()
    w.writerows(rows)

# ── Pooled counts and fits ───────────────────────────────────────────────────────────────────
pooled = defaultdict(lambda: [0.0, 0.0])
for r in rows:
    pooled[r["divergence"]][0] += r["recovered"]
    pooled[r["divergence"]][1] += r["planted"]
div = np.array(DIVERGENCES)
rec = np.array([pooled[d][0] for d in DIVERGENCES])
pla = np.array([pooled[d][1] for d in DIVERGENCES])
eps = 1e-9

def dp(L):
    return np.array([fragment_capture_exact(d, int(L), K) for d in DIVERGENCES])

def loglik(p):
    p = np.clip(p, eps, 1 - eps)
    return float(np.sum(rec * np.log(p) + (pla - rec) * np.log(1 - p)))

profile = [(L, loglik(dp(L))) for L in L_GRID]  # one parameter: effective read length
best_L, best_ll = max(profile, key=lambda t: t[1])
inside = [L for L, ll in profile if ll >= best_ll - 1.92]  # 95 % profile-likelihood interval (chi2_1 / 2)
profile2 = []  # two parameters: ceiling c0 (index/host competition at zero divergence) times the DP
for L in L_GRID:
    shape = dp(L)
    c0 = float(np.clip(np.sum(rec) / np.sum(pla * shape), eps, 1.0))  # MLE of c0 given L, capped at 1
    profile2.append((L, c0, loglik(c0 * shape)))
best2 = max(profile2, key=lambda t: t[2])
fit = dict(
    k=K, planted_read_len=READ_LEN, n_divergences=len(DIVERGENCES), pooled_planted=pla.tolist(), pooled_recovered=rec.tolist(),
    one_parameter=dict(L_eff=best_L, loglik=best_ll, L_95ci=[min(inside), max(inside)], loglik_at_L90=loglik(dp(READ_LEN)),
                       lrt_L90_vs_best=2 * (best_ll - loglik(dp(READ_LEN)))),
    two_parameter=dict(L_eff=best2[0], c0=best2[1], loglik=best2[2]),
    capture_at_zero_divergence=rec[0] / pla[0],
    caveat="pooled over families; binomial likelihood treats planted molecules as independent trials; iid substitutions only; clustered divergence deferred",
)
(OUT / "fit.json").write_text(json.dumps(fit, indent=2) + "\n")

# ── Figure ───────────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(5.2, 4))
xs = np.linspace(0, 0.15, 151)
ax.plot(xs, [fragment_capture_exact(x, READ_LEN, K) for x in xs], color="grey", label=f"exact DP, L={READ_LEN}")
ax.plot(xs, [fragment_capture_exact(x, best_L, K) for x in xs], color="tab:red", label=f"DP, fitted L_eff={best_L}")
for fam in sorted({r["family"] for r in rows}):
    sub = [r for r in rows if r["family"] == fam]
    ax.plot([r["divergence"] for r in sub], [r["capture"] for r in sub], "o-", ms=3, lw=0.6, alpha=0.5, label=fam)
lo = [s7.wilson(a, b)[0] for a, b in zip(rec, pla)]
hi = [s7.wilson(a, b)[1] for a, b in zip(rec, pla)]
ax.errorbar(div, rec / pla, yerr=np.clip([rec / pla - lo, np.array(hi) - rec / pla], 0, None), fmt="ks", ms=4, capsize=2, label="pooled (Wilson 95 %)")
ax.errorbar(*LUEBBERT, yerr=0.03, fmt="x", color="tab:green", label="Luebbert 2025 Fig 1c (EBOV)")
ax.set_xlabel("iid substitution rate on planted R2 reads")
ax.set_ylabel("molecules recovered / planted (net of unplanted twin)")
ax.set_ylim(0, 1.05)
ax.legend(fontsize=6)
ax.set_title("SENS-CAL-01 capture vs divergence (exploratory, cat42d index, one library)", fontsize=8)
fig.savefig(OUT / "fig_capture_vs_divergence.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(json.dumps(fit, indent=2))
print((OUT / "capture_by_divergence.tsv").read_text())
