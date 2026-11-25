#!/usr/bin/env bash
# KSHV round 2026-11-02, DSR-02 step. Submit with --dependency=afterany:<the three run arrays>.
# 1. symlink view $ROUND/_kshv/view/runs/<gse>/<arm>/<gsm> -> the run dir (layout dsr02_enumerate_calls.py reads)
# 2. enumerate calls (>= 3 molecules, plus any anellovirus) into $ROUND/_kshv/evidence/calls.tsv
# 3. submit one evidence array (scripts/dsr02_validate_call.py, row N of calls.tsv), throttle %6
#SBATCH -J kshv_dsr02_chain
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:30:00
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
ROUND=${ROUND_DIR:-$M/ViralScan-reproducibility/data/runs/round_2026-11-02}
REPO=${REPO_DIR:-$M/ViralScan-reproducibility/.claude/worktrees/round-kshv}
CTRL=$ROUND/_kshv; V=$CTRL/view${TAG:-}/runs; EV=$CTRL/evidence${TAG:-}   # TAG=_r2 for the OOM reruns (arms *_r2)
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH"
tail -n +2 "$CTRL/manifest.tsv" | while IFS=$'\t' read -r GSE GSM _; do
  for ARM in ${ARMS:-combined_off combined_artefact twostep}; do
    [ -s "$ROUND/$GSE/$GSM/$ARM/$GSM/results/viral_summary.tsv" ] || { echo "n/a (no summary): $GSE/$GSM/$ARM"; continue; }
    mkdir -p "$V/$GSE/$ARM"; ln -sfn "$ROUND/$GSE/$GSM/$ARM" "$V/$GSE/$ARM/$GSM"
  done
done
mkdir -p "$EV"
python "$REPO/scripts/dsr02_enumerate_calls.py" "$CTRL/view${TAG:-}" > "$EV/calls.tsv"
N=$(( $(wc -l < "$EV/calls.tsv") - 1 ))
[ "$N" -gt 0 ] || { echo "no calls to validate"; exit 0; }
sbatch --parsable -J kshv_dsr02 --array=0-$((N - 1))%6 --cpus-per-task=8 --mem=24G --time=12:00:00 \
  -o "$CTRL/logs/%x_%A_%a.log" --export=ALL,CALLS="$EV/calls.tsv",REPO="$REPO",ROUND="$ROUND" \
  "$REPO/scripts/slurm_kshv_dsr02_row.sh"
