#!/usr/bin/env bash
# One DSR-02 evidence row (submitted by slurm_kshv_dsr02_chain.sh); env CALLS, REPO, ROUND.
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
CODE=$M/ViralScan/.claude/worktrees/pin-kshv
HOST=/exports/archive/hg-funcgenom-research/evonk/old/intern/human_reference/refdata-gex-GRCh38-2024-A/fasta/genome.fa
PANEL=$M/ViralScan-reproducibility/data/references/panel_builds/viral_ref_cat42d/build/viral.fa
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
echo "code $(git -C "$CODE" describe --always --dirty) row=$SLURM_ARRAY_TASK_ID"
python "$REPO/scripts/dsr02_validate_call.py" --calls "$CALLS" --row "$SLURM_ARRAY_TASK_ID" \
  --panel-fasta "$PANEL" --host-fasta "$HOST" --cores "${SLURM_CPUS_PER_TASK:-8}"
