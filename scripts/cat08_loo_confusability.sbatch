#!/bin/bash
#SBATCH -J cat08_loo
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
# CAT-08 leave-fold-out confusability. Submit: sbatch -o <D>/logs/%x_%j.log scripts/cat08_loo_confusability.sbatch
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
ENVD=$M/conda/envs/viralscan_test_full
export PATH=$ENVD/bin:$PATH
export KALLISTO=$ENVD/lib/python3.11/site-packages/kb_python/bins/linux/kallisto/kallisto
export VIRAL_FA=$M/ViralScan-reproducibility/data/references/panel_builds/viral_ref_wp5/build_7e5a2ce/viral.fa
export CATALOG=$M/ViralScan/.claude/worktrees/pin-cat0840/src/viralscan/data/virus_catalog.tsv
export THREADS=$SLURM_CPUS_PER_TASK
python $M/ViralScan-reproducibility/.claude/worktrees/round-cat0840/scripts/cat08_loo_confusability.py $M/ViralScan-reproducibility/data/runs/round_2026-11-02/cat08_cat40/loo
echo DONE
