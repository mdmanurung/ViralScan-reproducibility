#!/usr/bin/env bash
# COVMAP-01-RUN / REVIEW-C-RUN: pyGenomeTracks coverage maps on the real EBV STARsolo BAM (GSM4796271), package 13ea776.
#SBATCH -J covmap_ebv
#SBATCH -c 4
#SBATCH --mem=160G
#SBATCH -t 12:00:00
#SBATCH -p highmem
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work/star_hostvirus/logs/%x_%j.log
set -euo pipefail
export PATH=/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full/bin:$PATH
export PYTHONPATH=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work/star_hostvirus/code_cov_13ea776/src
python -I - <<PY
import sys; sys.path.insert(0, "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work/star_hostvirus/code_cov_13ea776/src")
from viralscan.evidence import plot_coverage_maps
w = plot_coverage_maps(
    {"raw": "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work/star_hostvirus/GSM4796271/Aligned.sortedByCoord.out.bam"},
    "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work/star_hostvirus/covmap_ebv_13ea776",
    ["/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/references/panel_builds/viral_ref_cat42d/build/viral_panel.gtf"],
    references=["VIRUS|NC_007605.1"],
)
print("\n".join(w))
PY
