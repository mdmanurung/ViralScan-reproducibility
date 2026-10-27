#!/usr/bin/env bash
set -euo pipefail
run() { if [ "${DRY:-0}" = 1 ]; then echo "+ $*"; else "$@"; fi; }

[ -e "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work" ] || [ -L "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work" ] || { echo "missing source /exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work" >&2; exit 1; }
[ ! -e "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work" ] || { echo "destination exists /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work" >&2; exit 1; }
run mkdir -p "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs"
run mv -n "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work" "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work"
run ln -s "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work" "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work"
