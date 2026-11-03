#!/usr/bin/env bash
# `viralscan rerun-programs` with package 5b419d4 (KSHV productive markers PAN/K4/K3/ORF52, induced_in_lytic flag)
# on every finished run of this round (not the round-2 dirs), into NEW dirs posthoc/programs_5b419d4/ (never overwritten).
#SBATCH -J kshv_prog2
#SBATCH --cpus-per-task=2
#SBATCH --mem=48G
#SBATCH --time=04:00:00
set -uo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
R=$M/ViralScan-reproducibility/data/runs
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$M/ViralScan/.claude/worktrees/pin-kshv-5b419d4/src" MPLBACKEND=Agg
for d in "$R"/round_2026-11-02/GSE*/GSM*/*/GSM*; do
  [ -s "$d/results/viral_summary.tsv" ] || continue
  O=$d/posthoc/programs_5b419d4
  [ ! -e "$O" ] || continue
  echo "== $d"; python -m viralscan.menu rerun-programs --run-dir "$d" -o "$O" || echo "FAILED $d"
done
