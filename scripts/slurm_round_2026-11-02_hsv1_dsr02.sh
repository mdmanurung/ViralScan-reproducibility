#!/usr/bin/env bash
# DSR-02 read validation of the non-HSV-1 calls with >= 3 molecules, HSV-1 round 2026-11-02 (arms *_r2, package de55424).
# 3 viruses x 3 arms, minus HPV29 in the two arms where it is absent = 7 calls (array 0-6).
#   sbatch --array=0-6 --cpus-per-task=8 --mem=48G --time=12:00:00 -o $D/runs/round_2026-11-02/hsv1_SRR8315713/logs/%x_%A_%a.log scripts/slurm_round_2026-11-02_hsv1_dsr02.sh
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
D=$M/ViralScan-reproducibility/data
R=$D/runs/round_2026-11-02/hsv1_SRR8315713
CODE=$M/ViralScan/.claude/worktrees/pin-hsv1
REPRO=$M/ViralScan-reproducibility/.claude/worktrees/round-hsv1   # not $0: sbatch runs a spool copy
CALLS=("combined_off_r2|Cercopithecine herpesvirus" "combined_off_r2|Human herpesvirus 2"
       "combined_artefact_r2|Cercopithecine herpesvirus" "combined_artefact_r2|Human herpesvirus 2"
       "twostep_r2|Cercopithecine herpesvirus" "twostep_r2|Human herpesvirus 2" "twostep_r2|Human papillomavirus 29")
ARM=${CALLS[$SLURM_ARRAY_TASK_ID]%%|*}; VIRUS=${CALLS[$SLURM_ARRAY_TASK_ID]#*|}
SLUG=$(printf '%s' "$VIRUS" | tr -c 'A-Za-z0-9' _)
OUT=$R/dsr02_r2/${ARM}__$SLUG
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
[ ! -e "$OUT" ] || { echo "exists, not reusing: $OUT" >&2; exit 3; }
mkdir -p "$R/dsr02_r2"
python "$REPRO/scripts/dsr02_validate_call.py" --run-dir "$R/$ARM/out/SRR8315713" --virus "$VIRUS" --out "$OUT" \
  --panel-fasta "$D/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$D/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa" --cores "${SLURM_CPUS_PER_TASK:-8}"
