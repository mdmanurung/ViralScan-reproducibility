#!/usr/bin/env bash
# Round 2026-11-02, DSR-06 (GSE164690 HNSCC) and DSR-07 (E-MTAB-13687 tonsil atlas): one viralscan run per (library, arm).
# Same conventions as scripts/slurm_round_2026_11_02_dsr0304.sh: arms differ only by flags, -x and --strand
# come from the frozen round-1 chem JSON, reference cat42d, pinned code de55424 (clean), output <ds>/<lib>/<arm>.
# Usage: DS=hnscc_gse164690 LIB=SRR13419165 ARM=combined_off sbatch -J ... --cpus-per-task=4 --mem=32G --time=12:00:00 <this>
#SBATCH -o /exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02/logs/%x_%j.log
set -euo pipefail
: "${DS:?}" "${LIB:?}" "${ARM:?combined_off|combined_artefact|twostep}"
M=/exports/archive/hg-funcgenom-research/mdmanurung
RP=$M/ViralScan-reproducibility
W=$RP/data/runs/work
IN=$RP/data/inputs/benchmark_inputs/dsr_2026-10-05
CODE=$M/ViralScan/.claude/worktrees/pin-dsr0607
B=$RP/data/references/panel_builds/viral_ref_cat42d/build
VO=$RP/data/references/panel_builds/viral_ref_cat42d/build_virus_only
STAR_IDX=$RP/data/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b
CHEM=$W/dsr_round1/chem/$LIB.json
export PATH="$M/conda/envs/viralscan_test_full/bin:$M/conda/envs/R4_51/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
SHA=$(git -C "$CODE" describe --always --dirty)
case "$SHA" in *-dirty) echo "dirty pinned tree: $SHA" >&2; exit 2;; esac
# R1 = barcode read, R2 = cDNA read (frozen round-1 manifest orientation; ERR13027027 is swapped on purpose)
case "$DS/$LIB" in
  hnscc_gse164690/SRR13419165|hnscc_gse164690/SRR13418973)
    D=$IN/GSE164690/$LIB; R1=$D/${LIB}_2.fastq.gz; R2=$D/${LIB}_3.fastq.gz;;
  tonsil_atlas/ERR13027010)
    D=$IN/E-MTAB-13687/$LIB; R1=$D/${LIB}_1.fastq.gz; R2=$D/${LIB}_2.fastq.gz;;
  tonsil_atlas/ERR13027027)
    D=$IN/E-MTAB-13687/$LIB; R1=$D/${LIB}_2.fastq.gz; R2=$D/${LIB}_1.fastq.gz;;
  *) echo "unknown $DS/$LIB (ERR13027122 is n/a: HTO/ADT, not GEX)" >&2; exit 2;;
esac
for f in "$R1" "$R2" "$CHEM"; do [ -s "$f" ] || { echo "missing $f" >&2; exit 3; }; done
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
OUT=$RP/data/runs/round_2026-11-02/$DS/$LIB/${ARM_DIR:-$ARM}   # ARM_DIR: new dir name for a resubmission
META=$OUT.meta
[ ! -e "$OUT" ] && [ ! -e "$META" ] || { echo "run dir exists, refusing to reuse: $OUT" >&2; exit 4; }
mkdir -p "$META"
printf '%s\n' "$SHA" > "$META/code_sha.txt"; cp "$CHEM" "$META/check_chemistry.json"
ARGS=(-o "$OUT" --r1 "$R1" --r2 "$R2" "${IDX[@]}" --gtf "$B/viral_panel.gtf" -x "$TECH" -c "${SLURM_CPUS_PER_TASK:-4}"
      --cell-calling emptydrops --anellovirus-gene-ids --yes --verbose)
[ "$STRAND" = NONE ] || ARGS+=(--strand "$STRAND")
printf '%s\n' "code $SHA $DS/$LIB arm=$ARM -x $TECH --strand $STRAND"
/usr/bin/time -v -o "$META/time.txt" python -m viralscan.menu run "${ARGS[@]}" "${EXTRA[@]}"
test -n "$(find "$OUT" -name viral_summary.tsv -size +0 -print -quit)"
printf '%s\n' "DONE $DS/$LIB $ARM"
