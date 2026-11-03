#!/usr/bin/env python3
"""Purpose: pack `viralscan evidence` reads for an igv.js page, one small genome per locus.

Each locus gets its own reference (the viral genome, or a slice of a host chromosome),
a BAM of at most MAX_READS primary alignments drawn at random, and the GTF rows of that
reference. All files are embedded as base64 data URIs in one JS file, so a static page
can load them into igv.js without a server.

Run (from the repro checkout root):
  <conda>/envs/viralscan_test_full/bin/python \
    .claude/worktrees/round-dsr0304/scripts/make_igv_loci.py \
    data/runs/round_2026-11-02/_igv_browser_2026-11-03

Inputs:
  <evidence dir>/competitive_reads.umi_dedup.bam   UMI-deduplicated reads [viralscan evidence]
  data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa   host genome, for the host slice
  data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf   viral genes
  data/references/panel_builds/viral_ref_cat42d/build/viral.fa   viral genomes, unmasked here
Outputs (in <run_dir>):
  igv_loci.js     window.IGV_LOCI: one object per locus with data URIs for igv.js
  igv_loci.tsv    per locus: reads on the reference, reads drawn, reference length
  <locus>.bam/.bai/.fa/.fai/.gtf   the embedded files, for loading into desktop IGV
"""

import base64
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd
import pysam

# reads drawn per locus: keeps the page under a few MB and igv.js responsive
MAX_READS = 4000
SEED = 20261103
TRACKA = "data/runs/work/trackA_round1/evidence"
HOST_FA = "data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa"
VIRAL_GTF = "data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf"
VIRAL_FA = "data/references/panel_builds/viral_ref_cat42d/build/viral.fa"

# slice: (start, end) 1-based on the host chromosome; positions in the page start at 1
LOCI = [
    {
        "id": "hsv1",
        "evidence": f"{TRACKA}/hsv1__GSM3511327__combined_off__Human_herpesvirus_1",
        "contig": "VIRUS|NC_001806.2",
        "locus": "NC_001806.2:45,800-48,600",
    },
    {
        "id": "ebv",
        "evidence": f"{TRACKA}/ebv__GSM4796271__combined_off__Epstein_Barr_virus",
        "contig": "VIRUS|NC_007605.1",
        "locus": "NC_007605.1:165,500-168,000",
    },
    {
        "id": "hhv6b",
        "evidence": f"{TRACKA}/hhv6b__GSM6416035__combined_off__Human_herpesvirus_6b",
        "contig": "VIRUS|AF157706.1",
        "locus": "AF157706.1:86,500-89,500",
    },
    {
        "id": "hpv77_offtarget",
        "evidence": "data/runs/round_2026-11-02/hpv16/SRR19537339/evidence/twostep__hpv77",
        "contig": "HOST|chr1",
        "slice": (153_600_001, 153_615_000),
        "locus": "chr1_153600001:6,960-7,240",
    },
]


def data_uri(path):
    return (
        "data:application/octet-stream;base64,"
        + base64.b64encode(path.read_bytes()).decode()
    )


run_dir = Path(sys.argv[1])
run_dir.mkdir(parents=True, exist_ok=False)
random.seed(SEED)
viral_gtf = [
    line.split("\t", 1) for line in open(VIRAL_GTF) if not line.startswith("#")
]

# Write one reference, BAM and GTF per locus ------------------------------------------
loci_js, summary = [], []
for spec in LOCI:
    plain = re.sub(r"^(HOST|VIRUS)\|", "", spec["contig"])
    offset = spec["slice"][0] - 1 if "slice" in spec else 0
    name = f"{plain}_{spec['slice'][0]}" if "slice" in spec else plain
    stem = run_dir / spec["id"]

    # reference: the whole viral genome, or the host slice
    if "slice" in spec:
        seq = pysam.FastaFile(HOST_FA).fetch(plain, offset, spec["slice"][1])
    else:
        seq = pysam.FastaFile(VIRAL_FA).fetch(plain)
    Path(f"{stem}.fa").write_text(
        f">{name}\n" + "\n".join(seq[i : i + 60] for i in range(0, len(seq), 60)) + "\n"
    )
    pysam.faidx(f"{stem}.fa")

    # reads: primary alignments on the reference, a seeded random draw of MAX_READS
    with pysam.AlignmentFile(
        f"{spec['evidence']}/competitive_reads.umi_dedup.bam"
    ) as bam:
        region = (
            (spec["contig"], offset, spec["slice"][1])
            if "slice" in spec
            else (spec["contig"],)
        )
        reads = [
            a
            for a in bam.fetch(*region)
            if not (a.is_unmapped or a.is_secondary or a.is_supplementary)
            and a.reference_start >= offset
            and a.reference_end <= offset + len(seq)
        ]
    drawn = sorted(random.sample(range(len(reads)), min(MAX_READS, len(reads))))
    header = pysam.AlignmentHeader.from_dict(
        {"HD": {"VN": "1.6", "SO": "coordinate"}, "SQ": [{"SN": name, "LN": len(seq)}]}
    )
    with pysam.AlignmentFile(f"{stem}.bam", "wb", header=header) as out:
        for i in drawn:
            a = reads[i]
            b = pysam.AlignedSegment(header)
            b.query_name = a.query_name
            b.flag = a.flag
            b.reference_id = 0
            b.reference_start = a.reference_start - offset
            b.mapping_quality = a.mapping_quality
            b.cigartuples = a.cigartuples
            b.query_sequence = a.query_sequence
            b.query_qualities = a.query_qualities
            b.set_tags(a.get_tags())
            out.write(b)
    pysam.index(f"{stem}.bam")

    # genes: viral GTF rows of this genome; the host slice has no annotation here
    gtf = [f"{name}\t{rest}" for seqname, rest in viral_gtf if seqname == plain]
    Path(f"{stem}.gtf").write_text("".join(gtf))

    loci_js.append(
        {
            "id": spec["id"],
            "locus": spec["locus"],
            "reference": {
                "id": name,
                "name": name,
                "fastaURL": data_uri(Path(f"{stem}.fa")),
                "indexURL": data_uri(Path(f"{stem}.fa.fai")),
            },
            "bam": data_uri(Path(f"{stem}.bam")),
            "bai": data_uri(Path(f"{stem}.bam.bai")),
            "gtf": data_uri(Path(f"{stem}.gtf")) if len(gtf) else None,
            "n_reads": len(reads),
            "n_drawn": len(drawn),
            "length": len(seq),
            "offset": offset,
        }
    )
    summary.append(
        {
            "id": spec["id"],
            "reference": name,
            "length": len(seq),
            "offset": offset,
            "n_reads": len(reads),
            "n_drawn": len(drawn),
            "n_gtf_rows": len(gtf),
        }
    )

# Write outputs -------------------------------------------------------------------------
(run_dir / "igv_loci.js").write_text(f"window.IGV_LOCI = {json.dumps(loci_js)};\n")
pd.DataFrame(summary).to_csv(run_dir / "igv_loci.tsv", sep="\t", index=False)
