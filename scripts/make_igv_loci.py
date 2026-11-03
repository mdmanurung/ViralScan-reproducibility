#!/usr/bin/env python3
"""Purpose: pack `viralscan evidence` reads for an igv.js page, one small genome per locus.

Each locus gets its own reference (the viral genome, or a slice of a host chromosome),
a BAM of at most MAX_READS primary alignments (spliced ones first, then at random), and the GTF rows of that
reference. All files are embedded as base64 data URIs in one JS file, so a static page
can load them into igv.js without a server.

Run (from the repro checkout root):
  <conda>/envs/viralscan_test_full/bin/python \
    .claude/worktrees/round-dsr0304/scripts/make_igv_loci.py \
    data/runs/round_2026-11-02/_igv_browser_2026-11-03

Inputs:
  <evidence dir>/competitive_reads.umi_dedup.bam   UMI-deduplicated reads, host slice [viralscan evidence]
  <SPLICE>/<id>.splice.bam   viral reads realigned splice-aware [splice_realign_viral_reads.py]
  data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa   host genome, for the host slice
  data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf   viral genes
  data/references/panel_builds/viral_ref_cat42d/build/viral.fa   viral genomes, unmasked here
Outputs (in <run_dir>):
  igv_loci.js     window.IGV_LOCI: one object per locus with data URIs for igv.js
  igv_loci.tsv    per locus: reads on the reference, reads drawn, reference length
  <locus>.bam/.bai/.fa/.fai/.gtf/.genes.bed   the embedded files, for loading into desktop IGV
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
# spliced reads kept first, so split reads show at a junction; the rest are drawn at random
MAX_SPLICED = 1500
# gene track: transcripts longer than this (EBV latency, spanning most of the genome) are
# left out of the page's BED; CDS of one gene further apart than COPY_GAP are separate copies
MAX_FEATURE_BP = 20_000
COPY_GAP = 10_000
SEED = 20261103
TRACKA = "data/runs/work/trackA_round1/evidence"
HOST_FA = "data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa"
VIRAL_GTF = "data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf"
VIRAL_FA = "data/references/panel_builds/viral_ref_cat42d/build/viral.fa"
# splice-aware realignment of the viral reads [splice_realign_viral_reads.py]
SPLICE = "data/runs/round_2026-11-02/_splice_realign_2026-11-03"

# slice: (start, end) 1-based on the host chromosome; positions in the page start at 1
LOCI = [
    {
        "id": "hsv1",
        "evidence": f"{TRACKA}/hsv1__GSM3511327__combined_off__Human_herpesvirus_1",
        "contig": "NC_001806.2",
        "bam": f"{SPLICE}/hsv1.splice.bam",
        "locus": "NC_001806.2:45,800-48,600",
    },
    {
        "id": "ebv",
        "evidence": f"{TRACKA}/ebv__GSM4796271__combined_off__Epstein_Barr_virus",
        "contig": "NC_007605.1",
        "bam": f"{SPLICE}/ebv.splice.bam",
        "locus": "NC_007605.1:89,700-91,100",
    },
    {
        "id": "hhv6b",
        "evidence": f"{TRACKA}/hhv6b__GSM6416035__combined_off__Human_herpesvirus_6b",
        "contig": "AF157706.1",
        "bam": f"{SPLICE}/hhv6b.splice.bam",
        "locus": "AF157706.1:137,700-139,300",
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
        spec.get("bam", f"{spec['evidence']}/competitive_reads.umi_dedup.bam")
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
    spliced = [i for i, a in enumerate(reads) if "N" in a.cigarstring]
    spliced = random.sample(spliced, min(MAX_SPLICED, len(spliced)))
    rest = sorted(set(range(len(reads))) - set(spliced))
    drawn = sorted(
        spliced + random.sample(rest, min(MAX_READS - len(spliced), len(rest)))
    )
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

    # genes as BED12 for the page: one named row per transcript (or per gene without one),
    # blocks from exons, else CDS; igv.js labels BED rows, not every combined GTF transcript
    features = {}
    rows = [line.rstrip("\n").split("\t") for line in gtf]
    rows = [(f, dict(re.findall(r'(\w+) "([^"]*)"', f[8]))) for f in rows]
    # genes with transcript rows are drawn per transcript; their gene row is skipped
    with_transcripts = {a["gene_id"] for f, a in rows if f[2] == "transcript"}
    for f, attr in rows:
        if f[2] not in ("gene", "transcript", "exon", "CDS"):
            continue
        if f[2] == "gene" and attr["gene_id"] in with_transcripts:
            continue
        key = (
            attr["transcript_id"]
            if attr["gene_id"] in with_transcripts and f[2] != "gene"
            else attr["gene_id"]
        )
        label = (
            attr.get("gene_name") or attr.get("gene") or attr["gene_id"].split("_")[-1]
        )
        feat = features.setdefault(
            key, {"name": label, "strand": f[6], "exon": [], "CDS": [], "span": []}
        )
        span = (int(f[3]) - 1, int(f[4]))
        feat["span" if f[2] in ("gene", "transcript") else f[2]].append(span)
    bed, n_long = [], 0
    for feat in features.values():
        blocks = sorted(feat["exon"] or feat["CDS"] or feat["span"])
        if not blocks:
            continue
        # a CDS-only gene annotated in both terminal repeats: one feature per copy
        copies = [[blocks[0]]]
        for block in blocks[1:]:
            if not feat["exon"] and block[0] - copies[-1][-1][1] > COPY_GAP:
                copies.append([block])
            else:
                copies[-1].append(block)
        for blocks in copies:
            # CDS-only blocks reach out to the gene row's UTR ends, copy by copy
            if not feat["exon"]:
                for g0, g1 in feat["span"]:
                    if (
                        g0 <= blocks[0][0]
                        and blocks[-1][1] <= g1
                        and g1 - g0 < COPY_GAP
                    ):
                        blocks = [(g0, blocks[0][1]), *blocks[1:]]
                        blocks[-1] = (blocks[-1][0], g1)
            start, end = blocks[0][0], max(e for _, e in blocks)
            if end - start > MAX_FEATURE_BP:
                n_long += 1
                continue
            thick = [c for c in feat["CDS"] if start <= c[0] < end] or blocks
            bed.append(
                (
                    start,
                    end,
                    feat["name"],
                    feat["strand"],
                    min(t[0] for t in thick),
                    max(t[1] for t in thick),
                    blocks,
                )
            )
    Path(f"{stem}.genes.bed").write_text(
        "".join(
            f"{name}\t{s}\t{e}\t{n}\t0\t{st}\t{ts}\t{te}\t0\t{len(b)}\t"
            + ",".join(str(e1 - s1) for s1, e1 in b)
            + "\t"
            + ",".join(str(s1 - s) for s1, _ in b)
            + "\n"
            for s, e, n, st, ts, te, b in sorted(bed)
        )
    )

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
            "genes_bed": data_uri(Path(f"{stem}.genes.bed")) if len(gtf) else None,
            "n_reads": len(reads),
            "n_drawn": len(drawn),
            "n_spliced_drawn": len(spliced),
            "n_long_transcripts_left_out": n_long,
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
            "n_spliced_drawn": len(spliced),
            "n_gtf_rows": len(gtf),
            "n_long_transcripts_left_out": n_long,
        }
    )

# Write outputs -------------------------------------------------------------------------
(run_dir / "igv_loci.js").write_text(f"window.IGV_LOCI = {json.dumps(loci_js)};\n")
pd.DataFrame(summary).to_csv(run_dir / "igv_loci.tsv", sep="\t", index=False)
