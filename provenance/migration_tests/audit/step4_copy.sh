#!/usr/bin/env bash
# Copy the run-data dirs from the old checkout into the data root. Source is never modified or deleted.
set -u
O=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan
D=/exports/para-lipg-hpc/mdmanurung/ViralScan-data
L=/exports/para-lipg-hpc/mdmanurung/viralscan-split/audit/step4
mkdir -p "$D"
for d in sources logs cost01 starsolo_p22_6b references starsolo_p22_6 viral_panel_max_2026-09-28 ebv_latest_ref_2026-09-27 benchmark_runs; do
  echo "$(date +%T) start $d" >> $L/copy.log
  rsync -a --info=stats1 "$O/$d/" "$D/$d/" > $L/rsync_$d.log 2>&1; echo "$(date +%T) done $d rc=$?" >> $L/copy.log
done
echo ALLDONE >> $L/copy.log
