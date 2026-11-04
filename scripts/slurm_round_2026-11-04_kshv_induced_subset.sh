#!/usr/bin/env bash
# Seeded 20,000-molecule subset of GSM5725696 (KSHV induced, combined_off_r2) for the target verdict; see
# scripts/target_verdict_subset.py. The full library ran out of memory at 24G and 48G (MaxRSS 44.9 GB).
# Frame: the read lineage of the earlier full replay (job 25952505 row 8, 26,981,294 target reads).
#   sbatch scripts/slurm_round_2026-11-04_kshv_induced_subset.sh
#SBATCH -J r1104_kshv_sub
#SBATCH -p all
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=06:00:00
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-04_target_verdicts/logs/%x_%j.log
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
REPRO=$RP/.claude/worktrees/round-target-verdicts
RUNS=$RP/data/runs
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH"
python "$REPRO/scripts/target_verdict_subset.py" \
  --lineage "$RUNS/round_2026-11-02/_kshv/evidence_r2/_failed/GSE190558__GSM5725696__combined_off_r2__Human_herpesvirus_8.oom_25952505_8/read_lineage.tsv.gz" \
  --run-dir "$RUNS/round_2026-11-02/GSE190558/GSM5725696/combined_off_r2/GSM5725696" \
  --out "$RUNS/round_2026-11-04_target_verdicts/GSE190558/GSM5725696/subset" --n-molecules 20000 --seed 20261104
