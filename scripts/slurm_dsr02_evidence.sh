#!/usr/bin/env bash
# DSR-02: read-level check of one (run, virus) call with scripts/dsr02_validate_call.py
# (`viralscan evidence`: exact CB+UMI read replay, competitive alignment vs GRCh38 + panel, alignment QC,
# BLAST, interpretation flags; then per-read verdicts with a repeat class).
#
#   RUN_DIR=<sample run dir> VIRUS=<exact label or gene id> PANEL_FA=<viral fasta of that run's index> \
#   OUT=<evidence dir> sbatch scripts/slurm_dsr02_evidence.sh
#
#SBATCH -J dsr02_evidence
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH -o slurm_%x_%j.log
SITE_ROOT=${VIRALSCAN_SITE_ROOT:?set VIRALSCAN_SITE_ROOT to the site work root}

set -euo pipefail
: "${RUN_DIR:?}" "${VIRUS:?}" "${PANEL_FA:?}" "${OUT:?}"
CODE=${CODE:-$SITE_ROOT/vs_pinned/4346dc8}
ENV=$SITE_ROOT/conda/envs/viralscan_test_full
HOST=${HOST_FA:-${VIRALSCAN_REPRO_ROOT:-/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility}/data/references/grch38/refdata-gex-GRCh38-2024-A/genome.fa}  # copy, sha256 in data/metadata/host_reference_grch38/MANIFEST.tsv
export PATH="$ENV/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
echo "code_sha $(git -C "$CODE" rev-parse HEAD) virus=$VIRUS run=$RUN_DIR"
python "$CODE/scripts/dsr02_validate_call.py" --run-dir "$RUN_DIR" --virus "$VIRUS" --out "$OUT" \
  --panel-fasta "$PANEL_FA" --host-fasta "$HOST" --cores 8 --keep-intermediates
ls "$OUT"
