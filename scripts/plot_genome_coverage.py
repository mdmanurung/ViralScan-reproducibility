#!/usr/bin/env python3
"""Purpose: one viral genome, two tracks: read coverage and annotated genes.

A deliberately uncluttered genome-wide view of a `viralscan evidence` BAM: coverage of
UMI-deduplicated reads (spliced reads count only over their aligned blocks), and genes as
boxes on a + and a - strand row. Only the most-covered genes are labelled; genes longer
than a cutoff (spliced latency transcripts spanning most of a genome) are left out and
counted in the caption.

Run: <conda>/envs/viralscan_test_full/bin/python scripts/plot_genome_coverage.py \
       --bam <evidence dir>/competitive_reads.umi_dedup.bam --contig "VIRUS|AF157706.1" \
       --gtf data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf \
       --title "HHV-6B, GSM6416035" --out <run dir>/hhv6b_genome.png

Inputs:
  --bam   coordinate-sorted, indexed BAM [viralscan evidence]
  --gtf   GTF with gene rows for the contig (HOST|/VIRUS| prefix stripped) [viral_panel.gtf]
Outputs:
  --out   one PNG and a PDF beside it
  <out stem>.genes.tsv   every drawn gene with its mean coverage (source data of the plot)
"""

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
import pysam
from matplotlib.patches import Rectangle

# genes labelled: the most-covered ones only, so labels never pile up
N_LABELS = 8
# genes longer than this are spliced transcripts spanning most of the genome; left out
MAX_GENE_BP = 20_000
# labels on one strand stay at least this fraction of the genome apart
MIN_LABEL_GAP = 0.06

parser = argparse.ArgumentParser()
parser.add_argument("--bam", required=True)
parser.add_argument("--contig", required=True)
parser.add_argument("--gtf", required=True)
parser.add_argument("--title", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()

out = Path(args.out)
if out.exists():
    raise ValueError(f"output exists, refusing to overwrite: {out}")
plain_contig = re.sub(r"^(HOST|VIRUS)\|", "", args.contig)

# Coverage over aligned blocks ------------------------------------------------------

with pysam.AlignmentFile(args.bam) as bam:
    length = bam.get_reference_length(args.contig)
    delta = np.zeros(length + 1, dtype=np.int64)
    n_reads = 0
    for aln in bam.fetch(args.contig):
        if aln.is_unmapped or aln.is_secondary or aln.is_supplementary:
            continue
        n_reads += 1
        for b0, b1 in aln.get_blocks():
            delta[b0] += 1
            delta[b1] -= 1
coverage = np.cumsum(delta[:-1])

# Genes on this contig, with mean coverage --------------------------------------------

rows = []
for line in open(args.gtf):
    f = line.rstrip("\n").split("\t")
    if len(f) < 9 or f[2] != "gene" or f[0] != plain_contig:
        continue
    name = re.search(r'gene_name "([^"]+)"', f[8]) or re.search(
        r'(?:^|; )gene "([^"]+)"', f[8]
    )
    gene_id = re.search(r'gene_id "([^"]+)"', f[8])
    # without a name, the gene ID's last token is the ORF (HUM_HERP6B_U14 -> U14)
    label = (
        name.group(1) if name else gene_id.group(1).split("_")[-1] if gene_id else "?"
    )
    g0, g1 = int(f[3]) - 1, int(f[4])
    rows.append(
        {
            "gene": label,
            "start": g0 + 1,
            "end": g1,
            "strand": f[6],
            "mean_coverage": float(coverage[g0:g1].mean()),
        }
    )
genes = pd.DataFrame(rows)
too_long = genes["end"] - genes["start"] + 1 > MAX_GENE_BP
n_long = int(too_long.sum())
genes = genes[~too_long].reset_index(drop=True)
# label the most-covered genes, skipping one that would sit within MIN_LABEL_GAP of a
# label already placed on the same strand
placed: dict[str, list[float]] = {"+": [], "-": []}
labelled = set()
for i, g in genes.sort_values("mean_coverage", ascending=False).iterrows():
    if len(labelled) == N_LABELS:
        break
    mid = (g["start"] + g["end"]) / 2
    if all(abs(mid - m) >= MIN_LABEL_GAP * length for m in placed.get(g["strand"], [])):
        placed.setdefault(g["strand"], []).append(mid)
        labelled.add(i)

# Draw coverage and gene tracks ---------------------------------------------------------

plt.rcParams["pdf.fonttype"] = 42
fig, (ax_cov, ax_gene) = plt.subplots(
    2,
    1,
    figsize=(180 / 25.4, 75 / 25.4),
    sharex=True,
    gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.05},
)
x = np.arange(1, length + 1)
ax_cov.fill_between(x, coverage, step="mid", color="#4a7fb0", linewidth=0)
ax_cov.set_ylabel("reads (UMI-dedup.)", fontsize=7)
ax_cov.set_ylim(0, coverage.max() * 1.05 if coverage.max() else 1)
ax_cov.set_title(
    f"{args.title}\n{plain_contig}, {length:,} bp, {n_reads:,} reads",
    fontsize=8,
    loc="left",
)

# + strand above the midline, - strand below; labels above (+) or below (-) their box
for i, g in genes.iterrows():
    y = 0.62 if g["strand"] == "+" else 0.18
    ax_gene.add_patch(
        Rectangle(
            (g["start"], y),
            g["end"] - g["start"] + 1,
            0.2,
            facecolor="#c0392b" if i in labelled else "#9e9e9e",
            linewidth=0,
        )
    )
    if i in labelled:
        ax_gene.text(
            (g["start"] + g["end"]) / 2,
            y + 0.24 if g["strand"] == "+" else y - 0.06,
            g["gene"],
            ha="center",
            va="bottom" if g["strand"] == "+" else "top",
            fontsize=6,
        )
ax_gene.axhline(0.5, color="#bdbdbd", linewidth=0.5)
ax_gene.set_ylim(-0.15, 1.15)
ax_gene.set_yticks([0.28, 0.72], ["−", "+"], fontsize=7)
ax_gene.set_xlim(1, length)
ax_gene.xaxis.set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}")
)
ax_gene.set_xlabel(f"{plain_contig} position (kb)", fontsize=7)
caption = (
    f"{len(genes)} genes drawn; red = the {len(labelled)} most covered that do not crowd "
    "a neighbour's label"
)
if n_long:
    caption += f"; {n_long} spliced gene(s) > {MAX_GENE_BP // 1000} kb not drawn"
fig.text(0.01, -0.04, caption, fontsize=5.5, color="#616161", ha="left", va="top")
for ax in (ax_cov, ax_gene):
    ax.tick_params(labelsize=6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200, bbox_inches="tight")
fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
plt.close(fig)
genes.assign(labelled=genes.index.isin(labelled)).to_csv(
    out.with_suffix(".genes.tsv"), sep="\t", index=False
)
