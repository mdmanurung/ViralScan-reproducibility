#!/usr/bin/env bash
# ANDET-08: one job = plant a held-out set into the CAL-08 background and run viralscan on it, or (SET=twin)
# run viralscan on the unplanted background itself (byte-identical to the planted run's unplanted twin).
# Env: SET=A|B|C|H|twin  SEEDOFF=<int>   Output only under $ROOT/runs/<SET>; a finished dir is never overwritten.
#SBATCH -J andet08
set -euo pipefail
ROOT=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/sens
PKG=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan/.claude/worktrees/pin-sens   # de55424
REPRO=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/.claude/worktrees/round-sens
B=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/references/panel_builds/viral_ref_cat42d/build
WL=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/covid_viralscan/viralscan_ref/cellranger_whitelist.txt
export PATH=/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full/bin:$PATH PYTHONPATH=$PKG/src MPLBACKEND=Agg
test "$(git -C "$PKG" rev-parse --short HEAD)" = de55424
OUT=$ROOT/runs_v3/$SET
mkdir -p "$ROOT/runs_v3"; mkdir "$OUT"   # fails if it exists
cd "$OUT"
if [ "$SET" = twin ]; then
  mkdir in; ln -s "$ROOT/background/local_R1.fastq.gz" in/CAL08_R1.fastq.gz; ln -s "$ROOT/background/local_R2.fastq.gz" in/CAL08_R2.fastq.gz
  IN=in
else
  python "$REPRO/scripts/sens07_planted_sensitivity.py" plant --out-dir plant --technology 10xv3 \
    --background-r1 "$ROOT/background/local_R1.fastq.gz" --background-r2 "$ROOT/background/local_R2.fastq.gz" \
    --heldout-fasta "$ROOT/heldout_sets/set_$SET/heldout.fa" --transcripts-fasta "$ROOT/heldout_sets/set_$SET/heldout_cdna.fa" \
    --families "$ROOT/heldout_sets/set_$SET/families.tsv" --paf "$ROOT/heldout_sets/candidates_vs_panel.paf" \
    --per-family 1000 --levels 1 2 5 10 20 50 100 300 1000 3000 --cells-per-condition 5 \
    --library-strand forward --seed $((20261102 + SEEDOFF)) --n-background 12000000
  IN=plant/planted
  ln -s R1.fastq.gz $IN/CAL08_R1.fastq.gz; ln -s R2.fastq.gz $IN/CAL08_R2.fastq.gz
fi
/usr/bin/time -v -o time_viralscan.txt python -m viralscan.menu run -o run --r1 "$IN/CAL08_R1.fastq.gz" --r2 "$IN/CAL08_R2.fastq.gz" \
  -i "$B/panel.idx" -t "$B/panel.t2g" --gtf "$B/viral_panel.gtf" -x 10xv3 --strand forward \
  -c "${SLURM_CPUS_PER_TASK:-8}" --cell-calling emptydrops --anellovirus-gene-ids --yes --verbose
test -s run/CAL08/results/viral_summary.tsv
echo DONE "$SET"
