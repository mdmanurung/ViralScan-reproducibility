#!/usr/bin/env bash
# HOST-05 (round 2026-11-02): one native `viralscan` run per array task = host-filter arm x input. Read-only on inputs.
#   0 ebv_planted_none     1 ebv_planted_pinned     2 ebv_planted_star-default
#   3 ebv_unplanted_none   4 ebv_unplanted_pinned   5 ebv_unplanted_star-default
#   6 hhv6b_none           7 hhv6b_pinned
# EBV planted/unplanted = the round-2c SENS-07 plant (50M real pairs + 7,770 exact planted reads), reused read-only.
# HHV-6B = the real SRR20710641 library (R1 150 nt: not plantable without a trim, so unplanted only).
# Every arm: virus-only kb index (build_virus_only), so arms differ ONLY by the host-filter flags.
#   sbatch -p all -J host05 -c 8 --mem=64G -t 12:00:00 --array=0-7 -o $D/logs/%x_%A_%a.log scripts/host05_run_arm.sh
# Refuses to touch an existing arm directory. DRY_RUN=1 prints the command.
set -euo pipefail
REPRO=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility
D=$REPRO/data
M=/exports/archive/hg-funcgenom-research/mdmanurung
CODE=${CODE_DIR:-$M/ViralScan/.claude/worktrees/pin-host05}
ENVBIN=$M/conda/envs/viralscan_test_full/bin
ROOT=$D/runs/round_2026-11-02/host05
B=$D/references/panel_builds/viral_ref_cat42d/build
VO=$D/references/panel_builds/viral_ref_cat42d/build_virus_only
HOST_IDX=$D/references/starsolo/ebv_latest_ref_2026-09-27/star_host_2.7.11b
P2C=$D/runs/work/dsr_round2c/runs/ebv/sens07/SRR12682296/plant
IN=$D/inputs/benchmark_inputs/reference_strategy
export PATH="$ENVBIN:$PATH" PYTHONPATH="$CODE/src" MPLBACKEND=Agg
SHA=$(git -C "$CODE" describe --always --dirty); case "$SHA" in *-dirty) echo "dirty pin: $SHA" >&2; exit 2;; esac

ARMS=(ebv_planted_none ebv_planted_pinned ebv_planted_star-default ebv_unplanted_none ebv_unplanted_pinned
      ebv_unplanted_star-default hhv6b_none hhv6b_pinned)
ARM=${ARMS[${SLURM_ARRAY_TASK_ID:?array index}]}
case "$ARM" in
  ebv_planted_*)   S=SRR12682296; R1=$P2C/planted/${S}_R1.fastq.gz;   R2=$P2C/planted/${S}_R2.fastq.gz;   CH=$D/runs/work/dsr_round2/chem/$S.json;;
  ebv_unplanted_*) S=SRR12682296; R1=$P2C/unplanted/${S}_R1.fastq.gz; R2=$P2C/unplanted/${S}_R2.fastq.gz; CH=$D/runs/work/dsr_round2/chem/$S.json;;
  hhv6b_*)         S=SRR20710641; R1=$IN/$S/${S}_1.fastq.gz;          R2=$IN/$S/${S}_2.fastq.gz;          CH=$D/runs/work/dsr_round2/chem/$S.json;;
esac
case "$ARM" in *_none) HF=();; *_pinned) HF=(--host-filter starsolo --host-index "$HOST_IDX" --host-filter-star-params pinned);;
               *_star-default) HF=(--host-filter starsolo --host-index "$HOST_IDX" --host-filter-star-params star-default);; esac
read -r TECH STRAND < <(python - "$CH" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(d["chemistry"]["chemistry"], (d.get("strand_pilot") or {}).get("choice") or "NONE")
PY
)
OUT=$ROOT/$ARM/run; META=$ROOT/$ARM/meta
[ ! -e "$ROOT/$ARM" ] || { echo "exists, refusing to reuse: $ROOT/$ARM" >&2; exit 3; }
ARGS=(-o "$OUT" -s1 "$R1" -s2 "$R2" -i "$VO/virus_panel.idx" -t "$VO/virus_panel.t2g" -gtf "$B/viral_panel.gtf"
      -x "$TECH" -c "${SLURM_CPUS_PER_TASK:-8}" --cell-calling emptydrops --anellovirus-gene-ids --yes --verbose)
[ "$STRAND" = NONE ] || ARGS+=(--strand "$STRAND")
echo "code $SHA arm=$ARM $S -x $TECH --strand $STRAND ${HF[*]:-no host filter}"
if [ -n "${DRY_RUN-}" ]; then printf '%q ' python -m viralscan.menu "${ARGS[@]}" ${HF[@]+"${HF[@]}"}; echo; exit 0; fi
mkdir -p "$META"; echo "$SHA" > "$META/code_sha.txt"; cp "$CH" "$META/check_chemistry.json"
printf '%s\n' "$R1" "$R2" > "$META/inputs.txt"
/usr/bin/time -v -o "$META/time.txt" python -m viralscan.menu "${ARGS[@]}" ${HF[@]+"${HF[@]}"}
test -s "$OUT/$S/results/viral_summary.tsv"
echo "DONE $ARM"
