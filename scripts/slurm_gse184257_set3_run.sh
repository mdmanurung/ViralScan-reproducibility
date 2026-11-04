#!/usr/bin/env bash
# GSE184257 Set 3 held-out gate (PLAN PROG-MIXED-VETO-01): one viralscan run per (library, arm), package pkg_13ea776.
# Array index = data row of $CTRL/manifest.tsv (0-based); ARM from the environment:
#   combined_off      -i panel.idx
#   combined_artefact -i panel.idx --read-filter artefact
#   twostep           -i virus_panel.idx --host-filter starsolo --host-index <STAR GRCh38>
# -x/--strand come from the check-chemistry JSON in $ROUND/chem/. Output:
# $ROUND/<gse>/<gsm>/<arm>/ (never reused: exits if it exists), run metadata in $ROUND/<gse>/<gsm>/meta_<arm>/.
#   ARM=twostep sbatch --array=0-3 --cpus-per-task=4 --mem=64G --time=48:00:00 -J gse184_two -o $ROUND/logs/%x_%A_%a.log scripts/slurm_gse184257_set3_run.sh
#SBATCH -o slurm_%x_%j.log
set -euo pipefail
: "${ARM:?combined_off|combined_artefact|twostep}"
M=/exports/archive/hg-funcgenom-research/mdmanurung
REPRO=$M/ViralScan-reproducibility
ROUND=${ROUND_DIR:-$REPRO/data/runs/round_2026-11-04_veto}
CTRL=$ROUND   # manifest.tsv, chem/ (written by slurm_gse184257_set3_chem.sh)
CODE=${CODE_DIR:-$REPRO/data/pkg_13ea776}
B=$REPRO/data/references/panel_builds/viral_ref_cat42d/build
VO=$REPRO/data/references/panel_builds/viral_ref_cat42d/build_virus_only
STAR_IDX=$REPRO/data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
SHA=$(git -C "$CODE" describe --always --dirty)
case "$SHA" in *-dirty) echo "dirty pinned tree: $SHA" >&2; exit 2;; esac
IFS=$'\t' read -r GSE GSM R1 R2 < <(tail -n +2 "$CTRL/manifest.tsv" | sed -n "$((SLURM_ARRAY_TASK_ID + 1))p")
CHEM=$CTRL/chem/$GSM.json
[ -s "$CHEM" ] || { echo "no chemistry JSON for $GSM" >&2; exit 3; }
read -r TECH STRAND < <(python - "$CHEM" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(d["chemistry"]["chemistry"] or "NONE", (d.get("strand_pilot") or {}).get("choice") or "NONE")
PY
)
[ "$TECH" != NONE ] || { echo "chemistry unresolved for $GSM" >&2; exit 3; }
case "$ARM" in
  combined_off)      IDX=(-i "$B/panel.idx" -t "$B/panel.t2g"); EXTRA=();;
  combined_artefact) IDX=(-i "$B/panel.idx" -t "$B/panel.t2g"); EXTRA=(--read-filter artefact);;
  twostep)           IDX=(-i "$VO/virus_panel.idx" -t "$VO/virus_panel.t2g")
                     EXTRA=(--host-filter starsolo --host-index "$STAR_IDX");;
  *) echo "unknown ARM $ARM" >&2; exit 2;;
esac
ARMDIR=$ARM${ARM_SUFFIX:-}   # ARM_SUFFIX=_r2 for a rerun after OOM: a new dir, never the old one
OUT=$ROUND/$GSE/$GSM/$ARMDIR
META=$ROUND/$GSE/$GSM/meta_$ARMDIR
[ ! -e "$OUT" ] && [ ! -e "$META" ] || { echo "exists, not reusing: $OUT" >&2; exit 5; }
mkdir -p "$META"
printf '%s\n' "$SHA" > "$META/code_sha.txt"; cp "$CHEM" "$META/check_chemistry.json"
ARGS=(run -o "$OUT" --r1 "$R1" --r2 "$R2" "${IDX[@]}" --gtf "$B/viral_panel.gtf" -x "$TECH" -c "${SLURM_CPUS_PER_TASK:-4}"
      --cell-calling emptydrops --anellovirus-gene-ids --gene-programs --yes --verbose)
[ "$STRAND" = NONE ] || ARGS+=(--strand "$STRAND")
echo "code $SHA  $GSE/$GSM  arm=$ARM  -x $TECH --strand $STRAND  "
/usr/bin/time -v -o "$META/time.txt" python -m viralscan.menu "${ARGS[@]}" "${EXTRA[@]}"
test -s "$OUT/$GSM/results/viral_summary.tsv"
echo "DONE $GSE/$GSM $ARM"
