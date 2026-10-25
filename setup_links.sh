#!/usr/bin/env bash
# Create the local, never-committed links that let moved scripts/tests find package files (they were written for one combined repo).
# Links are per entry (docs/, schemas/, config/ exist in both repos) and are recorded in .git/info/exclude, never in .gitignore.
set -euo pipefail
cd "$(dirname "$0")"
: "${VIRALSCAN_PKG:=/exports/para-lipg-hpc/mdmanurung/ViralScan-pin2}"
: "${VIRALSCAN_DATA:=/exports/para-lipg-hpc/mdmanurung/ViralScan-data}"   # large run data lives here, not in the package checkout
made=()
link() { # link <target> <path-in-repro>; skips a path that already exists as a real file/dir
  if [ -e "$2" ] && [ ! -L "$2" ]; then return 0; fi
  mkdir -p "$(dirname "$2")"; ln -sfn "$1" "$2"; made+=("/$2")
}
link "$VIRALSCAN_PKG/src" src
link "$VIRALSCAN_PKG/.github" .github
for f in "$VIRALSCAN_PKG"/docs/*; do link "$f" "docs/$(basename "$f")"; done
for f in "$VIRALSCAN_PKG"/src/viralscan/schemas/v3/*.json; do link "$f" "schemas/v3/$(basename "$f")"; done
link "$VIRALSCAN_PKG/config/public_ship_scope.json" config/public_ship_scope.json
[ -d "$VIRALSCAN_PKG/extras/vendor_sources" ] && link "$VIRALSCAN_PKG/extras/vendor_sources" extras/vendor_sources
# analysis/panel_expansion moved into the package (curation/panel after the split)
if [ -d "$VIRALSCAN_PKG/curation/panel" ]; then link "$VIRALSCAN_PKG/curation/panel" analysis/panel_expansion
elif [ -d "$VIRALSCAN_PKG/analysis/panel_expansion" ]; then link "$VIRALSCAN_PKG/analysis/panel_expansion" analysis/panel_expansion; fi
mkdir -p links
for d in benchmark_runs references starsolo_p22_6 starsolo_p22_6b ebv_latest_ref_2026-09-27 viral_panel_max_2026-09-28 cost01 logs sources; do
  [ -e "$VIRALSCAN_DATA/$d" ] && link "$VIRALSCAN_DATA/$d" "links/$d"
done
# old package commit ids recorded in ledgers/tests must resolve here: borrow the package object store (local only)
if [ -d "$VIRALSCAN_PKG/.git/objects" ]; then
  mkdir -p .git/objects/info; grep -qxF "$VIRALSCAN_PKG/.git/objects" .git/objects/info/alternates 2>/dev/null || echo "$VIRALSCAN_PKG/.git/objects" >> .git/objects/info/alternates
fi
# local-only ignore block
ex=.git/info/exclude; mkdir -p .git/info; touch "$ex"
sed -i '/^# setup_links.sh begin/,/^# setup_links.sh end/d' "$ex"
{ echo "# setup_links.sh begin"; printf '%s\n' "/links/" "${made[@]}"; echo "# setup_links.sh end"; } >> "$ex"
echo "links ready (VIRALSCAN_PKG=$VIRALSCAN_PKG): ${#made[@]} links"
