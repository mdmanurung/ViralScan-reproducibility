# source this from the repo root: points experiments at the package checkout (VIRALSCAN_PKG) pinned in provenance/PACKAGE_BASE_SHA
export VIRALSCAN_PKG="${VIRALSCAN_PKG:-/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan}"
export PYTHONPATH="$VIRALSCAN_PKG/src:$VIRALSCAN_PKG:${PYTHONPATH:-}"
