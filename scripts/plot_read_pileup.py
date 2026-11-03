#!/usr/bin/env python3
"""Purpose: IGV-style read pileup of one region of a `viralscan evidence` BAM.

Draws a coverage track, the reads packed in rows (mismatches in IGV base colours,
soft clips as grey hatched ends, reads carrying the 10x TSO outlined in green),
the reference bases when the window is short, and an optional gene track.

Run: <conda>/envs/viralscan_test_full/bin/python scripts/plot_read_pileup.py \
       --bam <evidence dir>/competitive_reads.umi_dedup.bam \
       --region "HOST|chr1:153606990-153607180" \
       --fasta data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa \
       --title "HPV77 call, twostep, SRR19537339" --out <run dir>/hpv77_chr1.png

Inputs:
  --bam    coordinate-sorted, indexed BAM [viralscan evidence]
  --fasta  reference FASTA of the contig, indexed (.fai); BAM names carry a
           HOST| or VIRUS| prefix that is stripped before lookup
  --gtf    optional GTF with gene rows for the contig [viral_panel.gtf]
Outputs:
  --out    one PNG (and a PDF beside it)
"""

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pysam
from matplotlib.patches import Rectangle

TSO = "AAGCAGTGGTATCAACGCAGAGTACATGGG"
# a read "carries the TSO" if it holds any 12-mer of the TSO or its reverse complement
TSO_K = 12
MAX_ROWS = 60
BASE_COLOURS = {"A": "#1a9850", "C": "#2166ac", "G": "#e08214", "T": "#d73027"}
SHOW_BASES_BELOW = 160

