#!/usr/bin/env bash
# Functional check of every ViralScan verb on one real library (package 3.0.0b1).
# Usage: functional_check_b1.sh ID R1 R2 VIRUS TECH STRAND OUTROOT
#   TECH/STRAND are the values the 2026-11-02 repro runs used; they are only
#   the fallback when `run --kb-params auto` refuses (its advice is recorded).
# Every step runs even if an earlier one failed; steps.tsv records exit codes.
set -u
ID=$1; R1=$2; R2=$3; VIRUS=$4; TECH=$5; STRAND=$6; OUTROOT=$7
REPRO=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility
REF=$REPRO/data/references/panel_builds/viral_ref_cat42d/build
HOSTREF=/exports/archive/hg-funcgenom-research/evonk/old/intern/human_reference/refdata-gex-GRCh38-2024-A
K2=$REPRO/data/references/kraken2_db/k2_viral_20260626
CORES=${SLURM_CPUS_PER_TASK:-8}
VS="python -m viralscan"
D=$OUTROOT/$ID
mkdir -p "$D"
STEPS=$D/steps.tsv
printf 'step\texit\tseconds\n' > "$STEPS"
step() {  # step NAME CMD...
  local name=$1; shift
  local t0=$SECONDS
  echo "=== $name: $*" >> "$D/commands.log"
  "$@" > "$D/$name.log" 2>&1
  local rc=$?
  printf '%s\t%s\t%s\n' "$name" "$rc" "$((SECONDS - t0))" >> "$STEPS"
  return $rc
}

step check_env $VS check env --profile full
step check_chemistry $VS check chemistry --r1 "$R1" --r2 "$R2" -i "$REF/panel.idx" -t "$REF/panel.t2g" --json "$D/chemistry.json"

RUN=$D/run
if ! step run_auto $VS run -o "$RUN" -i "$REF/panel.idx" -t "$REF/panel.t2g" --r1 "$R1" --r2 "$R2" --kb-params auto -c "$CORES" --yes; then
  rm -rf "$RUN"
  step run_inherited $VS run -o "$RUN" -i "$REF/panel.idx" -t "$REF/panel.t2g" --r1 "$R1" --r2 "$R2" -x "$TECH" --strand "$STRAND" -c "$CORES" --yes
fi

step check_run $VS check run --run-dir "$RUN"
step status $VS status --run-dir "$RUN"
step open_run python - "$RUN" <<'PY'
import sys
from viralscan import open_run
r = open_run(sys.argv[1])
s, c, core = r.summary(), r.cells(), r.summary(core=True)
a = r.adata()
print("summary", s.shape, "core", core.shape, "cells", c.shape, "adata", a.shape)
print(core.to_string(max_rows=20))
PY

EV=$D/evidence
step evidence $VS evidence --run-dir "$RUN" -o "$EV" --virus "$VIRUS" --viral-fasta "$REF/viral.fa" \
  --host-fasta "$HOSTREF/fasta/genome.fa" --host-gtf "$HOSTREF/genes/genes.gtf" --splice --html --cell-tags --cores "$CORES"
TARGET=$(samtools idxstats "$EV/competitive_reads.umi_dedup.bam" 2>/dev/null | awk -F'\t' '$1 ~ /^VIRUS\|/' | sort -t$'\t' -k3,3nr | head -1 | cut -f1)
echo "coverage-map target: $TARGET" >> "$D/commands.log"
step evidence_plot_cov $VS evidence-plot --coverage-map --evidence-dir "$EV" --target "$TARGET" -o "$D/evidence_plot"

step rerun_multimap $VS rerun multimap --run-dir "$RUN" -o "$D/posthoc_rerun_multimap" --multimap-method em --cores "$CORES"
step rerun_programs $VS rerun programs --run-dir "$RUN" -o "$D/posthoc_rerun_programs"
ADATA=$(ls "$RUN"/*/kb-python/counts_unfiltered/adata.h5ad 2>/dev/null | head -1)
step rerun_hostresponse $VS rerun hostresponse --run-dir "$RUN" --output "$D/posthoc_hostresponse" --host-h5ad "$ADATA"
step discover $VS discover run --run-dir "$RUN" -o "$D/posthoc_discover" --kraken2-db "$K2" --cores "$CORES"

echo "done $ID" >> "$D/commands.log"
cat "$STEPS"
