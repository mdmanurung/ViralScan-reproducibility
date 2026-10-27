#!/usr/bin/env bash
set -euo pipefail
run() { if [ "${DRY:-0}" = 1 ]; then echo "+ $*"; else "$@"; fi; }

[ -L "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work" ] && run rm "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work"  # compat link only (rm of a symlink, not of data)
[ -e "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work" ] || { echo "nothing at /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work" >&2; exit 1; }
run mv -n "/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/work" "/exports/archive/hg-funcgenom-research/mdmanurung/viralscan_work"
