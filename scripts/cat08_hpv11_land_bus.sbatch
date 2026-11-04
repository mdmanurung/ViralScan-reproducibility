#!/bin/bash
#SBATCH -J cat08_hpv11_land
#SBATCH --cpus-per-task=2
#SBATCH --mem=48G
#SBATCH --time=02:00:00
# CAT-08 / HPV-11, landing step only: 25952512 built the index (12 h) but its pseudobam came out truncated.
# Reuse that index read-only; tile HPV-11 reads again and count landing targets from `kallisto bus` (new dir).
# Submit: sbatch -o <D>/logs/%x_%j.log scripts/cat08_hpv11_land_bus.sbatch
set -euo pipefail
M=/exports/archive/hg-funcgenom-research/mdmanurung
ENVD=$M/conda/envs/viralscan_test_full
export PATH=$ENVD/bin:$PATH
export KALLISTO=$ENVD/lib/python3.11/site-packages/kb_python/bins/linux/kallisto/kallisto
export BUSTOOLS=$ENVD/lib/python3.11/site-packages/kb_python/bins/linux/bustools/bustools
D=$M/ViralScan-reproducibility/data/runs/round_2026-11-02/cat08_cat40/hpv11_native_3d19cca_3d19cca_r2
python $M/ViralScan-reproducibility/.claude/worktrees/round-cat0840/scripts/cat08_tile_and_land.py \
  $HOME/.cache/viralscan/ncbi/NC_075235.1/NC_075235.1.fasta "$D/ref/index.idx" "$D/hpv11_reads_bus"
cat "$D/hpv11_reads_bus/summary.json"; echo; head -20 "$D/hpv11_reads_bus/landing_targets.tsv"
echo DONE
