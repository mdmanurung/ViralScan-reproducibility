#!/usr/bin/env bash
# Round 2026-11-02, HSV-1 SRR8315713 (Drop-seq): RUN-03 standard arm set + SCAUTOQC-01 gate.
# Arms differ only by flags. Common: cat42d, -x dropseq (SW-21 bypass), --strand forward (strand pilot),
# --cell-calling emptydrops. Geometry and strand come from dsr_round2/chem/SRR8315713.json.
#   combined_off       -i panel.idx
#   combined_artefact  -i panel.idx --read-filter artefact
#   twostep            -i virus_panel.idx --host-filter starsolo --host-index <STAR GRCh38-2024-A>
#   scautoqc_gate      -i panel.idx --scautoqc --umap   (SCAUTOQC-01 real-run gate)
# --tchem off: tchem names Drop-seq but has no kb technology for it, so --tchem auto aborts the run (jobs 25941198/99).
#   The chemistry is measured by check-chemistry (R1 20 bp, no on-list match, strand pilot), see meta/check_chemistry.json.
# Never deletes; refuses to reuse an existing arm directory.
#   ARM=combined_off sbatch -J r1102_off --cpus-per-task=4 --mem=32G --time=12:00:00 \
#       -o $D/runs/round_2026-11-02/hsv1_SRR8315713/logs/%x_%j.log scripts/slurm_round_2026-11-02_hsv1.sh
set -euo pipefail
: "${ARM:?combined_off|combined_artefact|twostep|scautoqc_gate}"
M=/exports/archive/hg-funcgenom-research/mdmanurung
D=$M/ViralScan-reproducibility/data
CODE=${CODE_DIR:-$M/ViralScan/.claude/worktrees/pin-hsv1}
B=$D/references/panel_builds/viral_ref_cat42d/build
VIRUS_ONLY=$D/references/panel_builds/viral_ref_cat42d/build_virus_only
STAR_IDX=$D/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b
IN=$D/inputs/benchmark_inputs/reference_strategy/SRR8315713
SAMPLE=SRR8315713
ARMDIR=$D/runs/round_2026-11-02/hsv1_$SAMPLE/$ARM${TAG:-}   # TAG=_r2 for a rerun in a fresh dir
export PATH="$M/conda/envs/viralscan_test_full/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
SHA=$(git -C "$CODE" describe --always --dirty)
case "$SHA" in *-dirty) echo "dirty pinned tree: $SHA" >&2; exit 2;; esac
[ "$(git -C "$CODE" rev-parse --short=7 HEAD)" = de55424 ] || { echo "not de55424" >&2; exit 2; }
EXTRA=()
case "$ARM" in
  combined_off|scautoqc_gate) IDX=(-i "$B/panel.idx" -t "$B/panel.t2g");;
  combined_artefact) IDX=(-i "$B/panel.idx" -t "$B/panel.t2g")
                     EXTRA=(--read-filter artefact);;
  twostep) IDX=(-i "$VIRUS_ONLY/virus_panel.idx" -t "$VIRUS_ONLY/virus_panel.t2g")
           EXTRA=(--host-filter starsolo --host-index "$STAR_IDX");;
  *) echo "unknown ARM $ARM" >&2; exit 2;;
esac
[ "$ARM" != scautoqc_gate ] || EXTRA=(--scautoqc --umap)
[ ! -e "$ARMDIR/out" ] || { echo "exists, not reusing: $ARMDIR/out" >&2; exit 3; }
mkdir -p "$ARMDIR/meta"
printf '%s\n' "$SHA" > "$ARMDIR/meta/code_sha.txt"
printf '%s\n' "${SLURM_JOB_ID:-nojob}" > "$ARMDIR/meta/jobid.txt"
cp "$D/runs/work/dsr_round2/chem/$SAMPLE.json" "$ARMDIR/meta/check_chemistry.json"
echo "code $SHA arm=$ARM -x dropseq --strand forward"
/usr/bin/time -v -o "$ARMDIR/meta/time.txt" python -m viralscan run \
  -o "$ARMDIR/out" --r1 "$IN/${SAMPLE}_1.fastq.gz" --r2 "$IN/${SAMPLE}_2.fastq.gz" \
  "${IDX[@]}" --gtf "$B/viral_panel.gtf" -x dropseq --strand forward -c "${SLURM_CPUS_PER_TASK:-4}" \
  --cell-calling emptydrops --tchem off --anellovirus-gene-ids --yes --verbose "${EXTRA[@]}"
find "$ARMDIR/out" -name viral_summary.tsv | grep -q .
echo "DONE $ARM $SHA"
