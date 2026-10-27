#!/usr/bin/env bash
# Rehearse a move batch in a scratch shared clone; never writes to the package repo.
# usage: rehearse.sh <batch> [git-ref=HEAD]
#   batch "baseline"  -> remove nothing, record results (re-run on merged main for step 1)
#   other batches     -> remove files listed in batches/<batch>.rm (explicit FILE paths, one per line;
#                        directories and missing paths are errors), run batches/<batch>.fix.sh in the tree
#                        if present, run pytest, diff against rehearsal/baseline/results.tsv.
# Exit 0 only when nothing is unexplained (see rehearse_diff.py).
set -euo pipefail
SPLIT=/exports/para-lipg-hpc/mdmanurung/viralscan-split
REPO=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan
E=/exports/archive/hg-funcgenom-research/mdmanurung/conda/envs/viralscan_test_full
PY=$SPLIT/env/bin/python
batch=${1:?usage: rehearse.sh <batch> [git-ref]}; ref=${2:-HEAD}
W=$SPLIT/rehearsal/$batch
rm -rf "$W"; mkdir -p "$W/tree"
sha=$(git -C "$REPO" rev-parse "$ref")
rmdir "$W/tree"
# shared clone: reads $REPO objects via alternates (never writes to $REPO), keeps history for git-based tests
git clone -q --shared --no-checkout "$REPO" "$W/tree"
git -C "$W/tree" checkout -q --detach "$sha"
echo "$ref $sha" > "$W/ref.txt"
cd "$W/tree"
# stacked batches: batches/<batch>.needs lists earlier batches applied first (their .rm and .fix.sh)
chain=""
[ -f "$SPLIT/audit/batches/$batch.needs" ] && chain=$(grep -v '^#' "$SPLIT/audit/batches/$batch.needs" | tr '\n' ' ')
for b in $chain $batch; do
  RM=$SPLIT/audit/batches/$b.rm
  if [ -f "$RM" ]; then
    while IFS= read -r f; do
      case "$f" in ''|\#*) continue;; esac
      [ -d "$f" ] && { echo "REFUSED: $f is a directory; list explicit files (R4)" >&2; exit 2; }
      [ -e "$f" ] || { echo "MISSING in $ref (batch $b): $f" >&2; exit 2; }
      git rm -q -f -- "$f"
    done < "$RM"
  fi
  FIX=$SPLIT/audit/batches/$b.fix.sh
  [ -f "$FIX" ] && { echo "applying $FIX"; bash "$FIX" || { echo "FIX FAILED: $FIX" >&2; exit 3; }; }
done
[ -n "${NOTEST:-}" ] && { echo "prepared $W/tree (NOTEST set)"; exit 0; }
ls tests/*.py tests/*/test_*.py 2>/dev/null | sort > "$W/files.txt"
n=$(( ($(wc -l < "$W/files.txt") + 2) / 3 )); split -l "$n" -d "$W/files.txt" "$W/chunk_"
for c in "$W"/chunk_??; do
  b=$(basename "$c")
  # shellcheck disable=SC2046
  PATH=$E/bin:$PATH PYTHONPATH=src timeout 900 python -m pytest $(cat "$c") -q -p no:cacheprovider \
    --continue-on-collection-errors --junitxml="$W/$b.xml" > "$W/$b.log" 2>&1 || true
  echo "$b: $(tail -1 "$W/$b.log")"
done
$PY "$SPLIT/audit/rehearse_diff.py" "$batch"
