#!/usr/bin/env bash
# DSR-02 read validation of the off-target calls (>= 3 molecules) of the DSR-06/07 round 2026-11-02 runs.
#   sbatch --array=0-8%4 scripts/slurm_round_2026_11_02_dsr0607_dsr02.sh   (row N of the calls table, 0-based)
#SBATCH -J r1102_dsr02_0607
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/logs/%x_%A_%a.log
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
CODE=$M/ViralScan/.claude/worktrees/pin-dsr0607
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
python "$RP/.claude/worktrees/round-dsr0607/scripts/dsr02_validate_call.py" \
  --calls "$RP/.claude/worktrees/round-dsr0607/analysis/round_2026-11-02/dsr0607_offtarget_calls.tsv" --row "$SLURM_ARRAY_TASK_ID" \
  --panel-fasta "$RP/data/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$RP/data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa" \
  --out-root "$RP/data/runs/round_2026-11-02/_dsr0607/evidence" --cores "${SLURM_CPUS_PER_TASK:-8}"
