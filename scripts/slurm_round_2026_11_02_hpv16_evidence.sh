#!/usr/bin/env bash
# Read validation of the EXPECTED HPV16 call in the infected raft SRR19537341 (round 2026-11-02, combined_off, de55424).
# DSR-02 checked only off-target calls; this checks the target call itself and gives a true-positive read pileup.
#   sbatch scripts/slurm_round_2026_11_02_hpv16_evidence.sh
#SBATCH -J r1102_hpv16_evid
#SBATCH -p all
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/logs/%x_%j.log
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
CODE=$M/ViralScan/.claude/worktrees/pin-dsr0304
RUN=$RP/data/runs/round_2026-11-02/hpv16/SRR19537341
OUT=$RUN/evidence/combined_off__hpv16
[ ! -e "$OUT" ] || { echo "exists, refusing: $OUT" >&2; exit 4; }
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
python "$RP/.claude/worktrees/round-dsr0304/scripts/dsr02_validate_call.py" \
  --run-dir "$RUN/combined_off/SRR19537341" --virus "Human papillomavirus 16" --out "$OUT" \
  --panel-fasta "$RP/data/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$RP/data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa" \
  --cores "${SLURM_CPUS_PER_TASK:-8}"
