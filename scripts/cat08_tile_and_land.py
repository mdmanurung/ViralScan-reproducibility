"""Tile 90 bp reads (both strands) from one FASTA, pseudoalign to a kallisto index, count landing targets.

Run: python scripts/cat08_tile_and_land.py FASTA INDEX OUT_DIR   (KALLISTO, SAMTOOLS env; OUT_DIR must not exist)
Outputs: OUT_DIR/landing_targets.tsv  target, reads (reads compatible with the target; multi-target reads count for each)
         OUT_DIR/summary.json         reads, unmapped, mapped, distinct landing targets
"""

import collections
import json
import os
import random
import subprocess
import sys
from pathlib import Path

FASTA, INDEX, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
KALLISTO = os.environ["KALLISTO"]
SAMTOOLS = os.environ.get("SAMTOOLS", "samtools")
READ_LENGTH, READ_STEP, SEED = 90, 30, 20261102
OUT.mkdir(parents=True)

seq = "".join(l.strip().upper() for l in FASTA.read_text().splitlines() if not l.startswith(">"))
rng = random.Random(SEED)
reverse = str.maketrans("ACGTN", "TGCAN")
n_reads = 0
with open(OUT / "reads.fq", "w") as fq:
    for start in range(0, len(seq) - READ_LENGTH + 1, READ_STEP):
        read = seq[start : start + READ_LENGTH]
        if "N" in read:
            continue
        if rng.random() < 0.5:
            read = read.translate(reverse)[::-1]
        fq.write(f"@r{start}\n{read}\n+\n{'I' * READ_LENGTH}\n")
        n_reads += 1
subprocess.run([KALLISTO, "quant", "-i", INDEX, "-o", OUT / "quant", "--single", "-l", str(READ_LENGTH), "-s", "20", "--pseudobam", OUT / "reads.fq"], check=True, capture_output=True)
sam = subprocess.run([SAMTOOLS, "view", OUT / "quant" / "pseudoalignments.bam"], check=True, capture_output=True, text=True).stdout
per_read = collections.defaultdict(set)
for rec in sam.splitlines():
    qname, flag, target = rec.split("\t")[:3]
    if not int(flag) & 4:
        per_read[qname].add(target)
targets = collections.Counter(t for ts in per_read.values() for t in ts)
with open(OUT / "landing_targets.tsv", "w") as f:
    f.write("target\treads\n")
    f.writelines(f"{t}\t{n}\n" for t, n in targets.most_common())
json.dump({"reads": n_reads, "mapped": len(per_read), "unmapped": n_reads - len(per_read), "distinct_targets": len(targets)}, open(OUT / "summary.json", "w"))