parser = argparse.ArgumentParser()
parser.add_argument("--bam", required=True)
parser.add_argument("--region", required=True, help="CONTIG:START-END, 1-based")
parser.add_argument("--fasta", required=True)
parser.add_argument("--gtf")
parser.add_argument("--title", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()

contig, span = args.region.rsplit(":", 1)
start, end = (int(x.replace(",", "")) for x in span.split("-"))
start0 = start - 1
plain_contig = re.sub(r"^(HOST|VIRUS)\|", "", contig)
out = Path(args.out)
if out.exists():
    raise ValueError(f"output exists, refusing to overwrite: {out}")

# Read the reference window and the reads ------------------------------------------

ref = pysam.FastaFile(args.fasta).fetch(plain_contig, start0, end).upper()
tso_kmers = {
    s[i : i + TSO_K]
    for s in (TSO, TSO[::-1].translate(str.maketrans("ACGT", "TGCA")))
    for i in range(len(s) - TSO_K + 1)
}

reads = []
with pysam.AlignmentFile(args.bam) as bam:
    for aln in bam.fetch(contig, start0, end):
        if aln.is_unmapped:
            continue
        seq = aln.query_sequence or ""
        mismatches = [
            (rpos, seq[qpos])
            for qpos, rpos in aln.get_aligned_pairs(matches_only=True)
            if start0 <= rpos < end and seq[qpos] != ref[rpos - start0]
        ]
        cig = aln.cigartuples
        clip_left = cig[0][1] if cig[0][0] == 4 else 0
        clip_right = cig[-1][1] if cig[-1][0] == 4 else 0
        reads.append(
            {
                "start": aln.reference_start,
                "end": aln.reference_end,
                "reverse": aln.is_reverse,
                "secondary": aln.is_secondary or aln.is_supplementary,
                "mismatches": mismatches,
                "clip_left": clip_left,
                "clip_right": clip_right,
                "tso": any(
                    seq[i : i + TSO_K] in tso_kmers for i in range(len(seq) - TSO_K + 1)
                ),
            }
        )

# Coverage over the window, and pack reads into rows (greedy, IGV-like) -------------

coverage = np.zeros(end - start0)
for r in reads:
    coverage[max(r["start"], start0) - start0 : min(r["end"], end) - start0] += 1

reads.sort(key=lambda r: r["start"] - r["clip_left"])
row_ends = []
for r in reads:
    left = r["start"] - r["clip_left"]
    row = next((i for i, e in enumerate(row_ends) if e < left - 2), None)
    if row is None:
        row_ends.append(0)
        row = len(row_ends) - 1
    row_ends[row] = r["end"] + r["clip_right"]
    r["row"] = row
n_rows = min(len(row_ends), MAX_ROWS)
hidden = sum(r["row"] >= MAX_ROWS for r in reads)

# Gene rows overlapping the window --------------------------------------------------

genes = []
if args.gtf:
    for line in open(args.gtf):
        f = line.rstrip("\n").split("\t")
        if len(f) < 9 or f[2] != "gene" or f[0] != plain_contig:
            continue
        g0, g1 = int(f[3]) - 1, int(f[4])
        if g1 > start0 and g0 < end:
            name = re.search(r'gene_name "([^"]+)"', f[8]) or re.search(
                r'gene_id "([^"]+)"', f[8]
            )
            genes.append((g0, g1, f[6], name.group(1) if name else "?"))

# Draw coverage, reference, reads and genes -----------------------------------------

plt.rcParams["pdf.fonttype"] = 42
heights = [
    1.2,
    0.35 if len(ref) <= SHOW_BASES_BELOW else 0.01,
    max(2.0, n_rows * 0.12),
    0.5,
]
fig, axes = plt.subplots(
    4,
    1,
    figsize=(180 / 25.4, sum(heights) + 0.9),
    sharex=True,
    gridspec_kw={"height_ratios": heights, "hspace": 0.08},
)
ax_cov, ax_ref, ax_reads, ax_gene = axes
x = np.arange(start0, end) + 1

ax_cov.fill_between(x, coverage, step="mid", color="#9e9e9e", linewidth=0)
ax_cov.set_ylabel("reads", fontsize=7)
ax_cov.set_title(
    f"{args.title}\n{contig}:{start:,}-{end:,}  ({len(reads)} UMI-deduplicated reads"
    + (f"; first {MAX_ROWS} rows drawn, {hidden} reads not drawn" if hidden else "")
    + "; coverage counts all)",
    fontsize=8,
    loc="left",
)

ax_ref.set_yticks([])
if len(ref) <= SHOW_BASES_BELOW:
    for i, b in enumerate(ref):
        ax_ref.text(
            start + i,
            0.5,
            b,
            ha="center",
            va="center",
            fontsize=4.5,
            color=BASE_COLOURS.get(b, "black"),
            family="monospace",
        )
ax_ref.set_ylim(0, 1)

for r in reads:
    if r["row"] >= MAX_ROWS:
        continue
    y = n_rows - r["row"] - 1
    face = "#bdbdbd" if r["secondary"] else ("#f4a582" if r["reverse"] else "#92c5de")
    ax_reads.add_patch(
        Rectangle(
            (r["start"] + 0.5, y + 0.1),
            r["end"] - r["start"],
            0.8,
            facecolor=face,
            edgecolor="#1b7837" if r["tso"] else "none",
            linewidth=0.8,
        )
    )
    for s, w in (
        (r["start"] - r["clip_left"], r["clip_left"]),
        (r["end"], r["clip_right"]),
    ):
        if w:
            ax_reads.add_patch(
                Rectangle(
                    (s + 0.5, y + 0.25),
                    w,
                    0.5,
                    facecolor="white",
                    edgecolor="#757575",
                    hatch="////",
                    linewidth=0.3,
                )
            )
    for rpos, base in r["mismatches"]:
        ax_reads.add_patch(
            Rectangle(
                (rpos + 0.5, y + 0.1),
                1,
                0.8,
                facecolor=BASE_COLOURS.get(base, "black"),
                linewidth=0,
            )
        )
ax_reads.set_ylim(0, max(n_rows, 1))
ax_reads.set_yticks([])
ax_reads.set_ylabel("reads", fontsize=7)

# one lane per gene so overlapping genes (E2/E4) do not share a label
for lane, (g0, g1, strand, name) in enumerate(genes):
    ax_gene.add_patch(
        Rectangle(
            (max(g0, start0) + 0.5, lane + 0.3),
            min(g1, end) - max(g0, start0),
            0.3,
            facecolor="#4d4d4d",
        )
    )
    ax_gene.text(
        max(g0, start0) + 2,
        lane + 0.65,
        f"{name} ({strand}, {g0 + 1:,}-{g1:,})",
        ha="left",
        fontsize=6,
    )
ax_gene.set_ylim(0, max(len(genes), 1) + 0.1)
ax_gene.xaxis.set_major_formatter(
    matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}")
)
ax_gene.set_yticks([])
ax_gene.set_ylabel("genes" if args.gtf else "", fontsize=7)
ax_gene.set_xlim(start - 0.5, end + 0.5)
ax_gene.set_xlabel(f"{plain_contig} position (bp)", fontsize=7)
for ax in axes:
    ax.tick_params(labelsize=6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

legend = [
    Rectangle((0, 0), 1, 1, facecolor=c, label=l)
    for l, c in (
        ("forward", "#92c5de"),
        ("reverse", "#f4a582"),
        ("secondary/suppl.", "#bdbdbd"),
    )
]
legend += [
    Rectangle(
        (0, 0),
        1,
        1,
        facecolor="white",
        edgecolor="#757575",
        hatch="////",
        label="soft clip",
    ),
    Rectangle(
        (0, 0), 1, 1, facecolor="white", edgecolor="#1b7837", label="carries TSO"
    ),
]
legend += [
    Rectangle((0, 0), 1, 1, facecolor=c, label=f"mismatch {b}")
    for b, c in BASE_COLOURS.items()
]
fig.legend(
    handles=legend,
    loc="lower center",
    ncol=9,
    fontsize=5.5,
    frameon=False,
    bbox_to_anchor=(0.5, -0.01),
)

out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=200, bbox_inches="tight")
fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
plt.close(fig)
