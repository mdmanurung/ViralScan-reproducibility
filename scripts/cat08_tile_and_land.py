"""Tile 90 bp reads (both strands) from one FASTA, pseudoalign to a kallisto index, count landing targets.

Run: python scripts/cat08_tile_and_land.py FASTA INDEX OUT_DIR   (KALLISTO, BUSTOOLS env; OUT_DIR must not exist)
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
BUSTOOLS = os.environ["BUSTOOLS"]
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
# kallisto bus, not quant --pseudobam: on the 466,532-target human+HPV index (25952512) kallisto 0.52 wrote a truncated
# pseudobam (no BGZF EOF, header unreadable). The bus file keeps each read's equivalence class, which is all we need.
subprocess.run([KALLISTO, "bus", "-i", INDEX, "-o", OUT / "bus", "-x", "bulk", "--single", OUT / "reads.fq"], check=True)
subprocess.run([BUSTOOLS, "sort", "-o", OUT / "bus" / "sorted.bus", OUT / "bus" / "output.bus"], check=True)
subprocess.run([BUSTOOLS, "text", "-o", OUT / "bus" / "sorted.txt", OUT / "bus" / "sorted.bus"], check=True)
names = (OUT / "bus" / "transcripts.txt").read_text().split()
ec_targets = {}
for line in (OUT / "bus" / "matrix.ec").read_text().splitlines():
    ec, members = line.split("\t")
    ec_targets[int(ec)] = [names[int(i)] for i in members.split(",")]
reads_per_ec = collections.Counter()
for line in (OUT / "bus" / "sorted.txt").read_text().splitlines():
    _, _, ec, count = line.split("\t")
    reads_per_ec[int(ec)] += int(count)
targets = collections.Counter()
for ec, n in reads_per_ec.items():
    for t in ec_targets[ec]:
        targets[t] += n
n_mapped = sum(reads_per_ec.values())
with open(OUT / "landing_targets.tsv", "w") as f:
    f.write("target\treads\n")
    f.writelines(f"{t}\t{n}\n" for t, n in targets.most_common())
json.dump({"reads": n_reads, "mapped": n_mapped, "unmapped": n_reads - n_mapped, "distinct_targets": len(targets)}, open(OUT / "summary.json", "w"))
