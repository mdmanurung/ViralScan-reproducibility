#!/usr/bin/env bash
# RUN-01 / RUN-02 (round 2026-11-02): one job per (dataset, step). Env: DS=ebv|hhv6b, ARM=chem|combined_off|combined_artefact|twostep.
# Pinned package: de55424 (detached worktree). Inputs are only read. Outputs: $DATA/runs/round_2026-11-02/<virus>_<acc>/<ARM>/
# chem runs `viralscan check-chemistry` (1M-pair strand pilot); the arms read -x and --strand from its JSON.
#   DS=ebv ARM=chem sbatch -J r2611_ebv_chem --cpus-per-task=4 --mem=32G --time=02:00:00 scripts/round_2026_11_02_run0102.sh
#SBATCH -o slurm_%x_%j.log
set -euo pipefail
: "${DS:?ebv|hhv6b}" "${ARM:?chem|combined_off|combined_artefact|twostep}"
M=/exports/archive/hg-funcgenom-research/mdmanurung
DATA=$M/ViralScan-reproducibility/data
CODE=$M/ViralScan/.claude/worktrees/pin-run0102
B=$DATA/references/panel_builds/viral_ref_cat42d/build
VIRUS_ONLY=$DATA/references/panel_builds/viral_ref_cat42d/build_virus_only
STAR_IDX=$DATA/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b
case "$DS" in ebv) ACC=SRR12682296;; hhv6b) ACC=SRR20710641;; *) echo "bad DS" >&2; exit 2;; esac
IN=$DATA/inputs/benchmark_inputs/reference_strategy/$ACC
R1=$IN/${ACC}_1.fastq.gz; R2=$IN/${ACC}_2.fastq.gz
D=$DATA/runs/round_2026-11-02/${DS}_$ACC
META=$D/_meta/$ARM
export PATH="$M/conda/envs/viralscan_test_full/bin:$M/conda/envs/R4_51/bin:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
SHA=$(git -C "$CODE" describe --always --dirty)
case "$SHA" in *-dirty) printf '%s\n' "dirty pinned tree: $SHA" >&2; exit 2;; esac
case "$SHA" in *-gde55424) ;; *) printf '%s\n' "unexpected pin $SHA" >&2; exit 2;; esac
CORES=${SLURM_CPUS_PER_TASK:-4}
mkdir -p "$D/_meta"
[ ! -e "$META" ] || { printf '%s\n' "exists, not overwriting: $META" >&2; exit 3; }
mkdir -p "$META"; printf '%s\n' "$SHA" > "$META/code_sha.txt"
printf '%s\n' "code $SHA ds=$DS arm=$ARM job=${SLURM_JOB_ID:-none}"
if [ "$ARM" = chem ]; then
  # check-chemistry exits 1 when unresolved; keep the exit code in the log
  set +e
  python -m viralscan.menu check-chemistry --r1 "$R1" --r2 "$R2" -i "$B/panel.idx" -t "$B/panel.t2g" \
    -c "$CORES" --json "$D/_meta/chem.json" > "$META/check_chemistry.txt" 2>&1
  rc=$?; set -e
  printf '%s\n' "exit=$rc" >> "$META/check_chemistry.txt"; cat "$META/check_chemistry.txt"
  exit 0
fi
CHEM=$D/_meta/chem.json
read -r TECH STRAND < <(python - "$CHEM" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print((d.get("chemistry") or {}).get("chemistry") or "NONE", (d.get("strand_pilot") or {}).get("choice") or "NONE")
PY
)
[ "$TECH" != NONE ] || { printf '%s\n' "chemistry unresolved for $ACC" >&2; exit 3; }
case "$ARM" in
  combined_off)      IDX=(-i "$B/panel.idx" -t "$B/panel.t2g"); EXTRA=();;
  combined_artefact) IDX=(-i "$B/panel.idx" -t "$B/panel.t2g"); EXTRA=(--read-filter artefact);;
  twostep)           IDX=(-i "$VIRUS_ONLY/virus_panel.idx" -t "$VIRUS_ONLY/virus_panel.t2g")
                     EXTRA=(--host-filter starsolo --host-index "$STAR_IDX");;
  *) printf '%s\n' "unknown ARM $ARM" >&2; exit 2;;
esac
OUT=$D/$ARM
ARGS=(-o "$OUT" --r1 "$R1" --r2 "$R2" "${IDX[@]}" --gtf "$B/viral_panel.gtf" -x "$TECH" -c "$CORES"
      --cell-calling emptydrops --anellovirus-gene-ids --yes --verbose)
[ "$STRAND" = NONE ] || ARGS+=(--strand "$STRAND")
printf '%s\n' "python -m viralscan.menu run ${ARGS[*]} ${EXTRA[*]}" > "$META/command.txt"
/usr/bin/time -v -o "$META/time.txt" python -m viralscan.menu run "${ARGS[@]}" "${EXTRA[@]}"
test -s "$OUT/$ACC/results/viral_summary.tsv"
printf '%s\n' "DONE $DS $ARM"
