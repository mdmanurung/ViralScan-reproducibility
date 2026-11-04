#!/bin/bash
#SBATCH -J cat08_hpv11
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=08:00:00
# CAT-08 / HPV-11: native `viralscan build-ref` (human host + every panel HPV genome except HPV-11 NC_075235.1),
# then 90 bp reads tiled from HPV-11 pseudoaligned to that index: where do reads of an absent type land?
# Submit: sbatch -o <D>/logs/%x_%j.log scripts/cat08_hpv11_native.sbatch
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
ENVD=$M/conda/envs/viralscan_test_full
PKG=$M/ViralScan/.claude/worktrees/pin-cat08-3d19cca
export PATH=$ENVD/bin:$PATH PYTHONPATH=$PKG/src
export KALLISTO=$ENVD/lib/python3.11/site-packages/kb_python/bins/linux/kallisto/kallisto
D=$M/ViralScan-reproducibility/data/runs/round_2026-11-02/cat08_cat40/hpv11_native_3d19cca_3d19cca
VIRAL_FA=$M/ViralScan-reproducibility/data/references/panel_builds/viral_ref_wp5/build_7e5a2ce/viral.fa
mkdir "$D"
python - "$VIRAL_FA" "$PKG/src/viralscan/data/virus_catalog.tsv" "$D/accessions.txt" <<'PY'
import csv, sys
fam = {r["accession"]: r["family"] for r in csv.DictReader(open(sys.argv[2]), delimiter="\t")}
acc = [l[1:].split()[0] for l in open(sys.argv[1]) if l[0] == ">"]
keep = [a for a in acc if fam[a.split(".")[0]] == "Papillomaviridae" and a != "NC_075235.1"]
open(sys.argv[3], "w").write("\n".join(keep) + "\n")
print(len(keep), "HPV accessions")
PY
git -C "$PKG" rev-parse HEAD
python -m viralscan build-ref --host human --ensembl-release 116 --virus-accessions $(cat "$D/accessions.txt") \
  --output "$D/ref" --ncbi-email "${NCBI_EMAIL:-mikhael.manurung@gmail.com}" --cores "$SLURM_CPUS_PER_TASK"
IDX=$(find "$D/ref" -name '*.idx' | head -1)
echo "index: $IDX"
"$KALLISTO" inspect "$IDX" > "$D/inspect.txt" 2>&1 || true
python $M/ViralScan-reproducibility/.claude/worktrees/round-cat0840/scripts/cat08_tile_and_land.py \
  $HOME/.cache/viralscan/ncbi/NC_075235.1/NC_075235.1.fasta "$IDX" "$D/hpv11_reads"
echo DONE
