#!/usr/bin/env python3
"""ANDET-08: per-genus probit LOD95 from the planted held-out runs (exploratory, pre-G3, n = 1 library).

Purpose: score every (held-out genome, planted level) condition against the unplanted twin, fit the
    SCI-03 probit (v3_lod.py) per genus with the genome as the resampling unit, and draw one figure.

Run:     PYTHONPATH=<package>/src python scripts/andet08_genus_lod95.py --root <sens dir> --out-dir <new dir>

Inputs:
    <root>/runs/{A,B,C,H}/plant/truth.tsv                         [sens07 plant]
    <root>/runs/{A,B,C,H}/run/CAL08/kb-python/counts_unfiltered/adata_multimap.h5ad   [viralscan run]
    <root>/runs/twin/run/CAL08/kb-python/counts_unfiltered/adata_multimap.h5ad        [viralscan run, unplanted]
    <root>/heldout_sets/set_*/selection_groups.tsv                [andet08_heldout_set.py]
Outputs (--out-dir, must not exist):
    per_condition.tsv   one row per (set, genome, level): net molecules, any-anello and genus-correct
    lod95_by_genus.tsv  probit LOD95, BCa interval, status, bracket, per genus x identity stratum
    twin_gate.tsv       anellovirus molecules in the unplanted background
    fig_detection_curves.png
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sens07_planted_sensitivity as s7  # noqa: E402
import v3_lod  # noqa: E402
from viralscan.virus_identity import VirusIdentityTable  # noqa: E402

# ── Parameters ───────────────────────────────────────────────────────────────────────────────
THRESHOLD = 1  # net molecules that count a condition as detected (the default 1-UMI call)
THRESHOLD_STRICT = 3  # sensitivity: three molecules
BOOT_SEED = 20261102  # bootstrap seed for the BCa interval (no default in v3_lod)
REPLICATES = 2000  # protocol uncertainty.replicates
LOW_SETS, HIGH_SETS = ("A", "B", "C"), ("H",)  # <95 % identity draws; the >=95 % contrast
GROUPS = ["Alphatorquevirus", "Betatorquevirus", "Gammatorquevirus", "Gyrovirus",
          "Samektorquevirus", "Hetorquevirus", "Memtorquevirus", "Anelloviridae"]

ap = argparse.ArgumentParser()
ap.add_argument("--root", type=Path, required=True)
ap.add_argument("--out-dir", type=Path, required=True)
args = ap.parse_args()
ROOT, OUT = args.root, args.out_dir
OUT.mkdir(parents=True)

H5 = "run/CAL08/kb-python/counts_unfiltered/adata_multimap.h5ad"
table = VirusIdentityTable.read_tsv(ROOT / "runs_v3/twin/run/CAL08/results/virus_identity.tsv")
gene_family = {g.gene_id: g.family for g in table.genes if g.viral}
gene_key = {g.gene_id: g.virus_key for g in table.genes if g.viral}


def viral_by_cell(path):
    """cell -> [(gene, molecules)] for anellovirus genes only (the matrix has millions of host entries)."""
    out = defaultdict(list)
    for (cb, gene), v in s7.load_counts(path, "X").items():
        if gene_family.get(gene) == "Anelloviridae":
            out[cb].append((gene, v))
    return out


twin = viral_by_cell(ROOT / "runs_v3/twin" / H5)

# ── Twin gate: anellovirus molecules in the unplanted background ─────────────────────────────
tw = defaultdict(float)
for entries in twin.values():
    for gene, v in entries:
        tw[gene_key[gene]] += v
with open(OUT / "twin_gate.tsv", "w") as fh:
    fh.write("virus_key\tmolecules_in_unplanted_background\n")
    for k, v in sorted(tw.items()):
        fh.write(f"{k}\t{v}\n")
    fh.write(f"ALL_Anelloviridae\t{sum(tw.values())}\n")

# ── Per-condition scoring ────────────────────────────────────────────────────────────────────
rows = []
for sset in (*LOW_SETS, *HIGH_SETS):
    d = ROOT / "runs_v3" / sset
    if not (d / H5).exists():
        print(f"set {sset}: no counts yet, skipped", file=sys.stderr)
        continue
    group_of = {r["genome"]: r for r in csv.DictReader(open(ROOT / f"heldout_sets/set_{sset}/selection_groups.tsv"), delimiter="\t")}
    counts = viral_by_cell(d / H5)
    cells = defaultdict(set)
    for r in csv.DictReader(open(d / "plant/truth.tsv"), delimiter="\t"):
        cells[(r["genome"], int(r["level"]))].add(r["cb"])
    for (genome, level), cbs in sorted(cells.items()):
        grp = group_of[genome]["group"]
        out = dict(set=sset, genome=genome, group=grp, level=level, band=group_of[genome]["band"],
                   nearest_identity=group_of[genome]["nearest_identity"], planted=level)
        for name, cnt in (("planted", counts), ("twin", twin)):
            fam = key = other = 0.0
            for cb in cbs:
                for gene, v in cnt.get(cb, ()):
                    fam += v
                    if gene_key[gene] == f"genus:{grp}":
                        key += v
            out[f"{name}_any"], out[f"{name}_genus"] = fam, key
        out["net_any"] = max(0.0, out["planted_any"] - out["twin_any"])
        out["net_genus"] = max(0.0, out["planted_genus"] - out["twin_genus"])
        rows.append(out)
with open(OUT / "per_condition.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
    w.writeheader()
    w.writerows(rows)

# ── Per-genome capture (levels >= 1000 pooled) and detectability ─────────────────────────────
HIGH_LEVELS = (1000, 3000)  # capture is read where the Poisson noise of the count is small
by_genome = defaultdict(list)
for r in rows:
    by_genome[r["genome"]].append(r)
genome_rows = []
for genome, rs in sorted(by_genome.items()):
    top = [r for r in rs if r["level"] in HIGH_LEVELS]
    planted = sum(r["level"] for r in top)
    got = sum(r["net_any"] for r in top)
    detected = [r["level"] for r in rs if r["net_any"] >= THRESHOLD]
    genome_rows.append(dict(
        genome=genome, group=rs[0]["group"], set=rs[0]["set"], band=rs[0]["band"], nearest_identity=rs[0]["nearest_identity"],
        capture_top=got / planted, capture_ci_low=s7.wilson(got, planted)[0], capture_ci_high=s7.wilson(got, planted)[1],
        detectable=any(r["level"] == max(r["level"] for r in rs) and r["net_any"] >= THRESHOLD for r in rs),
        lowest_level_detected=min(detected) if detected else "",
        poisson_lod95_molecules=(3 / (got / planted)) if got > 0 else "",  # 3 = minimum_molecules_for_detection(0.95, 1) rounded up
    ))
with open(OUT / "per_genome.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(genome_rows[0]), delimiter="\t")
    w.writeheader()
    w.writerows(genome_rows)
detectable = {g["genome"] for g in genome_rows if g["detectable"]}

# ── Probit per genus x stratum ───────────────────────────────────────────────────────────────
def fit(sel, column, threshold):
    units = defaultdict(list)
    for r in sel:
        units[r["genome"]].append((float(r["level"]), int(r[column] >= threshold)))
    x = [a for u in units.values() for a, _ in u]
    y = [b for u in units.values() for _, b in u]
    point = v3_lod.lod95(x, y)
    interval = v3_lod.lod_interval(units, seed=BOOT_SEED, strata={u: "all" for u in units}, replicates=REPLICATES)
    return len(units), point, interval

result = []
for stratum, sets, only_detectable in (
    ("identity<95", LOW_SETS, False),
    ("identity<95_detectable_only", LOW_SETS, True),  # post hoc, exploratory: genomes detected at the top level
    ("identity>=95", HIGH_SETS, False),
):
    for g in GROUPS:
        sel = [r for r in rows if r["group"] == g and r["set"] in sets and (r["genome"] in detectable or not only_detectable)]
        base = dict(group=g, stratum=stratum, n_genomes=len({r["genome"] for r in sel}))
        if not sel:
            result.append({**base, "response": "any_anello", "threshold": THRESHOLD, "status": "no_held_out_genome"})
            continue
        for column, threshold in (("net_any", THRESHOLD), ("net_any", THRESHOLD_STRICT), ("net_genus", THRESHOLD)):
            n, point, interval = fit(sel, column, threshold)
            result.append({**base, "response": column, "threshold": threshold, "status": point["status"], "lod95_molecules": point["lod"],
                           "interval": json.dumps(interval.get("interval")), "interval_status": interval.get("interval_status"),
                           "interval_reason": interval.get("reason_code"), "bracket": json.dumps(interval.get("bracket")),
                           "detected_fraction_by_level": json.dumps({lv: round(float(np.mean([r[column] >= threshold for r in sel if r["level"] == lv])), 3) for lv in sorted({r["level"] for r in sel})})})
keys = sorted({k for r in result for k in r}, key=lambda k: ["group", "stratum", "n_genomes", "response", "threshold", "status"].index(k) if k in ["group", "stratum", "n_genomes", "response", "threshold", "status"] else 99)
with open(OUT / "lod95_by_genus.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys, delimiter="\t")
    w.writeheader()
    w.writerows(result)

# ── Figure 2: per-genome capture versus nearest-panel identity, with the exact DP ────────────
from viralscan.sensitivity import fragment_capture_exact  # noqa: E402

fig2, ax2 = plt.subplots(figsize=(5.6, 4))
for g in GROUPS:
    sub = [r for r in genome_rows if r["group"] == g]
    ax2.scatter([float(r["nearest_identity"]) if r["nearest_identity"] != "" else 0.78 for r in sub], [r["capture_top"] for r in sub], s=12, label=g)
xs = np.linspace(0.78, 1.0, 100)
ax2.plot(xs, [fragment_capture_exact(1 - x, 90, 31) for x in xs], color="k", lw=1, label="exact DP, L=90, divergence = 1 - identity")
ax2.axvline(0.78, color="grey", lw=0.5, ls=":")
ax2.text(0.781, 0.5, "no alignment\nto the panel", fontsize=6)
ax2.set_xlabel("nearest-panel identity (minimap2; no alignment plotted at 0.78)")
ax2.set_ylabel("measured capture, net molecules / planted (levels 1000, 3000)")
ax2.legend(fontsize=5)
fig2.savefig(OUT / "fig_capture_vs_identity.png", dpi=200, bbox_inches="tight")
plt.close(fig2)

# ── Figure: detection fraction versus planted molecules, per genus ───────────────────────────
fig, axes = plt.subplots(2, 4, figsize=(180 / 25.4 * 1.4, 90 / 25.4 * 1.6), sharex=True, sharey=True)
for ax, g in zip(axes.flat, GROUPS):
    for stratum, sets, colour in (("<95 %", LOW_SETS, "tab:blue"), (">=95 %", HIGH_SETS, "tab:orange")):
        sel = [r for r in rows if r["group"] == g and r["set"] in sets]
        if not sel:
            continue
        levels = sorted({r["level"] for r in sel})
        for genome in sorted({r["genome"] for r in sel}):
            ax.plot(levels, [np.mean([r["net_any"] >= THRESHOLD for r in sel if r["genome"] == genome and r["level"] == lv]) for lv in levels],
                    color=colour, alpha=0.25, lw=0.7)
        ax.plot(levels, [np.mean([r["net_any"] >= THRESHOLD for r in sel if r["level"] == lv]) for lv in levels], "o-", color=colour, ms=3,
                label=f"{stratum} (n={len({r['genome'] for r in sel})})")
        _, point, _ = fit(sel, "net_any", THRESHOLD)
        if point["status"] == "ok":
            xs = np.logspace(0, np.log10(3000), 100)
            ax.plot(xs, stats.norm.cdf(point["intercept"] + point["slope"] * np.log10(xs)), color=colour, lw=1, ls="--")
            ax.axvline(point["lod"], color=colour, lw=0.6, ls=":")
    ax.axhline(0.95, color="grey", lw=0.5)
    ax.set_xscale("log")
    ax.set_title(g, fontsize=8)
    ax.legend(fontsize=6, loc="lower right")
for ax in axes[1]:
    ax.set_xlabel("planted molecules per condition (5 cells)", fontsize=7)
for ax in axes[:, 0]:
    ax.set_ylabel("fraction of genomes detected", fontsize=7)
fig.suptitle(f"ANDET-08 held-out anellovirus detection (net >= {THRESHOLD} molecule vs unplanted twin; exploratory, one library)", fontsize=8)
fig.tight_layout()
fig.savefig(OUT / "fig_detection_curves.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print((OUT / "lod95_by_genus.tsv").read_text())
