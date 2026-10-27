#!/usr/bin/env bash
# Parallel copy of benchmark_runs (second-level dirs, 12 rsync workers), then a full serial pass. Source is never modified.
set -u
O=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan/benchmark_runs
D=/exports/para-lipg-hpc/mdmanurung/ViralScan-data/benchmark_runs
L=/exports/para-lipg-hpc/mdmanurung/viralscan-split/audit/step4
mkdir -p "$D"
echo "$(date +%T) parallel start benchmark_runs" >> $L/copy.log
rsync -a --exclude='*/*/' "$O/" "$D/" 2>>$L/parallel.err   # files at depth 1-2 and the dir skeleton
(cd "$O" && find . -mindepth 2 -maxdepth 2 -type d | sed 's|^\./||') > $L/work_dirs.txt
export O D
xargs -a $L/work_dirs.txt -P 12 -I{} sh -c 'mkdir -p "$D/$(dirname "{}")"; rsync -a "$O/{}/" "$D/{}/" || echo "FAIL {}" >> '"$L"'/parallel.err'
echo "$(date +%T) workers done, final pass" >> $L/copy.log
rsync -a --info=stats1 "$O/" "$D/" > $L/rsync_benchmark_runs_final.log 2>&1; echo "$(date +%T) done benchmark_runs rc=$?" >> $L/copy.log
echo ALLDONE >> $L/copy.log
