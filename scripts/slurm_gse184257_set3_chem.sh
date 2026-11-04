#!/usr/bin/env bash
# Purpose: check-chemistry on the GSE184257 Set 3 libraries before any viral output is read
#          (pre-registration analysis/round_2026-11-02/prog_mixed_veto_prereg.md, "Datasets" 1).
# Run:     sbatch --array=0-3 scripts/slurm_gse184257_set3_chem.sh
# Inputs:  $ROUND/manifest.tsv (gse, gsm, r1, r2); FASTQs under data/runs/work/gse184257_set3/raw/ (read only)
# Outputs: $ROUND/chem/<GSM>.json and .txt (the only source of -x / --strand for the runs)
#SBATCH -J gse184_chem
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
set -uo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
REPRO=$M/ViralScan-reproducibility
ROUND=${ROUND_DIR:-$REPRO/data/runs/round_2026-11-04_veto}
CODE=${CODE_DIR:-$REPRO/data/pkg_13ea776}
B=$REPRO/data/references/panel_builds/viral_ref_cat42d/build
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
IFS=$'\t' read -r GSE GSM R1 R2 < <(tail -n +2 "$ROUND/manifest.tsv" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
[ ! -e "$ROUND/chem/$GSM.json" ] || { echo "exists: $GSM" >&2; exit 5; }
echo "code $(git -C "$CODE" describe --always --dirty)  $GSE/$GSM"
python -m viralscan.menu check-chemistry -s1 "$R1" -s2 "$R2" -i "$B/panel.idx" -t "$B/panel.t2g" -c 4 \
  --json "$ROUND/chem/$GSM.json" 2>&1 | tee "$ROUND/chem/$GSM.txt"
echo "exit=${PIPESTATUS[0]}" | tee -a "$ROUND/chem/$GSM.txt"
