# source this from the repo root: points experiments at the package checkout (VIRALSCAN_PKG) pinned in provenance/PACKAGE_BASE_SHA
export VIRALSCAN_PKG="${VIRALSCAN_PKG:-/exports/para-lipg-hpc/mdmanurung/ViralScan-pin2}"
export VIRALSCAN_DATA="${VIRALSCAN_DATA:-/exports/para-lipg-hpc/mdmanurung/ViralScan-data}"   # run dirs / references / large inputs (never in git)
export PYTHONPATH="$VIRALSCAN_PKG/src:${PYTHONPATH:-}"   # src only: the package root has its own scripts/ that would shadow ours
