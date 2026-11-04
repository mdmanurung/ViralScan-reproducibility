#!/usr/bin/env bash
# Print job state and detected viral_summary.tsv rows for the DSR-06/07 round 2026-11-02 runs (read-only).
#   bash scripts/collect_round_2026_11_02_dsr0607.sh > analysis/round_2026-11-02/dsr0607_collect.tsv
RUN=/exports/archive/hg-funcgenom-research/mdmanurung/ViralScan-reproducibility/data/runs/round_2026-11-02
printf 'dataset\tlibrary\tarm\tstate\telapsed\tviral_summary\n'
for d in hnscc_gse164690/SRR13419165 hnscc_gse164690/SRR13418973 tonsil_atlas/ERR13027010 tonsil_atlas/ERR13027027; do
  for a in combined_off combined_artefact twostep; do
    o=$RUN/$d/$a; s=$(find "$o" -name viral_summary.tsv -size +0 2>/dev/null | head -1)
    t=$(grep -E 'Elapsed|Exit status' "$o.meta/time.txt" 2>/dev/null | sed 's/.*: //' | paste -sd' ')
    printf '%s\t%s\t%s\t%s\t%s\n' "${d%/*}" "${d#*/}" "$a" "${s:-none}" "${t:-none}"
    [ -z "$s" ] || awk -F'\t' 'NR==1{for(i=1;i<=NF;i++)h[$i]=i;next} $h["detected"]!="False" && $h["detected"]!="false"{print "  "$h["virus_name"]"\t"$h["viral_molecules_total_est"]}' "$s"
  done
done
