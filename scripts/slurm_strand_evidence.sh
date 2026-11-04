#!/usr/bin/env bash
# Purpose: DEF-02 strand evidence. `viralscan evidence` post-hoc on completed combined_off runs, to collect
#          strand_qc.tsv (package EVID-03) per library. Does not choose the --strand default.
# Run:     sbatch --array=0-4 scripts/slurm_strand_evidence.sh
# Inputs:  $ROUND/strand_calls.tsv (library, chemistry, end, run_dir, virus); completed run dirs (read only);
#          panel viral.fa, GRCh38-2024-A genome.fa and genes.gtf
# Outputs: $ROUND/strand_evidence/<library>/ (fresh dir; strand_qc.tsv and the other evidence files)
#SBATCH -J strand_evid
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=24:00:00
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
REPRO=$M/ViralScan-reproducibility
ROUND=${ROUND_DIR:-$REPRO/data/runs/round_2026-11-04_veto}
CODE=${CODE_DIR:-$REPRO/data/pkg_13ea776}
HG=/exports/archive/hg-funcgenom-research/evonk/old/intern/human_reference/refdata-gex-GRCh38-2024-A
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
IFS=$'\t' read -r LIB CHEM END RUN VIRUS < <(tail -n +2 "$ROUND/strand_calls.tsv" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
OUT=$ROUND/strand_evidence/$LIB
[ ! -e "$OUT" ] || { echo "exists, not reusing: $OUT" >&2; exit 5; }
echo "code $(git -C "$CODE" describe --always --dirty)  $LIB ($CHEM, $END)  $VIRUS"
viralscan_cli() { python -m viralscan.menu "$@"; }
viralscan_cli evidence --run-dir "$RUN" --virus "$VIRUS" -o "$OUT" \
  --viral-fasta "$REPRO/data/references/panel_builds/viral_ref_cat42d/build/viral.fa" \
  --host-fasta "$HG/fasta/genome.fa" --host-gtf "$HG/genes/genes.gtf" --cores "${SLURM_CPUS_PER_TASK:-8}"
ls "$OUT"
