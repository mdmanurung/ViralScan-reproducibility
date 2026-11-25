#!/usr/bin/env bash
# `viralscan rerun-programs` (layer 2, latent vs productive) on every finished KSHV-round run that has none yet.
# Gene programmes were OFF in the runs (config gene_programs: false); this adds posthoc/programs/ only, no counts change.
#SBATCH -J kshv_prog
#SBATCH --cpus-per-task=2
#SBATCH --mem=32G
#SBATCH --time=04:00:00
set -uo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
ROUND=$M/ViralScan-reproducibility/data/runs/round_2026-11-02
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$M/ViralScan/.claude/worktrees/pin-kshv/src" MPLBACKEND=Agg
for d in "$ROUND"/GSE*/GSM*/*/GSM*; do
  [ -s "$d/results/viral_summary.tsv" ] || continue
  [ ! -e "$d/posthoc/programs/results/gene_program_summary.tsv" ] || continue
  echo "== $d"; python -m viralscan.menu rerun-programs --run-dir "$d" || echo "FAILED $d"
done
