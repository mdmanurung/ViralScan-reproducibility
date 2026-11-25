#!/usr/bin/env python3
"""Purpose: realign the viral reads of an evidence run splice-aware and list their junctions.

`viralscan evidence` aligns with `minimap2 -ax sr`, which never splits a read, so its BAMs
hold no splice junctions. This script realigns the same UMI-deduplicated viral reads to
the viral genome alone with `minimap2 -ax splice:sr` (the short-read splice preset;
plain `splice` maps none of the 64 bp HSV-1 reads), then tallies every junction (an N in
the CIGAR) and marks the ones that match an intron of the panel GTF exactly. A read
spliced at an annotated viral intron comes from spliced viral RNA, not viral DNA.

Run (from the repro checkout root):
  PATH=<conda>/envs/viralscan_test_full/bin:$PATH python \
    .claude/worktrees/round-dsr0304/scripts/splice_realign_viral_reads.py \
    data/runs/round_2026-11-02/_splice_realign_2026-11-03

Inputs:
  <evidence dir>/viral_reads.umi_dedup.fasta   reads kallisto gave the virus, UMI-deduplicated [viralscan evidence]
  data/references/panel_builds/viral_ref_cat42d/build/viral.fa         viral genomes
  data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf  exons (HSV-1, EBV) or CDS (HHV-6B)
Outputs (in <run_dir>):
  <id>.splice.bam(.bai)  primary splice-aware alignments to the viral genome
  junctions.tsv          per virus and junction: reads, motif strand, annotated or not
  splice_summary.tsv     per virus: reads, aligned, spliced, spliced at an annotated intron
  minimap2_version.txt   aligner version
"""

import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import pysam

THREADS = 4
# longest intron searched; EBV latency transcripts have introns of tens of kb
MAX_INTRON = 100_000
TRACKA = "data/runs/work/trackA_round1/evidence"
VIRAL_FA = "data/references/panel_builds/viral_ref_cat42d/build/viral.fa"
VIRAL_GTF = "data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf"
CALLS = {
    "hsv1": (
        f"{TRACKA}/hsv1__GSM3511327__combined_off__Human_herpesvirus_1",
        "NC_001806.2",
    ),
    "ebv": (
        f"{TRACKA}/ebv__GSM4796271__combined_off__Epstein_Barr_virus",
        "NC_007605.1",
    ),
    "hhv6b": (
        f"{TRACKA}/hhv6b__GSM6416035__combined_off__Human_herpesvirus_6b",
        "AF157706.1",
    ),
}

run_dir = Path(sys.argv[1])
run_dir.mkdir(parents=True, exist_ok=False)
gtf = pd.read_csv(
    VIRAL_GTF,
    sep="\t",
    header=None,
    comment="#",
    usecols=[0, 2, 3, 4, 6, 8],
    names=["contig", "feature", "start", "end", "strand", "attributes"],
)
gtf["transcript"] = (
    gtf["attributes"]
    .str.extract(r'transcript_id "([^"]+)"')[0]
    .fillna(gtf["attributes"].str.extract(r'gene_id "([^"]+)"')[0])
)

# Realign, tally junctions ---------------------------------------------------------------
junction_tables, summary = [], []
for call_id, (evidence, contig) in CALLS.items():
    genome = run_dir / f"{call_id}.genome.fa"
    genome.write_text(f">{contig}\n{pysam.FastaFile(VIRAL_FA).fetch(contig)}\n")
    bam = run_dir / f"{call_id}.splice.bam"

    # short-read splice-aware alignment, both transcript strands tried
    minimap2 = subprocess.Popen(
        [
            "minimap2",
            "-ax",
            "splice:sr",
            "--secondary=no",
            "-G",
            str(MAX_INTRON),
            "-t",
            str(THREADS),
            str(genome),
            f"{evidence}/viral_reads.umi_dedup.fasta",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["samtools", "sort", "-@", str(THREADS), "-o", str(bam), "-"],
        stdin=minimap2.stdout,
        check=True,
    )
    if minimap2.wait() != 0:
        raise ValueError(f"minimap2 failed for {call_id}")
    pysam.index(str(bam))

    # junctions: each N run in a primary alignment, with the motif strand minimap2 found (ts)
    junctions = Counter()
    n_reads = n_aligned = n_spliced = 0
    spliced_reads = {}
    for aln in pysam.AlignmentFile(str(bam)):
        if aln.is_secondary or aln.is_supplementary:
            continue
        n_reads += 1
        if aln.is_unmapped:
            continue
        n_aligned += 1
        pos, introns = aln.reference_start, []
        for op, length in aln.cigartuples:
            if op == 3:
                introns.append((pos + 1, pos + length))
            if op in (0, 2, 3, 7, 8):
                pos += length
        if introns:
            n_spliced += 1
            ts = aln.get_tag("ts") if aln.has_tag("ts") else "."
            motif = {
                "+": "-" if aln.is_reverse else "+",
                "-": "+" if aln.is_reverse else "-",
            }.get(ts, ".")
            for intron in introns:
                junctions[(*intron, motif)] += 1
            spliced_reads[aln.query_name] = introns

    # annotated introns: gaps between consecutive exons (or CDS) of one transcript
    rows = gtf[(gtf["contig"] == contig) & gtf["feature"].isin(["exon", "CDS"])]
    feature = "exon" if (rows["feature"] == "exon").any() else "CDS"
    rows = rows[rows["feature"] == feature].sort_values(["transcript", "start"])
    annotated = {}
    for transcript, exons in rows.groupby("transcript"):
        for left, right in zip(
            exons["end"].iloc[:-1], exons["start"].iloc[1:], strict=True
        ):
            if right - left > 1:
                annotated.setdefault((left + 1, right - 1), transcript)

    table = pd.DataFrame(
        [
            {"start": s, "end": e, "motif_strand": m, "reads": n}
            for (s, e, m), n in junctions.items()
        ],
        columns=["start", "end", "motif_strand", "reads"],
    )
    table["intron_bp"] = table["end"] - table["start"] + 1
    table["annotated_in"] = [
        annotated.get((s, e)) for s, e in zip(table["start"], table["end"], strict=True)
    ]
    table.insert(0, "contig", contig)
    table.insert(0, "call", call_id)
    junction_tables.append(table.sort_values("reads", ascending=False))
    annotated_hits = {
        (s, e)
        for s, e in zip(table["start"], table["end"], strict=True)
        if (s, e) in annotated
    }
    summary.append(
        {
            "call": call_id,
            "contig": contig,
            "annotation": feature,
            "n_annotated_introns": len(annotated),
            "reads": n_reads,
            "aligned": n_aligned,
            "spliced": n_spliced,
            "spliced_at_annotated_intron": sum(
                any(i in annotated_hits for i in introns)
                for introns in spliced_reads.values()
            ),
            "junctions": len(table),
            "annotated_junctions_seen": len(annotated_hits),
        }
    )

# Write outputs -------------------------------------------------------------------------
pd.concat(junction_tables).to_csv(run_dir / "junctions.tsv", sep="\t", index=False)
pd.DataFrame(summary).to_csv(run_dir / "splice_summary.tsv", sep="\t", index=False)
(run_dir / "minimap2_version.txt").write_text(
    subprocess.run(
        ["minimap2", "--version"], capture_output=True, text=True, check=True
    ).stdout
)
