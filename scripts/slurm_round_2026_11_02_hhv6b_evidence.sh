#!/usr/bin/env bash
# Read validation of the EXPECTED HHV-6B call in SRR20710641 (round 2026-11-02, combined_off, package de55424).
# DSR-02 so far checked only off-target calls; this checks the target call itself (host vs virus per molecule).
#   sbatch scripts/slurm_round_2026_11_02_hhv6b_evidence.sh
#SBATCH -J r2611_hhv6b_evid
#SBATCH -p all
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/hhv6b_SRR20710641/logs/%x_%j.log
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
CODE=$M/ViralScan/.claude/worktrees/pin-dsr0304
RUN=$RP/data/runs/round_2026-11-02/hhv6b_SRR20710641
OUT=$RUN/evidence/combined_off__hhv6b
[ ! -e "$OUT" ] || { echo "exists, refusing: $OUT" >&2; exit 4; }
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
python "$RP/.claude/worktrees/round-run0102/scripts/dsr02_validate_call.py" \
  --run-dir "$RUN/combined_off/SRR20710641" --virus "Human herpesvirus 6b" --out "$OUT" \
  --panel-fasta "$RP/data/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$RP/data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa" \
  --cores "${SLURM_CPUS_PER_TASK:-8}"
