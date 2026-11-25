#!/usr/bin/env bash
# DSR-03 read validation of the off-target HPV16 GSE189670 calls (round 2026-11-02): one dsr02_validate_call.py per array row.
# sbatch --array=0-7%4 -J r1102_dsr02 --cpus-per-task=8 --mem=32G --time=12:00:00 this
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/logs/%x_%A_%a.log
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
CODE=$M/ViralScan/.claude/worktrees/pin-dsr0304
RUNS=$RP/data/runs/round_2026-11-02/hpv16
# library arm virus-label slug
CALLS=(
  "SRR19537341 combined_off|Human papillomavirus 29|hpv29"
  "SRR19537339 combined_off|Human papillomavirus 29|hpv29"
  "SRR19537339 combined_off|Human papillomavirus 118|hpv118"
  "SRR19537341 combined_off|Human herpesvirus 8|hhv8"
  "SRR19537341 twostep|Human papillomavirus 77|hpv77"
  "SRR19537339 twostep|Human papillomavirus 77|hpv77"
  "SRR19537341 twostep|Cercopithecine herpesvirus|cercopithecine"
  "SRR19537339 twostep|Cercopithecine herpesvirus|cercopithecine"
)
IFS='|' read -r LA VIRUS SLUG <<< "${CALLS[$SLURM_ARRAY_TASK_ID]}"
read -r LIB ARM <<< "$LA"
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
OUT=$RUNS/$LIB/evidence/${ARM}__$SLUG
[ ! -e "$OUT" ] || { echo "exists, refusing: $OUT" >&2; exit 4; }
python "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/.claude/worktrees/round-dsr0304/scripts/dsr02_validate_call.py" --run-dir "$RUNS/$LIB/$ARM/$LIB" --virus "$VIRUS" --out "$OUT" \
  --panel-fasta "$RP/data/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$RP/data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa" --cores "${SLURM_CPUS_PER_TASK:-8}"
