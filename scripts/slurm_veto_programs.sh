#!/usr/bin/env bash
# Purpose: `viralscan rerun-programs` under both mixed-veto rules on each run listed in $ROUND/gate_libs.tsv
#          (PLAN PROG-MIXED-VETO-01 held-out gate). Same package for both rules, so `any` and `betabinomial`
#          differ only in the veto. Never overwrites: a run dir already holding the output is skipped.
# Run:     sbatch --array=0-N scripts/slurm_veto_programs.sh        (N = rows of gate_libs.tsv minus 1)
# Inputs:  $ROUND/gate_libs.tsv (library, group, run_dir); completed run dirs (read only)
# Outputs: <run_dir>/posthoc/programs_veto_any/ and <run_dir>/posthoc/programs_veto_betabinomial/
#SBATCH -J veto_prog
#SBATCH --cpus-per-task=2
#SBATCH --mem=48G
#SBATCH --time=04:00:00
set -uo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
REPRO=$M/ViralScan-reproducibility
ROUND=${ROUND_DIR:-$REPRO/data/runs/round_2026-11-04_veto}
CODE=${CODE_DIR:-$REPRO/data/pkg_13ea776}
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
IFS=$'\t' read -r LIB GROUP RUN < <(tail -n +2 "$ROUND/gate_libs.tsv" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
echo "code $(git -C "$CODE" describe --always --dirty)  $LIB ($GROUP)  $RUN"
for RULE in any betabinomial; do
  O=$RUN/posthoc/programs_veto_$RULE
  [ ! -e "$O" ] || { echo "exists, skipped: $O"; continue; }
  python -m viralscan.menu rerun-programs --run-dir "$RUN" -o "$O" --programme-mixed-veto "$RULE" || echo "FAILED $RULE $LIB"
done
