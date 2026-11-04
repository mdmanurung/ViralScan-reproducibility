#!/usr/bin/env bash
# SENS-CAL-01: one job = plant exact panel genomes at iid substitution rate $DIV (SET=d<DIV>), or run the
# unplanted 3M-pair background (SET=twin). Output only under $ROOT/calibration/runs_v3/$SET; never overwritten.
#SBATCH -J senscal01
set -euo pipefail
ROOT=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/sens
PKG=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan/.claude/worktrees/pin-sens   # de55424
REPRO=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/.claude/worktrees/round-sens
B=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/references/panel_builds/viral_ref_cat42d/build
WL=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/covid_viralscan/viralscan_ref/cellranger_whitelist.txt
export PATH=/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full/bin:$PATH PYTHONPATH=$PKG/src MPLBACKEND=Agg
test "$(git -C "$PKG" rev-parse --short HEAD)" = de55424
OUT=$ROOT/calibration/runs_v3/$SET
mkdir -p "$ROOT/calibration/runs_v3"; mkdir "$OUT"; cd "$OUT"
if [ "$SET" = twin ]; then
  mkdir in; ln -s "$ROOT/calibration/bg3M/R1.fastq.gz" in/CAL08_R1.fastq.gz; ln -s "$ROOT/calibration/bg3M/R2.fastq.gz" in/CAL08_R2.fastq.gz
  IN=in
else
  python "$REPRO/scripts/sens07_planted_sensitivity.py" plant --out-dir plant --technology 10xv3 \
    --background-r1 "$ROOT/calibration/bg3M/R1.fastq.gz" --background-r2 "$ROOT/calibration/bg3M/R2.fastq.gz" \
    --exact-fasta "$B/viral.fa" --families "$ROOT/calibration/families.tsv" --transcripts-fasta "$B/cdna.fa" \
    --library-strand forward --per-family 3 --levels 1000 --cells-per-condition 20 \
    --error-rate "$DIV" --seed 20261102 --n-background 3000000
  IN=plant/planted
  ln -s R1.fastq.gz $IN/CAL08_R1.fastq.gz; ln -s R2.fastq.gz $IN/CAL08_R2.fastq.gz
fi
python -m viralscan.menu run -o run --r1 "$IN/CAL08_R1.fastq.gz" --r2 "$IN/CAL08_R2.fastq.gz" \
  -i "$B/panel.idx" -t "$B/panel.t2g" --gtf "$B/viral_panel.gtf" -x 10xv3 --strand forward \
  -c "${SLURM_CPUS_PER_TASK:-8}" --cell-calling emptydrops --anellovirus-gene-ids --yes --verbose
test -s run/CAL08/results/viral_summary.tsv
echo DONE "$SET"
