#!/usr/bin/env bash
# Purpose: download GSE184257 Set 3 (PRJNA763826) for the PROG-MIXED-VETO-01 held-out gate
#          (analysis/round_2026-11-02/prog_mixed_veto_prereg.md, user decision Q3, 2026-11-04).
# Run:     sbatch scripts/slurm_gse184257_set3_download.sh        # array over the 4 Set 3 runs
# Inputs:  ENA read_run report per SRR (URLs, MD5, bytes) [scripts/fetch_reference_strategy_fastqs.py]
# Outputs (in data/runs/work/gse184257_set3/raw/<GSM>/):
#   <SRR>_1.fastq.gz, <SRR>_2.fastq.gz   FASTQs, MD5-checked against ENA
#   source_urls.tsv                      ENA URL, MD5 and bytes per mate
#   sha256.tsv                           SHA-256 and bytes of each FASTQ (provenance pin)
#   DONE                                 written last; absent means the download is incomplete
#
#SBATCH -J gse184257_dl
#SBATCH --array=0-3
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=12:00:00
set -euo pipefail

M=/exports/archive/hg-funcgenom-research/mdmanurung
REPRO=$M/ViralScan-reproducibility
PY=$M/conda/envs/viralscan_test_full/bin/python
OUT=$REPRO/data/runs/work/gse184257_set3/raw

# GSM | SRR | condition (ENA sample_title)
ROWS=(
"GSM6249889|SRR19685943|Mock 3dpi Set 3"
"GSM6249890|SRR19685944|Mock 6dpi Set 3"
"GSM6249891|SRR19685945|KSHV 3dpi Set 3"
"GSM6249892|SRR19685946|KSHV 6dpi Set 3"
)
IFS='|' read -r GSM SRR CONDITION <<< "${ROWS[$SLURM_ARRAY_TASK_ID]}"
D=$OUT/$GSM
if [ -e "$D/DONE" ]; then echo "$GSM already done"; exit 0; fi

# download both mates, MD5-checked against ENA
"$PY" "$REPRO/scripts/fetch_reference_strategy_fastqs.py" --srr "$SRR" --out-dir "$D"

# pin content hashes, then mark the folder complete
{
  printf 'file\tbytes\tsha256\n'
  for f in "$D/${SRR}"_1.fastq.gz "$D/${SRR}"_2.fastq.gz; do
    printf '%s\t%s\t%s\n' "$(basename "$f")" "$(stat -c %s "$f")" "$(sha256sum "$f" | cut -d' ' -f1)"
  done
} > "$D/sha256.tsv.tmp"
mv "$D/sha256.tsv.tmp" "$D/sha256.tsv"
printf '%s\t%s\t%s\t%s\n' "$GSM" "$SRR" "$CONDITION" "$(date -Is)" > "$D/DONE"
echo "DONE $GSM $SRR"
