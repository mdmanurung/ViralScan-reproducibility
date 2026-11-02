#!/usr/bin/env bash
# Round 2026-11-02, DSR-03 (HPV16 GSE189670) and DSR-04 (COVID x213/x216): one viralscan run per (library, arm).
# Arms differ only by flags (same as scripts/slurm_dsr_rerun_array.sh): combined_off | combined_artefact | twostep.
# -x and --strand come from the frozen round-1 chem JSON; reference is cat42d. Pinned code: de55424 (clean).
# Usage: DS=hpv16 LIB=SRR19537341 ARM=combined_off sbatch -J ... --cpus-per-task=8 --mem=32G --time=12:00:00 <this>
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/logs/%x_%j.log
set -euo pipefail
: "${DS:?}" "${LIB:?}" "${ARM:?combined_off|combined_artefact|twostep}"
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
W=$RP/data/runs/work
CODE=$M/ViralScan/.claude/worktrees/pin-dsr0304
B=$RP/data/references/panel_builds/viral_ref_cat42d/build
VO=$RP/data/references/panel_builds/viral_ref_cat42d/build_virus_only
STAR_IDX=$RP/data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b
CHEM=$W/dsr_round1/chem/$LIB.json
export PATH="$M/conda/envs/viralscan_test_full/bin:$M/conda/envs/R4_51/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
SHA=$(git -C "$CODE" describe --always --dirty)
case "$SHA" in *-dirty) echo "dirty pinned tree: $SHA" >&2; exit 2;; esac
case "$DS/$LIB" in
  hpv16/SRR19537341|hpv16/SRR19537339)
    D=$W/hpv16_gse189670/fastq/$LIB; R1=$D/${LIB}_2.fastq.gz; R2=$D/${LIB}_3.fastq.gz; WL="";;
  covid/LUM-SJ-x213-g|covid/LUM-SJ-x216-g)
    D=$RP/data/runs/covid_viralscan/data/$LIB; R1=$D/${LIB}_merged_R1.fastq.gz; R2=$D/${LIB}_merged_R2.fastq.gz
    WL=$RP/data/runs/covid_viralscan/viralscan_ref/cellranger_whitelist.txt;;
  *) echo "unknown $DS/$LIB" >&2; exit 2;;
esac
for f in "$R1" "$R2" "$CHEM" ${WL:+"$WL"}; do [ -s "$f" ] || { echo "missing $f" >&2; exit 3; }; done
case "$ARM" in
  combined_off)      IDX=(-i "$B/panel.idx" -t "$B/panel.t2g"); EXTRA=();;
  combined_artefact) IDX=(-i "$B/panel.idx" -t "$B/panel.t2g"); EXTRA=(--read-filter artefact);;
  twostep)           IDX=(-i "$VO/virus_panel.idx" -t "$VO/virus_panel.t2g")
                     EXTRA=(--host-filter starsolo --host-index "$STAR_IDX");;
  *) echo "unknown ARM $ARM" >&2; exit 2;;
esac
read -r TECH STRAND < <(python -I - "$CHEM" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(d["chemistry"]["chemistry"] or "NONE", (d.get("strand_pilot") or {}).get("choice") or "NONE")
PY
)
[ "$TECH" != NONE ] || { echo "chemistry unresolved for $LIB" >&2; exit 3; }
OUT=$RP/data/runs/round_2026-11-02/$DS/$LIB/$ARM
META=$OUT.meta
[ ! -e "$OUT" ] && [ ! -e "$META" ] || { echo "run dir exists, refusing to reuse: $OUT" >&2; exit 4; }
mkdir -p "$META"
printf '%s\n' "$SHA" > "$META/code_sha.txt"; cp "$CHEM" "$META/check_chemistry.json"
ARGS=(-o "$OUT" --r1 "$R1" --r2 "$R2" "${IDX[@]}" --gtf "$B/viral_panel.gtf" -x "$TECH" -c "${SLURM_CPUS_PER_TASK:-4}"
      --cell-calling emptydrops --anellovirus-gene-ids --yes --verbose)
[ "$STRAND" = NONE ] || ARGS+=(--strand "$STRAND")
[ -z "$WL" ] || ARGS+=(-w "$WL")
printf '%s\n' "code $SHA $DS/$LIB arm=$ARM -x $TECH --strand $STRAND ${WL:+-w $WL}"
/usr/bin/time -v -o "$META/time.txt" python -m viralscan.menu run "${ARGS[@]}" "${EXTRA[@]}"
test -n "$(find "$OUT" -name viral_summary.tsv -size +0 -print -quit)"
printf '%s\n' "DONE $DS/$LIB $ARM"
