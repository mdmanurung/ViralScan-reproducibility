#!/usr/bin/env bash
# Round 2026-11-04 target verdicts: `viralscan evidence --splice --host-gtf` on the EXPECTED virus of one library,
# row N of analysis/round_2026-11-04/target_verdict_calls.tsv (package 13ea776 worktree; main ed7da79 has identical evidence code).
# Output: data/runs/round_2026-11-04_target_verdicts/<dataset>/<sample>/evidence_splice/ (fresh; refuses an existing one).
#   sbatch --array=0-3,5-7%4 --mem=64G scripts/slurm_round_2026-11-04_target_verdict.sh
#   row 4 (GSM5725696) runs on the seeded subset: submit it with --dependency=afterok:<subset job> --array=4 --mem=32G
#SBATCH -J r1104_tverdict
#SBATCH -p all
#SBATCH --cpus-per-task=8
#SBATCH --time=12:00:00
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-04_target_verdicts/logs/%x_%A_%a.log
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
REPRO=$RP/.claude/worktrees/round-target-verdicts   # fixed path: sbatch runs a spool copy of this script
CODE=$RP/data/pkg_13ea776
RUNS=$RP/data/runs
EVHOME=/exports/archive/hg-funcgenom-research/evonk/old/intern/human_reference/refdata-gex-GRCh38-2024-A
CALLS=$REPRO/analysis/round_2026-11-04/target_verdict_calls.tsv
ROW=$SLURM_ARRAY_TASK_ID
IFS=$'\t' read -r _ DATASET SAMPLE RUN_DIR VIRUS _ < <(awk -F'\t' -v r="$ROW" 'NR>1 && $1==r' "$CALLS")
OUT=$RUNS/round_2026-11-04_target_verdicts/$DATASET/$SAMPLE/evidence_splice
[ ! -e "$OUT" ] || { echo "exists, refusing: $OUT" >&2; exit 4; }
mkdir -p "$(dirname "$OUT")"
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
echo "package $(git -C "$CODE" rev-parse HEAD) row=$ROW $DATASET/$SAMPLE virus=$VIRUS run=$RUNS/$RUN_DIR"
python "$REPRO/scripts/dsr02_validate_call.py" --run-dir "$RUNS/$RUN_DIR" --virus "$VIRUS" --out "$OUT" \
  --panel-fasta "$RP/data/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$EVHOME/fasta/genome.fa" --host-gtf "$EVHOME/genes/genes.gtf" \
  --splice --cores "${SLURM_CPUS_PER_TASK:-8}"
ls "$OUT"
