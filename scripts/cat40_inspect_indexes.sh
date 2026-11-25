#!/usr/bin/env bash
# CAT-40: kallisto inspect on the shipped (WP5) and earlier panel indexes. Read-only on indexes.
# Run: PKG=<package worktree> ENV=<conda env> scripts/cat40_inspect_indexes.sh <out_dir>   (out_dir must not exist)
set -euo pipefail
OUT=$1; mkdir "$OUT"
B=${REPRO:-/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility}/data/references/panel_builds
KALLISTO=$ENV/lib/python3.11/site-packages/kb_python/bins/linux/kallisto/kallisto  # kb's own binary; conda kallisto aborts on kb indexes (REL-16)
for name in viral_ref_wp5/build_7e5a2ce viral_ref_wp5/build_7e5a2ce_hostdlist viral_ref_cat42d/build viral_ref_final/build; do
  tag=${name//\//__}
  "$KALLISTO" inspect "$B/$name/panel.idx" > "$OUT/$tag.inspect.txt" 2>&1 || true
  PYTHONPATH=$PKG/src $ENV/bin/python -m viralscan.reference_gates inspect --from-text "$OUT/$tag.inspect.txt" --out "$OUT/$tag.json"
  sha256sum "$B/$name/panel.idx" >> "$OUT/index_sha256.txt"
done
